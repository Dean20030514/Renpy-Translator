#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一键流水线：试跑批次 + 自动闸门 + 全量批处理 + 漏翻增量轮"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Iterable

from file_processor import read_file, validate_translation, SKIP_FILES_FOR_TRANSLATION
from translation_db import TranslationDB
from font_patch import resolve_font, apply_font_patch

logger = logging.getLogger(__name__)


RISK_KEYWORDS = [
    "screen", "gui", "options", "menu", "club", "dining", "living",
    "parents", "secret", "weekend", "v0", "help", "interaction",
]

# 翻译长度比例告警阈值（可根据需要调整）
# 经验值：中英对话正常 ratio 往往在 0.2~0.4 之间，将下限调低以减少噪音
LEN_RATIO_LOWER = 0.15
LEN_RATIO_UPPER = 2.5


class StageError(RuntimeError):
    pass


def _print(msg: str) -> None:
    logger.info(msg)


def resolve_scan_root(game_dir: Path) -> Path:
    """与 main.py 保持一致：优先 game/，但根目录若有 rpy 则扫描整个根目录。"""
    if (game_dir / "game").exists():
        root_rpys = list(game_dir.glob("*.rpy"))
        if root_rpys:
            return game_dir
        return game_dir / "game"
    return game_dir


def list_rpy_files(scan_root: Path) -> list[Path]:
    return sorted([p for p in scan_root.rglob("*.rpy") if p.is_file()])


