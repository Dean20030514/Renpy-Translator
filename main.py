#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ren'Py 整文件翻译工具 — 将完整 .rpy 文件发给 AI，由 AI 自行识别可翻译内容

核心优势：
  - AI 看到完整文件上下文，自行判断什么该翻什么不该翻
  - 不会误翻 screen 关键字、变量名、配置值
  - 跨文件术语一致性（自动维护术语表）
  - 翻译安全校验（变量、标签、缩进、代码结构检查）

用法：
  python main.py --game-dir "E:\\Games\\MyGame" --provider xai --api-key YOUR_KEY
  python main.py --game-dir "E:\\Games\\MyGame" --provider openai --api-key YOUR_KEY --model gpt-4o
  python main.py --resume   # 从上次中断处继续

文件流程：
  扫描 .rpy → 拆分大文件 → 发送 AI 翻译 → JSON 回传 → Patch 回原文件 → 校验
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import shutil
import sys
import time
import threading
import concurrent.futures
from pathlib import Path
from typing import Optional

from dataclasses import dataclass, field

from api_client import APIClient, APIConfig
from file_processor import (
    split_file,
    apply_translations,
    validate_translation,
    estimate_tokens,
    read_file,
    protect_placeholders,
    restore_placeholders,
    check_response_item,
    check_response_chunk,
    _count_translatable_lines_in_chunk,
    SKIP_FILES_FOR_TRANSLATION,
)
from glossary import Glossary
from prompts import (
    build_system_prompt,
    build_user_prompt,
    build_retranslate_system_prompt,
    build_retranslate_user_prompt,
    build_tl_system_prompt,
    build_tl_user_prompt,
)
from translation_db import TranslationDB
from font_patch import resolve_font, apply_font_patch


# ============================================================
# Chunk 翻译结果
# ============================================================

@dataclass
class ChunkResult:
    """单个 chunk 的翻译结果（替代原有 8-tuple）"""
    part: int                              # chunk 序号
    kept: list = field(default_factory=list)       # 通过校验的翻译条目
    error: str | None = None               # 错误信息（None 表示成功）
    chunk_warnings: list = field(default_factory=list)  # chunk 级警告
    dropped_count: int = 0                 # 被 checker 丢弃的条数
    expected: int = 0                      # chunk 内预期可翻译行数
    returned: int = 0                      # API 实际返回条数
    dropped_items: list = field(default_factory=list)   # 被丢弃的原始条目


# ============================================================
# 进度管理（断点续传）
# ============================================================

class ProgressTracker:
    """追踪翻译进度，支持中断续传"""

    def __init__(self, progress_file: Path):
        self.path = progress_file
        self._lock = threading.Lock()
        self.data: dict = {"completed_files": [], "completed_chunks": {}, "stats": {}}
        self._load()

    def _load(self):
        if self.path.exists():
            self.data = json.loads(self.path.read_text(encoding='utf-8'))

    def save(self):
        with self._lock:
            self._save_unlocked()

    def _save_unlocked(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix('.tmp')
        tmp.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding='utf-8')
        os.replace(str(tmp), str(self.path))

    def is_file_done(self, rel_path: str) -> bool:
        return rel_path in self.data["completed_files"]

    def is_chunk_done(self, rel_path: str, part: int) -> bool:
        return part in self.data.get("completed_chunks", {}).get(rel_path, [])

    def mark_chunk_done(self, rel_path: str, part: int, translations: list[dict]):
        with self._lock:
            chunks = self.data.setdefault("completed_chunks", {})
            chunk_list = chunks.setdefault(rel_path, [])
            if part not in chunk_list:
                chunk_list.append(part)

            # 保存该 chunk 的翻译结果
            results = self.data.setdefault("results", {})
            file_results = results.setdefault(rel_path, [])
            file_results.extend(translations)
            self._save_unlocked()

    def get_file_translations(self, rel_path: str) -> list[dict]:
        """获取文件的所有已完成翻译"""
        return self.data.get("results", {}).get(rel_path, [])

    def mark_file_done(self, rel_path: str):
        with self._lock:
            if rel_path not in self.data["completed_files"]:
                self.data["completed_files"].append(rel_path)
            # 清理 chunk 和 results 数据（文件完成后不再需要，避免 progress.json 膨胀）
            self.data.get("completed_chunks", {}).pop(rel_path, None)
            self.data.get("results", {}).pop(rel_path, None)
            self._save_unlocked()

    def update_stats(self, key: str, value):
        with self._lock:
            self.data.setdefault("stats", {})[key] = value
            self._save_unlocked()



