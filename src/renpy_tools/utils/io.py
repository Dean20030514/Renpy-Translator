from __future__ import annotations
import json
from pathlib import Path
from typing import Iterable, Dict, Any


def ensure_parent_dir(path: str | Path) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def read_text_file(path: str | Path, encoding: str = 'utf-8') -> str:
    """统一以 UTF-8 优先读取，失败时对常见编码（utf-8-sig/cp1252/latin1）回退。

    始终忽略错误以提高健壮性，但建议尽量保证源码为 UTF-8。"""
    p = Path(path)
    encs = [encoding, 'utf-8-sig', 'cp1252', 'latin1']
    for enc in encs:
        try:
            return p.read_text(encoding=enc, errors="ignore")
        except OSError:
            continue
    # 最后再尝试 utf-8 忽略错误
    return p.read_text(encoding='utf-8', errors='ignore')


def write_text_file(path: str | Path, text: str, encoding: str = 'utf-8') -> None:
    p = ensure_parent_dir(path)
    p.write_text(text, encoding=encoding)


def read_jsonl_lines(path: str | Path) -> list[Dict[str, Any]]:
    p = Path(path)
    out = []
    with p.open('r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            out.append(json.loads(line))
    return out


def write_jsonl_lines(path: str | Path, rows: Iterable[Dict[str, Any]]):
    p = ensure_parent_dir(path)
    with p.open('w', encoding='utf-8') as f:
        for obj in rows:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")
