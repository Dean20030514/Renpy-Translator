#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用辅助函数 - 为 tools/ 脚本提供统一的工具函数
避免代码重复，提高维护性
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Optional

# 译文字段名称（按优先级）
TRANS_KEYS = ("zh", "cn", "zh_cn", "translation", "text_zh", "target", "tgt")


def load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    """加载 JSONL 文件，返回字典列表"""
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
    """保存字典列表为 JSONL 文件"""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


def get_id(obj: dict) -> Optional[str]:
    """提取条目的唯一ID，支持多种格式"""
    if obj.get("id"):
        return obj["id"]
    if obj.get("id_hash"):
        return obj["id_hash"]
    if all(k in obj for k in ("file", "line", "idx")):
        return f"{obj['file']}:{obj['line']}:{obj['idx']}"
    return None


def get_zh(obj: dict) -> tuple[Optional[str], Optional[str]]:
    """
    提取译文字段
    
    Returns:
        (field_name, value) - 字段名和译文内容，如果没有则返回 (None, None)
    """
    for key in TRANS_KEYS:
        value = obj.get(key)
        if value is not None and str(value).strip() != "":
            return key, str(value)
    return None, None


def has_zh(obj: dict) -> bool:
    """检查对象是否包含非空译文"""
    _, value = get_zh(obj)
    return value is not None


def get_en(obj: dict) -> Optional[str]:
    """提取英文原文"""
    en = obj.get("en") or obj.get("text") or obj.get("english") or obj.get("source")
    return str(en) if en is not None else None


def normalize_text(text: str) -> str:
    """标准化文本用于比较（去除多余空白）"""
    import re
    return re.sub(r"\s+", " ", text.strip())
