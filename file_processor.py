#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""文件处理器 — 拆分、打补丁、校验"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional


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
# 1. Token 估算与文件拆分
# ============================================================

def estimate_tokens(text: str) -> int:
    """粗略估算 token 数（英文 ~4 字符/token，中文 ~2 字符/token）"""
    # 混合估算：ASCII 字符 / 4 + 非 ASCII / 2
    ascii_count = sum(1 for c in text if ord(c) < 128)
    non_ascii = len(text) - ascii_count
    return ascii_count // 4 + non_ascii // 2 + 1


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

# 预编译为单一正则，按“最早出现”的匹配从左到右收集（用于 _extract_placeholder_sequence）
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
    # 重试逻辑暂不实现，避免改动范围过大
    # TODO: 当条数严重不符或丢弃条数过多时，可考虑自动重试该 chunk（需与 main 断点续传协调）
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
    # 原文非空但译文为空 → 丢弃该条，计漏翻
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


def _find_block_boundaries(lines: list[str]) -> list[int]:
    """找到 RPY 文件中的顶层块边界（行号列表）

    顶层块的特征：行首（无缩进）的 label, screen, init, define, transform, style 等
    """
    boundaries = [0]  # 文件开始
    top_level_re = re.compile(
        r'^(label\s|screen\s|init\s|init\b|define\s|default\s|'
        r'transform\s|style\s|translate\s|python\s|menu\s*:|image\s)'
    )

    for i, line in enumerate(lines):
        stripped = line.rstrip()
        if not stripped or stripped.startswith('#'):
            continue
        # 顶层块：没有前导空格的关键字
        if not line[0].isspace() and top_level_re.match(stripped):
            if i > 0 and i not in boundaries:
                boundaries.append(i)

    return sorted(set(boundaries))


def split_file(filepath: str, max_tokens: int = 50000) -> list[dict]:
    """将大文件按顶层块边界拆分为多个 chunk

    Args:
        filepath: RPY 文件路径
        max_tokens: 每个 chunk 的最大 token 数

    Returns:
        [{"content": str, "line_offset": int, "part": int, "total": int}, ...]
        如果文件不需要拆分，返回单个 chunk
    """
    path = Path(filepath)
    content = read_file(path)
    total_tokens = estimate_tokens(content)

    if total_tokens <= max_tokens:
        return [{"content": content, "line_offset": 0, "part": 1, "total": 1}]

    lines = content.split('\n')
    boundaries = _find_block_boundaries(lines)

    # 在边界处将行分组为 chunk
    chunks = []
    current_start = 0

    for i in range(1, len(boundaries)):
        chunk_lines = lines[current_start:boundaries[i]]
        chunk_text = '\n'.join(chunk_lines)
        chunk_tokens = estimate_tokens(chunk_text)

        if chunk_tokens > max_tokens and current_start < boundaries[i - 1]:
            # 当前累积块太大，在前一个边界处切割
            cut_lines = lines[current_start:boundaries[i - 1]]
            chunks.append({
                "content": '\n'.join(cut_lines),
                "line_offset": current_start,
            })
            current_start = boundaries[i - 1]

    # 最后一个块
    if current_start < len(lines):
        remaining = '\n'.join(lines[current_start:])
        remaining_tokens = estimate_tokens(remaining)
        if remaining_tokens > max_tokens:
            # 单个块超过上限，按行数强制拆分
            sub_chunks = _force_split_lines(lines, current_start, len(lines), max_tokens)
            chunks.extend(sub_chunks)
        else:
            chunks.append({
                "content": remaining,
                "line_offset": current_start,
            })

    # 对所有超大块进行强制拆分
    final_chunks = []
    for chunk in chunks:
        tok = estimate_tokens(chunk['content'])
        if tok > max_tokens:
            c_lines = chunk['content'].split('\n')
            sub = _force_split_lines(c_lines, chunk['line_offset'],
                                     chunk['line_offset'] + len(c_lines), max_tokens,
                                     base_offset=chunk['line_offset'])
            final_chunks.extend(sub)
        else:
            final_chunks.append(chunk)

    # 添加编号 + 上文上下文（第 2 个 chunk 起附带前一 chunk 末尾若干行）
    total = len(final_chunks)
    context_lines = 5  # 上文上下文行数
    for i, chunk in enumerate(final_chunks):
        chunk["part"] = i + 1
        chunk["total"] = total
        if i > 0:
            prev_content = final_chunks[i - 1]["content"]
            prev_lines = prev_content.split('\n')
            tail = prev_lines[-context_lines:] if len(prev_lines) >= context_lines else prev_lines
            chunk["prev_context"] = '\n'.join(tail)
            chunk["prev_context_offset"] = final_chunks[i - 1]["line_offset"] + len(prev_lines) - len(tail)

    return final_chunks


