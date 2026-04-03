#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""direct-mode 翻译引擎：将完整 .rpy 文件发给 AI，由 AI 自行识别可翻译内容。"""

from __future__ import annotations

import argparse
import concurrent.futures
import fnmatch
import json
import logging
import os
import re
import signal
import shutil
import sys
import time
import threading
from pathlib import Path
from typing import Optional

from core.api_client import APIClient, APIConfig, get_pricing, is_reasoning_model
from file_processor import (
    split_file,
    apply_translations,
    validate_translation,
    estimate_tokens,
    read_file,
    protect_placeholders,
    check_response_chunk,
    _count_translatable_lines_in_chunk,
    _find_block_boundaries,
    SKIP_FILES_FOR_TRANSLATION,
)
from core.glossary import Glossary
from core.prompts import (
    build_system_prompt,
    build_user_prompt,
    build_retranslate_system_prompt,
    build_retranslate_user_prompt,
)
from core.translation_db import TranslationDB
from tools.font_patch import resolve_font, apply_font_patch
from translators.retranslator import calculate_dialogue_density, build_retranslate_chunks
from core.translation_utils import (
    ChunkResult,
    TranslationContext,
    ProgressTracker,
    ProgressBar,
    CHECKER_DROP_RATIO_THRESHOLD,
    MIN_DROPPED_FOR_WARNING,
    MIN_DIALOGUE_LENGTH,
    _strip_char_prefix,
    _restore_placeholders_in_translations,
    _filter_checked_translations,
    _deduplicate_translations,
)

logger = logging.getLogger("renpy_translator")


# ============================================================
# Chunk 翻译（模块级函数，替代 translate_file 内的嵌套闭包）
# ============================================================

def _translate_chunk(ctx: TranslationContext, chunk: dict) -> ChunkResult:
    """翻译单个 chunk，返回 ChunkResult。

    原为 translate_file() 内的嵌套函数，通过闭包捕获 client/system_prompt/rel_path。
    重构后通过 TranslationContext 显式传参。
    """
    part = chunk["part"]
    chunk_info = {
        "part": part,
        "total": chunk["total"],
        "line_offset": chunk["line_offset"],
    }
    expected_count = _count_translatable_lines_in_chunk(chunk["content"])
    # 占位符保护
    protected_content, ph_mapping = protect_placeholders(chunk["content"])
    user_prompt = build_user_prompt(ctx.rel_path, protected_content, chunk_info)
    logger.debug(f"    [API ] 块 {part}/{chunk['total']}  "
          f"({estimate_tokens(chunk['content']):,} tokens)")
    try:
        translations = ctx.client.translate(ctx.system_prompt, user_prompt)
    except Exception as e:
        return ChunkResult(part=part, error=f"块 {part} API 调用失败: {e}", expected=expected_count)
    # 占位符还原
    _restore_placeholders_in_translations(translations, ph_mapping)
    # Chunk 级检查（条数一致）
    chunk_warnings = check_response_chunk(protected_content, translations)
    for w in chunk_warnings:
        logger.debug(f"    [CHECK] {w}")
    # 逐条检查
    kept, dropped_count, dropped_items, check_warns = _filter_checked_translations(translations)
    for w in check_warns:
        logger.debug(f"    {w}")
    if not translations:
        logger.debug(f"    [INFO] 块 {part}: 无需翻译的内容")
    else:
        logger.debug(f"    [OK  ] 块 {part}: 获得 {len(translations)} 条翻译"
              + (f", 丢弃 {dropped_count} 条" if dropped_count else ""))
    return ChunkResult(
        part=part, kept=kept, chunk_warnings=chunk_warnings + check_warns,
        dropped_count=dropped_count, expected=expected_count,
        returned=len(translations), dropped_items=dropped_items,
    )


def _should_retry(cr: ChunkResult) -> tuple[bool, bool]:
    """判断 chunk 是否需要重试。

    Returns: (should_retry, needs_split)
        needs_split=True 表示应拆分后重试而非原样重试（疑似输出截断）。
    """
    if cr.error:
        return True, False
    if cr.returned > 0 and cr.dropped_count >= MIN_DROPPED_FOR_WARNING and cr.dropped_count / cr.returned > CHECKER_DROP_RATIO_THRESHOLD:
        return True, False
    # 截断检测：返回条数 < 期望的 50%，强烈暗示 AI 输出被截断
    if cr.expected > 0 and cr.returned < cr.expected * 0.5:
        return True, True
    return False, False


