#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tl-mode 翻译引擎：扫描 Ren'Py tl/<lang>/ 目录中的空翻译槽位，AI 翻译后精确回填。"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import logging
import re
import shutil
import threading
import time
from pathlib import Path
from typing import Optional

from api_client import APIClient, APIConfig
from file_processor import (
    protect_placeholders,
    check_response_item,
)
from glossary import Glossary
from prompts import build_tl_system_prompt, build_tl_user_prompt
from translation_db import TranslationDB
from font_patch import resolve_font
from translation_utils import (
    TranslationContext,
    ProgressTracker,
    _restore_placeholders_in_translations,
    _filter_checked_translations,
    _build_fallback_dicts,
    _match_string_entry_fallback,
)

logger = logging.getLogger("renpy_translator")


def _translate_one_tl_chunk(
    ctx: TranslationContext, rel_path: str, ci: int, chunk_text: str, chunk_entries: list,
) -> tuple[str, int, dict[str, str], int, list[str]]:
    """翻译单个 tl-mode chunk。

    原为 run_tl_pipeline() 内的嵌套函数，通过闭包捕获 client/system_prompt。
    重构后通过 TranslationContext 显式传参。

    Returns:
        (rel_path, ci, kept_items_dict, dropped_count, warnings)
    """
    protected_text, ph_mapping = protect_placeholders(chunk_text)
    user_prompt = build_tl_user_prompt(protected_text, len(chunk_entries))
    translations = ctx.client.translate(ctx.system_prompt, user_prompt)

    _restore_placeholders_in_translations(translations, ph_mapping, extra_keys=("id",))

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


