#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PyInstaller 打包脚本：将 GUI 入口打包为单个 .exe。

用法:
    python build.py

产出:
    dist/多引擎游戏汉化工具.exe

注意:
    - 需要先安装 PyInstaller: pip install pyinstaller
    - 打包后的 .exe 包含所有 Python 文件，用户无需安装 Python
    - resources/fonts/ 下的字体文件会一并打包
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent


def main() -> int:
    # 收集所有需要打包的 Python 模块（非测试、非工具）
    hidden_imports = [
        "api_client", "config", "direct_translator", "direct_translator_dryrun",
        "file_processor",
        "file_processor.splitter", "file_processor.patcher",
        "file_processor.checker", "file_processor.validator",
        "font_patch", "glossary", "lang_config", "main",
        "one_click_pipeline", "prompts", "retranslator", "review_generator",
        "renpy_upgrade_tool", "renpy_text_utils", "start_launcher",
        "screen_translator", "tl_parser", "tl_translator",
        "translation_db", "translation_utils",
        "pipeline", "pipeline.helpers", "pipeline.gate", "pipeline.stages",
        "engines", "engines.engine_base", "engines.engine_detector",
        "engines.generic_pipeline", "engines.renpy_engine",
        "engines.rpgmaker_engine", "engines.csv_engine",
    ]

    # 数据文件
    datas = []
    # 字体资源
    fonts_dir = PROJECT_ROOT / "resources" / "fonts"
    if fonts_dir.exists():
        datas.append((str(fonts_dir), "resources/fonts"))
    # 示例配置
    example_config = PROJECT_ROOT / "renpy_translate.example.json"
    if example_config.exists():
        datas.append((str(example_config), "."))
    # prompt presets
    presets_dir = PROJECT_ROOT / "prompt_presets"
    if presets_dir.exists():
        datas.append((str(presets_dir), "prompt_presets"))

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--name", "多引擎游戏汉化工具",
        "--icon", "NONE",
        "--noconfirm",
        "--clean",
    ]

    for imp in hidden_imports:
        cmd += ["--hidden-import", imp]
    for src, dst in datas:
        cmd += ["--add-data", f"{src};{dst}"]

    cmd.append(str(PROJECT_ROOT / "gui.py"))

    print("=" * 60)
    print("PyInstaller 打包")
    print("=" * 60)
    print(f"入口: gui.py")
    print(f"Hidden imports: {len(hidden_imports)}")
    print(f"Data files: {len(datas)}")
    print()

    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT))

    if result.returncode == 0:
        exe_path = PROJECT_ROOT / "dist" / "多引擎游戏汉化工具.exe"
        print()
        print("=" * 60)
        print(f"打包成功: {exe_path}")
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"文件大小: {size_mb:.1f} MB")
        print("=" * 60)
    else:
        print()
        print("[ERROR] 打包失败")

    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
