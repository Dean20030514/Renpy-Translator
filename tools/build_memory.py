#!/usr/bin/env python3
"""
从已翻译 JSONL 和/或 tl 目录构建翻译记忆 (TM)。

用法:
    python tools/build_memory.py --jsonl translated.jsonl -o outputs/tm
    python tools/build_memory.py --tl-root game/tl/chinese -o outputs/tm
    python tools/build_memory.py --jsonl translated.jsonl --tl-root game/tl/chinese -o outputs/tm --min-len 5
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# 确保可以找到 src 目录
_project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_project_root / "src"))

from renpy_tools.utils.tm import TranslationMemory
from renpy_tools.utils.logger import get_logger

logger = get_logger(__name__)


def _load_tl_directory(tm: TranslationMemory, tl_root: Path) -> int:
    """从 Ren'Py tl 目录加载翻译对到 TM。"""
    count = 0
    for rpy_file in sorted(tl_root.rglob("*.rpy")):
        try:
            text = rpy_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        lines = text.splitlines()
        i = 0
        while i < len(lines) - 1:
            line = lines[i].strip()
            next_line = lines[i + 1].strip() if i + 1 < len(lines) else ""
            # Ren'Py tl 模式: old "english" → new "chinese"
            if line.startswith("old ") and next_line.startswith("new "):
                old_text = _extract_quoted(line[4:])
                new_text = _extract_quoted(next_line[4:])
                if old_text and new_text and old_text != new_text:
                    if tm.add(old_text, new_text):
                        count += 1
                i += 2
                continue
            i += 1
    return count


def _extract_quoted(s: str) -> str:
    """提取引号内的文本。"""
    s = s.strip()
    if len(s) >= 2:
        if (s[0] == '"' and s[-1] == '"') or (s[0] == "'" and s[-1] == "'"):
            return s[1:-1]
    return ""


def main() -> None:
    parser = argparse.ArgumentParser(
        description="从已翻译 JSONL 和/或 tl 目录构建翻译记忆 (TM)"
    )
    parser.add_argument(
        "--jsonl", nargs="*", default=[],
        help="已翻译的 JSONL 文件（可指定多个）",
    )
    parser.add_argument(
        "--tl-root", nargs="*", default=[],
        help="Ren'Py tl 翻译目录（可指定多个）",
    )
    parser.add_argument(
        "-o", "--output", required=True,
        help="TM 输出目录",
    )
    parser.add_argument(
        "--min-len", type=int, default=3,
        help="最小源文本长度（默认 3）",
    )
    args = parser.parse_args()

    if not args.jsonl and not args.tl_root:
        parser.error("至少指定 --jsonl 或 --tl-root 之一")

    tm = TranslationMemory(min_length=args.min_len)

    total = 0

    # 从 JSONL 加载
    for jsonl_path in args.jsonl:
        p = Path(jsonl_path)
        if p.is_dir():
            for f in sorted(p.rglob("*.jsonl")):
                loaded = tm.load_jsonl(f)
                total += loaded
        elif p.exists():
            loaded = tm.load_jsonl(p)
            total += loaded
        else:
            logger.warning(f"文件不存在: {p}")

    # 从 tl 目录加载
    for tl_path in args.tl_root:
        p = Path(tl_path)
        if p.is_dir():
            loaded = _load_tl_directory(tm, p)
            total += loaded
            logger.info(f"从 tl 目录加载 {loaded} 条: {p}")
        else:
            logger.warning(f"目录不存在: {p}")

    # 保存
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)
    tm_file = out_dir / "tm.jsonl"
    saved = tm.save_jsonl(tm_file)

    # 输出统计
    stats = tm.stats()
    stats_file = out_dir / "tm_stats.json"
    stats_file.write_text(
        json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    logger.info(f"TM 构建完成: {saved} 条保存到 {tm_file}")
    logger.info(f"统计: 唯一源文本 {stats['unique_sources']}, 总条目 {stats['total_entries']}")


if __name__ == "__main__":
    main()
