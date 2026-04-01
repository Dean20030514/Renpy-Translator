#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""direct-mode dry-run 分析辅助函数。

从 direct_translator.py 提取，用于 --dry-run --verbose 模式下的
文件级对话密度统计、直方图输出、术语扫描预览。
"""

from __future__ import annotations

import logging
from pathlib import Path

from file_processor import read_file

logger = logging.getLogger(__name__)


def _compute_file_dialogue_stats(filepath: Path) -> tuple[int, float]:
    """返回 (对话行数, 密度)，用于 dry-run 详情。"""
    from retranslator import calculate_dialogue_density
    content = read_file(filepath)
    density = calculate_dialogue_density(content)
    from renpy_text_utils import _is_user_visible_string_line
    dlg_count = sum(1 for line in content.splitlines()
                    if _is_user_visible_string_line(line))
    return dlg_count, density


def _print_density_histogram(densities: list[float]) -> None:
    """输出文字版对话密度分布直方图。"""
    if not densities:
        return
    buckets = [0] * 5  # [0-20%, 20-40%, 40-60%, 60-80%, 80-100%]
    labels = ["0-20%", "20-40%", "40-60%", "60-80%", "80-100%"]
    for d in densities:
        idx = min(int(d * 5), 4)
        buckets[idx] += 1
    max_count = max(buckets) if buckets else 1
    logger.info("\n对话密度分布:")
    for label, count in zip(labels, buckets):
        bar_len = count * 30 // max_count if max_count else 0
        bar = "#" * bar_len
        logger.info(f"  {label:>8s} | {bar:<30s} {count}")


def _print_term_scan_preview(glossary) -> None:
    """输出术语扫描结果预览。"""
    n_chars = len(getattr(glossary, 'characters', {}))
    n_terms = len(getattr(glossary, 'terms', {}))
    n_locked = len(getattr(glossary, 'locked_terms', []))
    n_notrans = len(getattr(glossary, 'no_translate', []))
    logger.info(f"\n术语扫描预览:")
    logger.info(f"  角色名: {n_chars} 个")
    logger.info(f"  术语表: {n_terms} 条" + (f"（其中锁定 {n_locked} 条）" if n_locked else ""))
    if n_notrans:
        logger.info(f"  禁翻片段: {n_notrans} 条")
