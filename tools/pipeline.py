#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pipeline.py — 一键执行 Extract → Prefill → Split → Ollama 翻译 → Merge → Validate → Patch → Build

只需提供 Ren'Py 项目根目录（包含 game/）与 Ollama 模型名。

示例：
  python tools/pipeline.py e:/MyRenpyGame \
    --model deepseek-r1-abliterated --host http://127.0.0.1:11434
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


WS = Path.cwd()


def run_step(cmd: list[str]):
    print("\n==>", " ".join(cmd))
    subprocess.run(cmd, check=True)


def main():
    ap = argparse.ArgumentParser(description="One-click pipeline using local Ollama model")
    ap.add_argument("project_root", help="Ren'Py 项目根目录（包含 game/）")
    ap.add_argument("--model", default="deepseek-r1-abliterated", help="Ollama 模型名")
    ap.add_argument("--host", default="http://127.0.0.1:11434", help="Ollama HTTP 地址")
    ap.add_argument("--workers", type=int, default=2, help="翻译并发 worker（默认 2）")
    ap.add_argument("--max-tokens", type=int, default=2000, help="分包近似最大 tokens（默认 2000）")
    ap.add_argument("--lang", default="zh_CN", help="构建包语言（默认 zh_CN）")
    args = ap.parse_args()

    py = sys.executable
    prj = str(Path(args.project_root))

    # 目录与路径
    extract_dir = WS / "outputs" / "extract"
    prefilled_dir = WS / "outputs" / "prefilled"
    qa_dir = WS / "outputs" / "qa"
    llm_batches_dir = WS / "outputs" / "llm_batches"
    llm_results_dir = WS / "outputs" / "llm_results"
    out_patch_dir = WS / "outputs" / "out_patch"
    build_cn_dir = WS / "outputs" / "build_cn"
    dict_dir = WS / "data" / "dictionaries"

    extract_dir.mkdir(parents=True, exist_ok=True)
    prefilled_dir.mkdir(parents=True, exist_ok=True)
    qa_dir.mkdir(parents=True, exist_ok=True)
    llm_batches_dir.mkdir(parents=True, exist_ok=True)
    llm_results_dir.mkdir(parents=True, exist_ok=True)
    out_patch_dir.mkdir(parents=True, exist_ok=True)
    build_cn_dir.mkdir(parents=True, exist_ok=True)

    # 固定输入/输出路径
    src_jsonl = extract_dir / "project_en_for_grok.jsonl"
    prefilled_jsonl = prefilled_dir / "prefilled.jsonl"
    merged_jsonl = prefilled_dir / "prefilled_llm_merged.jsonl"
    conflict_tsv = qa_dir / "llm_conflicts.tsv"
    qa_json = qa_dir / "qa.json"
    qa_tsv = qa_dir / "qa.tsv"
    qa_html = qa_dir / "qa.html"

    # 1) Extract
    run_step([py, "tools/extract.py", prj,
              "--glob", "**/*.rpy",
              "--exclude-dirs", "tl,saves,cache",
              "--workers", "auto",
              "--chunk-size", "400",
              "-o", str(extract_dir)])

    # 2) Prefill
    run_step([py, "tools/prefill.py",
              str(src_jsonl), str(dict_dir),
              "-o", str(prefilled_jsonl),
              "--case-insensitive",
              "--dict-backend", "memory"])  # 内存后端默认即可

    # 3) Split for LLM
    run_step([py, "tools/split.py",
              str(prefilled_jsonl), str(llm_batches_dir),
              "--skip-has-zh",
              "--max-tokens", str(args.max_tokens)])

    # 4) Ollama Translate
    run_step([py, "tools/translate.py",
              str(llm_batches_dir),
              "-o", str(llm_results_dir),
              "--model", str(args.model),
              "--host", str(args.host),
              "--workers", str(args.workers)])

    # 5) Merge
    run_step([py, "tools/merge.py",
              str(prefilled_jsonl), str(llm_results_dir),
              "-o", str(merged_jsonl),
              "--conflict-tsv", str(conflict_tsv)])

    # 6) Validate
    run_step([py, "tools/validate.py",
              str(src_jsonl), str(merged_jsonl),
              "--qa-json", str(qa_json),
              "--qa-tsv", str(qa_tsv),
              "--qa-html", str(qa_html),
              "--ignore-ui-punct",
              "--require-ph-count-eq",
              "--require-newline-eq"])

    # 7) Patch
    run_step([py, "tools/patch.py",
              prj, str(merged_jsonl),
              "-o", str(out_patch_dir),
              "--advanced",
              "--workers", "auto",
              "--chunk-size", "400"])

    # 8) Build CN Package
    run_step([py, "tools/build.py",
              prj,
              "-o", str(build_cn_dir),
              "--mode", "auto",
              "--zh-mirror", str(out_patch_dir),
              "--lang", str(args.lang)])

    print("\nAll done. Artifacts:")
    print("- LLM batches:", llm_batches_dir)
    print("- LLM results:", llm_results_dir)
    print("- Merged JSONL:", merged_jsonl)
    print("- QA reports:", qa_dir)
    print("- Patched zh.rpy:", out_patch_dir)
    print("- Build CN package:", build_cn_dir)


if __name__ == "__main__":
    main()
