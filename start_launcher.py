#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""中文交互启动器：避免 .bat 编码问题"""

from __future__ import annotations

import os
import shlex
import subprocess
import sys
from pathlib import Path


def ask(prompt: str, default: str = "") -> str:
    s = input(prompt).strip()
    s = _normalize_input(s)
    return s if s else default


def _normalize_input(s: str) -> str:
    """规范化用户输入：去首尾空白、常见中英文引号。"""
    if not s:
        return ""
    s = s.strip()
    # 去掉首尾常见引号（英文/中文）
    quote_chars = '"\'“”‘’'
    while len(s) >= 2 and s[0] in quote_chars and s[-1] in quote_chars:
        s = s[1:-1].strip()
    return s


def run(cmd: list[str]) -> int:
    print("\n============================================================")
    print("执行命令:")
    print(" ".join(shlex.quote(x) for x in cmd))
    print("============================================================\n")
    return subprocess.call(cmd, cwd=Path(__file__).parent)


def main() -> int:
    print("=" * 60)
    print("RenPy 汉化统一启动器")
    print("=" * 60)
    print("1. 主流程翻译（从头开始）")
    print("2. 主流程翻译（断点续跑）")
    print("3. 仅扫描与费用估算（Dry-run）")
    print("4. 一键流水线（试跑+闸门+全量+漏翻增量）")
    print("5. tl-mode 翻译（从头开始）")
    print("6. tl-mode 翻译（断点续跑）")
    print("7. Ren'Py 7→8 升级扫描（检测 Python 2 / 旧 API 问题）")

    mode = ask("\n输入模式 [1-7]（默认4）: ", "4")
    if mode == "7":
        scan_dir = ask("游戏 game 目录路径: ")
        if not scan_dir:
            print("[错误] 必须提供路径")
            return 1
        scan_dir = str(Path(scan_dir).expanduser())
        do_fix = ask("自动修复？[y/N]（默认 N）: ", "n").lower() == "y"
        cmd = [sys.executable, "renpy_upgrade_tool.py", scan_dir, "--backup"]
        if do_fix:
            cmd.append("--fix")
        return run(cmd)

    game_dir = ask("游戏根目录路径: ")
    if not game_dir:
        print("[错误] 必须提供游戏目录路径")
        return 1

    game_dir = str(Path(game_dir).expanduser())

    output_dir = ask("输出目录（默认 output）: ", "output")
    provider = ask("提供商 [xai/openai/deepseek/claude/gemini]（默认 xai）: ", "xai").lower()
    model = ask("模型（默认 grok-4-1-fast-reasoning）: ", "grok-4-1-fast-reasoning")

    py = sys.executable

    if mode == "3":
        cmd = [
            py, "main.py",
            "--game-dir", game_dir,
            "--provider", provider,
            "--model", model,
            "--dry-run",
        ]
        return run(cmd)

    api_key = ask("API 密钥: ")
    if not api_key:
        print("[错误] 非 dry-run 模式必须提供 API 密钥")
        return 1

    genre = ask("翻译风格 [adult/visual_novel/rpg/general]（默认 adult）: ", "adult")
    rpm = ask("RPM 每分钟请求数（默认 600）: ", "600")
    rps = ask("RPS 每秒请求数（默认 10）: ", "10")

    if mode in ("5", "6"):
        tl_lang = ask("tl 语言目录名（默认 chinese）: ", "chinese")
        workers = ask("并发线程数（默认 5）: ", "5")
        extra = ["--resume"] if mode == "6" else []
        cmd = [
            py, "-u", "main.py",
            "--game-dir", game_dir,
            "--output-dir", output_dir,
            "--provider", provider,
            "--api-key", api_key,
            "--model", model,
            "--genre", genre,
            "--rpm", rpm,
            "--rps", rps,
            "--workers", workers,
            "--tl-mode",
            "--tl-lang", tl_lang,
            *extra,
        ]
        return run(cmd)

    workers = ask("并发线程数（默认 3）: ", "3")

    if mode == "4":
        use_tl = ask("使用 tl-mode？[y/N]（默认 N，选 y 则跳过试跑/补翻，直接 tl 翻译）: ", "n").lower() == "y"
        cmd = [
            py, "one_click_pipeline.py",
            "--game-dir", game_dir,
            "--output-dir", output_dir,
            "--provider", provider,
            "--api-key", api_key,
            "--model", model,
            "--genre", genre,
            "--workers", workers,
            "--rpm", rpm,
            "--rps", rps,
            "--clean-output",
        ]
        if use_tl:
            tl_lang = ask("tl 语言目录名（默认 chinese）: ", "chinese")
            cmd += ["--tl-mode", "--tl-lang", tl_lang]
        else:
            pilot_count = ask("试跑文件数量（默认 20）: ", "20")
            gate_ratio = ask("闸门最大漏翻占比（默认 0.08）: ", "0.08")
            cmd += ["--pilot-count", pilot_count, "--gate-max-untranslated-ratio", gate_ratio]
        return run(cmd)

    extra = ["--resume"] if mode == "2" else []
    cmd = [
        py, "main.py",
        "--game-dir", game_dir,
        "--output-dir", output_dir,
        "--provider", provider,
        "--api-key", api_key,
        "--model", model,
        "--genre", genre,
        "--workers", workers,
        "--rpm", rpm,
        "--rps", rps,
        *extra,
    ]
    return run(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
