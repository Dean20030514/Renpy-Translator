#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pipeline.py — 一键执行 Extract → Prefill → Split → Ollama 翻译 → Merge → Validate → Patch → Build

只需提供 Ren'Py 项目根目录（包含 game/）与 Ollama 模型名。
支持 --resume 从上次失败的步骤继续执行。

示例：
  python tools/pipeline.py e:/MyRenpyGame \\
    --model deepseek-r1-abliterated --host http://127.0.0.1:11434

  # 从中断处继续
  python tools/pipeline.py e:/MyRenpyGame --resume
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


STEP_NAMES = [
    "unrpa", "extract", "prefill", "split", "translate",
    "merge", "validate", "patch", "build",
]


def _checkpoint_path(output_base: Path) -> Path:
    return output_base / ".pipeline_checkpoint.json"


def _load_checkpoint(output_base: Path) -> dict:
    cp = _checkpoint_path(output_base)
    if cp.exists():
        return json.loads(cp.read_text(encoding="utf-8"))
    return {"completed": []}


def _save_checkpoint(output_base: Path, data: dict):
    cp = _checkpoint_path(output_base)
    cp.parent.mkdir(parents=True, exist_ok=True)
    cp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def run_step(name: str, cmd: list[str]) -> bool:
    """运行单步命令，返回 True 成功 / False 失败。"""
    print(f"\n==> [{name}]", " ".join(cmd))
    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as exc:
        print(f"\n*** 步骤 [{name}] 失败 (exit {exc.returncode}) ***")
        return False


