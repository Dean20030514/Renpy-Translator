#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""目标语言参数化配置：支持多语言翻译（中文/日语/韩语/繁体中文等）。

核心设计：
- LanguageConfig dataclass 封装语言相关的检测函数、阈值、标点映射
- 预置 zh/ja/ko/zh-tw 四种语言配置
- --target-lang zh 时行为与未引入此模块前完全一致（零变更保证）
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable


# ============================================================
# 文字检测函数
# ============================================================

def detect_chinese_ratio(text: str) -> float:
    """检测文本中的中文字符占比（CJK Unified Ideographs）。"""
    if not text:
        return 0.0
    chinese = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    return chinese / len(text)


def detect_japanese_ratio(text: str) -> float:
    """检测文本中的日文字符占比（平假名 + 片假名 + 汉字）。"""
    if not text:
        return 0.0
    ja_chars = sum(1 for c in text if (
        '\u3040' <= c <= '\u309f' or  # 平假名
        '\u30a0' <= c <= '\u30ff' or  # 片假名
        '\u4e00' <= c <= '\u9fff'     # 汉字
    ))
    return ja_chars / len(text)


def detect_korean_ratio(text: str) -> float:
    """检测文本中的韩文字符占比（谚文音节）。"""
    if not text:
        return 0.0
    ko_chars = sum(1 for c in text if '\uac00' <= c <= '\ud7a3')
    return ko_chars / len(text)


# ============================================================
# 语言配置数据结构
# ============================================================

@dataclass
class LanguageConfig:
    """目标语言配置。"""
    code: str                    # "zh", "ja", "ko", "zh-tw"
    name: str                    # "Simplified Chinese", "Japanese"
    native_name: str             # "简体中文", "日本語"

    # Validator 相关
    target_script_detector: Callable[[str], float]  # 目标文字占比检测函数
    min_target_ratio: float      # W442 阈值

    # Prompt 相关
    translation_instruction: str  # "翻译为简体中文" / "日本語に翻訳"
    style_notes: str             # 语言特有的风格指导

    # Glossary 相关
    glossary_field: str          # "zh" / "ja" / "ko"

    # 兼容读取字段别名
    field_aliases: list[str] = field(default_factory=list)


# ============================================================
# 预置语言配置
# ============================================================

LANGUAGE_CONFIGS: dict[str, LanguageConfig] = {
    "zh": LanguageConfig(
        code="zh",
        name="Simplified Chinese",
        native_name="简体中文",
        target_script_detector=detect_chinese_ratio,
        min_target_ratio=0.05,
        translation_instruction="翻译为简体中文",
        style_notes="使用现代白话文，自然口语化，避免生硬直译",
        glossary_field="zh",
        field_aliases=["zh", "chinese", "cn"],
    ),
    "zh-tw": LanguageConfig(
        code="zh-tw",
        name="Traditional Chinese",
        native_name="繁體中文",
        target_script_detector=detect_chinese_ratio,  # 复用简体检测
        min_target_ratio=0.05,
        translation_instruction="翻譯為繁體中文",
        style_notes="使用繁體中文書寫，符合台灣/港澳用語習慣",
        glossary_field="zh-tw",
        field_aliases=["zh-tw", "zh_tw", "traditional_chinese"],
    ),
    "ja": LanguageConfig(
        code="ja",
        name="Japanese",
        native_name="日本語",
        target_script_detector=detect_japanese_ratio,
        min_target_ratio=0.05,
        translation_instruction="日本語に翻訳してください",
        style_notes="自然な日本語で翻訳してください。敬語・タメ口は原文のトーンに合わせてください",
        glossary_field="ja",
        field_aliases=["ja", "japanese", "jp"],
    ),
    "ko": LanguageConfig(
        code="ko",
        name="Korean",
        native_name="한국어",
        target_script_detector=detect_korean_ratio,
        min_target_ratio=0.05,
        translation_instruction="한국어로 번역해 주세요",
        style_notes="자연스러운 한국어로 번역해 주세요. 존댓말/반말은 원문의 톤에 맞춰 주세요",
        glossary_field="ko",
        field_aliases=["ko", "korean", "kr"],
    ),
}


def get_language_config(code: str) -> LanguageConfig:
    """获取语言配置，不存在则回退到 zh。"""
    return LANGUAGE_CONFIGS.get(code, LANGUAGE_CONFIGS["zh"])


def resolve_translation_field(item: dict, lang_config: LanguageConfig) -> str | None:
    """从翻译结果 dict 中兼容读取译文字段。

    按优先级尝试：lang_config.field_aliases → 通用字段名（translation/target/trans）。
    """
    for alias in lang_config.field_aliases:
        if alias in item:
            return item[alias]
    for generic in ("translation", "target", "trans"):
        if generic in item:
            return item[generic]
    return None
