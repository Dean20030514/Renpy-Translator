#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
unrpa.py — RPA 存档解包工具

支持 RPA-2.0 和 RPA-3.0 格式，可提取 .rpa 存档中的所有文件。
借鉴 RenpyTranslator 的多线程解包设计。

用法示例：
  # 解包单个 rpa 文件
  python tools/unrpa.py game/archive.rpa -o extracted/

  # 解包目录下所有 rpa
  python tools/unrpa.py "E:\\MyGame\\game" -o extracted/

  # 仅提取脚本文件
  python tools/unrpa.py game/scripts.rpa -o extracted/ --scripts-only
"""

from __future__ import annotations

import argparse
import os
import struct
import sys
import threading
from pathlib import Path
from typing import BinaryIO

# 添加 src 到路径
_project_root = Path(__file__).parent.parent
if str(_project_root / "src") not in sys.path:
    sys.path.insert(0, str(_project_root / "src"))

try:
    from rich.console import Console
    _console = Console()
except ImportError:
    _console = None

MAX_THREADS = 12
_write_semaphore = threading.Semaphore(MAX_THREADS)

# 脚本文件扩展名
SCRIPT_EXTS = {".rpy", ".rpyc", ".rpym", ".rpymc"}


def _log(msg: str, level: str = "info") -> None:
    if _console:
        style = {"info": "dim", "warning": "yellow", "error": "red"}.get(level, "")
        _console.print(f"[{style}]{msg}[/]")
    else:
        print(msg)


def _read_index_rpa3(f: BinaryIO, offset: int, key: int) -> dict[str, list[tuple[int, int, bytes]]]:
    """解析 RPA-3.0 索引"""
    import pickle
    f.seek(offset)
    raw = f.read()

    try:
        import zlib
        raw = zlib.decompress(raw)
    except Exception:
        pass

    index: dict = pickle.loads(raw)
    result: dict[str, list[tuple[int, int, bytes]]] = {}

    for name, entries in index.items():
        result[name] = []
        for entry in entries:
            if len(entry) == 2:
                entry_offset, entry_len = entry
                prefix = b""
            else:
                entry_offset, entry_len, prefix = entry[0], entry[1], entry[2]
            entry_offset ^= key
            entry_len ^= key
            result[name].append((entry_offset, entry_len, prefix))

    return result


def _read_index_rpa2(f: BinaryIO, offset: int) -> dict[str, list[tuple[int, int, bytes]]]:
    """解析 RPA-2.0 索引"""
    import pickle
    f.seek(offset)
    raw = f.read()

    try:
        import zlib
        raw = zlib.decompress(raw)
    except Exception:
        pass

    index: dict = pickle.loads(raw)
    result: dict[str, list[tuple[int, int, bytes]]] = {}

    for name, entries in index.items():
        result[name] = []
        for entry in entries:
            if len(entry) == 2:
                result[name].append((entry[0], entry[1], b""))
            else:
                result[name].append((entry[0], entry[1], entry[2]))

    return result


def extract_rpa(rpa_path: Path, out_dir: Path, scripts_only: bool = False) -> int:
    """解包单个 RPA 文件

    Args:
        rpa_path: .rpa 文件路径
        out_dir: 输出目录
        scripts_only: 仅提取脚本文件 (.rpy/.rpyc)

    Returns:
        提取的文件数
    """
    with open(rpa_path, "rb") as f:
        header = f.readline().decode("latin-1").strip()

        if header.startswith("RPA-3.0"):
            parts = header.split()
            offset = int(parts[1], 16)
            key = int(parts[2], 16)
            index = _read_index_rpa3(f, offset, key)
        elif header.startswith("RPA-2.0"):
            parts = header.split()
            offset = int(parts[1], 16)
            index = _read_index_rpa2(f, offset)
        else:
            _log(f"不支持的 RPA 格式: {header}", "error")
            return 0

        threads: list[threading.Thread] = []
        count = 0

        for name, entries in index.items():
            if scripts_only:
                ext = os.path.splitext(name)[1].lower()
                if ext not in SCRIPT_EXTS:
                    continue

            # 读取文件数据
            data_parts = []
            for entry_offset, entry_len, prefix in entries:
                f.seek(entry_offset)
                data = prefix + f.read(entry_len - len(prefix))
                data_parts.append(data)
            file_data = b"".join(data_parts)

            out_path = out_dir / name
            t = threading.Thread(
                target=_write_file_threaded,
                args=(_write_semaphore, name, out_path, file_data)
            )
            threads.append(t)
            t.start()
            count += 1

        for t in threads:
            t.join()

    return count


def _write_file_threaded(semaphore: threading.Semaphore, name: str, path: Path, data: bytes) -> None:
    """多线程文件写入"""
    with semaphore:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            f.write(data)


def main():
    parser = argparse.ArgumentParser(
        description="RPA 存档解包工具（支持 RPA-2.0/3.0）"
    )
    parser.add_argument(
        "input",
        help=".rpa 文件或包含 .rpa 的目录"
    )
    parser.add_argument(
        "-o", "--output",
        required=True,
        help="输出目录"
    )
    parser.add_argument(
        "--scripts-only",
        action="store_true",
        help="仅提取脚本文件 (.rpy/.rpyc)"
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    rpa_files: list[Path] = []
    if input_path.is_file() and input_path.suffix.lower() == ".rpa":
        rpa_files = [input_path]
    elif input_path.is_dir():
        rpa_files = sorted(input_path.rglob("*.rpa"))
    else:
        print(f"未找到 .rpa 文件: {input_path}")
        sys.exit(1)

    if not rpa_files:
        print("未找到 .rpa 文件")
        sys.exit(1)

    total = 0
    for rpa in rpa_files:
        _log(f"解包: {rpa.name}")
        n = extract_rpa(rpa, out_dir, scripts_only=args.scripts_only)
        _log(f"  提取 {n} 个文件")
        total += n

    if _console:
        _console.print(f"\n[bold green]完成[/]：共提取 {total} 个文件到 {out_dir}")
    else:
        print(f"\n完成：共提取 {total} 个文件到 {out_dir}")


if __name__ == "__main__":
    main()