def main():
    ap = argparse.ArgumentParser(description="One-click pipeline using local Ollama model")
    ap.add_argument("project_root", help="Ren'Py 项目根目录（包含 game/）")
    ap.add_argument("--model", default="deepseek-r1-abliterated", help="Ollama 模型名")
    ap.add_argument("--host", default="http://127.0.0.1:11434", help="Ollama HTTP 地址")
    ap.add_argument("--workers", type=int, default=2, help="翻译并发 worker（默认 2）")
    ap.add_argument("--max-tokens", type=int, default=2000, help="分包近似最大 tokens（默认 2000）")
    ap.add_argument("--lang", default="zh_CN", help="构建包语言（默认 zh_CN）")
    ap.add_argument("--output-base", default=None, help="输出根目录（默认 <cwd>/outputs）")
    ap.add_argument("--resume", action="store_true", help="从上次失败的步骤继续")
    ap.add_argument("--unrpa", action="store_true", help="先解包 RPA 存档再提取")
    ap.add_argument("--gen-hooks", action="store_true", help="构建时生成运行时 Hook 脚本")
    ap.add_argument("--font", default="SourceHanSansCN-Regular.otf", help="Hook 字体文件路径")
    args = ap.parse_args()

    py = sys.executable
    prj = str(Path(args.project_root))
    ws = Path.cwd()

    # 输出根目录
    output_base = Path(args.output_base) if args.output_base else ws / "outputs"

    # 目录与路径
    extract_dir = output_base / "extract"
    prefilled_dir = output_base / "prefilled"
    qa_dir = output_base / "qa"
    llm_batches_dir = output_base / "llm_batches"
    llm_results_dir = output_base / "llm_results"
    out_patch_dir = output_base / "out_patch"
    build_cn_dir = output_base / "build_cn"
    dict_dir = ws / "data" / "dictionaries"

    for d in (extract_dir, prefilled_dir, qa_dir,
              llm_batches_dir, llm_results_dir, out_patch_dir, build_cn_dir):
        d.mkdir(parents=True, exist_ok=True)

    # 固定输入/输出路径
    src_jsonl = extract_dir / "project_en_for_grok.jsonl"
    prefilled_jsonl = prefilled_dir / "prefilled.jsonl"
    merged_jsonl = prefilled_dir / "prefilled_llm_merged.jsonl"
    conflict_tsv = qa_dir / "llm_conflicts.tsv"
    qa_json = qa_dir / "qa.json"
    qa_tsv = qa_dir / "qa.tsv"
    qa_html = qa_dir / "qa.html"

    # Checkpoint / resume
    checkpoint = _load_checkpoint(output_base)
    completed = set(checkpoint.get("completed", []))

    # 定义所有步骤
    steps: list[tuple[str, list[str]]] = []

    # 可选步骤: 解包 RPA
    if args.unrpa:
        unrpa_dir = output_base / "unrpa"
        unrpa_dir.mkdir(parents=True, exist_ok=True)
        steps.append(
            ("unrpa", [py, "tools/unrpa.py", prj,
                       "-o", str(unrpa_dir), "--scripts-only"]),
        )

    steps += [
        ("extract", [py, "tools/extract.py", prj,
                     "--glob", "**/*.rpy",
                     "--exclude-dirs", "tl,saves,cache",
                     "--workers", "auto",
                     "--chunk-size", "400",
                     "-o", str(extract_dir)]),

        ("prefill", [py, "tools/prefill.py",
                     str(src_jsonl), str(dict_dir),
                     "-o", str(prefilled_jsonl),
                     "--case-insensitive",
                     "--dict-backend", "memory"]),

        ("split", [py, "tools/split.py",
                   str(prefilled_jsonl), str(llm_batches_dir),
                   "--skip-has-zh",
                   "--max-tokens", str(args.max_tokens)]),

        ("translate", [py, "tools/translate.py",
                       str(llm_batches_dir),
                       "-o", str(llm_results_dir),
                       "--model", str(args.model),
                       "--host", str(args.host),
                       "--workers", str(args.workers)]),

        ("merge", [py, "tools/merge.py",
                   str(prefilled_jsonl), str(llm_results_dir),
                   "-o", str(merged_jsonl),
                   "--conflict-tsv", str(conflict_tsv)]),

        ("validate", [py, "tools/validate.py",
                      str(src_jsonl), str(merged_jsonl),
                      "--qa-json", str(qa_json),
                      "--qa-tsv", str(qa_tsv),
                      "--qa-html", str(qa_html),
                      "--ignore-ui-punct",
                      "--require-ph-count-eq",
                      "--require-newline-eq"]),

        ("patch", [py, "tools/patch.py",
                   prj, str(merged_jsonl),
                   "-o", str(out_patch_dir),
                   "--advanced",
                   "--workers", "auto",
                   "--chunk-size", "400"]),

        ("build", [py, "tools/build.py",
                   prj,
                   "-o", str(build_cn_dir),
                   "--mode", "auto",
                   "--zh-mirror", str(out_patch_dir),
                   "--lang", str(args.lang)]
                  + (["--gen-hooks", "--font", args.font] if args.gen_hooks else [])),
    ]

    failed_step = None
    for name, cmd in steps:
        if args.resume and name in completed:
            print(f"\n--- [{name}] 已完成，跳过 ---")
            continue

        ok = run_step(name, cmd)
        if ok:
            completed.add(name)
            checkpoint["completed"] = sorted(completed)
            _save_checkpoint(output_base, checkpoint)
        else:
            failed_step = name
            print(f"\n流水线在 [{name}] 步骤中断。修复问题后使用 --resume 继续。")
            break

    if failed_step:
        sys.exit(1)

    # 全部成功，清理 checkpoint
    cp = _checkpoint_path(output_base)
    if cp.exists():
        cp.unlink()

    print("\n✓ 全部完成。产出文件：")
    print(f"  LLM batches:    {llm_batches_dir}")
    print(f"  LLM results:    {llm_results_dir}")
    print(f"  Merged JSONL:   {merged_jsonl}")
    print(f"  QA reports:     {qa_dir}")
    print(f"  Patched zh.rpy: {out_patch_dir}")
    print(f"  Build CN:       {build_cn_dir}")


if __name__ == "__main__":
    main()
