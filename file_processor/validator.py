#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Post-translation validation."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Optional

from file_processor.checker import (
    _extract_placeholder_sequence,
    MODEL_SPEAKING_PATTERNS,
    PLACEHOLDER_ORDER_PATTERNS,
)
from file_processor.patcher import (
    _count_unescaped_quote,
    _extract_first_quoted_text,
    _strip_double_quoted_segments,
)

logger = logging.getLogger(__name__)


def _looks_untranslated_dialogue(text: str) -> bool:
    """启发式判断文本是否像未翻译英文对话。"""
    if len(text) < 20:
        return False
    if any(token in text for token in ('/', '\\', '.png', '.jpg', '.webp', '.ttf', '#')):
        return False
    ascii_letters = sum(1 for c in text if ('a' <= c.lower() <= 'z'))
    cn_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    return cn_chars == 0 and ascii_letters >= 12


def validate_translation(
    original_content: str,
    translated_content: str,
    filename: str = "",
    glossary_terms: Optional[dict] = None,
    glossary_locked: Optional[set[str]] = None,
    glossary_no_translate: Optional[set[str]] = None,
    len_ratio_lower: float = 0.3,
    len_ratio_upper: float = 2.5,
) -> list[dict]:
    """全面校验翻译后的文件（规则化质量检查）

    Args:
        original_content: 原始文件内容
        translated_content: 翻译后文件内容
        filename: 文件名（用于报告）

    Returns:
        [{"level": "error"|"warning", "line": N, "message": "..."}]
    """
    # 规则编码约定（与 AiNiee TranslationCheckPlugin 风格对齐）：
    # - 结构/语法类：E1xx
    # - 占位符/标签/变量：E2xx / W2xx
    # - 换行与排版：E3xx / W3xx
    # - 术语与漏翻：W4xx
    issues = []
    orig_lines = original_content.split('\n')
    trans_lines = translated_content.split('\n')

    # 1. 行数必须一致
    if len(orig_lines) != len(trans_lines):
        issues.append({
            "level": "error",
            "code": "E100_LINE_COUNT_MISMATCH",
            "line": 0,
            "message": f"行数不一致: 原 {len(orig_lines)} 行, 译 {len(trans_lines)} 行"
        })
        return issues  # 行数不一致，后续检查无意义

    for i, (orig, trans) in enumerate(zip(orig_lines, trans_lines), 1):
        # 2. 缩进必须一致
        orig_indent = len(orig) - len(orig.lstrip())
        trans_indent = len(trans) - len(trans.lstrip())
        if orig_indent != trans_indent:
            issues.append({
                "level": "error",
                "code": "E110_INDENT_CHANGED",
                "line": i,
                "message": f"缩进被改变: 原 {orig_indent} 空格, 译 {trans_indent} 空格"
            })

        # 3. 如果原行没有引号字符串，翻译后也不应改变
        if '"' not in orig and "'" not in orig:
            if orig != trans:
                issues.append({
                    "level": "error",
                    "code": "E120_NON_STRING_MODIFIED",
                    "line": i,
                    "message": f"非字符串行被修改: \"{orig.strip()[:60]}\" -> \"{trans.strip()[:60]}\""
                })

        # 3.1 引号结构必须稳定，避免出现未闭合/多余引号导致脚本解析失败
        if '"' in orig or '"' in trans:
            oq = _count_unescaped_quote(orig, '"')
            tq = _count_unescaped_quote(trans, '"')
            if oq != tq:
                issues.append({
                    "level": "error",
                    "code": "E130_DQUOTE_MISMATCH",
                    "line": i,
                    "message": f"双引号结构变化: 原 {oq}, 译 {tq}"
                })

        # 单引号检查仅针对"代码层单引号字符串"，忽略双引号对话内部的 apostrophe（如 don't）
        orig_outside_dq = _strip_double_quoted_segments(orig)
        trans_outside_dq = _strip_double_quoted_segments(trans)
        has_sq_literal = (
            re.search(r"'[^'\\]*(?:\\.[^'\\]*)*'", orig_outside_dq) is not None
            or re.search(r"'[^'\\]*(?:\\.[^'\\]*)*'", trans_outside_dq) is not None
        )
        if has_sq_literal:
            oq = _count_unescaped_quote(orig_outside_dq, "'")
            tq = _count_unescaped_quote(trans_outside_dq, "'")
            if oq != tq:
                issues.append({
                    "level": "error",
                    "code": "E131_SQUOTE_MISMATCH",
                    "line": i,
                    "message": f"单引号结构变化: 原 {oq}, 译 {tq}"
                })

        # 4. 检查 label/screen/jump/call 关键字行是否被修改
        stripped = orig.strip()
        if re.match(r'^(label|screen|jump|call|show|hide|scene|define|default|'
                    r'init|python|style|transform)\s', stripped):
            # 只检查关键字和标识符部分（引号内的参数可以翻译）
            orig_no_str = re.sub(r'"[^"]*"', '""', orig)
            trans_no_str = re.sub(r'"[^"]*"', '""', trans)
            if orig_no_str != trans_no_str:
                issues.append({
                    "level": "error",
                    "code": "E140_CODE_STRUCT_CHANGED",
                    "line": i,
                    "message": f"代码结构被修改: {orig.strip()[:60]}"
                })

        # 5. 检查变量引用
        orig_vars = set(re.findall(r'\[(\w+)\]', orig))
        trans_vars = set(re.findall(r'\[(\w+)\]', trans))
        missing = orig_vars - trans_vars
        if missing:
            issues.append({
                "level": "error",
                "code": "E210_VAR_MISSING",
                "line": i,
                "message": f"变量丢失: {missing}"
            })
        extra = trans_vars - orig_vars
        if extra:
            issues.append({
                "level": "warning",
                "code": "W211_VAR_EXTRA",
                "line": i,
                "message": f"变量多出: {extra}"
            })

        # 6. 检查 Ren'Py 文本标签匹配
        orig_tags = re.findall(r'\{/?[a-zA-Z]+=?[^}]*\}', orig)
        trans_tags = re.findall(r'\{/?[a-zA-Z]+=?[^}]*\}', trans)
        if sorted(orig_tags) != sorted(trans_tags):
            issues.append({
                "level": "error",
                "code": "E220_TEXT_TAG_MISMATCH",
                "line": i,
                "message": f"文本标签不匹配: 原={orig_tags}, 译={trans_tags}"
            })

        # 7. 检查 {#identifier} 菜单标识符保留
        orig_ids = re.findall(r'\{#[^}]+\}', orig)
        trans_ids = re.findall(r'\{#[^}]+\}', trans)
        if sorted(orig_ids) != sorted(trans_ids):
            issues.append({
                "level": "error",
                "code": "E230_MENU_ID_MISMATCH",
                "line": i,
                "message": f"菜单标识符不匹配: 原={orig_ids}, 译={trans_ids}"
            })

        # 8. 行内转义换行符数量检查（保护 \\n 布局）
        orig_escaped_nl = orig.count('\\n')
        trans_escaped_nl = trans.count('\\n')
        if orig_escaped_nl != trans_escaped_nl:
            issues.append({
                "level": "warning",
                "code": "W310_ESCAPED_NL_MISMATCH",
                "line": i,
                "message": f"行内转义换行符数量不一致: 原 {orig_escaped_nl}, 译 {trans_escaped_nl}"
            })

        # 8.1 Python 百分号格式化占位符检查（%(name)s / %(value)d 等）
        orig_fmt = set(re.findall(r'%\([^)]+\)[sd]', orig))
        trans_fmt = set(re.findall(r'%\([^)]+\)[sd]', trans))
        if orig_fmt != trans_fmt:
            issues.append({
                "level": "error",
                "code": "E240_FMT_PLACEHOLDER_MISMATCH",
                "line": i,
                "message": f"格式化占位符不匹配: 原={orig_fmt}, 译={trans_fmt}"
            })

        # 8.2 占位符顺序：集合相同但顺序不同时标 W251（中英语序差异可能导致合理调序）
        orig_seq = _extract_placeholder_sequence(orig)
        trans_seq = _extract_placeholder_sequence(trans)
        if set(orig_seq) == set(trans_seq) and orig_seq != trans_seq:
            issues.append({
                "level": "warning",
                "code": "W251_PLACEHOLDER_ORDER",
                "line": i,
                "message": "占位符顺序与原文不一致（集合相同，可能因语序调整）"
            })

        # 9. 术语表使用检查：原文命中术语且存在预期译文时，译文应包含该术语
        if glossary_terms:
            for src_term, dst_term in glossary_terms.items():
                # 跳过内部保留键，例如 __game_version__
                if not src_term or not dst_term or str(src_term).startswith("__"):
                    continue
                # 忽略大小写与简单空白差异进行匹配
                if src_term.lower() in orig.lower() and dst_term not in trans:
                    # 对于锁定术语，未命中视为更严重的问题；其余仍作为普通 warning 提示
                    if glossary_locked and src_term in glossary_locked:
                        issues.append({
                            "level": "error",
                            "code": "E411_GLOSSARY_LOCK_MISS",
                            "line": i,
                            "message": f"锁定术语未命中: \"{src_term}\" -> 必须包含 \"{dst_term}\""
                        })
                    else:
                        issues.append({
                            "level": "warning",
                            "code": "W410_GLOSSARY_MISS",
                            "line": i,
                            "message": f"术语表未命中: \"{src_term}\" -> 建议包含 \"{dst_term}\""
                        })

        # 10. 漏翻提示：原文和译文完全相同且看起来是英文对话
        if orig == trans:
            orig_text = _extract_first_quoted_text(orig)
            if orig_text and _looks_untranslated_dialogue(orig_text):
                issues.append({
                    "level": "warning",
                    "code": "W420_SUSPECT_UNTRANSLATED",
                    "line": i,
                    "message": "疑似未翻译英文对话"
                })

        # 10.1 禁翻片段检查：原文命中禁翻字符串时，译文必须保留相同的英文片段
        if glossary_no_translate:
            orig_lower = orig.lower()
            trans_lower = trans.lower()
            for s in glossary_no_translate:
                if not s:
                    continue
                key = str(s)
                # 若原文中包含该片段（大小写不敏感），则要求译文中也包含同样的英文片段
                if key.lower() in orig_lower and key.lower() not in trans_lower:
                    issues.append({
                        "level": "error",
                        "code": "E420_NO_TRANSLATE_CHANGED",
                        "line": i,
                        "message": f"禁翻片段被修改: \"{key}\" 应保持英文不翻译"
                    })

        # 10.2 翻译风格规则检查（柔性提示）
        # W440: 模型自我描述/多余解释
        trans_lower = trans.lower()
        for pat in MODEL_SPEAKING_PATTERNS:
            if pat and pat in trans_lower:
                issues.append({
                    "level": "warning",
                    "code": "W440_MODEL_SPEAKING",
                    "line": i,
                    "message": "译文疑似包含模型自我描述或多余解释，请改为纯对白/叙述文本"
                })
                break

        # W441: 明显的中英标点连续混用（如 。.、？?、！!）
        if any(p in trans for p in ("。.", ".。", "？?", "?？", "！!", "!！")):
            issues.append({
                "level": "warning",
                "code": "W441_PUNCT_MIX",
                "line": i,
                "message": "译文中存在明显的中英标点连续混用（如 。. / ？? / ！!），建议统一为中文标点"
            })

        # 11. 翻译长度比例与密度异常告警（柔性质量提示）
        orig_text = _extract_first_quoted_text(orig)
        trans_text = _extract_first_quoted_text(trans)
        if orig_text and trans_text:
            # 仅对较长的对话/可见文本做检查，避免对短提示类文本产生噪音
            if len(orig_text) >= 20 and len(trans_text) >= 5:
                ratio = len(trans_text) / len(orig_text) if len(orig_text) else 0.0
                if ratio < len_ratio_lower or ratio > len_ratio_upper:
                    issues.append({
                        "level": "warning",
                        "code": "W430_LEN_RATIO_SUSPECT",
                        "line": i,
                        "message": f"译文长度比例异常: x{ratio:.2f}（原 {len(orig_text)} 字，译 {len(trans_text)} 字）"
                    })

            # W442: 译文仍几乎全英文（中文占比极低），但未被 W420 捕获
            # 为降低对代码行/术语密集行的误报，只对更长的文本做检查
            if len(orig_text) >= 25 and len(trans_text) >= 15:
                cn_chars = sum(1 for c in trans_text if '\u4e00' <= c <= '\u9fff')
                zh_ratio = cn_chars / len(trans_text)
                if zh_ratio < 0.05:
                    issues.append({
                        "level": "warning",
                        "code": "W442_SUSPECT_ENGLISH_OUTPUT",
                        "line": i,
                        "message": "译文中中文字符占比极低，疑似未按要求翻译为中文（如术语密集句子可忽略本提示）"
                    })

    # 统计
    errors = sum(1 for i in issues if i['level'] == 'error')
    warnings = sum(1 for i in issues if i['level'] == 'warning')
    if issues:
        logger.info(f"[VALIDATE] {filename}: {errors} 错误, {warnings} 警告")
    else:
        logger.info(f"[VALIDATE] {filename}: OK 通过")

    return issues
