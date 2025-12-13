"""
文件 I/O 工具函数

提供安全的文件读写功能：
- 多编码回退读取
- 原子写入（防止数据损坏）
- JSONL 读写支持
"""

from __future__ import annotations

import json
import os
import tempfile
import logging
from pathlib import Path
from typing import Iterable, Dict, Any, Optional

# 获取模块级 logger
logger = logging.getLogger(__name__)


def ensure_parent_dir(path: str | Path) -> Path:
    """确保父目录存在"""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def read_text_file(path: str | Path, encoding: str = 'utf-8') -> str:
    """统一以 UTF-8 优先读取，失败时对常见编码回退。

    尝试顺序：指定编码 -> utf-8-sig -> cp1252 -> latin1

    Args:
        path: 文件路径
        encoding: 首选编码

    Returns:
        文件内容
    """
    p = Path(path)
    encs = [encoding, 'utf-8-sig', 'cp1252', 'latin1']
    for enc in encs:
        try:
            return p.read_text(encoding=enc, errors="replace")
        except (OSError, UnicodeDecodeError):
            continue
    # 最后再尝试 utf-8 替换错误字符
    return p.read_text(encoding='utf-8', errors='replace')


def write_text_file(
    path: str | Path,
    text: str,
    encoding: str = 'utf-8',
    atomic: bool = True
) -> None:
    """写入文本文件

    Args:
        path: 文件路径
        text: 文件内容
        encoding: 编码
        atomic: 是否使用原子写入（先写临时文件再重命名）
    """
    p = ensure_parent_dir(path)

    if atomic:
        # 原子写入：先写入临时文件，再重命名
        fd, tmp_path = tempfile.mkstemp(
            dir=p.parent,
            prefix=f".{p.name}.",
            suffix=".tmp"
        )
        try:
            with os.fdopen(fd, 'w', encoding=encoding) as f:
                f.write(text)
            # 原子重命名
            os.replace(tmp_path, p)
        except Exception:
            # 清理临时文件
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise
    else:
        p.write_text(text, encoding=encoding)


def read_jsonl_lines(
    path: str | Path,
    skip_invalid: bool = True,
    log_errors: bool = True
) -> list[Dict[str, Any]]:
    """读取 JSONL 文件

    Args:
        path: 文件路径
        skip_invalid: 是否跳过无效行
        log_errors: 是否记录解析错误

    Returns:
        解析后的对象列表
    """
    p = Path(path)
    out: list[Dict[str, Any]] = []
    error_count = 0

    with p.open('r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                out.append(json.loads(line))
            except (ValueError, json.JSONDecodeError) as e:
                error_count += 1
                if log_errors:
                    logger.warning(
                        f"JSONL parse error at {p.name}:{line_num}: {e}"
                    )
                if not skip_invalid:
                    raise

    if error_count > 0 and log_errors:
        logger.warning(
            f"Skipped {error_count} invalid lines in {p.name}"
        )

    return out


def write_jsonl_lines(
    path: str | Path,
    rows: Iterable[Dict[str, Any]],
    atomic: bool = True
) -> int:
    """写入 JSONL 文件

    Args:
        path: 文件路径
        rows: 要写入的对象
        atomic: 是否使用原子写入

    Returns:
        写入的行数
    """
    p = ensure_parent_dir(path)
    count = 0

    if atomic:
        # 原子写入
        fd, tmp_path = tempfile.mkstemp(
            dir=p.parent,
            prefix=f".{p.name}.",
            suffix=".tmp"
        )
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                for obj in rows:
                    f.write(json.dumps(obj, ensure_ascii=False) + "\n")
                    count += 1
            os.replace(tmp_path, p)
        except Exception:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise
    else:
        with p.open('w', encoding='utf-8') as f:
            for obj in rows:
                f.write(json.dumps(obj, ensure_ascii=False) + "\n")
                count += 1

    return count


def append_jsonl_line(path: str | Path, obj: Dict[str, Any]) -> bool:
    """追加单行到 JSONL 文件

    Args:
        path: 文件路径
        obj: 要追加的对象

    Returns:
        是否成功写入
    """
    try:
        p = ensure_parent_dir(path)
        with p.open('a', encoding='utf-8') as f:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")
        return True
    except (OSError, IOError) as e:
        logger.error(f"Failed to append to JSONL file {path}: {e}")
        return False
    except (TypeError, ValueError) as e:
        logger.error(f"Failed to serialize object to JSON: {e}")
        return False