def _split_chunk(chunk: dict) -> tuple[dict, dict]:
    """将 chunk 二分为两个子 chunk。

    拆分点优先级：label/screen 边界 > 空行 > 直接二等分。
    只做一层拆分（不递归），避免复杂度爆炸。
    """
    lines = chunk["content"].splitlines(keepends=True)
    total_lines = len(lines)
    if total_lines < 2:
        # 无法拆分，返回原 chunk 和空 chunk
        empty = {"content": "", "line_offset": chunk["line_offset"] + total_lines,
                 "part": chunk["part"], "total": chunk["total"]}
        return chunk, empty

    mid = total_lines // 2
    search_start = max(1, mid - total_lines // 4)
    search_end = min(total_lines - 1, mid + total_lines // 4)
    best_split = mid  # fallback: 直接二等分

    # 优先级 1：label/screen/init 边界
    boundaries = _find_block_boundaries(lines)
    found_boundary = False
    for b in boundaries:
        if search_start <= b <= search_end:
            best_split = b
            found_boundary = True
            break

    if not found_boundary:
        # 优先级 2：空行（从中间向外搜索）
        for i in range(mid, search_end):
            if not lines[i].strip():
                best_split = i + 1
                break
        else:
            for i in range(mid - 1, search_start - 1, -1):
                if not lines[i].strip():
                    best_split = i + 1
                    break

    content_a = "".join(lines[:best_split])
    content_b = "".join(lines[best_split:])
    base_offset = chunk["line_offset"]

    chunk_a = {
        "content": content_a,
        "line_offset": base_offset,
        "part": chunk["part"],
        "total": chunk["total"],
    }
    if "prev_context" in chunk:
        chunk_a["prev_context"] = chunk["prev_context"]

    chunk_b = {
        "content": content_b,
        "line_offset": base_offset + best_split,
        "part": chunk["part"],
        "total": chunk["total"],
    }
    # chunk_b 的上下文 = chunk_a 末尾 5 行
    context_lines = lines[max(0, best_split - 5):best_split]
    chunk_b["prev_context"] = "".join(context_lines)

    return chunk_a, chunk_b


def _translate_chunk_with_retry(ctx: TranslationContext, chunk: dict, max_retries: int = 1) -> ChunkResult:
    """带自动重试的 chunk 翻译。截断时自动拆分重试。"""
    cr = _translate_chunk(ctx, chunk)
    for attempt in range(max_retries):
        should, needs_split = _should_retry(cr)
        if not should:
            break

        if needs_split:
            # 截断：拆分 chunk 后分别翻译，合并结果
            logger.debug(f"    [SPLIT] 块 {chunk['part']}: 返回 {cr.returned}/{cr.expected}，"
                         f"疑似截断，拆分重试")
            chunk_a, chunk_b = _split_chunk(chunk)
            cr_a = _translate_chunk(ctx, chunk_a)
            cr_b = _translate_chunk(ctx, chunk_b) if chunk_b["content"] else ChunkResult(part=chunk["part"])
            cr = ChunkResult(
                part=chunk["part"],
                kept=cr_a.kept + cr_b.kept,
                chunk_warnings=cr_a.chunk_warnings + cr_b.chunk_warnings,
                dropped_count=cr_a.dropped_count + cr_b.dropped_count,
                expected=cr_a.expected + cr_b.expected,
                returned=cr_a.returned + cr_b.returned,
                dropped_items=cr_a.dropped_items + cr_b.dropped_items,
            )
            break  # 拆分只做一层
        else:
            reason = cr.error or f"丢弃率过高 ({cr.dropped_count}/{cr.returned})"
            logger.debug(f"    [RETRY] 块 {chunk['part']}: {reason}，第 {attempt + 1} 次重试")
            cr = _translate_chunk(ctx, chunk)
    return cr


# ============================================================

def translate_file(
    rpy_path: Path,
    game_dir: Path,
    output_dir: Path,
    client: APIClient,
    glossary: Glossary,
    progress: ProgressTracker,
    quality_report: Optional[dict[str, list[dict]]] = None,
    genre: str = "adult",
    max_tokens_per_chunk: int = 4000,
    workers: int = 1,
    *,
    translation_db: Optional[TranslationDB] = None,
    run_id: str = "",
    stage: str = "single",
    provider: str = "",
    model: str = "",
    min_dialogue_density: float = 0.20,
    cot: bool = False,
) -> tuple[int, list[str], int, list[dict]]:
    """翻译单个 RPY 文件

    Returns:
        (translated_count, warnings, checker_dropped, chunk_stats_list)
        checker_dropped: 因 ResponseChecker 未通过而被丢弃的条数（保留原文计漏翻）。
        chunk_stats_list: per-chunk 指标 [{"chunk_idx": N, "expected": X, "returned": Y, "dropped": D}, ...]
    """
    rel_path = str(rpy_path.relative_to(game_dir))

    # 纯配置/UI 文件——直接复制，不翻译
    if rpy_path.name in SKIP_FILES_FOR_TRANSLATION:
        out_path = output_dir / rel_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        content = read_file(rpy_path)
        out_path.write_text(content, encoding="utf-8")
        progress.mark_file_done(rel_path)
        logger.debug(f"  [SKIP-CFG] {rel_path} (配置文件，跳过翻译)")
        return 0, [], 0, []

    # 断点续传：已完成则跳过
    if progress.is_file_done(rel_path):
        logger.debug(f"  [SKIP] {rel_path} (已完成)")
        return 0, [], 0, []

    content = read_file(rpy_path)
    tokens = estimate_tokens(content)
    logger.debug(f"  [FILE] {rel_path}  ({tokens:,} tokens)")

    # 密度检测：低密度文件走定向翻译，避免 AI 注意力被代码行稀释
    density = calculate_dialogue_density(content)
    if density < min_dialogue_density:
        logger.debug(f"    [DENSITY] 对话密度 {density * 100:.1f}% < {min_dialogue_density * 100:.0f}%，"
              f"使用定向翻译模式")
        return _translate_file_targeted(
            rpy_path, game_dir, output_dir, content, rel_path,
            client, glossary, progress, quality_report, genre,
            translation_db=translation_db, run_id=run_id, stage=stage,
            provider=provider, model=model,
        )

    # 拆分大文件
    chunks = split_file(str(rpy_path), max_tokens_per_chunk)
    if len(chunks) > 1:
        logger.debug(f"    拆分为 {len(chunks)} 个块")

    # 构建 prompt（按题材 + 术语表 + 项目名）
    project_name = game_dir.parent.name if game_dir.name.lower() == "game" else game_dir.name
    system_prompt = build_system_prompt(
        genre=genre,
        glossary_text=glossary.to_prompt_text(),
        project_name=project_name,
        cot=cot,
    )

    # 加载已完成的翻译（断点续传，只加载一次避免重复）
    all_translations = list(progress.get_file_translations(rel_path))
    all_warnings = []
    all_dropped_items: list[dict] = []
    chunk_stats_list: list[dict] = []

    # 筛选待翻译的 chunk
    pending_chunks = [c for c in chunks if not progress.is_chunk_done(rel_path, c["part"])]
    done_chunks = len(chunks) - len(pending_chunks)
    if done_chunks > 0:
        logger.debug(f"    [SKIP] {done_chunks}/{len(chunks)} 个块已完成")

    total_checker_dropped = 0

    # 构建翻译上下文（替代嵌套函数闭包捕获）
    ctx = TranslationContext(client=client, system_prompt=system_prompt, rel_path=rel_path)

    if workers > 1 and len(pending_chunks) > 1:
        # 并发翻译多个 chunk
        _backpressure = threading.Semaphore(workers * 2)

        def _submit_with_backpressure(pool, fn, *args):
            _backpressure.acquire()
            future = pool.submit(fn, *args)
            future.add_done_callback(lambda _: _backpressure.release())
            return future

        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {_submit_with_backpressure(executor, _translate_chunk_with_retry, ctx, c): c for c in pending_chunks}
            for future in concurrent.futures.as_completed(futures):
                cr = future.result()
                chunk_stats_list.append({"chunk_idx": cr.part, "expected": cr.expected, "returned": cr.returned, "dropped": cr.dropped_count})
                if cr.error:
                    logger.error(f"    [ERROR] {cr.error}")
                    all_warnings.append(cr.error)
                else:
                    all_warnings.extend(cr.chunk_warnings)
                    total_checker_dropped += cr.dropped_count
                    progress.mark_chunk_done(rel_path, cr.part, cr.kept)
                    all_translations.extend(cr.kept)
                    all_dropped_items.extend(cr.dropped_items)
    else:
        # 顺序翻译
        for chunk in pending_chunks:
            cr = _translate_chunk_with_retry(ctx, chunk)
            chunk_stats_list.append({"chunk_idx": cr.part, "expected": cr.expected, "returned": cr.returned, "dropped": cr.dropped_count})
            if cr.error:
                logger.error(f"    [ERROR] {cr.error}")
                all_warnings.append(cr.error)
                progress.save()
                continue
            all_warnings.extend(cr.chunk_warnings)
            total_checker_dropped += cr.dropped_count
            progress.mark_chunk_done(rel_path, cr.part, cr.kept)
            all_translations.extend(cr.kept)
            all_dropped_items.extend(cr.dropped_items)

    if not all_translations:
        # 没有需要翻译的内容，直接复制原文件
        out_path = output_dir / rel_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(content, encoding='utf-8')
        progress.mark_file_done(rel_path)
        return 0, [], total_checker_dropped, chunk_stats_list

    # 去重（多 chunk 可能有重叠）
    unique_translations = _deduplicate_translations(all_translations)

    # 应用翻译
    patched, patch_warnings, patch_stats = apply_translations(content, unique_translations)
    all_warnings.extend(patch_warnings)

    # 校验：同时传入术语表、锁定术语与禁翻片段
    issues = validate_translation(
        content,
        patched,
        rel_path,
        glossary_terms=glossary.terms,
        glossary_locked=glossary.locked_terms,
        glossary_no_translate=glossary.no_translate,
    )
    if quality_report is not None and issues:
        quality_report[rel_path] = issues
    for issue in issues:
        if issue['level'] == 'error':
            all_warnings.append(f"行 {issue['line']}: {issue['message']}")

    # 将每条翻译写入 translation_db（可选）
    if translation_db is not None and unique_translations:
        per_line: dict[int, dict[str, list[str]]] = {}
        for issue in issues:
            line_no = int(issue.get("line") or 0)
            code = issue.get("code") or ""
            level = issue.get("level") or ""
            if not line_no or not code or level not in ("error", "warning"):
                continue
            bucket = per_line.setdefault(line_no, {"errors": [], "warnings": []})
            if level == "error":
                bucket["errors"].append(code)
            else:
                bucket["warnings"].append(code)

        db_entries: list[dict] = []
        for item in unique_translations:
            line_no = int(item.get("line") or 0)
            original = item.get("original", "") or ""
            zh = item.get("zh", "") or ""
            if not line_no or not original:
                continue
            info = per_line.get(line_no, {"errors": [], "warnings": []})
            err_codes = info["errors"]
            warn_codes = info["warnings"]
            if err_codes:
                status = "error"
            elif warn_codes:
                status = "warning"
            else:
                status = "ok"
            db_entries.append(
                {
                    "file": rel_path,
                    "line": line_no,
                    "original": original,
                    "translation": zh,
                    "status": status,
                    "error_codes": err_codes,
                    "warning_codes": warn_codes,
                    "run_id": run_id,
                    "stage": stage,
                    "provider": provider,
                    "model": model,
                }
            )
        if db_entries:
            translation_db.add_entries(db_entries)

    # 写入 checker 丢弃的条目（仅用于归因统计，不参与回写）
    if translation_db is not None and all_dropped_items:
        try:
            dropped_db_entries: list[dict] = []
            for item in all_dropped_items:
                line_no = int(item.get("line") or 0)
                original = item.get("original", "") or ""
                zh = item.get("zh", "") or ""
                if not line_no or not original:
                    continue
                # 若同一 key 已有 kept 条目，不覆盖
                if translation_db.has_entry(rel_path, line_no, original):
                    continue
                dropped_db_entries.append({
                    "file": rel_path,
                    "line": line_no,
                    "original": original,
                    "translation": zh,
                    "status": "checker_dropped",
                    "error_codes": [],
                    "warning_codes": [],
                    "run_id": run_id,
                    "stage": stage,
                    "provider": provider,
                    "model": model,
                })
            if dropped_db_entries:
                translation_db.add_entries(dropped_db_entries)
        except (OSError, ValueError, TypeError) as e:
            logger.debug(f"记录 checker_dropped 到 translation_db 失败: {e}")

    # 写入回写失败的条目（用于根因分析）
    wb_failures = patch_stats.get("writeback_failures", [])
    if translation_db is not None and wb_failures:
        try:
            wb_db_entries: list[dict] = []
            for diag in wb_failures:
                line_no = int(diag.get("line") or 0)
                original = diag.get("original", "") or ""
                zh = diag.get("zh", "") or ""
                if not line_no or not original:
                    continue
                if translation_db.has_entry(rel_path, line_no, original):
                    continue
                wb_db_entries.append({
                    "file": rel_path,
                    "line": line_no,
                    "original": original,
                    "translation": zh,
                    "status": "writeback_failed",
                    "error_codes": [],
                    "warning_codes": [],
                    "run_id": run_id,
                    "stage": stage,
                    "provider": provider,
                    "model": model,
                    "diagnostic": {
                        "failure_type": diag.get("failure_type", "WF-08"),
                        "detail": diag.get("detail", ""),
                    },
                })
            if wb_db_entries:
                translation_db.add_entries(wb_db_entries)
        except (OSError, ValueError, TypeError) as e:
            logger.debug(f"记录 writeback_failed 到 translation_db 失败: {e}")

    # 写出翻译后的文件
    out_path = output_dir / rel_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(patched, encoding='utf-8')

    # 更新术语表
    glossary.update_from_translations(unique_translations)

    # 标记完成
    progress.mark_file_done(rel_path)

    return len(unique_translations), all_warnings, total_checker_dropped, chunk_stats_list


def _translate_file_targeted(
    rpy_path: Path,
    game_dir: Path,
    output_dir: Path,
    content: str,
    rel_path: str,
    client: APIClient,
    glossary: Glossary,
    progress: ProgressTracker,
    quality_report: Optional[dict[str, list[dict]]] = None,
    genre: str = "adult",
    *,
    translation_db: Optional[TranslationDB] = None,
    run_id: str = "",
    stage: str = "single",
    provider: str = "",
    model: str = "",
) -> tuple[int, list[str], int, list[dict]]:
    """低密度文件的定向翻译：提取对话行+上下文，走 retranslate 风格 prompt。

    与 retranslate_file 的区别：
    - 输入是未翻译的英文原文件（全量阶段），不是已翻译文件
    - 检测所有 _is_user_visible_string_line 的行（而非仅检测残留英文）
    - 输出到 output_dir（可能与 game_dir 不同）
    - 返回值与 translate_file 一致的 4-tuple
    """
    from renpy_text_utils import _is_user_visible_string_line

    all_lines = content.splitlines()

    # 提取所有对话行的 0-based 索引
    dialogue_indices: list[int] = []
    for i, line in enumerate(all_lines):
        if _is_user_visible_string_line(line):
            m = re.search(r'"([^"\\]*(?:\\.[^"\\]*)*)"', line)
            if m and len(m.group(1)) >= MIN_DIALOGUE_LENGTH:
                dialogue_indices.append(i)

    if not dialogue_indices:
        out_path = output_dir / rel_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(content, encoding="utf-8")
        progress.mark_file_done(rel_path)
        return 0, [], 0, []

    chunks = build_retranslate_chunks(all_lines, dialogue_indices, context=3, max_per_chunk=20)
    logger.debug(f"    [TARGETED] {len(dialogue_indices)} 行对话，{len(chunks)} 个 chunk")

    system_prompt = build_retranslate_system_prompt(
        glossary_text=glossary.to_prompt_text()
    )

    all_translations: list[dict] = []
    all_warnings: list[str] = []
    chunk_stats_list: list[dict] = []
    total_checker_dropped = 0

    for ci, chunk_lines in enumerate(chunks, 1):
        raw_for_detect = "\n".join(
            line for _, line, _ in chunk_lines if line != "..."
        )
        _, ph_mapping = protect_placeholders(raw_for_detect)

        if ph_mapping:
            inv = {orig: token for token, orig in ph_mapping}
            protected: list[tuple[int, str, bool]] = []
            for lineno, line, is_target in chunk_lines:
                if line == "...":
                    protected.append((lineno, line, is_target))
                    continue
                pl = line
                for orig, tok in inv.items():
                    pl = pl.replace(orig, tok)
                protected.append((lineno, pl, is_target))
        else:
            protected = list(chunk_lines)

        user_prompt = build_retranslate_user_prompt(rel_path, protected)
        target_count = sum(1 for _, _, t in chunk_lines if t)
        logger.debug(f"    [API ] 定向块 {ci}/{len(chunks)} ({target_count} 行)")

        try:
            translations = client.translate(system_prompt, user_prompt)
        except Exception as e:
            warn = f"定向块 {ci} API 调用失败: {e}"
            logger.error(f"    [ERROR] {warn}")
            all_warnings.append(warn)
            chunk_stats_list.append({"chunk_idx": ci, "expected": target_count,
                                     "returned": 0, "dropped": 0})
            continue

        _restore_placeholders_in_translations(translations, ph_mapping)
        _strip_char_prefix(translations)

        kept, dropped, _, check_warns = _filter_checked_translations(translations)
        all_warnings.extend(check_warns)
        total_checker_dropped += dropped

        chunk_stats_list.append({"chunk_idx": ci, "expected": target_count,
                                 "returned": len(translations), "dropped": dropped})

        if kept:
            logger.debug(f"    [OK  ] 定向块 {ci}: 获得 {len(kept)} 条翻译")
        all_translations.extend(kept)

    if not all_translations:
        out_path = output_dir / rel_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(content, encoding="utf-8")
        progress.mark_file_done(rel_path)
        return 0, all_warnings, total_checker_dropped, chunk_stats_list

    unique = _deduplicate_translations(all_translations)

    patched, patch_warnings, patch_stats_t = apply_translations(content, unique)
    all_warnings.extend(patch_warnings)

    issues = validate_translation(
        content, patched, rel_path,
        glossary_terms=glossary.terms,
        glossary_locked=glossary.locked_terms,
        glossary_no_translate=glossary.no_translate,
    )
    if quality_report is not None and issues:
        quality_report[rel_path] = issues
    for issue in issues:
        if issue["level"] == "error":
            all_warnings.append(f"行 {issue['line']}: {issue['message']}")

    # 写入回写失败诊断（定向翻译模式）
    wb_failures_t = patch_stats_t.get("writeback_failures", [])
    if translation_db is not None and wb_failures_t:
        try:
            for diag in wb_failures_t:
                line_no = int(diag.get("line") or 0)
                original = diag.get("original", "") or ""
                zh = diag.get("zh", "") or ""
                if not line_no or not original:
                    continue
                if translation_db.has_entry(rel_path, line_no, original):
                    continue
                translation_db.upsert_entry({
                    "file": rel_path, "line": line_no,
                    "original": original, "translation": zh,
                    "status": "writeback_failed",
                    "error_codes": [], "warning_codes": [],
                    "run_id": run_id, "stage": stage,
                    "provider": provider, "model": model,
                    "diagnostic": {
                        "failure_type": diag.get("failure_type", "WF-08"),
                        "detail": diag.get("detail", ""),
                    },
                })
        except (OSError, ValueError, TypeError) as e:
            logger.debug(f"记录 writeback_failed 到 translation_db 失败: {e}")

    if translation_db is not None and unique:
        db_entries = []
        for item in unique:
            line_no = int(item.get("line") or 0)
            original = item.get("original", "") or ""
            zh = item.get("zh", "") or ""
            if not line_no or not original:
                continue
            db_entries.append({
                "file": rel_path,
                "line": line_no,
                "original": original,
                "translation": zh,
                "status": "ok",
                "error_codes": [],
                "warning_codes": [],
                "run_id": run_id,
                "stage": stage,
                "provider": provider,
                "model": model,
            })
        if db_entries:
            translation_db.add_entries(db_entries)

    out_path = output_dir / rel_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(patched, encoding="utf-8")

    glossary.update_from_translations(unique)
    progress.mark_file_done(rel_path)

    return len(unique), all_warnings, total_checker_dropped, chunk_stats_list


# ---- Dry-run helpers ----


def _compute_file_dialogue_stats(filepath: Path) -> tuple[int, float]:
    """返回 (对话行数, 密度)，用于 dry-run 详情。"""
    from translators.retranslator import calculate_dialogue_density
    content = read_file(filepath)
    density = calculate_dialogue_density(content)
    from translators.renpy_text_utils import _is_user_visible_string_line
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


def run_pipeline(args: argparse.Namespace) -> None:
    """运行完整翻译流水线"""
    # SIGTERM 优雅终止支持（非 Windows 平台；Windows 使用 GUI 发送的 CTRL_C_EVENT）
    _interrupted = threading.Event()

    def _sigterm_handler(signum, frame):
        _interrupted.set()
        logger.info("[SIGTERM] 收到终止信号，正在保存进度...")

    if hasattr(signal, 'SIGTERM'):
        signal.signal(signal.SIGTERM, _sigterm_handler)

    game_dir = Path(args.game_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("=" * 60)
    logger.info("Ren'Py 整文件翻译工具")
    logger.info("=" * 60)
    logger.info(f"游戏目录: {game_dir}")
    logger.info(f"输出目录: {output_dir}")
    logger.info(f"API: {args.provider} / {args.model or '默认'}")
    logger.info("")

    # 初始化 API 客户端
    config = APIConfig(
        provider=args.provider,
        api_key=args.api_key or "dummy",
        model=args.model or "",
        rpm=args.rpm,
        rps=args.rps,
        timeout=args.timeout,
        temperature=args.temperature,
        max_response_tokens=args.max_response_tokens,
    )
    client = APIClient(config)
    logger.info(f"[API ] 提供商: {config.provider}, 模型: {config.model}")
    logger.info(f"[API ] 速率限制: RPM={args.rpm}, RPS={args.rps}")
    if args.workers > 1:
        logger.info(f"[API ] 并发线程: {args.workers}")

    # 初始化术语表
    glossary = Glossary()
    glossary_path = output_dir / "glossary.json"
    glossary.load(str(glossary_path))
    glossary.scan_game_directory(str(game_dir))

    # 加载外部词典
    if args.dict:
        for dict_path in args.dict:
            if not Path(dict_path).exists():
                logger.warning(f"[WARN] 词典文件不存在，跳过: {dict_path}")
                continue
            glossary.load_dict(dict_path)

    # 加载项目级系统 UI 术语（可选）
    system_terms_path = output_dir / "system_ui_terms.json"
    glossary.load_system_terms(str(system_terms_path))

    logger.info(f"[GLOSS] {len(glossary.characters)} 角色, "
          f"{len(glossary.terms)} 术语, "
          f"{len(glossary.memory)} 翻译记忆")

    # 初始化进度追踪
    progress = ProgressTracker(output_dir / "progress.json")
    if not args.resume and progress.data.get("completed_files"):
        logger.info(f"[INFO] 发现旧进度（已完成 {len(progress.data['completed_files'])} 个文件）")
        logger.info("[INFO] 清除旧进度，从头开始（如需续传请加 --resume）")
        progress.data = {"completed_files": [], "completed_chunks": {}, "stats": {}}
        progress.save()

    # 初始化 translation DB（用于增量与重翻统计）
    db_path = output_dir / "translation_db.json"
    translation_db = TranslationDB(db_path)
    translation_db.load()
    # 以时间戳标记本次运行；足够区分不同批次
    run_id = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
    stage = getattr(args, "stage", "single") or "single"

    # 扫描 RPY 文件
    rpy_files = sorted(game_dir.rglob('*.rpy'))
    if not rpy_files:
        logger.error("[ERROR] 未找到 .rpy 文件")
        return

    # 自动排除 Ren'Py 引擎自带文件（renpy/ 目录）
    engine_excluded = 0
    filtered = []
    for f in rpy_files:
        rel = str(f.relative_to(game_dir))
        # 排除 renpy/ 和 lib/ 引擎目录
        parts = f.relative_to(game_dir).parts
        if parts and parts[0].lower() in ('renpy', 'lib', '__pycache__'):
            engine_excluded += 1
            continue
        filtered.append(f)
    if engine_excluded:
        logger.info(f"[EXCL] 自动排除 {engine_excluded} 个引擎文件 (renpy/, lib/)")
    rpy_files = filtered

    if not rpy_files:
        logger.error("[ERROR] 排除引擎文件后未找到 .rpy 文件")
        return

    # 排除指定模式的文件
    if args.exclude:
        before = len(rpy_files)
        rpy_files = [
            f for f in rpy_files
            if not any(fnmatch.fnmatch(str(f.relative_to(game_dir)), pat) for pat in args.exclude)
        ]
        excluded = before - len(rpy_files)
        if excluded:
            logger.info(f"[EXCL] 排除了 {excluded} 个匹配的文件")

    # tl 优先模式：若启用且检测到 tl/ 目录中的 .rpy，则仅翻译 tl 下的脚本
    if args.tl_priority:
        tl_files = [
            f for f in rpy_files
            if f.relative_to(game_dir).parts and f.relative_to(game_dir).parts[0] == "tl"
        ]
        if tl_files:
            logger.info(f"[MODE] 启用 tl 优先模式：检测到 {game_dir / 'tl'}，仅翻译 tl 下的脚本，共 {len(tl_files)} 个文件")
            rpy_files = tl_files
        else:
            logger.warning(f"[WARN] 启用了 --tl-priority 但在 {game_dir / 'tl'} 下未找到 .rpy 文件，将回退为翻译所有非引擎脚本，请检查路径是否正确")

    # 按大小排序（小文件优先，便于快速积累翻译记忆）
    rpy_files.sort(key=lambda f: f.stat().st_size)

    total_files = len(rpy_files)
    done_files = sum(1 for f in rpy_files
                     if progress.is_file_done(str(f.relative_to(game_dir))))
    logger.info(f"\n[SCAN] 共 {total_files} 个 .rpy 文件, 已完成 {done_files} 个")

    # 延迟估算 token ―― 只统计未完成文件的 token
    remaining_files = [
        f for f in rpy_files
        if not progress.is_file_done(str(f.relative_to(game_dir)))
    ]
    if remaining_files:
        remaining_tokens = sum(estimate_tokens(read_file(f)) for f in remaining_files)
        logger.info(f"[SCAN] 剩余约 {remaining_tokens:,} tokens")
    else:
        remaining_tokens = 0

    # --dry-run: 仅展示待翻译信息，不实际调用 API
    if args.dry_run:
        from api_client import get_pricing, is_reasoning_model
        logger.info("\n" + "=" * 60)
        logger.info("[DRY-RUN] 以下文件将被翻译:")
        logger.info("=" * 60)
        file_stats = []
        max_chunk = getattr(args, 'max_chunk_tokens', 4000) or 4000
        total_chunks = 0
        for f in remaining_files:
            rel = f.relative_to(game_dir)
            tok = estimate_tokens(read_file(f))
            n_chunks = max(1, tok // max_chunk + (1 if tok % max_chunk else 0))
            total_chunks += n_chunks
            file_stats.append((rel, tok, f.stat().st_size, n_chunks))
            logger.info(f"  {rel}  ({tok:,} tokens, {f.stat().st_size / 1024:.0f} KB"
                  + (f", {n_chunks} chunks)" if n_chunks > 1 else ")"))

        # 统计分布
        if file_stats:
            small = sum(1 for _, t, _, _ in file_stats if t <= 10000)
            medium = sum(1 for _, t, _, _ in file_stats if 10000 < t <= 50000)
            large = sum(1 for _, t, _, _ in file_stats if t > 50000)
            logger.info(f"\n文件分布: 小(≤10K tokens): {small}, 中(10-50K): {medium}, 大(>50K): {large}")
            logger.info(f"预计 API 调用次数: {total_chunks}")

            # 显示最大的 5 个文件
            top5 = sorted(file_stats, key=lambda x: x[1], reverse=True)[:5]
            logger.info("\n最大文件:")
            for rel, tok, _, nc in top5:
                logger.info(f"  {rel}: {tok:,} tokens (约 {nc} 个 chunk)")

        # ---- 精确费用估算 ----
        price_in, price_out, price_exact = get_pricing(config.provider, config.model)
        reasoning = is_reasoning_model(config.model)

        # 输入 = 文件内容 + 每次请求的 system prompt 开销
        # system prompt 约 1500-2000 tokens，加上 user prompt 包装 ≈ 2000 tokens/request
        sys_prompt_overhead = 2000
        total_input = remaining_tokens + total_chunks * sys_prompt_overhead

        # 输出：整文件翻译的 JSON 输出 ≈ 原文件 token 数的 60%
        # （约 40% 行可翻译，每条包含 original + zh + JSON 结构）
        visible_output = int(remaining_tokens * 0.6)

        # 推理模型的 thinking tokens 通常是可见输出的 3~5 倍
        if reasoning:
            reasoning_tokens = visible_output * 4
            total_output = visible_output + reasoning_tokens
        else:
            reasoning_tokens = 0
            total_output = visible_output

        est_cost = (total_input * price_in + total_output * price_out) / 1_000_000

        # 如果用户通过 CLI 覆盖了价格
        if hasattr(args, 'input_price') and args.input_price is not None:
            price_in = args.input_price
        if hasattr(args, 'output_price') and args.output_price is not None:
            price_out = args.output_price
        if hasattr(args, 'input_price') and args.input_price is not None or \
           hasattr(args, 'output_price') and args.output_price is not None:
            est_cost = (total_input * price_in + total_output * price_out) / 1_000_000

        logger.info(f"\n{'=' * 40}")
        logger.info(f"模型: {config.model}")
        logger.info(f"定价: ${price_in:.2f} / ${price_out:.2f} 每百万 tokens (input/output)")
        if not price_exact:
            logger.info(f"[!] 模型 '{config.model}' 未在定价表中精确匹配，使用提供商兜底价格")
            logger.info(f"   建议用 --input-price / --output-price 手动指定准确价格")
        if reasoning:
            logger.info(f"[*] 推理模型: thinking tokens 会显著增加输出费用")
        logger.info(f"{'=' * 40}")
        logger.info(f"剩余文件: {len(remaining_files)}")
        logger.info(f"API 调用次数: ~{total_chunks}")
        logger.info(f"估计输入 tokens: ~{total_input:,} (内容 {remaining_tokens:,} + 提示词开销 {total_chunks * sys_prompt_overhead:,})")
        logger.info(f"估计可见输出 tokens: ~{visible_output:,}")
        if reasoning:
            logger.info(f"估计推理 tokens: ~{reasoning_tokens:,} (thinking)")
            logger.info(f"估计总输出 tokens: ~{total_output:,}")
        logger.info(f"\n>>> 估计费用: ${est_cost:.2f}")
        if reasoning:
            low = est_cost * 0.6
            high = est_cost * 1.5
            logger.info(f"   (推理 token 波动大，实际范围约 ${low:.2f} ~ ${high:.2f})")
        # ---- verbose 增强详情 ----
        if getattr(args, 'verbose', False) and file_stats:
            logger.info("\n" + "=" * 60)
            logger.info("[DRY-RUN] 详细分析（--verbose）")
            logger.info("=" * 60)

            densities = []
            min_density = getattr(args, 'min_dialogue_density', 0.20) or 0.20
            for rel, tok, _size, n_chunks in file_stats:
                fpath = game_dir / rel
                try:
                    dlg_count, density = _compute_file_dialogue_stats(fpath)
                except (OSError, ValueError, UnicodeDecodeError):
                    logger.debug(f"dry-run 文件统计失败: {fpath}", exc_info=True)
                    dlg_count, density = 0, 0.0
                densities.append(density)
                strategy = "定向" if density < min_density else "全文"
                est_file_cost = ((tok + sys_prompt_overhead) * price_in +
                                 int(tok * 0.6) * price_out) / 1_000_000
                logger.info(f"  {rel}: {dlg_count} 对话行, 密度 {density*100:.1f}%, "
                            f"~${est_file_cost:.4f}, 策略={strategy}")

            _print_density_histogram(densities)
            _print_term_scan_preview(glossary)

        logger.info("\n去掉 --dry-run 参数开始实际翻译。")
        return

    logger.info("")

    # 设置日志文件
    log_file = None
    if hasattr(args, 'log_file') and args.log_file:
        log_file = Path(args.log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)

    def log(msg: str):
        """同时输出到控制台和日志文件"""
        if log_file:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(msg + '\n')

    # 开始翻译
    start_time = time.time()
    total_translated = 0
    total_checker_dropped = 0
    total_warnings = []
    files_done_this_run = 0
    quality_report: dict[str, list[dict]] = {}
    all_chunk_stats: list[dict] = []

    # 进度条（仅非 quiet 模式下显示）
    show_progress_bar = not getattr(args, 'quiet', False) and not getattr(args, 'dry_run', False)
    progress_bar = ProgressBar(total_files) if show_progress_bar and total_files > 0 else None

    for i, rpy_path in enumerate(rpy_files, 1):
        # SIGTERM 中断检查
        if _interrupted.is_set():
            logger.info("[SIGTERM] 翻译中断，已保存进度。使用 --resume 继续。")
            break

        rel = rpy_path.relative_to(game_dir)
        done_count = len(progress.data.get("completed_files", []))
        pct = done_count / total_files * 100 if total_files > 0 else 0

        # ETA 计算
        eta_str = ""
        if files_done_this_run > 0:
            elapsed_so_far = time.time() - start_time
            remaining_files_count = total_files - done_count
            avg_time_per_file = elapsed_so_far / files_done_this_run
            eta_seconds = remaining_files_count * avg_time_per_file
            if eta_seconds > 3600:
                eta_str = f" | ETA {eta_seconds/3600:.1f}h"
            elif eta_seconds > 60:
                eta_str = f" | ETA {eta_seconds/60:.0f}min"
            else:
                eta_str = f" | ETA {eta_seconds:.0f}s"

        logger.info(f"\n[{i}/{total_files}] ({pct:.0f}%{eta_str}) {rel}")
        log(f"[{i}/{total_files}] ({pct:.0f}%) {rel}")

        try:
            count, warnings, checker_dropped, file_chunk_stats = translate_file(
                rpy_path,
                game_dir,
                output_dir / "game",
                client,
                glossary,
                progress,
                quality_report,
                genre=args.genre,
                max_tokens_per_chunk=args.max_chunk_tokens,
                workers=args.workers,
                translation_db=translation_db,
                run_id=run_id,
                stage=stage,
                provider=config.provider,
                model=config.model,
                min_dialogue_density=getattr(args, "min_dialogue_density", 0.20),
                cot=getattr(args, "cot", False),
            )
            total_translated += count
            total_checker_dropped += checker_dropped
            total_warnings.extend(warnings)
            all_chunk_stats.extend(file_chunk_stats)
            files_done_this_run += 1
            if progress_bar:
                progress_bar.cost = client.usage.estimated_cost
                progress_bar.update(1)
        except KeyboardInterrupt:
            logger.info("\n[中断] 保存进度...")
            glossary.save(str(glossary_path))
            progress.save()
            try:
                translation_db.save()
            except OSError as e:
                logger.debug(f"中断时保存 translation_db 失败: {e}")
            logger.info("[中断] 进度已保存，可用 --resume 继续")
            sys.exit(1)
        except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as e:
            msg = f"文件 {rel} 处理失败: {e}"
            logger.error(f"  [ERROR] {msg}")
            total_warnings.append(msg)
            continue

        # 定期保存术语表
        if i % 5 == 0:
            glossary.save(str(glossary_path))

    if progress_bar:
        progress_bar.finish()

    # 最终保存
    glossary.save(str(glossary_path))
    try:
        translation_db.save()
    except OSError as e:
        logger.warning(f"[WARN] 保存 translation_db.json 失败: {e}")

    # 复制非 .rpy 文件（可选）
    if args.copy_assets:
        logger.info("\n[复制] 复制非 .rpy 文件...")
        asset_count = 0
        for src in game_dir.rglob('*'):
            if src.is_file() and src.suffix.lower() not in ('.rpy', '.rpyc', '.rpymc', '.rpyb'):
                rel = src.relative_to(game_dir)
                dst = output_dir / "game" / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                if not dst.exists():
                    shutil.copy2(src, dst)
                    asset_count += 1
        if asset_count:
            logger.info(f"[复制] 复制了 {asset_count} 个资源文件")

    # 自动字体补丁（可选）
    if getattr(args, "patch_font", False):
        resources_fonts = Path(__file__).parent / "resources" / "fonts"
        font_path = resolve_font(resources_fonts, args.font_file or None)
        if font_path:
            apply_font_patch(output_dir / "game", game_dir, font_path)
        # resolve_font 内部已打印警告，此处无需再报错

    # 总结
    elapsed = time.time() - start_time
    logger.info("\n" + "=" * 60)
    logger.info("翻译完成")
    logger.info("=" * 60)
    logger.info(f"文件数: {total_files}")
    logger.info(f"翻译条目: {total_translated}")
    logger.info(f"Checker 丢弃（未写入译文）: {total_checker_dropped}")

    # per-chunk 指标摘要
    if all_chunk_stats:
        try:
            cs_total_expected = sum(c["expected"] for c in all_chunk_stats)
            cs_total_returned = sum(c["returned"] for c in all_chunk_stats)
            cs_total_dropped = sum(c["dropped"] for c in all_chunk_stats)
            ret_pct = (cs_total_returned / cs_total_expected * 100) if cs_total_expected else 0
            drop_pct = (cs_total_dropped / cs_total_returned * 100) if cs_total_returned else 0
            logger.info(f"[STATS] Chunks: {len(all_chunk_stats)} | "
                  f"Expected: {cs_total_expected} | "
                  f"Returned: {cs_total_returned} ({ret_pct:.1f}%) | "
                  f"Dropped: {cs_total_dropped} ({drop_pct:.1f}%)")
        except (ZeroDivisionError, KeyError, TypeError) as e:
            logger.debug(f"chunk 统计汇总计算失败: {e}")

    logger.info(f"警告: {len(total_warnings)}")
    logger.info(f"耗时: {elapsed / 60:.1f} 分钟")
    logger.info(f"API 用量: {client.usage.summary()}")
    logger.info(f"输出目录: {output_dir / 'game'}")

    if total_warnings:
        warnings_path = output_dir / "warnings.txt"
        warnings_path.write_text('\n'.join(total_warnings), encoding='utf-8')
        logger.info(f"警告详情: {warnings_path}")

    # 保存质量检查报告（按文件归档）
    if quality_report:
        quality_path = output_dir / "quality_report.json"
        quality_path.write_text(json.dumps(quality_report, ensure_ascii=False, indent=2), encoding='utf-8')
        logger.info(f"质量报告: {quality_path}")

    # 汇总 chunk_stats
    chunk_stats_summary = {}
    if all_chunk_stats:
        try:
            chunk_stats_summary = {
                "total_expected": sum(c["expected"] for c in all_chunk_stats),
                "total_returned": sum(c["returned"] for c in all_chunk_stats),
                "total_dropped": sum(c["dropped"] for c in all_chunk_stats),
                "per_chunk": all_chunk_stats,
            }
        except (KeyError, TypeError) as e:
            logger.debug(f"chunk 统计写入 report 失败: {e}")

    # 保存翻译报告
    report = {
        "total_files": total_files,
        "total_translated": total_translated,
        "total_checker_dropped": total_checker_dropped,
        "total_warnings": len(total_warnings),
        "elapsed_minutes": round(elapsed / 60, 1),
        "provider": args.provider,
        "model": config.model,
        "workers": args.workers,
        "api_requests": client.usage.total_requests,
        "input_tokens": client.usage.total_input_tokens,
        "output_tokens": client.usage.total_output_tokens,
        "estimated_cost_usd": round(client.usage.estimated_cost, 4),
        "chunk_stats": chunk_stats_summary,
    }
    report_path = output_dir / "report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    logger.info(f"翻译报告: {report_path}")


# ============================================================
# 对话密度检测
# ============================================================

