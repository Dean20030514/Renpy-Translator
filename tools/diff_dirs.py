#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Diff CN-EN — 目录级对比生成结构与缺失报告（可替代 顶层/校对/rpy_cn_en_diff.py）

用法：
  python tools/diff_rpy_dirs.py --cn <cn_dir> --en <en_dir> --out outputs/rpy_diff

说明：
  - 依赖模块 src/renpy_tools/diff/parser.py，便于在打包安装后可用；
  - 输出 summary.json / summary.csv 与每对文件的报告 Markdown、缺失片段 snippets。
"""
from __future__ import annotations

import os
import re
import csv
import argparse
import json
import sys
import pathlib
from typing import List, Dict, Tuple, Any
import concurrent.futures

# 添加 src 到路径
_project_root = pathlib.Path(__file__).parent.parent
if str(_project_root / "src") not in sys.path:
    sys.path.insert(0, str(_project_root / "src"))

# 统一日志
try:
    from renpy_tools.utils.logger import get_logger
    _logger = get_logger("diff_dirs")
except ImportError:
    _logger = None

def _log(level: str, msg: str) -> None:
    """统一日志输出"""
    if _logger:
        getattr(_logger, level, _logger.info)(msg)
    elif level in ("warning", "error"):
        print(f"[{level.upper()}] {msg}", file=sys.stderr)
    else:
        print(f"[{level.upper()}] {msg}")

try:
    from renpy_tools.diff.parser import parse_rpy, align_by_speaker  # type: ignore
except (ImportError, ModuleNotFoundError):
    _log("error", "renpy_tools.diff.parser not available. Please run inside repo or install the package.")
    sys.exit(2)

IMAGEBUTTON_JUMP_RE = re.compile(r"action\s+Jump\(\s*'([^']+)'\s*\)")


def safe_name_for_pair(basename: str) -> str:
    return re.sub(r'[^A-Za-z0-9_.-]+', '_', basename)

def make_pair_key(p: str) -> Tuple[str, str]:
    bn = os.path.basename(p)
    stem = os.path.splitext(bn)[0]
    return stem, stem

def discover_pairs(cn_dir: str, en_dir: str):
    cn_files = [os.path.join(cn_dir, f) for f in os.listdir(cn_dir) if f.endswith('.rpy')]
    en_files = [os.path.join(en_dir, f) for f in os.listdir(en_dir) if f.endswith('.rpy')]
    cn_map = { os.path.splitext(os.path.basename(p))[0]: p for p in cn_files }
    en_map = { os.path.splitext(os.path.basename(p))[0]: p for p in en_files }
    all_keys = set(cn_map) | set(en_map)
    pairs, cn_only, en_only = [], [], []
    for k in sorted(all_keys):
        if k in cn_map and k in en_map:
            pairs.append((k, cn_map[k], en_map[k]))
        elif k in cn_map:
            cn_only.append(cn_map[k])
        else:
            en_only.append(en_map[k])
    return pairs, cn_only, en_only


def relpath(p: str) -> str:
    try:
        return str(pathlib.Path(p).resolve())
    except (OSError, RuntimeError, ValueError):
        return p


def build_snippet_from_dialogue(d) -> str:
    text_escaped = d.text.replace('"', r'\"')
    if d.kind == 'speaker' and d.speaker:
        return f'{d.speaker} "{text_escaped}"'
    elif d.kind == 'text':
        return f'text "{text_escaped}"'
    else:
        return f'"{text_escaped}"'


def compare_pair(key: str, cn_file: str, en_file: str, out_dir: str) -> Dict:
    en_parsed = parse_rpy(en_file)
    cn_parsed = parse_rpy(cn_file)

    en_labels = set(en_parsed.labels.keys())
    cn_labels = set(cn_parsed.labels.keys())
    en_screens = set(en_parsed.screens.keys())
    cn_screens = set(cn_parsed.screens.keys())

    per_block_missing = []

    def analyze_block(kind: str, name: str, en_block, cn_block):
        mapping = align_by_speaker(en_block.dialogues, cn_block.dialogues)
        missing_entries = []
        menu_issues = []
        for en_idx, cn_idx in mapping:
            if en_idx is not None and cn_idx is None:
                d = en_block.dialogues[en_idx]
                missing_entries.append({
                    "en_index": en_idx,
                    "en_line_no": d.line_no,
                    "speaker": d.speaker if d.kind == "speaker" else d.kind,
                    "text": d.text,
                    "suggestion": build_snippet_from_dialogue(d)
                })
        en_menus = getattr(en_block, 'menus', []) or []
        cn_menus = getattr(cn_block, 'menus', []) or []
        max_m = max(len(en_menus), len(cn_menus))
        for mi in range(max_m):
            en_m = en_menus[mi] if mi < len(en_menus) else None
            cn_m = cn_menus[mi] if mi < len(cn_menus) else None
            if en_m and not cn_m:
                for ch in en_m.choices:
                    action = 'pass'
                    if ch.target_type == 'jump' and ch.target_name:
                        action = f"jump {ch.target_name}"
                    elif ch.target_type == 'call' and ch.target_name:
                        action = f"call {ch.target_name}"
                    elif ch.target_type == 'call_screen' and ch.target_name:
                        action = f"call screen {ch.target_name}"
                    suggestion = "\n".join([
                        "menu:",
                        f"    \"{ch.text.replace('\\"', r'\\\\\"')}\":",
                        f"        {action}",
                    ])
                    missing_entries.append({
                        "en_index": None,
                        "en_line_no": ch.line_no,
                        "speaker": "menu",
                        "text": ch.text,
                        "suggestion": suggestion
                    })
                continue
            if en_m and cn_m:
                e_choices = en_m.choices
                c_choices = cn_m.choices
                mlen = min(len(e_choices), len(c_choices))
                for ci in range(mlen):
                    e = e_choices[ci]
                    c = c_choices[ci]
                    e_t = (e.target_type or "", e.target_name or "")
                    c_t = (c.target_type or "", c.target_name or "")
                    if e_t != c_t:
                        menu_issues.append({
                            "menu_index": mi,
                            "choice_index": ci,
                            "en_target": e_t,
                            "cn_target": c_t,
                            "detail": "target_mismatch_or_order"
                        })
                if len(c_choices) < len(e_choices):
                    for ci in range(len(c_choices), len(e_choices)):
                        e = e_choices[ci]
                        action = 'pass'
                        if e.target_type == 'jump' and e.target_name:
                            action = f"jump {e.target_name}"
                        elif e.target_type == 'call' and e.target_name:
                            action = f"call {e.target_name}"
                        elif e.target_type == 'call_screen' and e.target_name:
                            action = f"call screen {e.target_name}"
                        suggestion = "\n".join([
                            "menu:",
                            f"    \"{e.text.replace('\\"', r'\\\\\"')}\":",
                            f"        {action}",
                        ])
                        missing_entries.append({
                            "en_index": None,
                            "en_line_no": e.line_no,
                            "speaker": "menu",
                            "text": e.text,
                            "suggestion": suggestion
                        })
        counts_diff = {}
        keys = ["jump","call","call_screen","scene","show","hide","menu","imagebutton_jumps"]
        for k in keys:
            counts_diff[k] = en_block.counts.get(k,0) - cn_block.counts.get(k,0)
        if missing_entries or any(v!=0 for v in counts_diff.values()) or menu_issues:
            per_block_missing.append({
                "type": kind,
                "name": name,
                "missing_dialogues": missing_entries,
                "counts_diff": counts_diff,
                "menu_issues": menu_issues,
                "en_dialogues": len(en_block.dialogues),
                "cn_dialogues": len(cn_block.dialogues),
                "en_start_line": en_block.start_line,
                "cn_start_line": cn_block.start_line,
            })

    for name in sorted(en_labels & cn_labels):
        analyze_block("label", name, en_parsed.labels[name], cn_parsed.labels[name])
    for name in sorted(en_screens & cn_screens):
        analyze_block("screen", name, en_parsed.screens[name], cn_parsed.screens[name])

    reports_dir = os.path.join(out_dir, "reports")
    os.makedirs(reports_dir, exist_ok=True)
    report_path = os.path.join(reports_dir, f"{safe_name_for_pair(key)}.md")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(f"# 遗缺对比报告 — {key}\n\n")
        f.write(f"EN: `{relpath(en_file)}`\n\n")
        f.write(f"CN: `{relpath(cn_file)}`\n\n")

    snippets_dir = os.path.join(out_dir, "snippets")
    os.makedirs(snippets_dir, exist_ok=True)
    snippets_path = os.path.join(snippets_dir, f"{safe_name_for_pair(key)}__cn_missing_snippets.rpy.txt")
    with open(snippets_path, 'w', encoding='utf-8') as sf:
        sf.write(f"# Snippets for pair: {key}\n")

    return {
        "key": key,
        "cn_file": relpath(cn_file),
        "en_file": relpath(en_file),
        "report_path": report_path,
        "snippets_path": snippets_path,
    }


def write_summary(out_dir: str, rows: List[Dict], cn_only: List[str], en_only: List[str]):
    os.makedirs(out_dir, exist_ok=True)
    csv_path = os.path.join(out_dir, 'summary.csv')
    with open(csv_path, 'w', newline='', encoding='utf-8') as cf:
        w = csv.writer(cf)
        w.writerow(["pair_key","en_file","cn_file","report_path","snippets_path"]) 
        for r in rows:
            w.writerow([r["key"], r["en_file"], r["cn_file"], r["report_path"], r["snippets_path"]])
    j_path = os.path.join(out_dir, 'summary.json')
    with open(j_path, 'w', encoding='utf-8') as jf:
        json.dump({"pairs": rows, "cn_only": cn_only, "en_only": en_only}, jf, ensure_ascii=False, indent=2)


def write_aggregate_md(out_dir: str, pair_rows: List[Dict]):
    """聚合视图：将各文件的报告入口汇总为一页，便于校对导航。"""
    md_path = os.path.join(out_dir, 'aggregate.md')
    lines = ["# Diff 汇总", ""]
    for r in sorted(pair_rows, key=lambda x: x["key"]):
        lines.append(f"- {r['key']} — [报告]({os.path.relpath(r['report_path'], out_dir)}) · [缺失片段]({os.path.relpath(r['snippets_path'], out_dir)})")
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines) + "\n")


def build_cross_file_graph(en_dir: str, out_dir: str):
    """扫描 EN 目录，基于 label/screen 与 jump/menu/imagebutton 生成跨文件引用 DOT 图。

    输出：
      - graph.dot：有向图，node=label|screen，edge=跳转/调用
      - graph.json：{ nodes:[..], edges:[{src,tgt,kind,file,line}], dangling:[tgt,...] }
    """
    try:
        parsed_files = []
        for f in os.listdir(en_dir):
            if f.endswith('.rpy'):
                path = os.path.join(en_dir, f)
                try:
                    pf = parse_rpy(path)
                    parsed_files.append(pf)
                except Exception:
                    continue
        nodes = set()
        for pf in parsed_files:
            nodes.update(pf.labels.keys())
            nodes.update(pf.screens.keys())
        edges = []
        dangling = set()
        for pf in parsed_files:
            cur_file = pf.path
            # 由菜单指向目标
            for b in list(pf.labels.values()) + list(pf.screens.values()):
                for mb in getattr(b, 'menus', []) or []:
                    for ch in mb.choices:
                        if ch.target_name:
                            kind = ch.target_type or 'menu'
                            edges.append({"src": b.name, "tgt": ch.target_name, "kind": kind, "file": cur_file, "line": ch.line_no})
                            if ch.target_name not in nodes:
                                dangling.add(ch.target_name)
                # imagebutton action Jump('xxx')
                for tgt, ln in getattr(b, 'imagebutton_jumps', []) or []:
                    edges.append({"src": b.name, "tgt": tgt, "kind": "imagebutton_jump", "file": cur_file, "line": ln})
                    if tgt not in nodes:
                        dangling.add(tgt)
        os.makedirs(out_dir, exist_ok=True)
        # DOT
        dot_path = os.path.join(out_dir, 'graph.dot')
        with open(dot_path, 'w', encoding='utf-8') as df:
            df.write("digraph RPY {\n")
            df.write("  rankdir=LR;\n  node [shape=box, fontsize=10];\n")
            for n in sorted(nodes):
                df.write(f"  \"{n}\";\n")
            for e in edges:
                color = {"jump":"black","call":"gray30","call_screen":"gray50","menu":"#2563eb","imagebutton_jump":"#f59e0b"}.get(e["kind"], "black")
                df.write(f"  \"{e['src']}\" -> \"{e['tgt']}\" [label={e['kind']!r}, color=\"{color}\"];\n")
            df.write("}\n")
        # JSON 概览
        with open(os.path.join(out_dir, 'graph.json'), 'w', encoding='utf-8') as jf:
            json.dump({"nodes": sorted(list(nodes)), "edges": edges, "dangling": sorted(list(dangling))}, jf, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[WARN] 构建跨文件引用图失败: {e}")


def main():
    ap = argparse.ArgumentParser(description="Bulk diff CN vs EN Ren'Py .rpy scripts and generate reports.")
    ap.add_argument("--cn", required=True, help="Directory containing CN .rpy files")
    ap.add_argument("--en", required=True, help="Directory containing EN .rpy files")
    ap.add_argument("--out", default="./rpy_diff_out", help="Output directory for reports and summary")
    ap.add_argument("--pairs", action="store_true", help="Only detect and list pairs, do not parse/compare")
    ap.add_argument("--workers", default="auto", help="并发 worker 数（auto=cpu-1，0=不并行）")
    args = ap.parse_args()

    cn_dir = args.cn
    en_dir = args.en
    out_dir = args.out
    if not os.path.isdir(cn_dir):
        print(f"[ERROR] CN dir not found: {cn_dir}", file=sys.stderr)
        sys.exit(2)
    if not os.path.isdir(en_dir):
        print(f"[ERROR] EN dir not found: {en_dir}", file=sys.stderr)
        sys.exit(2)

    pairs, cn_only, en_only = discover_pairs(cn_dir, en_dir)
    print(f"Detected {len(pairs)} pair(s). CN-only: {len(cn_only)} | EN-only: {len(en_only)}")
    for key, cn_p, en_p in pairs:
        print(f"  - {key}: CN={os.path.basename(cn_p)} | EN={os.path.basename(en_p)}")

    if args.pairs:
        if cn_only:
            print("\n[CN only]")
            for p in cn_only: print("  -", os.path.basename(p))
        if en_only:
            print("\n[EN only]")
            for p in en_only: print("  -", os.path.basename(p))
        return

    rows = []
    os.makedirs(out_dir, exist_ok=True)

    # 解析 workers
    def parse_workers(w):
        if isinstance(w, int):
            return w
        if isinstance(w, str):
            if w == 'auto':
                c = os.cpu_count() or 1
                return max(1, c - 1)
            try:
                return int(w)
            except ValueError:
                return 0
        return 0
    workers = parse_workers(args.workers)

    if workers and workers > 0:
        with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as ex:
            futures = [ex.submit(compare_pair, key, cn_p, en_p, out_dir) for key, cn_p, en_p in pairs]
            for fut in concurrent.futures.as_completed(futures):
                try:
                    rows.append(fut.result())
                except Exception as e:
                    print(f"[WARN] pair 处理失败: {e}")
    else:
        for key, cn_p, en_p in pairs:
            row = compare_pair(key, cn_p, en_p, out_dir)
            rows.append(row)

    write_summary(out_dir, rows, cn_only, en_only)
    write_aggregate_md(out_dir, rows)
    # 生成跨文件引用图（基于 EN 结构）
    build_cross_file_graph(en_dir, out_dir)

if __name__ == "__main__":
    main()
