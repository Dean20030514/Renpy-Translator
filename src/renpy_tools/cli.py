#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ren'Py 汉化工具集 - 命令行入口

提供统一的命令行接口，可以调用各种工具：
- extract: 从 .rpy 文件提取文本
- prefill: 使用字典预填充翻译
- split: 分割 JSONL 文件为批次
- translate: 使用 Ollama 翻译
- merge: 合并翻译结果
- validate: 验证翻译质量
- autofix: 自动修复常见问题
- patch: 将翻译回填到 .rpy 文件
- build: 构建中文版游戏包

用法:
    renpy-tools <command> [options]
    renpy-tools --help
    renpy-tools <command> --help
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


# 获取工具目录
TOOLS_DIR = Path(__file__).parent.parent.parent / "tools"


def get_available_tools() -> dict[str, Path]:
    """获取可用的工具列表"""
    tools = {}
    if TOOLS_DIR.exists():
        for tool_file in TOOLS_DIR.glob("*.py"):
            if tool_file.name.startswith("_"):
                continue
            if tool_file.name.startswith("test_"):
                continue
            name = tool_file.stem
            tools[name] = tool_file
    return tools


def run_tool(tool_path: Path, args: list[str]) -> int:
    """运行指定的工具"""
    cmd = [sys.executable, str(tool_path)] + args
    result = subprocess.run(cmd, check=False)
    return result.returncode


def main():
    """主入口函数"""
    tools = get_available_tools()
    tool_names = sorted(tools.keys())

    parser = argparse.ArgumentParser(
        prog="renpy-tools",
        description="Ren'Py 汉化工具集 - 命令行入口",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
可用命令:
  extract       从 .rpy 文件提取文本
  prefill       使用字典预填充翻译
  split         分割 JSONL 文件为批次
  translate     使用 Ollama 本地翻译
  translate_api 使用云端 API 翻译
  merge         合并翻译结果
  validate      验证翻译质量
  autofix       自动修复常见问题
  patch         将翻译回填到 .rpy 文件
  build         构建中文版游戏包
  pipeline      一键执行完整流程

示例:
  renpy-tools extract /path/to/game -o outputs/extract
  renpy-tools translate outputs/llm_batches -o outputs/llm_results --model qwen2.5:14b
  renpy-tools pipeline /path/to/game --model deepseek-r1-abliterated

所有可用工具: {', '.join(tool_names)}
        """
    )

    parser.add_argument(
        "command",
        nargs="?",
        help="要运行的命令（工具名称）"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="列出所有可用的工具"
    )
    parser.add_argument(
        "--version",
        action="version",
        version="renpy-tools 0.2.0"
    )

    # 解析第一个参数
    args, remaining = parser.parse_known_args()

    if args.list:
        print("可用工具:")
        for name in tool_names:
            print(f"  - {name}")
        return 0

    if not args.command:
        parser.print_help()
        return 0

    # 查找并运行工具
    command = args.command

    if command not in tools:
        # 尝试模糊匹配
        matches = [t for t in tool_names if command in t]
        if len(matches) == 1:
            command = matches[0]
        elif len(matches) > 1:
            print(f"错误: '{args.command}' 匹配多个工具: {', '.join(matches)}")
            return 1
        else:
            print(f"错误: 未知命令 '{args.command}'")
            print(f"可用命令: {', '.join(tool_names)}")
            return 1

    tool_path = tools[command]
    return run_tool(tool_path, remaining)


if __name__ == "__main__":
    sys.exit(main())