# ============================================================
# 主流程
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
        print(f"  [SKIP-CFG] {rel_path} (配置文件，跳过翻译)")
        return 0, [], 0, []

    # 断点续传：已完成则跳过
    if progress.is_file_done(rel_path):
        print(f"  [SKIP] {rel_path} (已完成)")
        return 0, [], 0, []

    content = read_file(rpy_path)
    tokens = estimate_tokens(content)
    print(f"  [FILE] {rel_path}  ({tokens:,} tokens)")

    # 密度检测：低密度文件走定向翻译，避免 AI 注意力被代码行稀释
    density = calculate_dialogue_density(content)
    if density < min_dialogue_density:
        print(f"    [DENSITY] 对话密度 {density * 100:.1f}% < {min_dialogue_density * 100:.0f}%，"
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
        print(f"    拆分为 {len(chunks)} 个块")

    # 构建 prompt（按题材 + 项目名选择外部模板）
    project_name = game_dir.parent.name if game_dir.name.lower() == "game" else game_dir.name
    system_prompt = build_system_prompt(
        genre=genre,
        glossary_text=glossary.to_prompt_text(),
        project_name=project_name,
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
        print(f"    [SKIP] {done_chunks}/{len(chunks)} 个块已完成")

    total_checker_dropped = 0

    def _translate_chunk(chunk) -> ChunkResult:
        """翻译单个 chunk，返回 ChunkResult。"""
        part = chunk["part"]
        chunk_info = {
            "part": part,
            "total": chunk["total"],
            "line_offset": chunk["line_offset"],
        }
        expected_count = _count_translatable_lines_in_chunk(chunk["content"])
        # 占位符保护 — 发 API 前将 [var]、{{#id}}、%(name)s 等替换为令牌
        protected_content, ph_mapping = protect_placeholders(chunk["content"])
        user_prompt = build_user_prompt(rel_path, protected_content, chunk_info)
        print(f"    [API ] 块 {part}/{chunk['total']}  "
              f"({estimate_tokens(chunk['content']):,} tokens)")
        try:
            translations = client.translate(system_prompt, user_prompt)
        except Exception as e:
            return ChunkResult(part=part, error=f"块 {part} API 调用失败: {e}", expected=expected_count)
        # 占位符还原 — 将响应中的令牌还原为原始占位符
        for t in translations:
            t["original"] = restore_placeholders(t.get("original") or "", ph_mapping)
            t["zh"] = restore_placeholders(t.get("zh") or "", ph_mapping)
        # Chunk 级检查（条数一致）
        chunk_warnings = check_response_chunk(protected_content, translations)
        for w in chunk_warnings:
            print(f"    [CHECK] {w}")
        # 逐条检查 — 有警告则丢弃该条，不写入译文（宁可漏翻也不误翻）
        kept: list[dict] = []
        dropped_items: list[dict] = []
        dropped_count = 0
        for t in translations:
            item_warnings = check_response_item(t)
            if item_warnings:
                dropped_count += 1
                dropped_items.append(t)
                for w in item_warnings:
                    print(f"    [CHECK-DROPPED] {w}")
                    all_warnings.append(f"[CHECK-DROPPED] {w}")
            else:
                kept.append(t)
        if not translations:
            print(f"    [INFO] 块 {part}: 无需翻译的内容")
        else:
            print(f"    [OK  ] 块 {part}: 获得 {len(translations)} 条翻译"
                  + (f", 丢弃 {dropped_count} 条" if dropped_count else ""))
        return ChunkResult(
            part=part, kept=kept, chunk_warnings=chunk_warnings,
            dropped_count=dropped_count, expected=expected_count,
            returned=len(translations), dropped_items=dropped_items,
        )

    if workers > 1 and len(pending_chunks) > 1:
        # 并发翻译多个 chunk
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(_translate_chunk, c): c for c in pending_chunks}
            for future in concurrent.futures.as_completed(futures):
                cr = future.result()
                chunk_stats_list.append({"chunk_idx": cr.part, "expected": cr.expected, "returned": cr.returned, "dropped": cr.dropped_count})
                if cr.error:
                    print(f"    [ERROR] {cr.error}")
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
            cr = _translate_chunk(chunk)
            chunk_stats_list.append({"chunk_idx": cr.part, "expected": cr.expected, "returned": cr.returned, "dropped": cr.dropped_count})
            if cr.error:
                print(f"    [ERROR] {cr.error}")
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
    seen = set()
    unique_translations = []
    for t in all_translations:
        key = (t.get('line', 0), t.get('original', ''))
        if key not in seen:
            seen.add(key)
            unique_translations.append(t)

    # 应用翻译
    patched, patch_warnings, _ = apply_translations(content, unique_translations)
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
                key = (rel_path, line_no, original)
                if key in translation_db._index:
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
        except Exception:
            pass

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
    import re as _re
    from one_click_pipeline import _is_user_visible_string_line

    all_lines = content.splitlines()

    # 提取所有对话行的 0-based 索引
    dialogue_indices: list[int] = []
    for i, line in enumerate(all_lines):
        if _is_user_visible_string_line(line):
            m = _re.search(r'"([^"\\]*(?:\\.[^"\\]*)*)"', line)
            if m and len(m.group(1)) >= 4:
                dialogue_indices.append(i)

    if not dialogue_indices:
        out_path = output_dir / rel_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(content, encoding="utf-8")
        progress.mark_file_done(rel_path)
        return 0, [], 0, []

    chunks = build_retranslate_chunks(all_lines, dialogue_indices, context=3, max_per_chunk=20)
    print(f"    [TARGETED] {len(dialogue_indices)} 行对话，{len(chunks)} 个 chunk")

    system_prompt = build_retranslate_system_prompt(
        glossary_text=glossary.to_prompt_text()
    )

    all_translations: list[dict] = []
    all_warnings: list[str] = []
    chunk_stats_list: list[dict] = []
    total_checker_dropped = 0
    _char_prefix_re = _re.compile(r'^[a-zA-Z_]\w*\s+"((?:[^"\\]|\\.)*)"$')

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
        print(f"    [API ] 定向块 {ci}/{len(chunks)} ({target_count} 行)")

        try:
            translations = client.translate(system_prompt, user_prompt)
        except Exception as e:
            warn = f"定向块 {ci} API 调用失败: {e}"
            print(f"    [ERROR] {warn}")
            all_warnings.append(warn)
            chunk_stats_list.append({"chunk_idx": ci, "expected": target_count,
                                     "returned": 0, "dropped": 0})
            continue

        for t in translations:
            t["original"] = restore_placeholders(t.get("original") or "", ph_mapping)
            t["zh"] = restore_placeholders(t.get("zh") or "", ph_mapping)

        for t in translations:
            for key in ("original", "zh"):
                val = t.get(key, "") or ""
                m2 = _char_prefix_re.match(val)
                if m2:
                    t[key] = m2.group(1)

        kept: list[dict] = []
        dropped = 0
        for t in translations:
            item_warnings = check_response_item(t)
            if item_warnings:
                for w in item_warnings:
                    all_warnings.append(f"[CHECK-DROPPED] {w}")
                dropped += 1
                total_checker_dropped += 1
            else:
                kept.append(t)

        chunk_stats_list.append({"chunk_idx": ci, "expected": target_count,
                                 "returned": len(translations), "dropped": dropped})

        if kept:
            print(f"    [OK  ] 定向块 {ci}: 获得 {len(kept)} 条翻译")
        all_translations.extend(kept)

    if not all_translations:
        out_path = output_dir / rel_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(content, encoding="utf-8")
        progress.mark_file_done(rel_path)
        return 0, all_warnings, total_checker_dropped, chunk_stats_list

    seen: set[tuple] = set()
    unique: list[dict] = []
    for t in all_translations:
        key = (t.get("line", 0), t.get("original", ""))
        if key not in seen:
            seen.add(key)
            unique.append(t)

    patched, patch_warnings, _ = apply_translations(content, unique)
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


def run_pipeline(args: argparse.Namespace) -> None:
    """运行完整翻译流水线"""
    game_dir = Path(args.game_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Ren'Py 整文件翻译工具")
    print("=" * 60)
    print(f"游戏目录: {game_dir}")
    print(f"输出目录: {output_dir}")
    print(f"API: {args.provider} / {args.model or '默认'}")
    print()

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
    print(f"[API ] 提供商: {config.provider}, 模型: {config.model}")
    print(f"[API ] 速率限制: RPM={args.rpm}, RPS={args.rps}")
    if args.workers > 1:
        print(f"[API ] 并发线程: {args.workers}")

    # 初始化术语表
    glossary = Glossary()
    glossary_path = output_dir / "glossary.json"
    glossary.load(str(glossary_path))
    glossary.scan_game_directory(str(game_dir))

    # 加载外部词典
    if args.dict:
        for dict_path in args.dict:
            glossary.load_dict(dict_path)

    # 加载项目级系统 UI 术语（可选）
    system_terms_path = output_dir / "system_ui_terms.json"
    glossary.load_system_terms(str(system_terms_path))

    print(f"[GLOSS] {len(glossary.characters)} 角色, "
          f"{len(glossary.terms)} 术语, "
          f"{len(glossary.memory)} 翻译记忆")

    # 初始化进度追踪
    progress = ProgressTracker(output_dir / "progress.json")
    if not args.resume and progress.data.get("completed_files"):
        print(f"[INFO] 发现旧进度（已完成 {len(progress.data['completed_files'])} 个文件）")
        print("[INFO] 清除旧进度，从头开始（如需续传请加 --resume）")
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
        print("[ERROR] 未找到 .rpy 文件")
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
        print(f"[EXCL] 自动排除 {engine_excluded} 个引擎文件 (renpy/, lib/)")
    rpy_files = filtered

    if not rpy_files:
        print("[ERROR] 排除引擎文件后未找到 .rpy 文件")
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
            print(f"[EXCL] 排除了 {excluded} 个匹配的文件")

    # tl 优先模式：若启用且检测到 tl/ 目录中的 .rpy，则仅翻译 tl 下的脚本
    if args.tl_priority:
        tl_files = [
            f for f in rpy_files
            if f.relative_to(game_dir).parts and f.relative_to(game_dir).parts[0] == "tl"
        ]
        if tl_files:
            print(f"[MODE] 启用 tl 优先模式：检测到 {game_dir / 'tl'}，仅翻译 tl 下的脚本，共 {len(tl_files)} 个文件")
            rpy_files = tl_files
        else:
            print(f"[WARN] 启用了 --tl-priority 但在 {game_dir / 'tl'} 下未找到 .rpy 文件，将回退为翻译所有非引擎脚本，请检查路径是否正确")

    # 按大小排序（小文件优先，便于快速积累翻译记忆）
    rpy_files.sort(key=lambda f: f.stat().st_size)

    total_files = len(rpy_files)
    done_files = sum(1 for f in rpy_files
                     if progress.is_file_done(str(f.relative_to(game_dir))))
    print(f"\n[SCAN] 共 {total_files} 个 .rpy 文件, 已完成 {done_files} 个")

    # 延迟估算 token ―― 只统计未完成文件的 token
    remaining_files = [
        f for f in rpy_files
        if not progress.is_file_done(str(f.relative_to(game_dir)))
    ]
    if remaining_files:
        remaining_tokens = sum(estimate_tokens(read_file(f)) for f in remaining_files)
        print(f"[SCAN] 剩余约 {remaining_tokens:,} tokens")
    else:
        remaining_tokens = 0

    # --dry-run: 仅展示待翻译信息，不实际调用 API
    if args.dry_run:
        from api_client import get_pricing, is_reasoning_model
        print("\n" + "=" * 60)
        print("[DRY-RUN] 以下文件将被翻译:")
        print("=" * 60)
        file_stats = []
        max_chunk = getattr(args, 'max_chunk_tokens', 4000) or 4000
        total_chunks = 0
        for f in remaining_files:
            rel = f.relative_to(game_dir)
            tok = estimate_tokens(read_file(f))
            n_chunks = max(1, tok // max_chunk + (1 if tok % max_chunk else 0))
            total_chunks += n_chunks
            file_stats.append((rel, tok, f.stat().st_size, n_chunks))
            print(f"  {rel}  ({tok:,} tokens, {f.stat().st_size / 1024:.0f} KB"
                  + (f", {n_chunks} chunks)" if n_chunks > 1 else ")"))

        # 统计分布
        if file_stats:
            small = sum(1 for _, t, _, _ in file_stats if t <= 10000)
            medium = sum(1 for _, t, _, _ in file_stats if 10000 < t <= 50000)
            large = sum(1 for _, t, _, _ in file_stats if t > 50000)
            print(f"\n文件分布: 小(≤10K tokens): {small}, 中(10-50K): {medium}, 大(>50K): {large}")
            print(f"预计 API 调用次数: {total_chunks}")

            # 显示最大的 5 个文件
            top5 = sorted(file_stats, key=lambda x: x[1], reverse=True)[:5]
            print("\n最大文件:")
            for rel, tok, _, nc in top5:
                print(f"  {rel}: {tok:,} tokens (约 {nc} 个 chunk)")

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

        print(f"\n{'=' * 40}")
        print(f"模型: {config.model}")
        print(f"定价: ${price_in:.2f} / ${price_out:.2f} 每百万 tokens (input/output)")
        if not price_exact:
            print(f"[!] 模型 '{config.model}' 未在定价表中精确匹配，使用提供商兜底价格")
            print(f"   建议用 --input-price / --output-price 手动指定准确价格")
        if reasoning:
            print(f"[*] 推理模型: thinking tokens 会显著增加输出费用")
        print(f"{'=' * 40}")
        print(f"剩余文件: {len(remaining_files)}")
        print(f"API 调用次数: ~{total_chunks}")
        print(f"估计输入 tokens: ~{total_input:,} (内容 {remaining_tokens:,} + 提示词开销 {total_chunks * sys_prompt_overhead:,})")
        print(f"估计可见输出 tokens: ~{visible_output:,}")
        if reasoning:
            print(f"估计推理 tokens: ~{reasoning_tokens:,} (thinking)")
            print(f"估计总输出 tokens: ~{total_output:,}")
        print(f"\n>>> 估计费用: ${est_cost:.2f}")
        if reasoning:
            low = est_cost * 0.6
            high = est_cost * 1.5
            print(f"   (推理 token 波动大，实际范围约 ${low:.2f} ~ ${high:.2f})")
        print("\n去掉 --dry-run 参数开始实际翻译。")
        return

    print()

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

    for i, rpy_path in enumerate(rpy_files, 1):
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

        print(f"\n[{i}/{total_files}] ({pct:.0f}%{eta_str}) {rel}")
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
            )
            total_translated += count
            total_checker_dropped += checker_dropped
            total_warnings.extend(warnings)
            all_chunk_stats.extend(file_chunk_stats)
            files_done_this_run += 1
        except KeyboardInterrupt:
            print("\n[中断] 保存进度...")
            glossary.save(str(glossary_path))
            progress.save()
            try:
                translation_db.save()
            except Exception:
                pass
            print("[中断] 进度已保存，可用 --resume 继续")
            sys.exit(1)
        except Exception as e:
            msg = f"文件 {rel} 处理失败: {e}"
            print(f"  [ERROR] {msg}")
            total_warnings.append(msg)
            continue

        # 定期保存术语表
        if i % 5 == 0:
            glossary.save(str(glossary_path))

    # 最终保存
    glossary.save(str(glossary_path))
    try:
        translation_db.save()
    except Exception as e:
        print(f"[WARN] 保存 translation_db.json 失败: {e}")

    # 复制非 .rpy 文件（可选）
    if args.copy_assets:
        print("\n[复制] 复制非 .rpy 文件...")
        asset_count = 0
        for src in game_dir.rglob('*'):
            if src.is_file() and src.suffix.lower() not in ('.rpy', '.rpyc', '.rpyb'):
                rel = src.relative_to(game_dir)
                dst = output_dir / "game" / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                if not dst.exists():
                    shutil.copy2(src, dst)
                    asset_count += 1
        if asset_count:
            print(f"[复制] 复制了 {asset_count} 个资源文件")

    # 自动字体补丁（可选）
    if getattr(args, "patch_font", False):
        resources_fonts = Path(__file__).parent / "resources" / "fonts"
        font_path = resolve_font(resources_fonts, args.font_file or None)
        if font_path:
            apply_font_patch(output_dir / "game", game_dir, font_path)
        # resolve_font 内部已打印警告，此处无需再报错

    # 总结
    elapsed = time.time() - start_time
    print("\n" + "=" * 60)
    print("翻译完成")
    print("=" * 60)
    print(f"文件数: {total_files}")
    print(f"翻译条目: {total_translated}")
    print(f"Checker 丢弃（未写入译文）: {total_checker_dropped}")

    # per-chunk 指标摘要
    if all_chunk_stats:
        try:
            cs_total_expected = sum(c["expected"] for c in all_chunk_stats)
            cs_total_returned = sum(c["returned"] for c in all_chunk_stats)
            cs_total_dropped = sum(c["dropped"] for c in all_chunk_stats)
            ret_pct = (cs_total_returned / cs_total_expected * 100) if cs_total_expected else 0
            drop_pct = (cs_total_dropped / cs_total_returned * 100) if cs_total_returned else 0
            print(f"[STATS] Chunks: {len(all_chunk_stats)} | "
                  f"Expected: {cs_total_expected} | "
                  f"Returned: {cs_total_returned} ({ret_pct:.1f}%) | "
                  f"Dropped: {cs_total_dropped} ({drop_pct:.1f}%)")
        except Exception:
            pass

    print(f"警告: {len(total_warnings)}")
    print(f"耗时: {elapsed / 60:.1f} 分钟")
    print(f"API 用量: {client.usage.summary()}")
    print(f"输出目录: {output_dir / 'game'}")

    if total_warnings:
        warnings_path = output_dir / "warnings.txt"
        warnings_path.write_text('\n'.join(total_warnings), encoding='utf-8')
        print(f"警告详情: {warnings_path}")

    # 保存质量检查报告（按文件归档）
    if quality_report:
        quality_path = output_dir / "quality_report.json"
        quality_path.write_text(json.dumps(quality_report, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f"质量报告: {quality_path}")

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
        except Exception:
            pass

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
    print(f"翻译报告: {report_path}")


# ============================================================
# 对话密度检测
# ============================================================

def calculate_dialogue_density(content: str) -> float:
    """计算文件中对话行占非空行的比例。

    用于全量翻译时自动选择翻译策略：
    高密度文件 → 整文件翻译（AI 自主识别）；
    低密度文件 → 定向翻译（工具指定哪些行翻译）。
    """
    from one_click_pipeline import _is_user_visible_string_line

    non_empty = 0
    dialogue = 0
    for line in content.splitlines():
        if not line.strip():
            continue
        non_empty += 1
        if _is_user_visible_string_line(line):
            dialogue += 1
    return dialogue / non_empty if non_empty else 0.0


# ============================================================
# 补翻模式 (--retranslate)
# ============================================================

def find_untranslated_lines(content: str) -> list[tuple[int, str]]:
    """扫描文件内容，找出仍含英文对话的行。

    复用 one_click_pipeline._is_user_visible_string_line 判断用户可见性，
    再用中/英字符比判断是否仍为未翻译英文。

    Returns:
        [(0-based_line_index, quoted_english_text), ...]
    """
    import re as _re
    from one_click_pipeline import _is_user_visible_string_line

    # screen 属性关键字——引号后紧跟这些词说明是 UI 布局行而非对话
    _SCREEN_ATTR_KW = {"xalign", "yalign", "xpos", "ypos", "xsize", "ysize",
                       "xoffset", "yoffset", "xanchor", "yanchor", "at",
                       "align", "pos", "anchor", "size", "area"}

    results = []
    for i, line in enumerate(content.splitlines()):
        if not _is_user_visible_string_line(line):
            continue
        stripped = line.strip()

        # --- 二次过滤：排除非对话行 ---
        # auto 图片定义行：auto "path_%s.png"（来自 SAZMOD locations.rpy 等）
        if stripped.startswith('auto "'):
            continue
        # imagebutton 属性行：idle/hover/insensitive "image_name"
        if stripped.startswith(('idle "', 'hover "', 'insensitive "')):
            continue

        m = _re.search(r'"([^"\\]*(?:\\.[^"\\]*)*)"', line)
        if not m:
            continue
        s = m.group(1)
        if len(s) < 20:
            continue
        if any(x in s for x in ("/", "\\", ".png", ".jpg", ".webp", ".ttf", ".webm")):
            continue

        # screen 布局行：text "..." 后紧跟 xalign/ypos 等属性
        # 样本：text "Davide" xalign .5 ypos 150
        after_quote = line[m.end():]
        first_word = after_quote.split()[0] if after_quote.split() else ""
        if first_word.lower() in _SCREEN_ATTR_KW:
            continue

        cn = sum(1 for c in s if "\u4e00" <= c <= "\u9fff")
        en = sum(1 for c in s if "a" <= c.lower() <= "z")
        if cn == 0 and en >= 12:
            results.append((i, s))
    return results


def build_retranslate_chunks(
    all_lines: list[str],
    untranslated_indices: list[int],
    context: int = 3,
    max_per_chunk: int = 20,
) -> list[list[tuple[int, str, bool]]]:
    """将漏翻行分组为小 chunk，每个 chunk 附带上下文行。

    对非连续的漏翻行，合并重叠的上下文窗口，用 ``...`` 分隔符标记不连续区域。

    Returns:
        list of chunks; 每个 chunk 为 [(1-based_lineno, line_content, is_target), ...]
        分隔行以 lineno=0、content="..." 表示。
    """
    if not untranslated_indices:
        return []

    target_set = set(untranslated_indices)
    n_lines = len(all_lines)

    def _merge_ranges(indices: list[int]) -> list[tuple[int, int]]:
        ranges: list[tuple[int, int]] = []
        for idx in sorted(indices):
            lo = max(0, idx - context)
            hi = min(n_lines - 1, idx + context)
            if ranges and lo <= ranges[-1][1] + 1:
                ranges[-1] = (ranges[-1][0], hi)
            else:
                ranges.append((lo, hi))
        return ranges

    chunks: list[list[tuple[int, str, bool]]] = []
    for start in range(0, len(untranslated_indices), max_per_chunk):
        group = untranslated_indices[start:start + max_per_chunk]
        ranges = _merge_ranges(group)
        chunk_lines: list[tuple[int, str, bool]] = []
        for ri, (lo, hi) in enumerate(ranges):
            if ri > 0:
                chunk_lines.append((0, "...", False))
            for idx in range(lo, hi + 1):
                chunk_lines.append((idx + 1, all_lines[idx], idx in target_set))
        chunks.append(chunk_lines)

    return chunks


def retranslate_file(
    rpy_path: Path,
    game_dir: Path,
    output_dir: Path,
    client: APIClient,
    glossary: Glossary,
    progress: ProgressTracker,
    quality_report: Optional[dict[str, list[dict]]] = None,
    genre: str = "adult",
    context_lines: int = 3,
    max_per_chunk: int = 20,
    *,
    translation_db: Optional[TranslationDB] = None,
    run_id: str = "",
    stage: str = "retranslate",
    provider: str = "",
    model: str = "",
) -> tuple[int, list[str]]:
    """补翻单个文件中残留的英文对话行。

    流程：扫描漏翻行 → 构建小 chunk → 发送专用 prompt → 逐条检查 → 回写。
    走 apply_translations + validate_translation 现有安全流程。

    Returns:
        (translated_count, warnings)
    """
    rel_path = str(rpy_path.relative_to(game_dir))

    if progress.is_file_done(rel_path):
        return 0, []

    content = read_file(rpy_path)
    all_lines = content.splitlines()

    untranslated = find_untranslated_lines(content)
    if not untranslated:
        progress.mark_file_done(rel_path)
        return 0, []

    print(f"  [RETRANSLATE] {rel_path}: {len(untranslated)} 行待补翻")

    indices = [idx for idx, _ in untranslated]
    chunks = build_retranslate_chunks(all_lines, indices, context_lines, max_per_chunk)

    system_prompt = build_retranslate_system_prompt(
        glossary_text=glossary.to_prompt_text()
    )

    all_translations: list[dict] = []
    all_warnings: list[str] = []

    for ci, chunk_lines in enumerate(chunks, 1):
        # 占位符保护：先在拼接的原始文本上检测模式，再逐行替换
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
        print(f"    [API ] 补翻块 {ci}/{len(chunks)} ({target_count} 行)")

        try:
            translations = client.translate(system_prompt, user_prompt)
        except Exception as e:
            warn = f"补翻块 {ci} API 调用失败: {e}"
            print(f"    [ERROR] {warn}")
            all_warnings.append(warn)
            continue

        for t in translations:
            t["original"] = restore_placeholders(t.get("original") or "", ph_mapping)
            t["zh"] = restore_placeholders(t.get("zh") or "", ph_mapping)

        import re as _re
        _char_prefix_re = _re.compile(r'^[a-zA-Z_]\w*\s+"((?:[^"\\]|\\.)*)"$')
        for t in translations:
            for key in ("original", "zh"):
                val = t.get(key, "") or ""
                m = _char_prefix_re.match(val)
                if m:
                    t[key] = m.group(1)

        kept: list[dict] = []
        for t in translations:
            item_warnings = check_response_item(t)
            if item_warnings:
                for w in item_warnings:
                    print(f"    [CHECK-DROPPED] {w}")
                    all_warnings.append(f"[CHECK-DROPPED] {w}")
            else:
                kept.append(t)

        if kept:
            print(f"    [OK  ] 补翻块 {ci}: 获得 {len(kept)} 条翻译")
        all_translations.extend(kept)

    if not all_translations:
        progress.mark_file_done(rel_path)
        return 0, all_warnings

    # 去重
    seen: set[tuple] = set()
    unique: list[dict] = []
    for t in all_translations:
        key = (t.get("line", 0), t.get("original", ""))
        if key not in seen:
            seen.add(key)
            unique.append(t)

    # 回写（走现有安全流程）
    patched, patch_warnings, _ = apply_translations(content, unique)
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

    # 原地补翻时自动备份原文件（.bak 已存在则不覆盖，保留最早备份）
    if out_path.resolve() == rpy_path.resolve():
        bak_path = out_path.with_suffix(out_path.suffix + ".bak")
        if not bak_path.exists():
            try:
                shutil.copy2(out_path, bak_path)
            except Exception:
                pass

    out_path.write_text(patched, encoding="utf-8")

    glossary.update_from_translations(unique)
    progress.mark_file_done(rel_path)

    return len(unique), all_warnings


def run_retranslate_pipeline(args: argparse.Namespace) -> None:
    """运行漏翻补翻流水线。

    扫描 --game-dir 中的已翻译 .rpy 文件，提取残留英文对话行，
    构建小 chunk 发送专用 prompt，将补翻结果回写到 --output-dir。
    """
    game_dir = Path(args.game_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Ren'Py 漏翻补翻模式")
    print("=" * 60)
    print(f"扫描目录: {game_dir}")
    print(f"输出目录: {output_dir}")
    print(f"API: {args.provider} / {args.model or '默认'}")
    if game_dir.resolve() == output_dir.resolve():
        print("[WARN] 输入输出目录相同，将原地覆写已翻译文件。如未备份请 Ctrl+C 中止。")
    print()

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
    print(f"[API ] 提供商: {config.provider}, 模型: {config.model}")

    glossary = Glossary()
    glossary_path = output_dir / "glossary.json"
    glossary.load(str(glossary_path))
    if args.dict:
        for dict_path in args.dict:
            glossary.load_dict(dict_path)

    # 补翻使用独立进度文件，不干扰主翻译进度
    progress = ProgressTracker(output_dir / "retranslate_progress.json")
    if not args.resume and progress.data.get("completed_files"):
        progress.data = {"completed_files": [], "completed_chunks": {}, "stats": {}}
        progress.save()

    db_path = output_dir / "translation_db.json"
    translation_db = TranslationDB(db_path)
    translation_db.load()
    run_id = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())

    # 扫描 .rpy 文件，排除引擎目录
    rpy_files = sorted(game_dir.rglob("*.rpy"))
    filtered = []
    for f in rpy_files:
        parts = f.relative_to(game_dir).parts
        if parts and parts[0].lower() in ("renpy", "lib", "__pycache__"):
            continue
        filtered.append(f)
    rpy_files = filtered

    if not rpy_files:
        print("[ERROR] 未找到 .rpy 文件")
        return

    # 预扫描：统计各文件漏翻行数
    print(f"[SCAN] 扫描 {len(rpy_files)} 个文件的漏翻行...")
    files_with_untranslated: list[tuple[Path, int]] = []
    total_untranslated = 0
    for f in rpy_files:
        content = read_file(f)
        ut = find_untranslated_lines(content)
        if ut:
            files_with_untranslated.append((f, len(ut)))
            total_untranslated += len(ut)

    if not files_with_untranslated:
        print("[INFO] 未发现漏翻行，无需补翻")
        return

    done_count = sum(
        1 for f, _ in files_with_untranslated
        if progress.is_file_done(str(f.relative_to(game_dir)))
    )
    print(f"[SCAN] 发现 {total_untranslated} 行漏翻，分布在 "
          f"{len(files_with_untranslated)} 个文件中"
          f"（已完成 {done_count} 个）")

    start_time = time.time()
    total_translated = 0
    total_warnings: list[str] = []
    quality_report: dict[str, list[dict]] = {}

    for i, (rpy_path, n_ut) in enumerate(files_with_untranslated, 1):
        rel = rpy_path.relative_to(game_dir)
        print(f"\n[{i}/{len(files_with_untranslated)}] {rel} ({n_ut} 行)")

        try:
            count, warnings = retranslate_file(
                rpy_path, game_dir, output_dir, client, glossary, progress,
                quality_report, genre=args.genre,
                translation_db=translation_db,
                run_id=run_id, stage="retranslate",
                provider=config.provider, model=config.model,
            )
            total_translated += count
            total_warnings.extend(warnings)
        except KeyboardInterrupt:
            print("\n[中断] 保存进度...")
            glossary.save(str(glossary_path))
            progress.save()
            try:
                translation_db.save()
            except Exception:
                pass
            print("[中断] 进度已保存，可用 --resume 继续")
            sys.exit(1)
        except Exception as e:
            msg = f"文件 {rel} 补翻失败: {e}"
            print(f"  [ERROR] {msg}")
            total_warnings.append(msg)

        if i % 5 == 0:
            glossary.save(str(glossary_path))

    # 最终保存
    glossary.save(str(glossary_path))
    try:
        translation_db.save()
    except Exception as e:
        print(f"[WARN] 保存 translation_db 失败: {e}")

    elapsed = time.time() - start_time
    print("\n" + "=" * 60)
    print("补翻完成")
    print("=" * 60)
    print(f"补翻条目: {total_translated}")
    print(f"警告: {len(total_warnings)}")
    print(f"耗时: {elapsed / 60:.1f} 分钟")
    print(f"API 用量: {client.usage.summary()}")

    report = {
        "mode": "retranslate",
        "total_untranslated_scanned": total_untranslated,
        "files_with_untranslated": len(files_with_untranslated),
        "total_translated": total_translated,
        "total_warnings": len(total_warnings),
        "elapsed_minutes": round(elapsed / 60, 1),
        "provider": args.provider,
        "model": config.model,
        "api_requests": client.usage.total_requests,
        "input_tokens": client.usage.total_input_tokens,
        "output_tokens": client.usage.total_output_tokens,
        "estimated_cost_usd": round(client.usage.estimated_cost, 4),
    }
    report_path = output_dir / "retranslate_report.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"补翻报告: {report_path}")


# ============================================================
# tl-mode（翻译框架槽位模式）
# ============================================================

# Language switch button snippet injected into screen preferences()
_LANG_BUTTON_SNIPPET = '''
                vbox:
                    style_prefix "radio"
                    label _("Language")
                    textbutton "English" action Language(None)
                    textbutton "中文" action Language("{lang}")
'''


def _clean_rpyc(game_dir: Path) -> None:
    """Safely delete .rpyc files to force Ren'Py recompilation.

    CRITICAL: Only deletes files whose extension is exactly '.rpyc'.
    Each file is validated before deletion to prevent accidental data loss.
    """
    count = 0
    for rpyc in game_dir.rglob("*.rpyc"):
        if rpyc.is_file() and rpyc.suffix == ".rpyc":
            rpyc.unlink()
            count += 1
    if count:
        print(f"[TL-CLEAN] 删除 {count} 个 .rpyc 缓存文件")


def _apply_tl_game_patches(game_dir: Path, tl_lang: str) -> None:
    """Apply font patch and language switch to game directory for tl-mode.

    1. Copy Chinese font from resources/fonts/ into game dir.
    2. Patch all gui.rpy files (define gui.*_font) — same approach as direct-mode.
    3. Write chinese_language_patch.rpy with config.language + translate python font override.
    4. Inject Language radio buttons into all screen preferences() definitions.
    """
    resources_fonts = Path(__file__).parent / "resources" / "fonts"
    font_path = resolve_font(resources_fonts)
    if not font_path:
        print("[TL-PATCH] 未找到中文字体，跳过字体补丁")
        print("[TL-PATCH] 请将 .ttf/.otf 字体文件放入 resources/fonts/ 目录")
        return

    font_name = font_path.name

    # 1. Copy font to game dir
    dst_font = game_dir / font_name
    if not dst_font.exists():
        shutil.copy2(font_path, dst_font)
        print(f"[TL-PATCH] 复制字体: {font_name} -> game/")
    else:
        print(f"[TL-PATCH] 字体已存在: {font_name}")

    # 2. Patch all gui.rpy (define gui.*_font = "...")
    _font_re = re.compile(
        r'^(\s*define\s+gui\.\w+_font\s*=\s*)["\']([^"\']*)["\'](\s*)$',
        re.MULTILINE,
    )
    for gui_rpy in game_dir.rglob("gui.rpy"):
        try:
            gui_rpy.relative_to(game_dir / "tl")
            continue
        except ValueError:
            pass
        gui_text = gui_rpy.read_text(encoding="utf-8-sig")
        new_gui, count = _font_re.subn(
            lambda m: m.group(1) + '"' + font_name + '"' + m.group(3),
            gui_text,
        )
        if count:
            gui_rpy.write_text(new_gui, encoding="utf-8")
            print(f"[TL-PATCH] 更新 {gui_rpy.relative_to(game_dir.parent)}: "
                  f"{count} 处 gui.*_font -> {font_name}")

    # 3. Write chinese_language_patch.rpy (default language + translate python font override)
    tl_dir = game_dir / "tl" / tl_lang
    tl_dir.mkdir(parents=True, exist_ok=True)
    patch_rpy = tl_dir / "chinese_language_patch.rpy"
    patch_content = (
        f'init python:\n'
        f'    config.language = "{tl_lang}"\n'
        f'\n'
        f'translate {tl_lang} python:\n'
        f'    gui.text_font = "{font_name}"\n'
        f'    gui.name_text_font = "{font_name}"\n'
        f'    gui.interface_text_font = "{font_name}"\n'
    )
    patch_rpy.write_text(patch_content, encoding="utf-8")
    print(f"[TL-PATCH] 写入语言补丁: {patch_rpy.relative_to(game_dir.parent)}")

    # 4. Inject language buttons into screen preferences()
    _inject_language_buttons(game_dir, tl_lang)


def _inject_language_buttons(game_dir: Path, tl_lang: str) -> None:
    """Find all screen preferences() in .rpy files and inject Language radio buttons."""
    import re as _re

    snippet = _LANG_BUTTON_SNIPPET.replace("{lang}", tl_lang)
    marker = 'action Language('

    for rpy in game_dir.rglob("*.rpy"):
        # Skip tl directory files
        try:
            rpy.relative_to(game_dir / "tl")
            continue
        except ValueError:
            pass

        text = rpy.read_text(encoding="utf-8-sig")
        if "screen preferences()" not in text:
            continue
        if marker in text:
            print(f"[TL-PATCH] 语言按钮已存在: {rpy.relative_to(game_dir.parent)}")
            continue

        # Find the Skip section's closing line to insert after
        lines = text.splitlines(True)
        insert_idx = None
        in_skip = False
        for i, line in enumerate(lines):
            stripped = line.strip()
            if 'label _("Skip")' in stripped:
                in_skip = True
            if in_skip and stripped.startswith('textbutton') and 'Transitions' in stripped:
                insert_idx = i + 1
                break

        if insert_idx is None:
            # Fallback: find after Rollback Side section
            for i, line in enumerate(lines):
                stripped = line.strip()
                if 'label _("Rollback Side")' in stripped:
                    # Find the last textbutton in this vbox
                    for j in range(i + 1, min(i + 10, len(lines))):
                        if lines[j].strip().startswith('textbutton') and 'right' in lines[j].lower():
                            insert_idx = j + 1
                            break
                    break

        if insert_idx is None:
            print(f"[TL-PATCH] 无法定位注入点: {rpy.relative_to(game_dir.parent)}")
            continue

        # Create backup
        bak = rpy.with_suffix(".rpy.lang_bak")
        if not bak.exists():
            shutil.copy2(rpy, bak)

        lines.insert(insert_idx, snippet)
        rpy.write_text("".join(lines), encoding="utf-8")
        print(f"[TL-PATCH] 注入语言按钮: {rpy.relative_to(game_dir.parent)}")


def build_tl_chunks(
    entries: list,
    max_per_chunk: int = 30,
) -> list[tuple[str, list]]:
    """将 DialogueEntry / StringEntry 列表打包为 AI 翻译 chunk。

    Returns:
        [(chunk_text, chunk_entries), ...] — chunk_text 为发给 AI 的文本，
        chunk_entries 为该 chunk 对应的条目列表（回填时使用）。
    """
    from tl_parser import DialogueEntry

    chunks: list[tuple[str, list]] = []
    for start in range(0, len(entries), max_per_chunk):
        group = entries[start:start + max_per_chunk]
        lines: list[str] = []
        for entry in group:
            if isinstance(entry, DialogueEntry):
                char_part = f" [Char: {entry.character}]" if entry.character else " [Char: ]"
                text = entry.original
                multiline = " [MULTILINE]" if "\n" in text or "\\n" in text else ""
                lines.append(f"[ID: {entry.identifier}]{char_part}{multiline}")
                lines.append(f'"{text}"')
            else:
                text = entry.old
                multiline = " [MULTILINE]" if "\n" in text or "\\n" in text else ""
                lines.append(f"[STRING]{multiline}")
                lines.append(f'"{text}"')
            lines.append("")
        chunks.append(("\n".join(lines), group))
    return chunks


def run_tl_pipeline(args: argparse.Namespace) -> None:
    """运行 tl-mode 翻译流水线。

    流程：scan_tl_directory → 提取空槽位 → 分 chunk → AI 翻译 → fill_translation 回填。
    """
    from tl_parser import (
        scan_tl_directory,
        get_untranslated_entries,
        fill_translation,
        postprocess_tl_directory,
        print_tl_stats,
        DialogueEntry,
        StringEntry,
    )

    game_dir = Path(args.game_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    tl_lang = getattr(args, "tl_lang", "chinese") or "chinese"

    print("=" * 60)
    print("Ren'Py tl-mode 翻译")
    print("=" * 60)
    print(f"游戏目录: {game_dir}")
    print(f"tl 语言: {tl_lang}")
    print(f"API: {args.provider} / {args.model or '默认'}")
    print()

    # ── 0. 自动字体补丁 + 语言切换注入 ──
    _apply_tl_game_patches(game_dir, tl_lang)
    print()

    # ── 1. 扫描 ──
    tl_dir = str(game_dir / "tl")
    results = scan_tl_directory(tl_dir, tl_lang)
    if not results:
        print("[TL-MODE] 未找到 tl 文件，请确认路径是否正确")
        return
    print_tl_stats(results)

    untrans_dlg, untrans_str = get_untranslated_entries(results)
    total_untrans = len(untrans_dlg) + len(untrans_str)
    if total_untrans == 0:
        print("\n[TL-MODE] 所有条目已翻译，无需操作")
        return

    print(f"\n[TL-MODE] 待翻译: {len(untrans_dlg)} 个对话, {len(untrans_str)} 个字符串")

    # ── 初始化基础设施 ──
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
    print(f"[API ] 提供商: {config.provider}, 模型: {config.model}")

    glossary = Glossary()
    glossary_path = output_dir / "glossary.json"
    glossary.load(str(glossary_path))
    if args.dict:
        for dict_path in args.dict:
            glossary.load_dict(dict_path)

    progress = ProgressTracker(output_dir / "tl_progress.json")
    if not args.resume and progress.data.get("completed_files"):
        progress.data = {"completed_files": [], "completed_chunks": {}, "stats": {}}
        progress.save()

    db_path = output_dir / "translation_db.json"
    translation_db = TranslationDB(db_path)
    translation_db.load()
    run_id = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())

    system_prompt = build_tl_system_prompt(
        glossary_text=glossary.to_prompt_text(),
        genre=args.genre,
    )

    # ── 1b. 自动回填不需要 AI 翻译的条目（纯空白/纯标点原文） ──
    auto_filled: list = []
    remaining_dlg: list = []
    remaining_str: list = []
    for e in untrans_dlg:
        if not e.original.strip():
            e.translation = e.original  # keep original whitespace
            auto_filled.append(e)
        else:
            remaining_dlg.append(e)
    for e in untrans_str:
        if not e.old.strip():
            e.new = e.old
            auto_filled.append(e)
        else:
            remaining_str.append(e)
    if auto_filled:
        print(f"[TL-MODE] 自动回填 {len(auto_filled)} 条纯空白条目")
        af_by_file: dict[str, list] = {}
        for e in auto_filled:
            af_by_file.setdefault(e.tl_file, []).append(e)
        for fpath, af_entries in af_by_file.items():
            bak = Path(fpath + ".bak")
            if not bak.exists():
                try:
                    shutil.copy2(fpath, bak)
                except Exception:
                    pass
            modified = fill_translation(fpath, af_entries)
            Path(fpath).write_text(modified, encoding="utf-8")

    untrans_dlg = remaining_dlg
    untrans_str = remaining_str
    total_untrans = len(untrans_dlg) + len(untrans_str)
    if total_untrans == 0:
        print("\n[TL-MODE] 所有条目已翻译或自动回填，无需 AI 操作")
        postprocess_tl_directory(str(game_dir / "tl"), tl_lang)
        return

    # ── 2. 按文件分组 + 分 chunk ──
    all_entries = list(untrans_dlg) + list(untrans_str)
    by_file: dict[str, list] = {}
    for entry in all_entries:
        by_file.setdefault(entry.tl_file, []).append(entry)

    for entries in by_file.values():
        entries.sort(key=lambda e: e.tl_line)

    start_time = time.time()
    total_translated = 0
    total_checker_dropped = 0
    total_filled = 0
    total_fallback_matched = 0
    total_warnings: list[str] = []
    files_processed = 0
    workers = max(1, getattr(args, "workers", 1))

    # ── 2a. 收集所有待翻译 chunk ──
    all_chunk_tasks: list[tuple] = []
    file_meta: dict[str, tuple] = {}  # rel_path → (file_path, entries, total_chunks)

    for file_path, entries in by_file.items():
        rel_path = file_path
        try:
            rel_path = str(Path(file_path).relative_to(game_dir))
        except ValueError:
            pass

        if progress.is_file_done(rel_path):
            print(f"  [SKIP] {rel_path} (已完成)")
            continue

        chunks = build_tl_chunks(entries)
        file_meta[rel_path] = (file_path, entries, len(chunks))

        for ci, (chunk_text, chunk_entries) in enumerate(chunks, 1):
            if progress.is_chunk_done(rel_path, ci):
                continue
            all_chunk_tasks.append((rel_path, ci, chunk_text, chunk_entries))

    print(f"\n[TL-MODE] {len(file_meta)} 个文件, "
          f"{len(all_chunk_tasks)} 个 chunk 待处理, "
          f"{workers} 线程并发")

    # ── 2b. 并发翻译 chunk ──
    file_translations: dict[str, dict[str, str]] = {}
    _lock = threading.Lock()
    _completed = [0]

    def _translate_one_chunk(
        rel_path: str, ci: int, chunk_text: str, chunk_entries: list,
    ) -> tuple[str, int, dict[str, str], int, list[str]]:
        protected_text, ph_mapping = protect_placeholders(chunk_text)
        user_prompt = build_tl_user_prompt(protected_text, len(chunk_entries))
        translations = client.translate(system_prompt, user_prompt)

        for t in translations:
            t["id"] = restore_placeholders(t.get("id") or "", ph_mapping)
            t["original"] = restore_placeholders(t.get("original") or "", ph_mapping)
            t["zh"] = restore_placeholders(t.get("zh") or "", ph_mapping)

        kept_items: dict[str, str] = {}
        dropped = 0
        warnings: list[str] = []
        for t in translations:
            item_w = check_response_item(t)
            if item_w:
                dropped += 1
                warnings.extend(f"[CHECK-DROPPED] {w}" for w in item_w)
            else:
                tid = t.get("id", "")
                zh = t.get("zh", "")
                if tid and zh:
                    kept_items[tid] = zh
        return rel_path, ci, kept_items, dropped, warnings

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        future_map: dict[concurrent.futures.Future, tuple] = {}
        for rel_path, ci, chunk_text, chunk_entries in all_chunk_tasks:
            total = file_meta[rel_path][2]
            fut = pool.submit(
                _translate_one_chunk, rel_path, ci, chunk_text, chunk_entries,
            )
            future_map[fut] = (rel_path, ci, len(chunk_entries), total)

        for fut in concurrent.futures.as_completed(future_map):
            rel_path, ci, _entry_count, total = future_map[fut]
            try:
                rp, _chunk_idx, kept_items, dropped, warnings = fut.result()
                with _lock:
                    file_translations.setdefault(rp, {}).update(kept_items)
                    total_checker_dropped += dropped
                    total_warnings.extend(warnings)
                    _completed[0] += 1
                    n = _completed[0]
                print(f"  [{n}/{len(all_chunk_tasks)}] {rp} "
                      f"chunk {ci}/{total}: 保留 {len(kept_items)} 条"
                      + (f", 丢弃 {dropped} 条" if dropped else ""))
                progress.mark_chunk_done(rp, ci, [])
            except Exception as e:
                with _lock:
                    total_warnings.append(f"{rel_path} chunk {ci}: {e}")
                    _completed[0] += 1
                    n = _completed[0]
                print(f"  [{n}/{len(all_chunk_tasks)}] [ERROR] "
                      f"{rel_path} chunk {ci}/{total}: {e}")

    # ── 3. 匹配 + 回填（串行，保证文件写入安全） ──
    _ph_token_re = re.compile(r"__RENPY_PH_\d+__")

    for rel_path, (file_path, entries, _total_chunks) in file_meta.items():
        ft = file_translations.get(rel_path, {})
        if not ft:
            progress.mark_file_done(rel_path)
            files_processed += 1
            continue

        matched_entries: list = []
        db_entries: list[dict] = []
        for entry in entries:
            if isinstance(entry, DialogueEntry):
                zh = ft.get(entry.identifier)
                if zh:
                    entry.translation = zh
                    matched_entries.append(entry)
                    total_translated += 1
                    db_entries.append({
                        "file": rel_path,
                        "line": entry.tl_line,
                        "original": entry.original,
                        "translation": zh,
                        "status": "ok",
                        "error_codes": [],
                        "warning_codes": [],
                        "run_id": run_id,
                        "stage": "tl-mode",
                        "provider": config.provider,
                        "model": config.model,
                    })
            else:  # StringEntry — 四层 fallback 匹配（精确 → strip → 去占位符令牌 → 转义规范化）
                zh = ft.get(entry.old)
                fb_level = 0
                if not zh:
                    old_stripped = entry.old.strip()
                    for tid, tzh in ft.items():
                        if tid.strip() == old_stripped:
                            zh = tzh
                            fb_level = 2
                            break
                if not zh:
                    old_clean = _ph_token_re.sub("", entry.old).strip()
                    for tid, tzh in ft.items():
                        tid_clean = _ph_token_re.sub("", tid).strip()
                        if tid_clean == old_clean and tid_clean:
                            zh = tzh
                            fb_level = 3
                            break
                if not zh:
                    old_norm = entry.old.replace('\\"', '"').replace("\\n", "\n").strip()
                    for tid, tzh in ft.items():
                        tid_norm = tid.replace('\\"', '"').replace("\\n", "\n").strip()
                        if tid_norm == old_norm and tid_norm:
                            zh = tzh
                            fb_level = 4
                            break
                if zh:
                    if fb_level:
                        total_fallback_matched += 1
                        print(f"  [TL-MATCH] fallback L{fb_level}: "
                              f"{entry.old[:40]!r}")
                    entry.new = zh
                    matched_entries.append(entry)
                    total_translated += 1
                    db_entries.append({
                        "file": rel_path,
                        "line": entry.tl_line,
                        "original": entry.old,
                        "translation": zh,
                        "status": "ok",
                        "error_codes": [],
                        "warning_codes": [],
                        "run_id": run_id,
                        "stage": "tl-mode",
                        "provider": config.provider,
                        "model": config.model,
                    })

        if db_entries and translation_db is not None:
            translation_db.add_entries(db_entries)

        # ── 4. 回填 ──
        if matched_entries:
            bak_path = Path(file_path + ".bak")
            if not bak_path.exists():
                try:
                    shutil.copy2(file_path, bak_path)
                except Exception:
                    pass

            modified_content = fill_translation(file_path, matched_entries)
            Path(file_path).write_text(modified_content, encoding="utf-8")
            total_filled += len(matched_entries)
            print(f"  [FILL] 回填 {len(matched_entries)} 条到 {rel_path}")

        progress.mark_file_done(rel_path)
        files_processed += 1

    # ── 4b. 重试未匹配条目（小 chunk + 最多 1 轮） ──
    retry_results = scan_tl_directory(str(game_dir / "tl"), tl_lang)
    retry_dlg, retry_str = get_untranslated_entries(retry_results)
    retry_all = [e for e in retry_dlg if e.original.strip()] + \
                [e for e in retry_str if e.old.strip()]
    if retry_all:
        print(f"\n[TL-RETRY] {len(retry_all)} 条未匹配，重试中（chunk=5）…")
        retry_by_file: dict[str, list] = {}
        for e in retry_all:
            retry_by_file.setdefault(e.tl_file, []).append(e)

        for fpath, r_entries in retry_by_file.items():
            r_entries.sort(key=lambda e: e.tl_line)
            r_chunks = build_tl_chunks(r_entries, max_per_chunk=5)
            r_kept: dict[str, str] = {}
            for _ci, (chunk_text, _cen) in enumerate(r_chunks, 1):
                ptext, phmap = protect_placeholders(chunk_text)
                up = build_tl_user_prompt(ptext, len(_cen))
                ts = client.translate(system_prompt, up)
                for t in ts:
                    t["id"] = restore_placeholders(t.get("id") or "", phmap)
                    t["original"] = restore_placeholders(
                        t.get("original") or "", phmap)
                    t["zh"] = restore_placeholders(t.get("zh") or "", phmap)
                for t in ts:
                    iw = check_response_item(t)
                    if not iw and t.get("id") and t.get("zh"):
                        r_kept[t["id"]] = t["zh"]

            r_matched: list = []
            for entry in r_entries:
                if isinstance(entry, DialogueEntry):
                    zh = r_kept.get(entry.identifier)
                    if zh:
                        entry.translation = zh
                        r_matched.append(entry)
                        total_translated += 1
                else:
                    zh = r_kept.get(entry.old)
                    if not zh:
                        old_norm = entry.old.replace('\\"', '"') \
                                       .replace("\\n", "\n").strip()
                        for tid, tzh in r_kept.items():
                            tid_norm = tid.replace('\\"', '"') \
                                          .replace("\\n", "\n").strip()
                            if tid_norm == old_norm and tid_norm:
                                zh = tzh
                                break
                    if zh:
                        entry.new = zh
                        r_matched.append(entry)
                        total_translated += 1

            if r_matched:
                modified = fill_translation(fpath, r_matched)
                Path(fpath).write_text(modified, encoding="utf-8")
                total_filled += len(r_matched)
                print(f"  [TL-RETRY] 回填 {len(r_matched)} 条到 "
                      f"{Path(fpath).name}")

    # ── 4c. 后处理：修复 nvl clear 兼容性 + 空 translate 块 ──
    tl_dir = str(game_dir / "tl")
    postprocess_tl_directory(tl_dir, tl_lang)

    # ── 4d. 清理 rpyc 缓存（强制 Ren'Py 重编译） ──
    _clean_rpyc(game_dir)

    # ── 5. 保存 & 报告 ──
    glossary.save(str(glossary_path))
    try:
        translation_db.save()
    except Exception as e:
        print(f"[WARN] 保存 translation_db 失败: {e}")

    elapsed = time.time() - start_time
    print("\n" + "=" * 60)
    print("tl-mode 翻译完成")
    print("=" * 60)
    print(f"[TL-MODE] 扫描: {len(results)} 个文件")
    print(f"[TL-MODE] 待翻译: {len(untrans_dlg)} 个对话, {len(untrans_str)} 个字符串")
    print(f"[TL-MODE] 翻译成功: {total_translated} 条")
    print(f"[TL-MODE] Checker 丢弃: {total_checker_dropped} 条")
    print(f"[TL-MODE] Fallback 匹配: {total_fallback_matched} 条")
    print(f"[TL-MODE] 回填成功: {total_filled} 条")
    print(f"[TL-MODE] 耗时: {elapsed / 60:.1f} 分钟")
    print(f"[TL-MODE] API 用量: {client.usage.summary()}")

    report = {
        "mode": "tl-mode",
        "tl_lang": tl_lang,
        "total_files": len(results),
        "total_dialogues_scanned": sum(len(r.dialogues) for r in results),
        "total_strings_scanned": sum(len(r.strings) for r in results),
        "untranslated_dialogues": len(untrans_dlg),
        "untranslated_strings": len(untrans_str),
        "translated": total_translated,
        "checker_dropped": total_checker_dropped,
        "fallback_matched": total_fallback_matched,
        "filled": total_filled,
        "elapsed_minutes": round(elapsed / 60, 1),
        "provider": args.provider,
        "model": config.model,
        "api_requests": client.usage.total_requests,
        "input_tokens": client.usage.total_input_tokens,
        "output_tokens": client.usage.total_output_tokens,
        "estimated_cost_usd": round(client.usage.estimated_cost, 4),
    }
    report_path = output_dir / "tl_mode_report.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"[TL-MODE] 报告: {report_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Ren'Py 整文件翻译工具 — AI 自主识别翻译内容",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--game-dir", required=True, help="游戏目录（自动检测 game/ 子目录，自动排除 renpy/ 引擎文件）")
    parser.add_argument("--output-dir", default="output", help="输出目录 (默认: output)")
    parser.add_argument("--provider", required=True, choices=['xai', 'grok', 'openai', 'deepseek', 'claude', 'gemini'],
                        help="API 提供商")
    parser.add_argument("--api-key", default="", help="API 密钥（dry-run 模式可不填）")
    parser.add_argument("--model", default="", help="模型名称 (留空使用默认)")
    parser.add_argument("--genre", default="adult", choices=['adult', 'visual_novel', 'rpg', 'general'],
                        help="翻译风格 (默认: adult)")
    parser.add_argument("--rpm", type=int, default=60, help="每分钟请求数限制 (默认: 60)")
    parser.add_argument("--rps", type=int, default=5, help="每秒请求数限制 (默认: 5)")
    parser.add_argument("--timeout", type=float, default=180.0, help="API 超时秒数 (默认: 180)")
    parser.add_argument("--temperature", type=float, default=0.1, help="生成温度 (默认: 0.1, 低=一致性高)")
    parser.add_argument("--max-chunk-tokens", type=int, default=4000,
                        help="每个分块最大 token 数 (默认: 4000，适配 AI 输出长度限制)")
    parser.add_argument("--resume", action="store_true", help="从上次中断处继续")
    parser.add_argument("--dict", nargs="*", default=[], metavar="PATH",
                        help="外部词典文件（CSV/JSONL，可多个）")
    parser.add_argument("--copy-assets", action="store_true",
                        help="复制非 .rpy 资源文件到输出目录")
    parser.add_argument("--workers", type=int, default=1,
                        help="并发翻译线程数 (默认: 1, 建议不超过 3)")
    parser.add_argument("--exclude", nargs="*", default=[], metavar="PATTERN",
                        help="排除匹配的文件 (glob 模式, 如 'tl/*' '*.bak')")
    parser.add_argument("--dry-run", action="store_true",
                        help="仅扫描统计，不实际翻译（预估费用）")
    parser.add_argument("--max-response-tokens", type=int, default=32768,
                        help="API 最大响应 token 数 (默认: 32768)")
    parser.add_argument("--log-file", default="", metavar="PATH",
                        help="保存详细日志到文件")
    parser.add_argument("--target-lang", default="zh",
                        help="目标语言 (默认: zh 简体中文)")
    parser.add_argument("--input-price", type=float, default=None, metavar="USD",
                        help="手动指定输入价格 (每百万 tokens, 美元)")
    parser.add_argument("--output-price", type=float, default=None, metavar="USD",
                        help="手动指定输出价格 (每百万 tokens, 美元)")
    parser.add_argument("--tl-priority", action="store_true",
                        help="启用 tl 优先模式：若检测到 tl/ 目录，则仅翻译 tl 下的脚本")
    parser.add_argument("--stage", default="single",
                        help="内部使用：由一键流水线指定当前运行阶段 (single/pilot/full/incremental)")
    parser.add_argument("--patch-font", action="store_true", default=False,
                        help="启用自动字体补丁：将 resources/fonts/ 字体复制到输出并改写 gui.*_font")
    parser.add_argument("--font-file", default="", metavar="PATH",
                        help="指定字体文件路径，覆盖默认的 resources/fonts/ 查找")
    parser.add_argument("--retranslate", action="store_true",
                        help="补翻模式：扫描已翻译文件中残留的英文对话行，构建小 chunk 精准补翻。"
                             "若 --output-dir 与 --game-dir 相同则原地覆写，建议先备份或指向不同目录")
    parser.add_argument("--min-dialogue-density", type=float, default=0.20, metavar="RATIO",
                        help="对话密度阈值 (默认: 0.20)；密度低于此值的文件在全量阶段自动走定向翻译模式")
    parser.add_argument("--tl-mode", action="store_true",
                        help="tl 模式：读取 tl/<lang>/ 目录中的空翻译槽位，AI 翻译后精确回填。"
                             "需配合 --game-dir 指向包含 tl/ 目录的 game 目录")
    parser.add_argument("--tl-lang", default="chinese", metavar="LANG",
                        help="tl 目录的语言子目录名 (默认: chinese)")

    args = parser.parse_args()

    # dry-run 模式不需要 API key
    if not args.dry_run and not args.api_key:
        print("[ERROR] 非 dry-run 模式必须提供 --api-key")
        sys.exit(1)

    # 智能检测游戏目录
    game_dir = Path(args.game_dir)
    # 如果用户传入的是游戏根目录（包含 game/ 子目录），优先扫描 game/
    # 但也保留原始根目录，以便在 game/ 不存在时回退扫描整个目录
    project_root = game_dir
    if (game_dir / "game").exists():
        # 检查 game/ 外是否也有 .rpy 文件
        root_rpys = [f for f in game_dir.glob('*.rpy')]
        if root_rpys:
            # 根目录也有 .rpy，扫描整个根目录
            print(f"[INFO] 根目录和 game/ 都包含 .rpy 文件，扫描整个目录")
        else:
            game_dir = game_dir / "game"
    args.game_dir = str(game_dir)

    if not game_dir.exists():
        print(f"[ERROR] 游戏目录不存在: {game_dir}")
        sys.exit(1)

    tl_mode = getattr(args, "tl_mode", False)
    if args.retranslate and tl_mode:
        print("[ERROR] --retranslate 和 --tl-mode 互斥，不能同时使用")
        sys.exit(1)

    if tl_mode:
        run_tl_pipeline(args)
    elif args.retranslate:
        run_retranslate_pipeline(args)
    else:
        run_pipeline(args)


if __name__ == "__main__":
    main()