def _clean_rpyc(game_dir: Path, modified_files: "set[str] | None" = None) -> None:
    """Delete .rpyc cache files to force Ren'Py recompilation.

    Args:
        game_dir: Game root directory.
        modified_files: If provided, only delete .rpyc for these .rpy relative paths.
            Otherwise fall back to full recursive cleanup.
    """
    count = 0
    if modified_files:
        for rpy_rel in modified_files:
            rpyc = game_dir / (rpy_rel + "c")  # .rpy → .rpyc
            if rpyc.is_file() and rpyc.suffix == ".rpyc":
                rpyc.unlink()
                count += 1
    else:
        for rpyc in game_dir.rglob("*.rpyc"):
            if rpyc.is_file() and rpyc.suffix == ".rpyc":
                rpyc.unlink()
                count += 1
    if count:
        logger.info(f"[RPYC] 已清理 {count} 个缓存文件")


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
        logger.info("[TL-PATCH] 未找到中文字体，跳过字体补丁")
        logger.info("[TL-PATCH] 请将 .ttf/.otf 字体文件放入 resources/fonts/ 目录")
        return

    font_name = font_path.name

    # 1. Copy font to game dir
    dst_font = game_dir / font_name
    if not dst_font.exists():
        shutil.copy2(font_path, dst_font)
        logger.info(f"[TL-PATCH] 复制字体: {font_name} -> game/")
    else:
        logger.info(f"[TL-PATCH] 字体已存在: {font_name}")

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
            logger.info(f"[TL-PATCH] 更新 {gui_rpy.relative_to(game_dir.parent)}: "
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
    logger.info(f"[TL-PATCH] 写入语言补丁: {patch_rpy.relative_to(game_dir.parent)}")

    # 4. Inject language buttons into screen preferences()
    _inject_language_buttons(game_dir, tl_lang)


def _inject_language_buttons(game_dir: Path, tl_lang: str) -> None:
    """Find all screen preferences() in .rpy files and inject Language radio buttons."""
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
            logger.info(f"[TL-PATCH] 语言按钮已存在: {rpy.relative_to(game_dir.parent)}")
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
            logger.info(f"[TL-PATCH] 无法定位注入点: {rpy.relative_to(game_dir.parent)}")
            continue

        # Create backup
        bak = rpy.with_suffix(".rpy.lang_bak")
        if not bak.exists():
            shutil.copy2(rpy, bak)

        lines.insert(insert_idx, snippet)
        rpy.write_text("".join(lines), encoding="utf-8")
        logger.info(f"[TL-PATCH] 注入语言按钮: {rpy.relative_to(game_dir.parent)}")


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

    logger.info("=" * 60)
    logger.info("Ren'Py tl-mode 翻译")
    logger.info("=" * 60)
    logger.info(f"游戏目录: {game_dir}")
    logger.info(f"tl 语言: {tl_lang}")
    logger.info(f"API: {args.provider} / {args.model or '默认'}")
    logger.info("")

    # ── 0. 自动字体补丁 + 语言切换注入 ──
    _apply_tl_game_patches(game_dir, tl_lang)
    logger.info("")

    # ── 1. 扫描 ──
    tl_dir = str(game_dir / "tl")
    results = scan_tl_directory(tl_dir, tl_lang)
    if not results:
        logger.info("[TL-MODE] 未找到 tl 文件，请确认路径是否正确")
        return
    print_tl_stats(results)

    untrans_dlg, untrans_str = get_untranslated_entries(results)
    total_untrans = len(untrans_dlg) + len(untrans_str)
    if total_untrans == 0:
        logger.info("\n[TL-MODE] 所有条目已翻译，无需操作")
        return

    logger.info(f"\n[TL-MODE] 待翻译: {len(untrans_dlg)} 个对话, {len(untrans_str)} 个字符串")

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
    logger.info(f"[API ] 提供商: {config.provider}, 模型: {config.model}")

    glossary = Glossary()
    glossary_path = output_dir / "glossary.json"
    glossary.load(str(glossary_path))
    if args.dict:
        for dict_path in args.dict:
            if not Path(dict_path).exists():
                logger.warning(f"[WARN] 词典文件不存在，跳过: {dict_path}")
                continue
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
        logger.info(f"[TL-MODE] 自动回填 {len(auto_filled)} 条纯空白条目")
        af_by_file: dict[str, list] = {}
        for e in auto_filled:
            af_by_file.setdefault(e.tl_file, []).append(e)
        for fpath, af_entries in af_by_file.items():
            bak = Path(fpath + ".bak")
            if not bak.exists():
                try:
                    shutil.copy2(fpath, bak)
                except OSError as e:
                    logger.warning(f"创建备份失败 {bak}: {e}")
            modified = fill_translation(fpath, af_entries)
            Path(fpath).write_text(modified, encoding="utf-8")

    untrans_dlg = remaining_dlg
    untrans_str = remaining_str
    total_untrans = len(untrans_dlg) + len(untrans_str)
    if total_untrans == 0:
        logger.info("\n[TL-MODE] 所有条目已翻译或自动回填，无需 AI 操作")
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
            logger.debug(f"  [SKIP] {rel_path} (已完成)")
            continue

        chunks = build_tl_chunks(entries)
        file_meta[rel_path] = (file_path, entries, len(chunks))

        for ci, (chunk_text, chunk_entries) in enumerate(chunks, 1):
            if progress.is_chunk_done(rel_path, ci):
                continue
            all_chunk_tasks.append((rel_path, ci, chunk_text, chunk_entries))

    logger.info(f"\n[TL-MODE] {len(file_meta)} 个文件, "
          f"{len(all_chunk_tasks)} 个 chunk 待处理, "
          f"{workers} 线程并发")

    # ── 2b. 并发翻译 chunk ──
    file_translations: dict[str, dict[str, str]] = {}
    _lock = threading.Lock()
    _completed = [0]

    # 构建翻译上下文（替代嵌套函数闭包捕获）
    ctx = TranslationContext(client=client, system_prompt=system_prompt, rel_path="")

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        future_map: dict[concurrent.futures.Future, tuple] = {}
        for rel_path, ci, chunk_text, chunk_entries in all_chunk_tasks:
            total = file_meta[rel_path][2]
            fut = pool.submit(
                _translate_one_tl_chunk, ctx, rel_path, ci, chunk_text, chunk_entries,
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
                    n_completed = _completed[0]
                    n_kept = len(kept_items)
                logger.info(f"  [{n_completed}/{len(all_chunk_tasks)}] {rp} "
                     f"chunk {ci}/{total}: 保留 {n_kept} 条"
                     + (f", 丢弃 {dropped} 条" if dropped else ""))
                progress.mark_chunk_done(rp, ci, [])
            except Exception as e:
                with _lock:
                    total_warnings.append(f"{rel_path} chunk {ci}: {e}")
                    _completed[0] += 1
                    n_completed = _completed[0]
                logger.error(f"  [{n_completed}/{len(all_chunk_tasks)}] [ERROR] "
                      f"{rel_path} chunk {ci}/{total}: {e}")

    # ── 3. 匹配 + 回填（串行，保证文件写入安全） ──
    modified_rpy_files: set[str] = set()

    for rel_path, (file_path, entries, _total_chunks) in file_meta.items():
        ft = file_translations.get(rel_path, {})
        if not ft:
            progress.mark_file_done(rel_path)
            files_processed += 1
            continue

        # 预建 fallback 查找表（O(1) 替代 O(n) 遍历）
        ft_stripped, ft_clean, ft_norm = _build_fallback_dicts(ft)

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
                zh, fb_level = _match_string_entry_fallback(
                    entry.old, ft, ft_stripped, ft_clean, ft_norm,
                )
                if zh:
                    if fb_level:
                        total_fallback_matched += 1
                        logger.debug(f"  [TL-MATCH] fallback L{fb_level}: "
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
                except OSError as e:
                    logger.warning(f"创建备份失败 {bak_path}: {e}")

            modified_content = fill_translation(file_path, matched_entries)
            Path(file_path).write_text(modified_content, encoding="utf-8")
            total_filled += len(matched_entries)
            modified_rpy_files.add(rel_path)
            logger.debug(f"  [FILL] 回填 {len(matched_entries)} 条到 {rel_path}")

        progress.mark_file_done(rel_path)
        files_processed += 1

    # ── 4b. 重试未匹配条目（小 chunk + 最多 1 轮） ──
    retry_results = scan_tl_directory(str(game_dir / "tl"), tl_lang)
    retry_dlg, retry_str = get_untranslated_entries(retry_results)
    retry_all = [e for e in retry_dlg if e.original.strip()] + \
                [e for e in retry_str if e.old.strip()]
    if retry_all:
        logger.info(f"\n[TL-RETRY] {len(retry_all)} 条未匹配，重试中（chunk=5）…")
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
                _restore_placeholders_in_translations(ts, phmap, extra_keys=("id",))
                for t in ts:
                    iw = check_response_item(t)
                    if not iw and t.get("id") and t.get("zh"):
                        r_kept[t["id"]] = t["zh"]

            r_stripped, r_clean, r_norm = _build_fallback_dicts(r_kept)
            r_matched: list = []
            for entry in r_entries:
                if isinstance(entry, DialogueEntry):
                    zh = r_kept.get(entry.identifier)
                    if zh:
                        entry.translation = zh
                        r_matched.append(entry)
                        total_translated += 1
                else:
                    zh, _ = _match_string_entry_fallback(
                        entry.old, r_kept, r_stripped, r_clean, r_norm,
                    )
                    if zh:
                        entry.new = zh
                        r_matched.append(entry)
                        total_translated += 1

            if r_matched:
                modified = fill_translation(fpath, r_matched)
                Path(fpath).write_text(modified, encoding="utf-8")
                total_filled += len(r_matched)
                try:
                    modified_rpy_files.add(str(Path(fpath).relative_to(game_dir)))
                except ValueError:
                    pass  # 无法计算相对路径时跳过精确清理
                logger.debug(f"  [TL-RETRY] 回填 {len(r_matched)} 条到 "
                      f"{Path(fpath).name}")

    # ── 4c. 后处理：修复 nvl clear 兼容性 + 空 translate 块 ──
    tl_dir = str(game_dir / "tl")
    postprocess_tl_directory(tl_dir, tl_lang)

    # ── 4d. 清理 rpyc 缓存（强制 Ren'Py 重编译） ──
    if not getattr(args, "no_clean_rpyc", False):
        _clean_rpyc(game_dir, modified_rpy_files if modified_rpy_files else None)

    # ── 5. 保存 & 报告 ──
    glossary.save(str(glossary_path))
    try:
        translation_db.save()
    except OSError as e:
        logger.warning(f"[WARN] 保存 translation_db 失败: {e}")

    elapsed = time.time() - start_time
    logger.info("\n" + "=" * 60)
    logger.info("tl-mode 翻译完成")
    logger.info("=" * 60)
    logger.info(f"[TL-MODE] 扫描: {len(results)} 个文件")
    logger.info(f"[TL-MODE] 待翻译: {len(untrans_dlg)} 个对话, {len(untrans_str)} 个字符串")
    logger.info(f"[TL-MODE] 翻译成功: {total_translated} 条")
    logger.info(f"[TL-MODE] Checker 丢弃: {total_checker_dropped} 条")
    logger.info(f"[TL-MODE] Fallback 匹配: {total_fallback_matched} 条")
    logger.info(f"[TL-MODE] 回填成功: {total_filled} 条")
    logger.info(f"[TL-MODE] 耗时: {elapsed / 60:.1f} 分钟")
    logger.info(f"[TL-MODE] API 用量: {client.usage.summary()}")

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
    logger.info(f"[TL-MODE] 报告: {report_path}")


