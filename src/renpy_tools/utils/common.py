#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用辅助函数 - 为 tools/ 脚本提供统一的工具函数
避免代码重复，提高维护性
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Optional

# ========================================
# 常量定义（统一来源）
# ========================================

# 译文字段名称（按优先级）
TRANS_KEYS = ("zh", "cn", "zh_cn", "translation", "text_zh", "target", "tgt", "zh_final")

# 英文原文字段名称（按优先级）
EN_KEYS = ("en", "text", "english", "source", "src", "original", "english_text")

# 常见的资源文件扩展名
ASSET_EXTS = (
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp",  # 图片
    ".mp3", ".ogg", ".wav", ".flac", ".m4a",  # 音频
    ".mp4", ".webm", ".avi", ".mkv",  # 视频
    ".ttf", ".otf", ".woff", ".woff2",  # 字体
    ".json", ".yaml", ".yml", ".xml",  # 数据
)

# 应跳过翻译的关键词
SKIP_KEYWORDS = frozenset({
    "true", "false", "none", "null",
    "yes", "no", "ok", "cancel",
})


# ========================================
# JSONL 读写函数
# ========================================

def load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    """加载 JSONL 文件，返回字典列表

    Args:
        path: 文件路径

    Returns:
        解析后的字典列表
    """
    lines = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    lines.append(json.loads(line))
                except (ValueError, json.JSONDecodeError):
                    continue
    return lines


def save_jsonl(path: str | Path, data: list[dict[str, Any]]) -> None:
    """保存字典列表为 JSONL 文件

    Args:
        path: 文件路径
        data: 要保存的数据
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


# ========================================
# 字段提取函数
# ========================================

def get_id(obj: dict) -> Optional[str]:
    """提取条目的唯一ID，支持多种格式

    支持的格式：
    - 直接 id 字段
    - id_hash 字段
    - file:line:idx 组合

    Args:
        obj: 数据对象

    Returns:
        ID 字符串，如果没有则返回 None
    """
    # 检查 id 字段（注意：0 或空字符串也是有效值需要特殊处理）
    if "id" in obj and obj["id"] is not None:
        id_val = obj["id"]
        # 如果是字符串，确保不是空的
        if isinstance(id_val, str):
            if id_val.strip():
                return id_val
        else:
            # 数字或其他类型，转换为字符串
            return str(id_val)

    # 检查 id_hash 字段
    if "id_hash" in obj and obj["id_hash"] is not None:
        hash_val = obj["id_hash"]
        if isinstance(hash_val, str):
            if hash_val.strip():
                return hash_val
        else:
            return str(hash_val)

    # 尝试从 file:line:idx 组合生成 ID
    if all(k in obj for k in ("file", "line", "idx")):
        file_val = obj["file"]
        line_val = obj["line"]
        idx_val = obj["idx"]
        # 验证各字段有效性
        if file_val is not None and line_val is not None and idx_val is not None:
            return f"{file_val}:{line_val}:{idx_val}"

    return None


def get_zh(obj: dict) -> tuple[Optional[str], Optional[str]]:
    """提取译文字段

    Args:
        obj: 数据对象

    Returns:
        (field_name, value) - 字段名和译文内容，如果没有则返回 (None, None)
    """
    for key in TRANS_KEYS:
        value = obj.get(key)
        if value is not None and str(value).strip() != "":
            return key, str(value)
    return None, None


def has_zh(obj: dict) -> bool:
    """检查对象是否包含非空译文

    Args:
        obj: 数据对象

    Returns:
        是否包含译文
    """
    _, value = get_zh(obj)
    return value is not None


def get_en(obj: dict) -> Optional[str]:
    """提取英文原文

    Args:
        obj: 数据对象

    Returns:
        英文原文，如果没有则返回 None
    """
    for key in EN_KEYS:
        value = obj.get(key)
        if value is not None:
            return str(value)
    return None


# ========================================
# 文本处理函数
# ========================================

_WHITESPACE_RE = re.compile(r"\s+")


def normalize_text(text: str) -> str:
    """标准化文本用于比较（去除多余空白）

    Args:
        text: 输入文本

    Returns:
        标准化后的文本
    """
    return _WHITESPACE_RE.sub(" ", text.strip())


def is_asset_path(text: str) -> bool:
    """检查文本是否为资源路径

    Args:
        text: 输入文本

    Returns:
        是否为资源路径
    """
    text_lower = text.lower().strip()
    # 检查扩展名
    for ext in ASSET_EXTS:
        if text_lower.endswith(ext):
            return True
    # 检查路径分隔符
    if "/" in text or "\\" in text:
        return True
    return False


def should_skip_translation(text: str) -> bool:
    """检查文本是否应跳过翻译

    Args:
        text: 输入文本

    Returns:
        是否应跳过
    """
    if not text or not text.strip():
        return True

    text_lower = text.lower().strip()

    # 跳过关键词
    if text_lower in SKIP_KEYWORDS:
        return True

    # 跳过资源路径
    if is_asset_path(text):
        return True

    return False
