#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用辅助函数 - 为 tools/ 脚本提供统一的工具函数
避免代码重复，提高维护性

本模块是所有常量、辅助函数的唯一来源（Single Source of Truth）
其他模块应从此处导入，避免重复定义
"""
from __future__ import annotations

import json
import logging
import os
import re
import time
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional, Callable, TypeVar, Generic

# 获取模块级 logger
logger = logging.getLogger(__name__)

# ========================================
# 常量定义（统一来源 - Single Source of Truth）
# ========================================

# 译文字段名称（按优先级）
TRANS_KEYS = ("zh", "cn", "zh_cn", "translation", "text_zh", "target", "tgt", "zh_final")

# 英文原文字段名称（按优先级）
EN_KEYS = ("en", "text", "english", "source", "src", "original", "english_text")

# 占位符正则表达式（统一定义，避免各模块重复）
# 1) 方括号变量: [name]
# 2) 百分号格式: %s / %d / %02d / %(name)s / %.2f / %e %g %x %o ...
# 3) 花括号格式: {0} / {0:.2f} / {name!r:>8}
PH_RE = re.compile(
    r"\[[A-Za-z_][A-Za-z0-9_]*\]"                              # [name]
    r"|%(?:\([^)]+\))?[+#0\- ]?\d*(?:\.\d+)?[sdifeEfgGxXo]"    # %s, %02d, %(name)s
    r"|\{\d+(?:![rsa])?(?::[^{}]+)?\}"                          # {0}, {0:.2f}
    r"|\{[A-Za-z_][A-Za-z0-9_]*(?:![rsa])?(?::[^{}]+)?\}"       # {name}
)

# Ren'Py 文本标签
RENPY_SINGLE_TAGS = frozenset({"w", "nw", "p", "fast", "k"})
RENPY_PAIRED_TAGS = frozenset({"i", "b", "u", "color", "a", "size", "font", "alpha"})

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


# ========================================
# 占位符处理函数（从 placeholder.py 统一导出）
# ========================================

def _is_escaped_brace(s: str, start: int, end: int) -> bool:
    """是否位于 {{...}} 的转义环境中"""
    left = (start - 1 >= 0 and s[start - 1] == '{')
    right = (end < len(s) and s[end] == '}')
    return left or right


def _iter_placeholders(s: str):
    """迭代提取所有占位符"""
    if not s:
        return
    for m in PH_RE.finditer(s):
        a, b = m.span()
        if _is_escaped_brace(s, a, b):
            continue
        yield m.group(0)


def ph_set(s: str) -> set[str]:
    """提取文本中的唯一占位符集合

    Args:
        s: 输入文本

    Returns:
        占位符集合
    """
    return set(_iter_placeholders(s or ""))


def ph_multiset(s: str) -> dict[str, int]:
    """统计文本中占位符的出现次数

    Args:
        s: 输入文本

    Returns:
        占位符 -> 出现次数的字典

    Example:
        >>> ph_multiset("Hello [name], score: {0}, {0}")
        {'[name]': 1, '{0}': 2}
    """
    cnt: dict[str, int] = {}
    for ph in _iter_placeholders(s or ""):
        cnt[ph] = cnt.get(ph, 0) + 1
    return cnt


def strip_renpy_tags(s: str) -> str:
    """去除 Ren'Py 文本标签，保留文本与占位符

    Args:
        s: 输入文本

    Returns:
        去除标签后的文本
    """
    if not s:
        return ""
    tag_open_re = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)(?:=[^}]*)?\}")
    tag_close_re = re.compile(r"\{/([A-Za-z_][A-Za-z0-9_]*)\}")
    
    out = []
    i = 0
    n = len(s)
    while i < n:
        ch = s[i]
        if ch == '{':
            if i + 1 < n and s[i + 1] == '{':
                out.append('{')
                i += 2
                continue
            m1 = tag_open_re.match(s, i)
            if m1:
                name = m1.group(1)
                if name in RENPY_SINGLE_TAGS or name in RENPY_PAIRED_TAGS:
                    i = m1.end()
                    continue
            m2 = tag_close_re.match(s, i)
            if m2:
                name = m2.group(1)
                if name in RENPY_PAIRED_TAGS:
                    i = m2.end()
                    continue
        out.append(ch)
        i += 1
    return ''.join(out)


# ========================================
# 速率限制器
# ========================================

class AdaptiveRateLimiter:
    """自适应速率限制器 - 根据 API 响应自动调整请求频率
    
    当遇到 429 错误时自动降低请求频率，成功时缓慢恢复
    """
    
    def __init__(
        self,
        initial_rps: float = 10.0,
        min_rps: float = 1.0,
        max_rps: float = 50.0,
        decrease_factor: float = 0.7,
        increase_factor: float = 1.05
    ):
        """初始化速率限制器
        
        Args:
            initial_rps: 初始每秒请求数
            min_rps: 最小每秒请求数
            max_rps: 最大每秒请求数
            decrease_factor: 遇到限制时的降低因子
            increase_factor: 成功时的增长因子
        """
        self.rps = initial_rps
        self.min_rps = min_rps
        self.max_rps = max_rps
        self.decrease_factor = decrease_factor
        self.increase_factor = increase_factor
        self._last_request_time = 0.0
        self._lock = threading.Lock()
        self._total_requests = 0
        self._rate_limited_count = 0
    
    def acquire(self) -> None:
        """获取请求许可，必要时等待"""
        with self._lock:
            now = time.time()
            interval = 1.0 / self.rps
            wait_time = self._last_request_time + interval - now
            if wait_time > 0:
                time.sleep(wait_time)
            self._last_request_time = time.time()
            self._total_requests += 1
    
    def on_rate_limit(self) -> None:
        """当遇到速率限制时调用"""
        with self._lock:
            self.rps = max(self.min_rps, self.rps * self.decrease_factor)
            self._rate_limited_count += 1
            logger.warning(f"Rate limited, reducing RPS to {self.rps:.2f}")
    
    def on_success(self) -> None:
        """请求成功时调用"""
        with self._lock:
            self.rps = min(self.max_rps, self.rps * self.increase_factor)
    
    @property
    def stats(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            "current_rps": self.rps,
            "total_requests": self._total_requests,
            "rate_limited_count": self._rate_limited_count,
        }


# ========================================
# 翻译质量评分
# ========================================

@dataclass
class QualityScore:
    """翻译质量评分结果"""
    score: float  # 0-100
    issues: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_good(self) -> bool:
        """分数是否达到合格标准（>=70）"""
        return self.score >= 70
    
    @property
    def is_excellent(self) -> bool:
        """分数是否达到优秀标准（>=90）"""
        return self.score >= 90


def calculate_quality_score(
    source: str,
    target: str,
    check_english: bool = True
) -> QualityScore:
    """计算翻译质量分数
    
    Args:
        source: 原文
        target: 译文
        check_english: 是否检查英文残留
    
    Returns:
        QualityScore 对象
    """
    score = 100.0
    issues = []
    details = {}
    
    # 空翻译检查
    if not target or not target.strip():
        return QualityScore(score=0, issues=["empty_translation"], details={"fatal": True})
    
    # 1. 占位符检查 (-30)
    src_ph = ph_multiset(source)
    tgt_ph = ph_multiset(target)
    if src_ph != tgt_ph:
        missing = {k: v for k, v in src_ph.items() if src_ph.get(k, 0) > tgt_ph.get(k, 0)}
        extra = {k: v for k, v in tgt_ph.items() if tgt_ph.get(k, 0) > src_ph.get(k, 0)}
        issues.append("placeholder_mismatch")
        details["placeholder"] = {"missing": missing, "extra": extra}
        score -= 30
    
    # 2. 换行符检查 (-20)
    src_newlines = source.count('\n')
    tgt_newlines = target.count('\n')
    if src_newlines != tgt_newlines:
        issues.append("newline_mismatch")
        details["newlines"] = {"source": src_newlines, "target": tgt_newlines}
        score -= 20
    
    # 3. 长度比例检查 (-15)
    src_len = len(source.strip())
    tgt_len = len(target.strip())
    if src_len > 0:
        ratio = tgt_len / src_len
        if ratio < 0.3:
            issues.append("too_short")
            details["length_ratio"] = ratio
            score -= 15
        elif ratio > 3.0:
            issues.append("too_long")
            details["length_ratio"] = ratio
            score -= 10
    
    # 4. 英文残留检查 (-25)
    if check_english:
        # 检查是否包含常见英文单词（排除占位符内的内容）
        text_for_check = target
        for ph in tgt_ph.keys():
            text_for_check = text_for_check.replace(ph, " ")
        
        english_words = re.findall(r'\b[a-zA-Z]{3,}\b', text_for_check)
        # 排除常见缩写和特殊词
        allowed_words = {"ok", "OK", "app", "APP", "PC", "CPU", "GPU", "UI", "API"}
        leaked_words = [w for w in english_words if w not in allowed_words and w.upper() not in allowed_words]
        
        if leaked_words:
            issues.append("english_leakage")
            details["leaked_words"] = leaked_words[:10]  # 只记录前10个
            score -= min(25, len(leaked_words) * 5)  # 每个英文单词扣5分，最多25分
    
    # 5. 重复标点检查 (-5)
    if re.search(r'[。！？]{2,}|\.{4,}|!{2,}|\?{2,}', target):
        issues.append("duplicate_punctuation")
        score -= 5
    
    return QualityScore(
        score=max(0, score),
        issues=issues,
        details=details
    )


# ========================================
# 配置管理
# ========================================

@dataclass
class TranslationConfig:
    """翻译配置"""
    # 翻译服务配置
    provider: str = "ollama"
    model: str = "qwen2.5:14b"
    host: str = "http://127.0.0.1:11434"
    api_key: str = ""
    
    # 性能配置
    workers: int = 4
    timeout: float = 120.0
    max_retries: int = 3
    
    # 翻译参数
    temperature: float = 0.2
    quality_threshold: float = 0.7
    
    # 缓存配置
    enable_cache: bool = True
    cache_db_path: str = ""
    
    # 增量翻译
    incremental: bool = True
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TranslationConfig":
        """从字典创建配置"""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
    
    @classmethod
    def from_yaml(cls, path: str | Path) -> "TranslationConfig":
        """从 YAML 文件加载配置"""
        try:
            import yaml
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            # 支持嵌套结构
            flat_data = {}
            for section in ["translation", "performance", "cache"]:
                if section in data and isinstance(data[section], dict):
                    flat_data.update(data[section])
            flat_data.update({k: v for k, v in data.items() if not isinstance(v, dict)})
            return cls.from_dict(flat_data)
        except ImportError:
            logger.warning("PyYAML not installed, cannot load YAML config")
            return cls()
        except Exception as e:
            logger.warning(f"Failed to load config from {path}: {e}")
            return cls()
    
    @classmethod
    def from_env(cls) -> "TranslationConfig":
        """从环境变量加载配置"""
        return cls(
            provider=os.environ.get("RENPY_TRANSLATE_PROVIDER", "ollama"),
            model=os.environ.get("RENPY_TRANSLATE_MODEL", "qwen2.5:14b"),
            host=os.environ.get("RENPY_OLLAMA_HOST", "http://127.0.0.1:11434"),
            api_key=os.environ.get("RENPY_API_KEY", ""),
            workers=int(os.environ.get("RENPY_WORKERS", "4")),
            timeout=float(os.environ.get("RENPY_TIMEOUT", "120")),
            temperature=float(os.environ.get("RENPY_TEMPERATURE", "0.2")),
            enable_cache=os.environ.get("RENPY_CACHE", "1").lower() in ("1", "true", "yes"),
        )
    
    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "translation": {
                "provider": self.provider,
                "model": self.model,
                "host": self.host,
                "temperature": self.temperature,
                "quality_threshold": self.quality_threshold,
            },
            "performance": {
                "workers": self.workers,
                "timeout": self.timeout,
                "max_retries": self.max_retries,
            },
            "cache": {
                "enable_cache": self.enable_cache,
                "cache_db_path": self.cache_db_path,
                "incremental": self.incremental,
            },
        }


# ========================================
# 翻译缓存
# ========================================

class TranslationCache:
    """翻译缓存 - 支持增量翻译
    
    使用内存缓存 + 可选的持久化存储
    """
    
    def __init__(self, cache_file: Optional[str | Path] = None):
        """初始化缓存
        
        Args:
            cache_file: 可选的缓存文件路径（JSONL格式）
        """
        self._cache: dict[str, dict[str, Any]] = {}
        self._cache_file = Path(cache_file) if cache_file else None
        self._dirty = False
        self._lock = threading.Lock()
        
        if self._cache_file and self._cache_file.exists():
            self._load_from_file()
    
    def _load_from_file(self) -> None:
        """从文件加载缓存"""
        try:
            with self._cache_file.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        obj = json.loads(line)
                        key = self._make_key(obj.get("en", ""), obj.get("context_hash", ""))
                        self._cache[key] = obj
            logger.info(f"Loaded {len(self._cache)} entries from cache")
        except Exception as e:
            logger.warning(f"Failed to load cache: {e}")
    
    def _make_key(self, text: str, context_hash: str = "") -> str:
        """生成缓存键"""
        import hashlib
        content = f"{text}|{context_hash}"
        return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]
    
    def get(self, text: str, context_hash: str = "") -> Optional[str]:
        """获取缓存的翻译
        
        Args:
            text: 原文
            context_hash: 上下文哈希（可选）
        
        Returns:
            缓存的译文，如果没有则返回 None
        """
        key = self._make_key(text, context_hash)
        with self._lock:
            entry = self._cache.get(key)
            if entry:
                return entry.get("zh")
        return None
    
    def put(
        self,
        text: str,
        translation: str,
        context_hash: str = "",
        quality_score: float = 0.0,
        metadata: Optional[dict] = None
    ) -> None:
        """存储翻译到缓存
        
        Args:
            text: 原文
            translation: 译文
            context_hash: 上下文哈希
            quality_score: 质量分数
            metadata: 额外元数据
        """
        key = self._make_key(text, context_hash)
        entry = {
            "en": text,
            "zh": translation,
            "context_hash": context_hash,
            "quality_score": quality_score,
            "timestamp": time.time(),
        }
        if metadata:
            entry.update(metadata)
        
        with self._lock:
            self._cache[key] = entry
            self._dirty = True
    
    def get_stats(self) -> dict[str, Any]:
        """获取缓存统计信息
        
        Returns:
            包含 total、dirty、file_path 等统计信息的字典
        """
        with self._lock:
            return {
                "total": len(self._cache),
                "dirty": self._dirty,
                "file_path": str(self._cache_file) if self._cache_file else None,
            }
    
    def save(self) -> None:
        """保存缓存到文件"""
        if not self._cache_file or not self._dirty:
            return
        
        with self._lock:
            try:
                self._cache_file.parent.mkdir(parents=True, exist_ok=True)
                with self._cache_file.open("w", encoding="utf-8") as f:
                    for entry in self._cache.values():
                        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                self._dirty = False
                logger.info(f"Saved {len(self._cache)} entries to cache")
            except Exception as e:
                logger.error(f"Failed to save cache: {e}")
    
    def __len__(self) -> int:
        return len(self._cache)
    
    def __contains__(self, key: str) -> bool:
        return key in self._cache