def _force_split_lines(lines: list[str], start: int, end: int,
                       max_tokens: int, base_offset: int = -1) -> list[dict]:
    """当单个块超过 max_tokens 时，按行数均匀拆分

    优先在空行处切割，降低截断上下文的风险。
    """
    if base_offset < 0:
        base_offset = start
    subset = lines[start:end] if start < end else lines
    total_tok = estimate_tokens('\n'.join(subset))
    n_parts = (total_tok // max_tokens) + 1
    part_size = max(len(subset) // n_parts, 100)

    chunks = []
    cur = 0
    while cur < len(subset):
        target_end = min(cur + part_size, len(subset))
        # 尝试在附近的空行处切割
        if target_end < len(subset):
            best = target_end
            for delta in range(0, min(50, part_size // 4)):
                if target_end + delta < len(subset) and not subset[target_end + delta].strip():
                    best = target_end + delta + 1
                    break
                if target_end - delta > cur and not subset[target_end - delta].strip():
                    best = target_end - delta + 1
                    break
            target_end = best
        chunk_text = '\n'.join(subset[cur:target_end])
        chunks.append({"content": chunk_text, "line_offset": base_offset + cur})
        cur = target_end

    return chunks


# ============================================================
# 2. 翻译回写（Patch）
# ============================================================

# Regex for translate strings block: old "..." and new "..."
_RE_STRINGS_OLD = re.compile(r'^\s*old\s+"((?:[^"\\]|\\.)*)"\s*$')
_RE_STRINGS_NEW = re.compile(r'^\s*new\s+"((?:[^"\\]|\\.)*)"\s*$')
_RE_STRINGS_NEW_LINE = re.compile(r'^(\s*new\s+)"((?:[^"\\]|\\.)*)"(\s*)$')


def _parse_strings_blocks(lines: list[str]) -> tuple[dict, set]:
    """Parse translate <lang> strings: blocks; return (strings_pairs, strings_old_lines).

    strings_pairs: (old_line_1based, old_text) -> {"new_line": int, "old_text": str, "new_text": str}
    strings_old_lines: set of old line numbers (1-based) for alignment skip.
    """
    strings_pairs: dict = {}
    strings_old_lines: set = set()
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if re.match(r'^translate\s+\w+\s+strings\s*:', stripped):
            i += 1
            while i < len(lines):
                old_m = _RE_STRINGS_OLD.match(lines[i])
                if old_m:
                    old_line_no = i + 1
                    old_text = old_m.group(1) if old_m.group(1) else ''
                    i += 1
                    if i < len(lines):
                        new_m = _RE_STRINGS_NEW.match(lines[i])
                        if new_m:
                            new_line_no = i + 1
                            new_text = new_m.group(1) if new_m.group(1) else ''
                            strings_pairs[(old_line_no, old_text)] = {
                                "new_line": new_line_no,
                                "old_text": old_text,
                                "new_text": new_text,
                            }
                            strings_old_lines.add(old_line_no)
                            i += 1
                            continue
                elif stripped.startswith('translate ') or (stripped and not line[0].isspace()):
                    break
                i += 1
            continue
        i += 1
    return strings_pairs, strings_old_lines


def _align_original_with_file(
    lines: list[str], item: dict, strings_old_lines: set
) -> tuple[dict, Optional[str]]:
    """Align item['original'] to the actual quoted text on the given line.
    Only exact match + prefix/suffix (threshold 0.8). Skip lines that are strings old lines.
    Returns (item, warning_msg or None). When aligned, warning_msg is '行 N: original 已对齐'.
    """
    line_num = int(item.get('line') or 0)
    original = item.get('original', '') or ''
    if not line_num or not original:
        return item, None
    if line_num in strings_old_lines:
        return item, None
    idx = line_num - 1
    if idx < 0 or idx >= len(lines):
        return item, None
    line = lines[idx]
    # Double-quoted and single-quoted segments (handle escapes)
    dq = re.findall(r'"((?:[^"\\]|\\.)*)"', line)
    sq = re.findall(r"'((?:[^'\\]|\\.)*)'", line)
    candidates = dq + sq
    if not candidates:
        return item, None
    norm_orig = ' '.join(original.split())
    best: Optional[str] = None
    best_score = 0.0
    for seg in candidates:
        norm_seg = ' '.join(seg.split())
        if seg == original or norm_seg == norm_orig:
            best = seg
            best_score = 1.0
            break
        shorter, longer = (norm_orig, norm_seg) if len(norm_orig) <= len(norm_seg) else (norm_seg, norm_orig)
        if not shorter:
            continue
        if longer.startswith(shorter) or longer.endswith(shorter):
            score = len(shorter) / len(longer)
            if score >= 0.8 and score > best_score:
                best = seg
                best_score = score
    if best is not None and best_score >= 0.8:
        return dict(item, original=best), f"行 {line_num}: original 已对齐"
    return item, None


def _apply_strings_translations(
    lines: list[str], strings_items: list[dict], strings_pairs: dict
) -> tuple[int, list[str]]:
    """Apply translations for translate strings entries only; write to new "" lines.
    Returns (applied_count, warnings).
    """
    applied = 0
    warnings: list[str] = []
    for item in strings_items:
        line_num = item.get('line', 0)
        original = item.get('original', '')
        zh = item.get('zh', '')
        if not original or not zh:
            continue
        key = (line_num, original)
        pair = strings_pairs.get(key)
        if not pair:
            continue
        new_line_no = pair["new_line"]
        idx = new_line_no - 1
        if idx < 0 or idx >= len(lines):
            continue
        line_text = lines[idx]
        m = _RE_STRINGS_NEW_LINE.match(line_text)
        if not m:
            warnings.append(f"行 {new_line_no}: strings new 行格式异常，跳过")
            continue
        escaped_zh = _escape_for_renpy_string(zh, '"')
        new_line = m.group(1) + '"' + escaped_zh + '"' + m.group(3)
        lines[idx] = new_line
        applied += 1
    return applied, warnings


def apply_translations(
    original_content: str, translations: list[dict]
) -> tuple[str, list[str], dict]:
    """将翻译结果应用到原始文件

    核心安全策略：只替换引号内的字符串内容，绝不修改代码结构
    四遍匹配策略：精确 → 近偏移 → 远偏移 → 全文扫描
    安全检查可自动修复常见变量问题

    Args:
        original_content: 原始文件内容
        translations: [{"line": N, "original": "...", "zh": "..."}, ...]

    Returns:
        (patched_content, warnings, stats)
        stats: {"alignment_count": int, "strings_applied_count": int}
    """
    lines = original_content.split('\n')
    warnings = []
    applied = 0
    skipped = 0
    auto_fixed = 0
    alignment_count = 0
    strings_applied_count = 0

    # 解析 translate strings 块，供专用回写与对齐跳过
    strings_pairs, strings_old_lines = _parse_strings_blocks(lines)

    # 预过滤：original 对齐 → 安全检查（支持自动修复）
    safe_items = []
    for item in translations:
        line_num = item.get('line', 0)
        original = item.get('original', '')
        zh = item.get('zh', '')

        if not original or not zh:
            continue

        # 方案 b：用该行真实引号文本覆盖 AI 返回的 original（strings 的 old 行不参与对齐）
        item, align_msg = _align_original_with_file(lines, item, strings_old_lines)
        if align_msg:
            warnings.append(align_msg)
            alignment_count += 1
        original = item.get('original', '')
        zh = item.get('zh', '')

        issue = _check_translation_safety(original, zh)
        if issue:
            # 语义变更：W251（占位符顺序不一致）仅告警，仍允许应用翻译，不跳过
            if "W251" in issue:
                safe_items.append(item)
                warnings.append(f"行 {line_num}: {issue}，已应用翻译")
                continue
            # 尝试自动修复变量/标签问题
            fixed_zh = _auto_fix_translation(original, zh)
            if fixed_zh and fixed_zh != zh:
                recheck = _check_translation_safety(original, fixed_zh)
                if not recheck:
                    item = dict(item, zh=fixed_zh)
                    auto_fixed += 1
                else:
                    warnings.append(f"行 {line_num}: 安全检查失败 - {issue}")
                    skipped += 1
                    continue
            else:
                warnings.append(f"行 {line_num}: 安全检查失败 - {issue}")
                skipped += 1
                continue
        safe_items.append(item)

    # 方案 a：translate strings 专用回写，不经过 _replace_string_in_line
    strings_items = []
    normal_items = []
    for item in safe_items:
        key = (item.get('line', 0), item.get('original', ''))
        if key in strings_pairs:
            strings_items.append(item)
        else:
            normal_items.append(item)
    applied_strings, strings_warnings = _apply_strings_translations(lines, strings_items, strings_pairs)
    applied += applied_strings
    strings_applied_count = applied_strings
    warnings.extend(strings_warnings)

    # 记录已应用的 (行号, 原文) 对 — 允许同行多次翻译不同文本
    applied_pairs = set()

    def _try_apply(try_idx: int, original: str, zh: str) -> bool:
        """尝试在指定行应用翻译"""
        if try_idx < 0 or try_idx >= len(lines):
            return False
        if (try_idx, original) in applied_pairs:
            return False
        new_line = _replace_string_in_line(lines[try_idx], original, zh)
        if new_line is not None:
            lines[try_idx] = new_line
            applied_pairs.add((try_idx, original))
            return True
        return False

    # 第一遍：精确行号匹配（仅 normal 条目）
    remaining = []
    for item in normal_items:
        line_num = item.get('line', 0)
        original = item.get('original', '')
        zh = item.get('zh', '')
        idx = line_num - 1

        if _try_apply(idx, original, zh):
            applied += 1
        else:
            remaining.append(item)

    # 第二遍：近偏移搜索（±5行范围）— 不报警告
    still_remaining = []
    for item in remaining:
        line_num = item.get('line', 0)
        original = item.get('original', '')
        zh = item.get('zh', '')
        idx = line_num - 1
        found = False

        for delta in [-1, 1, -2, 2, -3, 3, -4, 4, -5, 5]:
            if _try_apply(idx + delta, original, zh):
                found = True
                applied += 1
                break

        if not found:
            still_remaining.append(item)

    # 第三遍：远偏移搜索（±50行范围）— 不报警告
    far_remaining = []
    for item in still_remaining:
        line_num = item.get('line', 0)
        original = item.get('original', '')
        zh = item.get('zh', '')
        idx = line_num - 1
        found = False

        for try_idx in range(max(0, idx - 50), min(len(lines), idx + 51)):
            if _try_apply(try_idx, original, zh):
                found = True
                applied += 1
                break

        if not found:
            far_remaining.append(item)

    # 第四遍：全文扫描（针对仍未匹配的项）
    for item in far_remaining:
        line_num = item.get('line', 0)
        original = item.get('original', '')
        zh = item.get('zh', '')
        found = False

        for try_idx in range(len(lines)):
            if _try_apply(try_idx, original, zh):
                found = True
                applied += 1
                break

        if not found:
            warnings.append(f"行 {line_num}: 未找到原文 \"{original[:50]}\"")
            skipped += 1

    parts = [f"应用 {applied}"]
    if skipped:
        parts.append(f"跳过 {skipped}")
    if auto_fixed:
        parts.append(f"自动修复 {auto_fixed}")
    if applied > 0 or skipped > 0:
        print(f"  [PATCH] {', '.join(parts)} 条翻译")

    stats = {"alignment_count": alignment_count, "strings_applied_count": strings_applied_count}
    return '\n'.join(lines), warnings, stats


def _replace_string_in_line(line: str, original: str, replacement: str) -> Optional[str]:
    """在一行中替换引号内的字符串内容

    只替换引号内的文本，保持引号和周围代码不变。
    支持 Ren'Py 格式标签 ({i}, {b}, {color}, 等)。
    支持 AI 截断的模糊匹配。
    """
    # 统一先做字符串安全转义，避免把译文中的引号直接注入代码结构
    safe_replacement_dq = _escape_for_renpy_string(replacement, '"')
    safe_replacement_sq = _escape_for_renpy_string(replacement, "'")

    # === 阶段 1：精确匹配 ===
    for quote in ('"', "'"):
        pattern = f'{quote}{original}{quote}'
        if pattern in line:
            safe_replacement = safe_replacement_dq if quote == '"' else safe_replacement_sq
            return line.replace(pattern, f'{quote}{safe_replacement}{quote}', 1)

    # 尝试处理转义引号
    escaped = original.replace('"', '\\"')
    if escaped != original and f'"{escaped}"' in line:
        return line.replace(f'"{escaped}"', f'"{safe_replacement_dq}"', 1)

    # 尝试三引号
    if f'"""{original}"""' in line:
        return line.replace(f'"""{original}"""', f'"""{safe_replacement_dq}"""', 1)

    # 尝试 _() 包裹
    if f'_("{original}")' in line:
        return line.replace(f'_("{original}")', f'_("{safe_replacement_dq}")', 1)

    # === 阶段 2：标准化空白匹配 ===
    norm_original = ' '.join(original.split())
    if norm_original != original:
        for quote in ('"', "'"):
            pattern = f'{quote}{norm_original}{quote}'
            if pattern in line:
                safe_replacement = safe_replacement_dq if quote == '"' else safe_replacement_sq
                return line.replace(pattern, f'{quote}{safe_replacement}{quote}', 1)

    # === 阶段 3：从行中提取引号内文本，尝试高级匹配 ===
    # 找到行中所有引号内的文本段
    quoted_parts = re.findall(r'"([^"]+)"', line)
    if not quoted_parts:
        return None

    for line_text in quoted_parts:
        # 3a. 精确比较
        if line_text == original:
            return line.replace(f'"{line_text}"', f'"{safe_replacement_dq}"', 1)

        # 3b. 标准化空白比较
        if ' '.join(line_text.split()) == norm_original:
            return line.replace(f'"{line_text}"', f'"{safe_replacement_dq}"', 1)

        # 3c. Ren'Py 格式标签处理：去掉标签后比较
        stripped_text = re.sub(r'\{/?[^}]+\}', '', line_text)
        if not stripped_text:
            continue

        norm_stripped = ' '.join(stripped_text.split())
        if stripped_text == original or norm_stripped == norm_original:
            # 提取前缀标签和后缀标签，翻译时保留标签结构
            prefix_m = re.match(r'((?:\{[^}]+\})+)', line_text)
            prefix_tags = prefix_m.group(0) if prefix_m else ''
            suffix_m = re.search(r'((?:\{/[^}]+\})+)$', line_text)
            suffix_tags = suffix_m.group(0) if suffix_m else ''
            new_text = prefix_tags + safe_replacement_dq + suffix_tags
            return line.replace(f'"{line_text}"', f'"{new_text}"', 1)

        # 3d. 标签子串匹配 — 原文是被标签包裹的更大文本的一部分
        tag_wrapped_re = re.compile(
            r'(\{[^/][^}]*\})' + re.escape(original) + r'(\{/[^}]+\})'
        )
        tw_match = tag_wrapped_re.search(line_text)
        if tw_match:
            old_segment = tw_match.group(0)
            new_segment = tw_match.group(1) + replacement + tw_match.group(2)
            new_line_text = line_text.replace(old_segment, new_segment, 1)
            return line.replace(f'"{line_text}"', f'"{new_line_text}"', 1)

        # 3e. AI 截断匹配 — AI 可能只返回了部分文本
        if len(original) >= 15:
            # AI 的文本可能是原文去掉标签后截断的前缀
            if stripped_text.startswith(original) or norm_stripped.startswith(norm_original):
                # 如果有标签且 AI 覆盖了足够多的原文，视为有效的截断匹配
                has_tags = (line_text != stripped_text)
                ratio = len(original) / len(stripped_text) if stripped_text else 0
                if has_tags and ratio >= 0.5:
                    prefix_m = re.match(r'((?:\{[^}]+\})+)', line_text)
                    prefix_tags = prefix_m.group(0) if prefix_m else ''
                    suffix_m = re.search(r'((?:\{/[^}]+\})+)$', line_text)
                    suffix_tags = suffix_m.group(0) if suffix_m else ''
                    new_text = prefix_tags + safe_replacement_dq + suffix_tags
                    return line.replace(f'"{line_text}"', f'"{new_text}"', 1)
                # 无标签时，截断前缀不安全，跳过
                continue
            # 反过来：AI 返回完整但源文件更长（AI 省略了几个词）
            if original.startswith(stripped_text[:15]) and len(original) > len(stripped_text):
                # AI 返回的更长，不安全匹配
                continue
            # AI 截断了文本末尾（警告中显示50字符截断）
            if len(original) >= 45 and stripped_text.startswith(original[:40]):
                prefix_m = re.match(r'((?:\{[^}]+\})+)', line_text)
                prefix_tags = prefix_m.group(0) if prefix_m else ''
                suffix_m = re.search(r'((?:\{/[^}]+\})+)$', line_text)
                suffix_tags = suffix_m.group(0) if suffix_m else ''
                new_text = prefix_tags + safe_replacement_dq + suffix_tags
                return line.replace(f'"{line_text}"', f'"{new_text}"', 1)

    return None


def _escape_for_renpy_string(text: str, quote: str = '"') -> str:
    """将译文转义为可安全写入 Ren'Py 字符串的内容。"""
    escaped = text.replace('\\', '\\\\').replace('\r', '')
    escaped = escaped.replace('\n', r'\n')
    if quote == '"':
        escaped = escaped.replace('"', r'\"')
    else:
        escaped = escaped.replace("'", r"\\'")
    return escaped


def _count_unescaped_quote(line: str, quote: str) -> int:
    """统计一行内未被反斜杠转义的引号数量。"""
    count = 0
    escaped = False
    for ch in line:
        if escaped:
            escaped = False
            continue
        if ch == '\\':
            escaped = True
            continue
        if ch == quote:
            count += 1
    return count


def _extract_first_quoted_text(line: str) -> Optional[str]:
    """提取行内首个双引号字符串内容。"""
    m = re.search(r'"((?:[^"\\]|\\.)*)"', line)
    return m.group(1) if m else None


def _strip_double_quoted_segments(line: str) -> str:
    """移除双引号字符串片段，避免将对话中的英文缩写单引号误判为结构变化。"""
    return re.sub(r'"(?:[^"\\]|\\.)*"', '""', line)


def _looks_untranslated_dialogue(text: str) -> bool:
    """启发式判断文本是否像未翻译英文对话。"""
    if len(text) < 20:
        return False
    if any(token in text for token in ('/', '\\', '.png', '.jpg', '.webp', '.ttf', '#')):
        return False
    ascii_letters = sum(1 for c in text if ('a' <= c.lower() <= 'z'))
    cn_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    return cn_chars == 0 and ascii_letters >= 12


def _auto_fix_translation(original: str, zh: str) -> Optional[str]:
    """尝试自动修复翻译中的变量/标签问题

    常见问题：AI 翻译了变量名（如 [mother] → [母亲]），或丢失/多出变量。
    """
    # 修复变量：将原文中的变量占位符恢复到译文中
    orig_vars = re.findall(r'\[\w+\]', original)
    zh_vars = re.findall(r'\[\w+\]', zh)
    orig_var_names = set(re.findall(r'\[(\w+)\]', original))
    zh_var_names = set(re.findall(r'\[(\w+)\]', zh))

    fixed = zh
    missing = orig_var_names - zh_var_names
    extra = zh_var_names - orig_var_names

    if missing and extra and len(missing) == len(extra):
        # AI 可能翻译了变量名，逐个替换回来
        # 尝试按位置匹配
        for extra_var in list(extra):
            # 找最可能对应的原始变量
            for miss_var in list(missing):
                zh_pattern = f'[{extra_var}]'
                if zh_pattern in fixed:
                    fixed = fixed.replace(zh_pattern, f'[{miss_var}]', 1)
                    extra.discard(extra_var)
                    missing.discard(miss_var)
                    break
    elif missing and not extra:
        # 变量丢失：AI 删除了变量引用，无法安全修复
        return None

    # 修复标签：确保 Ren'Py 标签匹配
    orig_tags = re.findall(r'\{/?[a-z]+=?[^}]*\}', original, re.I)
    zh_tags = re.findall(r'\{/?[a-z]+=?[^}]*\}', fixed, re.I)
    if sorted(orig_tags) != sorted(zh_tags):
        # 如果原文有标签但译文没有，AI 可能故意移除了（因为我们会在匹配时重新加上）
        # 不自动修复标签
        if not orig_tags and zh_tags:
            # 译文多出标签，尝试移除
            fixed = re.sub(r'\{/?[a-z]+=?[^}]*\}', '', fixed, flags=re.I)
        else:
            return None

    return fixed if fixed != zh else None


def _check_translation_safety(original: str, zh: str) -> Optional[str]:
    """检查翻译是否安全（不会破坏游戏）

    Returns:
        问题描述字符串，如果安全返回 None
    """
    # 检查变量占位符是否保留
    orig_vars = set(re.findall(r'\[(\w+)\]', original))
    zh_vars = set(re.findall(r'\[(\w+)\]', zh))
    missing_vars = orig_vars - zh_vars
    if missing_vars:
        return f"变量丢失: {missing_vars}"
    extra_vars = zh_vars - orig_vars
    if extra_vars:
        return f"变量多出: {extra_vars}"

    # 检查 Ren'Py 标签是否保留
    orig_tags = re.findall(r'\{/?[a-z]+=?[^}]*\}', original, re.I)
    zh_tags = re.findall(r'\{/?[a-z]+=?[^}]*\}', zh, re.I)
    if sorted(orig_tags) != sorted(zh_tags):
        return f"标签不匹配: 原={orig_tags}, 译={zh_tags}"

    # 检查换行符数量是否一致（统一用字面量 '\n' 比较）
    if original.count('\\n') != zh.count('\\n'):
        return f"换行符数量不匹配: 原={original.count(chr(92) + 'n')}, 译={zh.count(chr(92) + 'n')}"

    # 检查 {#identifier} 菜单标识符是否保留
    orig_ids = re.findall(r'\{#[^}]+\}', original)
    zh_ids = re.findall(r'\{#[^}]+\}', zh)
    if sorted(orig_ids) != sorted(zh_ids):
        return f"菜单标识符不匹配: 原={orig_ids}, 译={zh_ids}"

    # 检查 %(name)s 格式化占位符是否保留
    orig_fmt = set(re.findall(r'%\([^)]+\)[sd]', original))
    zh_fmt = set(re.findall(r'%\([^)]+\)[sd]', zh))
    if orig_fmt != zh_fmt:
        return f"格式化占位符不匹配: 原={orig_fmt}, 译={zh_fmt}"

    # 检查翻译长度比例是否合理（只对较长文本检查）
    if len(original) > 30:
        ratio = len(zh) / len(original)
        if ratio > 3.0:
            return f"译文异常过长 (x{ratio:.1f})，可能包含多余内容"
        if ratio < 0.05:
            return f"译文异常过短 (x{ratio:.2f})，可能截断"

    # 占位符顺序校验：仅在集合已一致时执行，顺序不同标 W251（语义：允许 apply，仅告警）
    orig_seq = _extract_placeholder_sequence(original)
    zh_seq = _extract_placeholder_sequence(zh)
    if set(orig_seq) == set(zh_seq) and orig_seq != zh_seq:
        return "占位符顺序与原文不一致 (W251)"

    return None


# ============================================================
# 3. 翻译后校验
# ============================================================

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
                    "message": f"非字符串行被修改: \"{orig.strip()[:60]}\" → \"{trans.strip()[:60]}\""
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

        # 单引号检查仅针对“代码层单引号字符串”，忽略双引号对话内部的 apostrophe（如 don't）
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
                            "message": f"锁定术语未命中: \"{src_term}\" → 必须包含 \"{dst_term}\""
                        })
                    else:
                        issues.append({
                            "level": "warning",
                            "code": "W410_GLOSSARY_MISS",
                            "line": i,
                            "message": f"术语表未命中: \"{src_term}\" → 建议包含 \"{dst_term}\""
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
        print(f"  [VALIDATE] {filename}: {errors} 错误, {warnings} 警告")
    else:
        print(f"  [VALIDATE] {filename}: OK 通过")

    return issues


# ============================================================
# 辅助函数
# ============================================================

def read_file(path) -> str:
    """读取文件，自动处理编码"""
    if not isinstance(path, Path):
        path = Path(path)
    for enc in ['utf-8', 'utf-8-sig', 'latin-1', 'gbk']:
        try:
            return path.read_text(encoding=enc)
        except (UnicodeDecodeError, UnicodeError):
            continue
    return path.read_text(encoding='utf-8', errors='replace')