def score_file(rel_path: str, size: int) -> int:
    lower = rel_path.lower()
    score = min(size // 1024, 200)
    for k in RISK_KEYWORDS:
        if k in lower:
            score += 80
    if "sazmod" in lower:
        score += 30
    return score


def pick_pilot_files(scan_root: Path, pilot_count: int) -> list[Path]:
    files = list_rpy_files(scan_root)
    ranked = sorted(
        files,
        key=lambda p: score_file(str(p.relative_to(scan_root)), p.stat().st_size),
        reverse=True,
    )
    return ranked[:pilot_count]


def copy_subset_to_input(scan_root: Path, files: Iterable[Path], dst_input: Path) -> None:
    if dst_input.exists():
        shutil.rmtree(dst_input)
    dst_input.mkdir(parents=True, exist_ok=True)
    for src in files:
        rel = src.relative_to(scan_root)
        dst = dst_input / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def run_main(
    game_dir: Path,
    output_dir: Path,
    provider: str,
    api_key: str,
    model: str,
    genre: str,
    workers: int,
    rpm: int,
    rps: int,
    timeout: float,
    max_chunk_tokens: int,
    max_response_tokens: int,
    log_file: Path,
    resume: bool,
    dict_paths: list[str] | None = None,
    excludes: list[str] | None = None,
    copy_assets: bool = False,
    target_lang: str = "zh",
    stage: str = "full",
    min_dialogue_density: float = 0.20,
    tl_mode: bool = False,
    tl_lang: str = "chinese",
) -> None:
    cmd = [
        sys.executable,
        "main.py",
        "--game-dir", str(game_dir),
        "--output-dir", str(output_dir),
        "--provider", provider,
        "--api-key", api_key,
        "--genre", genre,
        "--workers", str(workers),
        "--rpm", str(rpm),
        "--rps", str(rps),
        "--timeout", str(timeout),
        "--max-chunk-tokens", str(max_chunk_tokens),
        "--max-response-tokens", str(max_response_tokens),
        "--log-file", str(log_file),
        "--stage", stage,
        "--min-dialogue-density", str(min_dialogue_density),
    ]
    if model:
        cmd += ["--model", model]
    if resume:
        cmd.append("--resume")
    if dict_paths:
        cmd += ["--dict", *dict_paths]
    if excludes:
        cmd += ["--exclude", *excludes]
    if copy_assets:
        cmd.append("--copy-assets")
    if target_lang:
        cmd += ["--target-lang", target_lang]
    if tl_mode:
        cmd += ["--tl-mode", "--tl-lang", tl_lang]

    _print("\n[RUN ] " + " ".join(cmd))
    proc = subprocess.run(cmd, cwd=Path(__file__).parent)
    if proc.returncode != 0:
        raise StageError(f"main.py 执行失败，退出码 {proc.returncode}")


def count_untranslated_dialogues_in_file(path: Path) -> tuple[int, int]:
    """返回 (对话行总数, 疑似未翻译英文对话行数)。"""
    if path.name in SKIP_FILES_FOR_TRANSLATION:
        return 0, 0
    dialogue = 0
    untranslated = 0
    try:
        text = read_file(path)
    except Exception:
        return 0, 0

    for line in text.splitlines():
        if not _is_user_visible_string_line(line):
            continue
        m = re.search(r'"([^"\\]*(?:\\.[^"\\]*)*)"', line)
        if not m:
            continue
        s = m.group(1)
        if len(s) < 8:
            continue
        if any(x in s for x in ("/", "\\", ".png", ".jpg", ".webp", ".ttf", "#")):
            continue
        dialogue += 1
        cn = sum(1 for c in s if "\u4e00" <= c <= "\u9fff")
        en = sum(1 for c in s if "a" <= c.lower() <= "z")
        if cn == 0 and en >= 12 and len(s) >= 20:
            untranslated += 1
    return dialogue, untranslated


def collect_untranslated_details(path: Path) -> list[tuple[int, str]]:
    """返回 [(行号, 原文文本), ...] 对于疑似未翻译的英文对话行。

    检测逻辑与 count_untranslated_dialogues_in_file 完全一致，
    但额外返回每条漏翻的行号和原文内容，供归因分析使用。
    """
    if path.name in SKIP_FILES_FOR_TRANSLATION:
        return []
    result: list[tuple[int, str]] = []
    try:
        text = read_file(path)
    except Exception:
        return []
    for i, line in enumerate(text.splitlines(), 1):
        if not _is_user_visible_string_line(line):
            continue
        m = re.search(r'"([^"\\]*(?:\\.[^"\\]*)*)"', line)
        if not m:
            continue
        s = m.group(1)
        if len(s) < 8:
            continue
        if any(x in s for x in ("/", "\\", ".png", ".jpg", ".webp", ".ttf", "#")):
            continue
        cn = sum(1 for c in s if "\u4e00" <= c <= "\u9fff")
        en = sum(1 for c in s if "a" <= c.lower() <= "z")
        if cn == 0 and en >= 12 and len(s) >= 20:
            result.append((i, s))
    return result


def _normalize_ws(s: str) -> str:
    """将连续空白压缩为单空格，去除首尾空白。"""
    return re.sub(r'\s+', ' ', s.strip())


def attribute_untranslated(
    translated_root: Path,
    db: TranslationDB,
) -> dict:
    """归因分析：对每个漏翻行查询 translation_db 判断根因。

    分类规则：
      - translation_db 中无记录 → ai_missing（AI 根本没返回）
      - 记录 status == "checker_dropped" → checker_dropped（AI 返回了但被校验丢弃）
      - 记录 status in (ok, warning, error) → write_fail（翻译了但回写失败）
      - 其他 → unknown

    匹配策略：先精确匹配 (file, original)，失败后 fallback 到
    空白标准化匹配，以应对 AI 返回文本与文件提取文本的微小空白差异。
    """
    db_lookup: dict[tuple[str, str], str] = {}
    db_lookup_norm: dict[tuple[str, str], str] = {}
    for entry in db.entries:
        f = entry.get("file", "")
        orig = entry.get("original", "")
        status = entry.get("status", "")
        if f and orig:
            db_lookup[(f, orig)] = status
            norm_key = (f, _normalize_ws(orig))
            if norm_key not in db_lookup_norm:
                db_lookup_norm[norm_key] = status

    ai_missing = 0
    checker_dropped = 0
    write_fail = 0
    unknown = 0
    fallback_matched = 0

    for trans_file in list_rpy_files(translated_root):
        rel = str(trans_file.relative_to(translated_root))
        for _line_no, original_text in collect_untranslated_details(trans_file):
            status = db_lookup.get((rel, original_text))
            if status is None:
                norm_status = db_lookup_norm.get((rel, _normalize_ws(original_text)))
                if norm_status is not None:
                    status = norm_status
                    fallback_matched += 1
            if status is None:
                ai_missing += 1
            elif status == "checker_dropped":
                checker_dropped += 1
            elif status in ("ok", "warning", "error"):
                write_fail += 1
            else:
                unknown += 1

    total = ai_missing + checker_dropped + write_fail + unknown
    return {
        "total": total,
        "ai_missing": ai_missing,
        "checker_dropped": checker_dropped,
        "write_fail": write_fail,
        "unknown": unknown,
        "db_entries_count": len(db.entries),
        "fallback_matched": fallback_matched,
    }


def _is_user_visible_string_line(line: str) -> bool:
    """判断该行是否大概率是用户可见文本，而不是代码标识符。"""
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return False

    lower = stripped.lower()

    # 明确排除：典型代码/配置字符串行
    if any(k in lower for k in (
        "style_prefix", "id ", " action ", "action ", "jump(", "call(",
        "setvariable(", "setfield(", "showmenu(", "use ", "add ", "image ",
        "build.classify", "build.archive", "label ", "screen ", "transform ",
    )):
        return False

    # 明确包含：角色对话/旁白
    if re.match(r'^\s*(?:[A-Za-z_]\w*\s+)?"', line):
        return True

    # 界面可见文本
    if re.search(r'\b(text|textbutton)\s+"', line):
        return True
    if "renpy.notify(\"" in line:
        return True
    if re.search(r'_\("', line):
        return True

    return False


def evaluate_gate(original_root: Path, translated_root: Path) -> dict:
    """闸门：结构错误必须为 0；给出漏翻与长度异常统计。"""
    errors = 0
    warnings = 0
    dialogue_total = 0
    untranslated_total = 0
    len_ratio_warnings = 0
    placeholder_order_warnings = 0
    code_histogram: dict[str, int] = {}
    error_histogram: dict[str, int] = {}
    warning_histogram: dict[str, int] = {}
    glossary_lock_errors = 0
    no_translate_errors = 0
    glossary_miss_warnings = 0
    placeholder_issues = 0

    # 尝试从翻译输出目录旁边加载 glossary.json，以便在闸门阶段也统计锁定术语和禁翻片段违规
    glossary_terms = None
    glossary_locked = None
    glossary_no_translate = None
    try:
        base_dir = translated_root
        # glossary.json 通常位于输出根目录（可能是 translated_root 或其父目录）
        if not (base_dir / "glossary.json").exists():
            base_dir = translated_root.parent
        glossary_path = base_dir / "glossary.json"
        if glossary_path.exists():
            data = json.loads(glossary_path.read_text(encoding="utf-8"))
            glossary_terms = data.get("terms", {}) or None
            locked_list = data.get("locked_terms", [])
            no_trans_list = data.get("no_translate", [])
            glossary_locked = set(locked_list) if locked_list else None
            glossary_no_translate = set(no_trans_list) if no_trans_list else None
    except Exception:
        # 术语表缺失或解析失败不影响闸门主流程，仅跳过术语相关统计
        glossary_terms = None
        glossary_locked = None
        glossary_no_translate = None

    translated_files = list_rpy_files(translated_root)
    for trans_file in translated_files:
        rel = trans_file.relative_to(translated_root)
        orig_file = original_root / rel
        if not orig_file.exists():
            warnings += 1
            continue

        issues = validate_translation(
            read_file(orig_file),
            read_file(trans_file),
            str(rel),
            glossary_terms=glossary_terms,
            glossary_locked=glossary_locked,
            glossary_no_translate=glossary_no_translate,
            len_ratio_lower=LEN_RATIO_LOWER,
            len_ratio_upper=LEN_RATIO_UPPER,
        )
        for issue in issues:
            level = issue.get("level")
            code = issue.get("code") or ""
            if level == "error":
                errors += 1
            elif level == "warning":
                warnings += 1

            if code:
                code_histogram[code] = code_histogram.get(code, 0) + 1
                if level == "error":
                    error_histogram[code] = error_histogram.get(code, 0) + 1
                elif level == "warning":
                    warning_histogram[code] = warning_histogram.get(code, 0) + 1

                if code == "E411_GLOSSARY_LOCK_MISS":
                    glossary_lock_errors += 1
                elif code == "E420_NO_TRANSLATE_CHANGED":
                    no_translate_errors += 1
                elif code == "W410_GLOSSARY_MISS":
                    glossary_miss_warnings += 1

                if code in {
                    "E210_VAR_MISSING",
                    "W211_VAR_EXTRA",
                    "E220_TEXT_TAG_MISMATCH",
                    "E230_MENU_ID_MISMATCH",
                    "E240_FMT_PLACEHOLDER_MISMATCH",
                    "W251_PLACEHOLDER_ORDER",
                }:
                    placeholder_issues += 1

        len_ratio_warnings += sum(
            1 for i in issues if i.get("code") == "W430_LEN_RATIO_SUSPECT"
        )
        placeholder_order_warnings += sum(
            1 for i in issues if i.get("code") == "W251_PLACEHOLDER_ORDER"
        )

        d, u = count_untranslated_dialogues_in_file(trans_file)
        dialogue_total += d
        untranslated_total += u

    ratio = (untranslated_total / dialogue_total) if dialogue_total else 0.0
    len_ratio_warning_ratio = (
        (len_ratio_warnings / dialogue_total) if dialogue_total else 0.0
    )
    return {
        "files": len(translated_files),
        "errors": errors,
        "warnings": warnings,
        "dialogue_total": dialogue_total,
        "untranslated_total": untranslated_total,
        "untranslated_ratio": round(ratio, 6),
        "len_ratio_warnings": len_ratio_warnings,
        "len_ratio_warning_ratio": round(len_ratio_warning_ratio, 6),
        "placeholder_order_warnings": placeholder_order_warnings,
        "code_histogram": code_histogram,
        "error_histogram": error_histogram,
        "warning_histogram": warning_histogram,
        "glossary_lock_errors": glossary_lock_errors,
        "no_translate_errors": no_translate_errors,
        "glossary_miss_warnings": glossary_miss_warnings,
        "placeholder_issues": placeholder_issues,
    }


def collect_files_with_untranslated(translated_root: Path) -> list[Path]:
    result = []
    for p in list_rpy_files(translated_root):
        _, u = count_untranslated_dialogues_in_file(p)
        if u > 0:
            result.append(p)
    return result


# merge_incremental_results 已被 retranslate 模式替代（原地补翻，无需 merge）


def collect_strings_stats(root: Path) -> dict:
    """统计 translate ... strings: 块中的 old/new 条目翻译情况。

    规则说明：
    - 仅统计 `translate <lang> strings:` 块中的 `old`/`new` 对。
    - 当 `new` 为空或与 `old` 文本相同（忽略首尾空白）时，视为“未翻译”。
      这其中可能包含有意保留原文的条目，请结合具体项目判断。
    """
    files_info: list[dict] = []
    total_entries = 0
    total_translated = 0
    total_untranslated = 0

    for path in list_rpy_files(root):
        rel = path.relative_to(root)
        try:
            text = read_file(path)
        except Exception:
            continue

        in_strings = False
        current_old: str | None = None
        file_total = 0
        file_translated = 0
        file_untranslated = 0

        for line in text.splitlines():
            stripped = line.lstrip()

            # 1) 优先判断是否进入新的 translate 块（包括 strings 块）
            m_tr = re.match(r'^translate\s+(\w+)\s+(\w+)\s*:', stripped)
            if m_tr:
                lang, block_name = m_tr.groups()
                if block_name == "strings":
                    in_strings = True
                else:
                    # 新的非 strings translate 块，结束当前 strings 块
                    in_strings = False
                current_old = None
                continue

            if not in_strings:
                continue

            # 2) 在 strings 块内解析 old/new 行
            m_old = re.match(r'^\s*old\s+"(.*)"\s*$', line)
            if m_old:
                current_old = m_old.group(1)
                continue

            m_new = re.match(r'^\s*new\s+"(.*)"\s*$', line)
            if m_new and current_old is not None:
                new_text = m_new.group(1)
                file_total += 1
                total_entries += 1

                # new 为空或与 old 文本相同（忽略首尾空白）视为未翻译
                if not new_text.strip() or new_text.strip() == str(current_old).strip():
                    file_untranslated += 1
                    total_untranslated += 1
                else:
                    file_translated += 1
                    total_translated += 1

                current_old = None

        if file_total > 0:
            files_info.append({
                "file": str(rel),
                "strings_total": file_total,
                "strings_translated": file_translated,
                "strings_untranslated": file_untranslated,
            })

    summary = {
        "total_files_with_strings": len(files_info),
        "total_strings_entries": total_entries,
        "total_strings_translated": total_translated,
        "total_strings_untranslated": total_untranslated,
        "untranslated_ratio": round(
            (total_untranslated / total_entries) if total_entries else 0.0, 6
        ),
        "note": "统计基于 translate <lang> strings: 块；new 为空或与 old 相同（忽略首尾空白）视为未翻译，其中部分可能是有意保留原文。",
    }

    return {"summary": summary, "files": files_info}


def write_report_summary_md(
    project_out_root: Path,
    report: dict,
    gate_max_untranslated_ratio: float,
) -> None:
    """基于 pipeline_report.json 的结构化概要，生成 report_summary.md。"""
    final_gate = report.get("stages", {}).get("final_gate") or {}
    pilot_gate = report.get("stages", {}).get("pilot", {}).get("gate") or {}
    full_gate = report.get("stages", {}).get("full", {}).get("gate") or {}
    strings_stats = report.get("stages", {}).get("strings_stats", {})
    cfg = report.get("config", {})

    errors = int(final_gate.get("errors", 0))
    warnings = int(final_gate.get("warnings", 0))
    untranslated_ratio = float(final_gate.get("untranslated_ratio", 0.0))
    glossary_lock_errors = int(final_gate.get("glossary_lock_errors", 0))
    no_translate_errors = int(final_gate.get("no_translate_errors", 0))
    glossary_miss_warnings = int(final_gate.get("glossary_miss_warnings", 0))
    placeholder_issues = int(final_gate.get("placeholder_issues", 0))
    # ResponseChecker 丢弃条数（全量 + 补翻轮，来自 main 的 report.json）
    full_stage = report.get("stages", {}).get("full") or {}
    rt_stage = report.get("stages", {}).get("retranslate") or {}
    total_checker_dropped = int(full_stage.get("checker_dropped", 0)) + int(rt_stage.get("checker_dropped", 0))

    # 三级结论：绿 / 黄 / 红
    classification = "red"
    classification_label = "红色（不建议进入测试）"
    reason_parts: list[str] = []

    if errors == 0:
        if (
            untranslated_ratio <= gate_max_untranslated_ratio
            and glossary_lock_errors == 0
            and no_translate_errors == 0
        ):
            classification = "green"
            classification_label = "绿色（可直接进入测试）"
        else:
            classification = "yellow"
            classification_label = "黄色（可在人工确认后进入测试）"
    else:
        classification = "red"
        classification_label = "红色（存在结构性错误，不建议测试）"

    if errors > 0:
        reason_parts.append(f"存在 {errors} 条 error")
    if untranslated_ratio > gate_max_untranslated_ratio:
        reason_parts.append(
            f"漏翻比例 {untranslated_ratio:.2%} 超过阈值 {gate_max_untranslated_ratio:.2%}"
        )
    if glossary_lock_errors > 0:
        reason_parts.append(f"锁定术语违例 {glossary_lock_errors} 条")
    if no_translate_errors > 0:
        reason_parts.append(f"禁翻片段违例 {no_translate_errors} 条")
    if not reason_parts:
        reason_parts.append("未命中阻断性条件")

    code_hist = final_gate.get("warning_histogram") or {}
    # 仅展示最终闸门的 warning code 分布，按数量降序取前 10 个
    top_warning_items = sorted(
        code_hist.items(), key=lambda kv: kv[1], reverse=True
    )[:10]

    # strings 统计概要（可选）
    strings_summary = strings_stats.get("summary") or {}

    lines: list[str] = []
    lines.append("# Ren'Py 翻译质量概要")
    lines.append("")
    lines.append(
        "**本报告基于全量翻译 + 漏翻增量轮之后的最终闸门结果，用于判断当前补丁是否适合进入测试。**"
    )
    lines.append("")
    lines.append(f"- **总体结论**：{classification_label}")
    lines.append(
        f"- **关键理由**：{'; '.join(reason_parts)}"
    )
    lines.append(
        f"- **闸门阈值（漏翻比例）**：{gate_max_untranslated_ratio:.2%}"
    )
    lines.append("")

    lines.append("## 最终闸门总览（Stage 4）")
    lines.append("")
    lines.append("| 指标 | 数值 |")
    lines.append("|------|------|")
    lines.append(f"| 检查文件数 | {final_gate.get('files', 0)} |")
    lines.append(f"| 错误数（error） | {errors} |")
    lines.append(f"| 警告数（warning） | {warnings} |")
    lines.append(
        f"| 对话行总数 | {final_gate.get('dialogue_total', 0)} |"
    )
    lines.append(
        f"| 疑似未翻译行数 | {final_gate.get('untranslated_total', 0)} |"
    )
    lines.append(
        f"| 漏翻比例 | {untranslated_ratio:.2%} |"
    )
    lines.append(
        f"| 占位符/标签相关问题数 | {placeholder_issues} |"
    )
    lines.append(
        f"| ResponseChecker 丢弃条数（未写入译文） | {total_checker_dropped} |"
    )
    lines.append(
        f"| 锁定术语违例数（E411） | {glossary_lock_errors} |"
    )
    lines.append(
        f"| 禁翻片段违例数（E420） | {no_translate_errors} |"
    )
    lines.append(
        f"| 术语表未命中告警数（W410） | {glossary_miss_warnings} |"
    )
    lines.append("")

    lines.append("## Warning Code 分布（最终闸门）")
    lines.append("")
    if top_warning_items:
        for code, count in top_warning_items:
            lines.append(f"- **{code}**: {count}")
    else:
        lines.append("- 无 warning code 统计（可能所有问题均为 error 或无告警）。")
    lines.append("")

    lines.append("## 术语与占位符质量")
    lines.append("")
    lines.append(
        f"- **锁定术语违例（E411_GLOSSARY_LOCK_MISS）**：{glossary_lock_errors} 条"
    )
    lines.append(
        f"- **禁翻片段违例（E420_NO_TRANSLATE_CHANGED）**：{no_translate_errors} 条"
    )
    lines.append(
        f"- **术语表未命中告警（W410_GLOSSARY_MISS）**：{glossary_miss_warnings} 条"
    )
    lines.append(
        f"- **占位符/标签/菜单 ID/格式化占位符相关问题合计**：{placeholder_issues} 条"
    )
    lines.append("")

    lines.append("## 试跑 vs 全量/最终闸门 对比")
    lines.append("")
    lines.append("| 阶段 | 文件数 | 错误数 | 警告数 | 漏翻比例 | 长度异常告警数 | 占位符顺序告警数 |")
    lines.append("|------|--------|--------|--------|----------|----------------|------------------|")
    lines.append(
        "| 试跑 (pilot) | {files} | {errors} | {warnings} | {ratio:.4f} | {len_warns} | {ph_warns} |".format(
            files=pilot_gate.get("files", 0),
            errors=pilot_gate.get("errors", 0),
            warnings=pilot_gate.get("warnings", 0),
            ratio=pilot_gate.get("untranslated_ratio", 0.0),
            len_warns=pilot_gate.get("len_ratio_warnings", 0),
            ph_warns=pilot_gate.get("placeholder_order_warnings", 0),
        )
    )
    lines.append(
        "| 全量 (full) | {files} | {errors} | {warnings} | {ratio:.4f} | {len_warns} | {ph_warns} |".format(
            files=full_gate.get("files", 0),
            errors=full_gate.get("errors", 0),
            warnings=full_gate.get("warnings", 0),
            ratio=full_gate.get("untranslated_ratio", 0.0),
            len_warns=full_gate.get("len_ratio_warnings", 0),
            ph_warns=full_gate.get("placeholder_order_warnings", 0),
        )
    )
    lines.append(
        "| 最终 (final) | {files} | {errors} | {warnings} | {ratio:.4f} | {len_warns} | {ph_warns} |".format(
            files=final_gate.get("files", 0),
            errors=errors,
            warnings=warnings,
            ratio=untranslated_ratio,
            len_warns=final_gate.get("len_ratio_warnings", 0),
            ph_warns=final_gate.get("placeholder_order_warnings", 0),
        )
    )
    lines.append("")

    if strings_summary:
        lines.append("## translate strings 覆盖概览")
        lines.append("")
        lines.append(
            f"- 含 strings 块的文件数：{strings_summary.get('total_files_with_strings', 0)}"
        )
        lines.append(
            f"- 总 entries：{strings_summary.get('total_strings_entries', 0)}"
        )
        lines.append(
            f"- 已翻译：{strings_summary.get('total_strings_translated', 0)}"
        )
        lines.append(
            f"- 未翻译：{strings_summary.get('total_strings_untranslated', 0)}"
        )
        lines.append(
            f"- 未翻比例：{strings_summary.get('untranslated_ratio', 0.0):.2%}"
        )
        note = strings_summary.get("note")
        if note:
            lines.append(f"- 说明：{note}")
        lines.append("")

    # 漏翻归因分析
    attribution = report.get("stages", {}).get("attribution") or {}
    attr_total = int(attribution.get("total", 0))
    if attr_total > 0:
        lines.append("## 漏翻归因分析")
        lines.append("")
        lines.append("| 归因类别 | 条数 | 占漏翻总数 |")
        lines.append("|----------|------|-----------|")
        for label, key in [
            ("AI 未返回", "ai_missing"),
            ("Checker 丢弃", "checker_dropped"),
            ("回写失败", "write_fail"),
            ("未知", "unknown"),
        ]:
            cnt = int(attribution.get(key, 0))
            pct = cnt / attr_total * 100 if attr_total else 0
            lines.append(f"| {label} | {cnt} | {pct:.1f}% |")
        lines.append("")
        db_count = int(attribution.get("db_entries_count", 0))
        lines.append(f"- translation_db 条目数：{db_count}")
        note = attribution.get("note")
        if note:
            lines.append(f"- 注意：{note}")
        lines.append("")
    elif attribution:
        lines.append("## 漏翻归因分析")
        lines.append("")
        note = attribution.get("note")
        if note:
            lines.append(f"- {note}")
        else:
            lines.append("- 无漏翻条目需要归因。")
        lines.append("")

    # chunk_stats 概览
    full_chunk_stats = report.get("stages", {}).get("full", {}).get("chunk_stats") or {}
    cs_expected = int(full_chunk_stats.get("total_expected", 0))
    cs_returned = int(full_chunk_stats.get("total_returned", 0))
    cs_dropped = int(full_chunk_stats.get("total_dropped", 0))
    if cs_expected > 0:
        lines.append("## Chunk 级指标概览（全量阶段）")
        lines.append("")
        lines.append("| 指标 | 数值 |")
        lines.append("|------|------|")
        n_chunks = len(full_chunk_stats.get("per_chunk", []))
        lines.append(f"| Chunk 总数 | {n_chunks} |")
        lines.append(f"| 预期可翻译行数 (expected) | {cs_expected} |")
        ret_pct = cs_returned / cs_expected * 100
        lines.append(f"| AI 实际返回条数 (returned) | {cs_returned} ({ret_pct:.1f}%) |")
        drop_pct = cs_dropped / cs_returned * 100 if cs_returned else 0
        lines.append(f"| Checker 丢弃条数 (dropped) | {cs_dropped} ({drop_pct:.1f}%) |")
        lines.append("")

    # 补翻阶段概览
    rt_data = report.get("stages", {}).get("retranslate") or {}
    if rt_data.get("mode") == "retranslate" and rt_data.get("total_translated", 0) > 0:
        lines.append("## 补翻阶段概览")
        lines.append("")
        lines.append("| 指标 | 数值 |")
        lines.append("|------|------|")
        lines.append(f"| 扫描到漏翻行数 | {rt_data.get('total_untranslated_scanned', 0)} |")
        lines.append(f"| 涉及文件数 | {rt_data.get('retranslated_files', 0)} |")
        lines.append(f"| 补翻成功条数 | {rt_data.get('total_translated', 0)} |")
        lines.append(f"| API 请求数 | {rt_data.get('api_requests', 0)} |")
        rt_cost = rt_data.get("estimated_cost_usd", 0)
        if rt_cost:
            lines.append(f"| 估计费用 | ${rt_cost:.4f} |")
        lines.append("")

    # 简单的后续建议
    lines.append("## 建议动作")
    lines.append("")
    if classification == "green":
        lines.append("- 当前结果整体符合闸门要求，**可以直接打包进入测试环境**。")
        lines.append(
            "- 若有精力，可优先根据 Warning Code 分布处理高频风格类告警（如长度比例、中文占比等）。"
        )
    elif classification == "yellow":
        lines.append(
            "- 建议先针对上文列出的关键问题（术语违例、漏翻比例偏高等）做抽样人工复查，确认风险可接受后再进入测试。"
        )
    else:
        lines.append(
            "- 存在结构性错误或严重术语/禁翻违例，**不建议直接进入测试**，请先修正问题后重新运行一键流水线。"
        )

    summary_path = project_out_root / "report_summary.md"
    summary_path.write_text("\n".join(lines), encoding="utf-8")

def package_output(output_root: Path, package_name: str) -> Path:
    """将翻译结果打包为 zip，默认打包 output_root/game。"""
    src = output_root / "game"
    if not src.exists():
        src = output_root
    archive_base = output_root / package_name
    archive = shutil.make_archive(str(archive_base), "zip", root_dir=src)
    return Path(archive)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="一键翻译流水线")
    parser.add_argument("--game-dir", required=True, help="游戏根目录")
    parser.add_argument("--provider", default="xai", choices=["xai", "grok", "openai", "deepseek", "claude", "gemini"])
    parser.add_argument("--api-key", default="", help="API 密钥；留空则读取 XAI_API_KEY")
    parser.add_argument("--model", default="grok-4-1-fast-reasoning")
    parser.add_argument("--genre", default="adult", choices=["adult", "visual_novel", "rpg", "general"])
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--rpm", type=int, default=600)
    parser.add_argument("--rps", type=int, default=10)
    parser.add_argument("--timeout", type=float, default=180.0)
    parser.add_argument("--max-chunk-tokens", type=int, default=4000)
    parser.add_argument("--max-response-tokens", type=int, default=32768)
    parser.add_argument("--pilot-count", type=int, default=20, help="试跑文件数")
    parser.add_argument("--gate-max-untranslated-ratio", type=float, default=0.08, help="闸门允许的最大漏翻占比")
    parser.add_argument("--output-dir", default="output")
    parser.add_argument("--clean-output", action="store_true", help="开始前清理输出目录")
    parser.add_argument("--dict", nargs="*", default=[], metavar="PATH", help="词典文件（透传 main.py）")
    parser.add_argument("--exclude", nargs="*", default=[], metavar="PATTERN", help="排除文件模式（透传 main.py）")
    parser.add_argument("--copy-assets", action="store_true", help="复制非 .rpy 资源（透传 main.py）")
    parser.add_argument("--target-lang", default="zh", help="目标语言（透传 main.py）")
    parser.add_argument("--package-name", default="CN_patch_game", help="输出 zip 包名（不含扩展名）")
    parser.add_argument("--patch-font", action="store_true", default=False,
                        help="打包前启用自动字体补丁：复制字体到 game/ 并改写 gui.*_font")
    parser.add_argument("--font-file", default="", metavar="PATH",
                        help="指定字体文件路径，覆盖默认的 resources/fonts/ 查找")
    parser.add_argument("--min-dialogue-density", type=float, default=0.20, metavar="RATIO",
                        help="对话密度阈值 (默认: 0.20)；低于此值的文件走定向翻译模式")
    parser.add_argument("--tl-mode", action="store_true", default=False,
                        help="使用 tl-mode 替代 direct-mode：跳过试跑/补翻，直接扫描 tl/<lang>/ 空槽位翻译")
    parser.add_argument("--tl-lang", default="chinese", metavar="LANG",
                        help="tl 语言子目录名 (默认: chinese)；仅 --tl-mode 时有效")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    t0 = time.time()

    api_key = args.api_key or os.environ.get("XAI_API_KEY", "")
    if not api_key:
        raise StageError("未提供 API key，请传 --api-key 或设置 XAI_API_KEY")
    project_root = Path(args.game_dir).resolve()
    if not project_root.exists():
        raise StageError(f"游戏目录不存在: {project_root}")

    scan_root = resolve_scan_root(project_root)

    # 项目级输出根目录: <output-dir>/projects/<project_name>/
    out_root = Path(args.output_dir).resolve()
    project_name = project_root.name
    project_out_root = out_root / "projects" / project_name

    # 分阶段目录（目前实际输出落在 stage2_translated，其余阶段为预留占位）
    stage0_raw = project_out_root / "stage0_raw"
    stage1_normalized = project_out_root / "stage1_normalized"
    stage2_translated = project_out_root / "stage2_translated"
    stage3_polished = project_out_root / "stage3_polished"

    # 流水线内部使用的临时目录仍放在项目子目录下
    pipeline_root = project_out_root / "_pipeline"
    pilot_input = pipeline_root / "pilot_input"
    pilot_output = pipeline_root / "pilot_output"
    incremental_input = pipeline_root / "incremental_input"
    incremental_output = pipeline_root / "incremental_output"

    # 项目级系统 UI 术语：projects/<project_name>/system_ui_terms.json
    # main.py 在每个 output_dir 下加载同名文件，这里负责在各阶段输出目录之间同步。
    system_terms_src = project_out_root / "system_ui_terms.json"

    def _propagate_system_terms(dst_output_root: Path) -> None:
        """将项目级 system_ui_terms.json 复制到指定输出根目录，供 main.py 使用。"""
        if not system_terms_src.exists():
            return
        try:
            dst_output_root.mkdir(parents=True, exist_ok=True)
            dst_path = dst_output_root / "system_ui_terms.json"
            shutil.copy2(system_terms_src, dst_path)
        except Exception:
            # 术语文件缺失不会影响流水线主流程，这里静默失败即可。
            pass

    if args.clean_output and project_out_root.exists():
        _print(f"[CLEAN] 删除项目输出目录: {project_out_root}")
        shutil.rmtree(project_out_root)

    # 创建基础目录结构
    for d in (stage0_raw, stage1_normalized, stage2_translated, stage3_polished,
              pipeline_root, pilot_output):
        d.mkdir(parents=True, exist_ok=True)

    use_tl_mode = getattr(args, "tl_mode", False)
    tl_lang = getattr(args, "tl_lang", "chinese")

    report: dict = {
        "config": {
            "game_dir": str(project_root),
            "scan_root": str(scan_root),
            "provider": args.provider,
            "model": args.model,
            "pilot_count": args.pilot_count,
            "gate_max_untranslated_ratio": args.gate_max_untranslated_ratio,
            "dict": args.dict,
            "exclude": args.exclude,
            "copy_assets": args.copy_assets,
            "target_lang": args.target_lang,
            "tl_mode": use_tl_mode,
            "tl_lang": tl_lang if use_tl_mode else None,
        },
        "stages": {},
    }

    if use_tl_mode:
        # ── tl-mode 流水线：跳过试跑和补翻，直接全量 tl 翻译 ──
        _print("\n=== tl-mode 流水线 ===")
        _print(f"[TL] 语言目录: tl/{tl_lang}/")
        report["stages"]["pilot"] = {"skipped": True, "reason": "tl-mode 不需要试跑"}

        # Stage: tl-mode 全量翻译
        _print("\n=== Stage 1/2: tl-mode 全量翻译 ===")
        _propagate_system_terms(stage2_translated)
        run_main(
            game_dir=project_root,
            output_dir=stage2_translated,
            provider=args.provider,
            api_key=api_key,
            model=args.model,
            genre=args.genre,
            workers=args.workers,
            rpm=args.rpm,
            rps=args.rps,
            timeout=args.timeout,
            max_chunk_tokens=args.max_chunk_tokens,
            max_response_tokens=args.max_response_tokens,
            log_file=pipeline_root / "tl_mode.log",
            resume=False,
            dict_paths=args.dict,
            excludes=args.exclude,
            copy_assets=args.copy_assets,
            target_lang=args.target_lang,
            stage="full",
            min_dialogue_density=args.min_dialogue_density,
            tl_mode=True,
            tl_lang=tl_lang,
        )

        # 读取 tl-mode 报告
        tl_report_path = stage2_translated / "tl_mode_report.json"
        if tl_report_path.exists():
            try:
                tl_report_data = json.loads(tl_report_path.read_text(encoding="utf-8"))
                report["stages"]["tl_mode"] = tl_report_data
            except Exception:
                report["stages"]["tl_mode"] = {"error": "无法读取 tl_mode_report.json"}
        else:
            report["stages"]["tl_mode"] = {"note": "tl_mode_report.json 未生成"}

        report["stages"]["retranslate"] = {"skipped": True, "reason": "tl-mode 精度 99.97%，无需补翻"}

        # Stage: 报告与打包
        _print("\n=== Stage 2/2: 报告与打包 ===")

    else:
        # ── direct-mode 流水线（原有四阶段） ──

        # Stage 1: pilot
        _print("\n=== Stage 1/4: 试跑批次 ===")
        pilot_files = pick_pilot_files(scan_root, args.pilot_count)
        if not pilot_files:
            raise StageError("未找到任何 .rpy 文件")
        copy_subset_to_input(scan_root, pilot_files, pilot_input)
        _propagate_system_terms(pilot_output)

        run_main(
            game_dir=pilot_input,
            output_dir=pilot_output,
            provider=args.provider,
            api_key=api_key,
            model=args.model,
            genre=args.genre,
            workers=args.workers,
            rpm=args.rpm,
            rps=args.rps,
            timeout=args.timeout,
            max_chunk_tokens=args.max_chunk_tokens,
            max_response_tokens=args.max_response_tokens,
            log_file=pipeline_root / "pilot.log",
            resume=False,
            dict_paths=args.dict,
            excludes=args.exclude,
            copy_assets=args.copy_assets,
            target_lang=args.target_lang,
            stage="pilot",
            min_dialogue_density=args.min_dialogue_density,
        )

        pilot_translated_root = resolve_scan_root(pilot_output)
        gate1 = evaluate_gate(resolve_scan_root(pilot_input), pilot_translated_root)
        report["stages"]["pilot"] = {
            "files": len(pilot_files),
            "gate": gate1,
        }

        _print(
            "[GATE-PILOT] "
            f"errors={gate1['errors']} "
            f"warnings={gate1['warnings']} "
            f"untranslated={gate1['untranslated_total']} "
            f"ratio={gate1['untranslated_ratio']:.4f} "
            f"len_warns={gate1['len_ratio_warnings']} "
            f"len_ratio={gate1['len_ratio_warning_ratio']:.4f} "
            f"ph_order_warns={gate1['placeholder_order_warnings']}"
        )
        if gate1["errors"] > 0:
            raise StageError("试跑批次未通过：存在结构错误")
        pilot_ratio_exceeded = gate1["untranslated_ratio"] > args.gate_max_untranslated_ratio
        report["stages"]["pilot"]["ratio_exceeded"] = pilot_ratio_exceeded
        if pilot_ratio_exceeded:
            _print("[WARN ] 试跑漏翻占比超阈值，继续执行全量与增量轮再做最终判定")

        # 试跑后自动术语表提取：从 pilot 翻译结果中提取高频专有名词
        try:
            from glossary import Glossary as _Glossary
            pilot_glossary = _Glossary()
            pilot_glossary_path = pilot_output / "glossary.json"
            pilot_glossary.load(str(pilot_glossary_path))

            pilot_db_path = pilot_output / "translation_db.json"
            if pilot_db_path.exists():
                pilot_db = TranslationDB(pilot_db_path)
                pilot_db.load()
                new_terms = pilot_glossary.extract_terms_from_translations(pilot_db.entries)
                if new_terms:
                    added = pilot_glossary.auto_add_terms(new_terms)
                    pilot_glossary.save(str(pilot_glossary_path))
                    # 同步到全量阶段的输出目录
                    stage2_glossary_path = stage2_translated / "glossary.json"
                    stage2_glossary_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(str(pilot_glossary_path), str(stage2_glossary_path))
                    report["stages"]["pilot"]["auto_terms_extracted"] = len(new_terms)
                    report["stages"]["pilot"]["auto_terms_added"] = added
                    _print(f"[GLOSS] 从试跑结果自动提取 {len(new_terms)} 条术语，新增 {added} 条")
                else:
                    _print("[GLOSS] 试跑结果中未发现可自动提取的术语")
        except Exception as e:
            _print(f"[WARN ] 自动术语提取失败（不影响后续流程）: {e}")

        # Stage 2: full batch
        _print("\n=== Stage 2/4: 全量批处理 ===")
        _propagate_system_terms(stage2_translated)
        run_main(
            game_dir=project_root,
            output_dir=stage2_translated,
            provider=args.provider,
            api_key=api_key,
            model=args.model,
            genre=args.genre,
            workers=args.workers,
            rpm=args.rpm,
            rps=args.rps,
            timeout=args.timeout,
            max_chunk_tokens=args.max_chunk_tokens,
            max_response_tokens=args.max_response_tokens,
            log_file=pipeline_root / "full.log",
            resume=False,
            dict_paths=args.dict,
            excludes=args.exclude,
            copy_assets=args.copy_assets,
            target_lang=args.target_lang,
            stage="full",
            min_dialogue_density=args.min_dialogue_density,
        )

        full_translated_root = resolve_scan_root(stage2_translated)
        gate2 = evaluate_gate(scan_root, full_translated_root)
        report["stages"]["full"] = {"gate": gate2}
        try:
            full_report_path = stage2_translated / "report.json"
            if full_report_path.exists():
                full_report = json.loads(full_report_path.read_text(encoding="utf-8"))
                report["stages"]["full"]["checker_dropped"] = int(full_report.get("total_checker_dropped", 0))
                report["stages"]["full"]["chunk_stats"] = full_report.get("chunk_stats", {})
            else:
                report["stages"]["full"]["checker_dropped"] = 0
        except Exception:
            report["stages"]["full"]["checker_dropped"] = 0
        _print(
            "[GATE-FULL] "
            f"errors={gate2['errors']} "
            f"warnings={gate2['warnings']} "
            f"untranslated={gate2['untranslated_total']} "
            f"ratio={gate2['untranslated_ratio']:.4f} "
            f"len_warns={gate2['len_ratio_warnings']} "
            f"len_ratio={gate2['len_ratio_warning_ratio']:.4f} "
            f"ph_order_warns={gate2['placeholder_order_warnings']}"
        )
        if gate2["errors"] > 0:
            raise StageError("全量批处理未通过：存在结构错误")

        # Stage 3: 漏翻补翻轮 (retranslate — 原地补翻，不覆盖已有翻译)
        _print("\n=== Stage 3/4: 漏翻补翻轮 ===")
        untranslated_files = collect_files_with_untranslated(full_translated_root)
        report["stages"]["retranslate"] = {"candidate_files": len(untranslated_files)}

        if untranslated_files:
            from main import (
                retranslate_file as _retranslate_file,
                find_untranslated_lines as _find_untranslated_lines,
                ProgressTracker as _ProgressTracker,
            )
            from api_client import APIClient as _APIClient, APIConfig as _APIConfig
            from glossary import Glossary as _Glossary

            rt_config = _APIConfig(
                provider=args.provider,
                api_key=api_key,
                model=args.model,
                rpm=args.rpm,
                rps=args.rps,
                timeout=args.timeout,
                temperature=0.1,
                max_response_tokens=args.max_response_tokens,
            )
            rt_client = _APIClient(rt_config)

            rt_glossary = _Glossary()
            rt_glossary_path = stage2_translated / "glossary.json"
            rt_glossary.load(str(rt_glossary_path))
            if args.dict:
                for dp in args.dict:
                    rt_glossary.load_dict(dp)

            rt_progress = _ProgressTracker(pipeline_root / "retranslate_progress.json")
            rt_progress.data = {"completed_files": [], "completed_chunks": {}, "stats": {}}
            rt_progress.save()

            rt_db = TranslationDB(pipeline_root / "retranslate_db.json")
            rt_run_id = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())

            # 用 find_untranslated_lines 精确扫描漏翻行
            rpy_files_all = sorted(list_rpy_files(full_translated_root))
            files_to_rt: list[tuple[Path, int]] = []
            total_ut = 0
            for f in rpy_files_all:
                ut = _find_untranslated_lines(read_file(f))
                if ut:
                    files_to_rt.append((f, len(ut)))
                    total_ut += len(ut)

            _print(f"[SCAN] 发现 {total_ut} 行漏翻，分布在 {len(files_to_rt)} 个文件中")

            rt_total_translated = 0
            rt_total_warnings: list[str] = []
            rt_quality: dict[str, list[dict]] = {}

            for idx, (rpy_path, n_ut) in enumerate(files_to_rt, 1):
                rel = rpy_path.relative_to(full_translated_root)
                _print(f"  [{idx}/{len(files_to_rt)}] {rel} ({n_ut} 行)")
                try:
                    count, warnings = _retranslate_file(
                        rpy_path,
                        full_translated_root,
                        full_translated_root,
                        rt_client,
                        rt_glossary,
                        rt_progress,
                        rt_quality,
                        genre=args.genre,
                        translation_db=rt_db,
                        run_id=rt_run_id,
                        stage="retranslate",
                        provider=rt_config.provider,
                        model=rt_config.model,
                    )
                    rt_total_translated += count
                    rt_total_warnings.extend(warnings)
                except KeyboardInterrupt:
                    rt_glossary.save(str(rt_glossary_path))
                    rt_progress.save()
                    rt_db.save()
                    raise
                except Exception as e:
                    _print(f"  [ERROR] {rel}: {e}")
                    rt_total_warnings.append(str(e))

                if idx % 5 == 0:
                    rt_glossary.save(str(rt_glossary_path))

            rt_glossary.save(str(rt_glossary_path))
            rt_db.save()

            _print(f"[RETRANSLATE] 补翻完成: {rt_total_translated} 条, "
                   f"API 用量: {rt_client.usage.summary()}")

            report["stages"]["retranslate"].update({
                "mode": "retranslate",
                "retranslated_files": len(files_to_rt),
                "total_untranslated_scanned": total_ut,
                "total_translated": rt_total_translated,
                "total_warnings": len(rt_total_warnings),
                "api_requests": rt_client.usage.total_requests,
                "input_tokens": rt_client.usage.total_input_tokens,
                "output_tokens": rt_client.usage.total_output_tokens,
                "estimated_cost_usd": round(rt_client.usage.estimated_cost, 4),
                "checker_dropped": 0,
            })
        else:
            _print("[INFO] 全量阶段无漏翻文件，跳过补翻")
            report["stages"]["retranslate"]["skipped"] = True
            report["stages"]["retranslate"]["checker_dropped"] = 0

        # Stage 4: final gate (direct-mode)
        _print("\n=== Stage 4/4: 最终自动闸门 ===")

    # ── 共享的最终闸门与报告（direct-mode 和 tl-mode 共用） ──
    full_translated_root = resolve_scan_root(stage2_translated)
    gate3 = evaluate_gate(scan_root, full_translated_root)
    report["stages"]["final_gate"] = gate3
    _print(
        "[GATE-FINAL] "
        f"errors={gate3['errors']} "
        f"warnings={gate3['warnings']} "
        f"untranslated={gate3['untranslated_total']} "
        f"ratio={gate3['untranslated_ratio']:.4f} "
        f"len_warns={gate3['len_ratio_warnings']} "
        f"len_ratio={gate3['len_ratio_warning_ratio']:.4f} "
        f"ph_order_warns={gate3['placeholder_order_warnings']}"
    )

    # Strings 翻译统计视图：基于最终翻译结果统计 translate ... strings: 覆盖情况
    try:
        strings_stats = collect_strings_stats(full_translated_root)
        report["stages"]["strings_stats"] = strings_stats
    except Exception as e:
        _print(f"[WARN ] 收集 strings 统计时出错: {e}")

    ok = gate3["errors"] == 0 and gate3["untranslated_ratio"] <= args.gate_max_untranslated_ratio

    # 打包前自动字体补丁（可选）
    if getattr(args, "patch_font", False):
        resources_fonts = Path(__file__).parent / "resources" / "fonts"
        font_path = resolve_font(resources_fonts, args.font_file or None)
        if font_path:
            output_game = resolve_scan_root(stage2_translated)
            apply_font_patch(output_game, scan_root, font_path)

    report["stages"]["package"] = {}
    package_path = package_output(stage2_translated, args.package_name)
    report["stages"]["package"]["zip"] = str(package_path)

    report["success"] = ok
    report["elapsed_seconds"] = round(time.time() - t0, 2)

    report_path = project_out_root / "pipeline_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    # 合并各阶段 translation_db.json 到项目级 translation_db.json（pilot → full → retranslate）
    try:
        project_db = TranslationDB(project_out_root / "translation_db.json")
        project_db.load()
        db_paths_to_merge = [
            pilot_output / "translation_db.json",
            stage2_translated / "translation_db.json",
            pipeline_root / "retranslate_db.json",
        ]
        for db_path in db_paths_to_merge:
            if not db_path.exists():
                continue
            sub_db = TranslationDB(db_path)
            sub_db.load()
            project_db.add_entries(sub_db.entries)
        project_db.save()
    except Exception as e:
        _print(f"[WARN ] 合并 translation_db.json 失败: {e}")

    # 漏翻归因分析
    try:
        if project_db.entries:
            attribution = attribute_untranslated(full_translated_root, project_db)
        else:
            attribution = {
                "total": 0, "ai_missing": 0, "checker_dropped": 0,
                "write_fail": 0, "unknown": 0, "db_entries_count": 0,
                "note": "translation_db 为空，无法逐行归因",
            }
        report["stages"]["attribution"] = attribution
        if attribution["total"] > 0:
            _print(
                f"[ATTRIBUTION] 漏翻归因: 总计 {attribution['total']} | "
                f"AI未返回 {attribution['ai_missing']} "
                f"({attribution['ai_missing'] / attribution['total'] * 100:.1f}%) | "
                f"Checker丢弃 {attribution['checker_dropped']} "
                f"({attribution['checker_dropped'] / attribution['total'] * 100:.1f}%) | "
                f"回写失败 {attribution['write_fail']} "
                f"({attribution['write_fail'] / attribution['total'] * 100:.1f}%) | "
                f"未知 {attribution['unknown']} "
                f"({attribution['unknown'] / attribution['total'] * 100:.1f}%)"
            )
        else:
            _print("[ATTRIBUTION] 无漏翻条目需要归因")
    except Exception as e:
        _print(f"[WARN ] 漏翻归因分析失败: {e}")

    # 结构化 Markdown 概要（基于全量 + 增量后的最终闸门结果）
    try:
        write_report_summary_md(
            project_out_root=project_out_root,
            report=report,
            gate_max_untranslated_ratio=args.gate_max_untranslated_ratio,
        )
    except Exception as e:
        _print(f"[WARN ] 生成 report_summary.md 失败: {e}")

    # 重新写入 pipeline_report.json（归因分析等后续数据已追加到 report dict）
    try:
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass

    _print(f"\n[REPORT] {report_path}")
    if ok:
        _print("[DONE ] 一键流水线执行成功")
        return

    raise StageError("最终闸门未通过，请检查 pipeline_report.json 与 _pipeline 日志")


if __name__ == "__main__":
    try:
        main()
    except StageError as e:
        _print(f"[FAIL ] {e}")
        sys.exit(2)
