#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""File reading & splitting utilities."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def estimate_tokens(text: str) -> int:
    """粗略估算 token 数（英文 ~4 字符/token，中文 ~2 字符/token）"""
    ascii_count = sum(1 for c in text if ord(c) < 128)
    non_ascii = len(text) - ascii_count
    return ascii_count // 4 + non_ascii // 2 + 1


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
