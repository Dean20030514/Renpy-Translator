#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Placeholder protection & response checking."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


# 纯配置/UI 文件——不包含用户可见对话，翻译和漏翻统计均应跳过。
# 文件名匹配（不含路径），按项目需要可追加。
SKIP_FILES_FOR_TRANSLATION = {
    "define.rpy",
    "variables.rpy",
    "screens.rpy",
    "earlyoptions.rpy",
    "options.rpy",
}


# ============================================================
# 可配置的风格/质量检测关键词
# ============================================================

# 模型自我描述或多余解释的典型片段（可根据需要扩充）
MODEL_SPEAKING_PATTERNS = [
    "作为一个ai语言模型",
    "作为一名ai语言模型",
    "作为一个语言模型",
    "as an ai language model",
    "i am an ai language model",
    "i am a large language model",
    "as a language model",
]

# 占位符顺序校验用 pattern：从左到右依次匹配，用于提取有序占位符序列
# 格式 (regex, category_name)；匹配顺序影响提取结果（更具体的模式应靠前，如 {#id} 在通用 {tag} 前）
# 'tag' 模式同时覆盖样式标签（{color=...}/{b}/{i} 等）和控制标签（{w}/{p}/{nw}/{fast}/{cps=N}/{done} 等）
PLACEHOLDER_ORDER_PATTERNS = [
    (r'\[\w+\]', 'var'),
    (r'\{#[^}]+\}', 'menu_id'),
    (r'\{/?[a-zA-Z]+=?[^}]*\}', 'tag'),
    (r'%\([^)]+\)[sd]', 'fmt'),
]

# 预编译为单一正则，按"最早出现"的匹配从左到右收集（用于 _extract_placeholder_sequence）
_PLACEHOLDER_ORDER_REGEX = re.compile(
    '|'.join(f'({p})' for p, _ in PLACEHOLDER_ORDER_PATTERNS)
)


def _extract_placeholder_sequence(text: str) -> list[str]:
    """按从左到右顺序提取文本中的占位符序列，用于顺序一致性校验。

    使用 PLACEHOLDER_ORDER_PATTERNS 对应的联合正则，finditer 保证出现顺序。
    例如：'{color=#f00}[name]{/color}' -> ['{color=#f00}', '[name]', '{/color}']
    """
    out: list[str] = []
    for m in _PLACEHOLDER_ORDER_REGEX.finditer(text):
        # 取第一个非空分组即为当前匹配的占位符
        for g in m.groups():
            if g is not None:
                out.append(g)
                break
    return out


# 占位符保护：发 API 前将 [var]、{{#id}}、%(name)s 等替换为令牌，避免模型误翻；解析后还原
_PLACEHOLDER_PROTECT_PREFIX = "__RENPY_PH_"
_PLACEHOLDER_PROTECT_SUFFIX = "__"


def protect_placeholders(text: str) -> tuple[str, list[tuple[str, str]]]:
    """将文本中的占位符替换为唯一令牌，供发往 API 时使用。

    使用与 PLACEHOLDER_ORDER_PATTERNS 相同的模式提取占位符，按首次出现顺序去重后，
    对同一占位符的每一次出现均替换（全局替换）。例如 "[name] says hi to [name]" 中
    两个 [name] 都会变为 __RENPY_PH_0__。
    Returns:
        (替换后的文本, mapping: [(token, original), ...])
    """
    if not text.strip():
        return text, []
    matches: list[tuple[int, int, str]] = []
    for m in _PLACEHOLDER_ORDER_REGEX.finditer(text):
        for g in m.groups():
            if g is not None:
                matches.append((m.start(), m.end(), g))
                break
    if not matches:
        return text, []
    # 按首次出现顺序去重
    ordered: list[str] = []
    seen: set[str] = set()
    for _s, _e, matched in matches:
        if matched not in seen:
            seen.add(matched)
            ordered.append(matched)
    mapping = [
        (f"{_PLACEHOLDER_PROTECT_PREFIX}{i}{_PLACEHOLDER_PROTECT_SUFFIX}", orig)
        for i, orig in enumerate(ordered)
    ]
    orig_to_token = {orig: token for token, orig in mapping}
    # 从后往前替换，避免偏移变化
    replacements = [
        (s, e, orig_to_token[m]) for s, e, m in matches
    ]
    replacements.sort(key=lambda x: x[0], reverse=True)
    result = text
    for start, end, token in replacements:
        result = result[:start] + token + result[end:]
    return result, mapping


def restore_placeholders(text: str, mapping: list[tuple[str, str]]) -> str:
    """将保护阶段生成的令牌还原为原始占位符。

    Args:
        text: 可能包含 __RENPY_PH_0__ 等令牌的字符串
        mapping: protect_placeholders 返回的 [(token, original), ...]
    """
    if not mapping or not text:
        return text
    for token, original in mapping:
        text = text.replace(token, original)
    return text


def _count_translatable_lines_in_chunk(content: str) -> int:
    """启发式统计 chunk 中「可能需翻译」的行数。

    排除规则：
      - 注释行、空行
      - 不含双引号的行
      - 已包含中文字符的行（视为已翻译，不计入 expected）
    """
    count = 0
    for line in content.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if '"' not in s:
            continue
        if any("\u4e00" <= c <= "\u9fff" for c in s):
            continue
        count += 1
    return count


def check_response_chunk(chunk_content: str, translations: list[dict]) -> list[str]:
    """Chunk 级 ResponseChecker：API 返回条数与 chunk 内可翻译行数是否一致。

    Returns:
        警告信息列表；若条数不一致则包含一条 [CHECK] 级警告及差值说明。
    """
    warnings: list[str] = []
    expected = _count_translatable_lines_in_chunk(chunk_content)
    actual = len(translations)
    if expected != actual:
        delta = actual - expected
        warnings.append(
            f"chunk 条数不一致: 预期约 {expected} 条（按含引号行估算）, 实际返回 {actual} 条, 差值 {delta:+d}"
        )
    return warnings


def check_response_item(item: dict, line_offset: int = 0) -> list[str]:
    """轻量 ResponseChecker：对单条 API 返回的翻译做本地校验，不调 API。

    检查：原文非空时译文非空、占位符集合一致、必要字段存在。
    任一不通过则返回非空列表，调用方应丢弃该条（不写入译文，保留原文计漏翻）。
    Returns:
        警告信息列表，空表示通过。
    """
    warnings: list[str] = []
    line = item.get("line", 0) or 0
    if line_offset:
        line = line + line_offset
    original = (item.get("original") or "").strip()
    zh = (item.get("zh") or "").strip()

    if not original:
        warnings.append(f"行 {line}: original 为空")
        return warnings
    # 原文非空但译文为空 -> 丢弃该条，计漏翻
    if not zh:
        warnings.append(f"行 {line}: 译文为空")
        return warnings
    orig_placeholders = set(_extract_placeholder_sequence(original))
    zh_placeholders = set(_extract_placeholder_sequence(zh))
    if orig_placeholders != zh_placeholders:
        missing = orig_placeholders - zh_placeholders
        extra = zh_placeholders - orig_placeholders
        parts = []
        if missing:
            parts.append(f"译文缺少占位符 {missing}")
        if extra:
            parts.append(f"译文多出占位符 {extra}")
        warnings.append(f"行 {line}: 占位符与原文不一致 — {'; '.join(parts)}")
    return warnings
