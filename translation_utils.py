#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""翻译引擎公共辅助：TranslationContext、ProgressTracker、占位符处理、checker 过滤、去重等。

所有翻译模式（direct / tl / retranslate）共享的基础设施。
"""

from __future__ import annotations

import json
import logging
import os
import re
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from file_processor import (
    check_response_item,
    restore_placeholders,
)

logger = logging.getLogger("renpy_translator")

# ============================================================
# 可配置阈值常量
# ============================================================

CHECKER_DROP_RATIO_THRESHOLD = 0.3   # chunk 丢弃率超此值触发重试
MIN_DROPPED_FOR_WARNING = 3          # 丢弃数达此值才触发警告
MIN_DIALOGUE_LENGTH = 4              # 定向翻译中对话行最小长度
SAVE_INTERVAL = 10                   # ProgressTracker 每 N 次 mark 写磁盘

# ============================================================
# Chunk 翻译结果
# ============================================================

@dataclass
class ChunkResult:
    """单个 chunk 的翻译结果"""
    part: int                              # chunk 序号
    kept: list = field(default_factory=list)       # 通过校验的翻译条目
    error: str | None = None               # 错误信息（None 表示成功）
    chunk_warnings: list = field(default_factory=list)  # chunk 级警告
    dropped_count: int = 0                 # 被 checker 丢弃的条数
    expected: int = 0                      # chunk 内预期可翻译行数
    returned: int = 0                      # API 实际返回条数
    dropped_items: list = field(default_factory=list)   # 被丢弃的原始条目


# ============================================================
# 翻译上下文（替代嵌套函数的闭包捕获）
# ============================================================

@dataclass
class TranslationContext:
    """翻译引擎共享上下文，将嵌套函数的闭包变量显式化。

    注意：并发路径（ThreadPoolExecutor）中不应直接修改 all_warnings，
    而是通过 ChunkResult 返回 warnings，由主线程串行合并。
    """
    client: object              # APIClient 实例
    system_prompt: str          # 当前翻译的系统 prompt
    rel_path: str               # 当前文件相对路径（用于 user_prompt 构建）


# ============================================================
# 进度管理（断点续传）
# ============================================================

class ProgressTracker:
    """追踪翻译进度，支持中断续传"""

    def __init__(self, progress_file: Path):
        self.path = progress_file
        self._lock = threading.Lock()
        self._dirty = 0  # 未写入磁盘的 mark 操作计数
        self.data: dict = {"completed_files": [], "completed_chunks": {}, "stats": {}}
        self._load()

    def _load(self) -> None:
        if self.path.exists():
            try:
                self.data = json.loads(self.path.read_text(encoding='utf-8'))
            except (json.JSONDecodeError, OSError) as e:
                logger.warning(f"[PROGRESS] 进度文件损坏，已重置: {e}")
                self.data = {}
        # 确保必需 key 存在（防损坏文件缺 key 导致 KeyError）
        self.data.setdefault("completed_files", [])
        self.data.setdefault("completed_chunks", {})
        self.data.setdefault("stats", {})

    def save(self) -> None:
        with self._lock:
            self._save_unlocked()
            self._dirty = 0

    def _save_unlocked(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix('.tmp')
        try:
            tmp.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding='utf-8')
            # Windows 上 os.replace 可能因杀毒软件/索引服务短暂锁文件而失败，重试几次
            last_err: BaseException | None = None
            for attempt in range(5):
                try:
                    os.replace(str(tmp), str(self.path))
                    return
                except PermissionError as e:
                    last_err = e
                    time.sleep(0.1 * (attempt + 1))
            # 重试全部失败，尝试回退方案：直接写目标文件
            try:
                self.path.write_text(
                    json.dumps(self.data, ensure_ascii=False, indent=2), encoding='utf-8')
                tmp.unlink(missing_ok=True)
                return
            except OSError:
                pass
            if last_err:
                raise last_err
        except BaseException:
            try:
                tmp.unlink(missing_ok=True)
            except OSError:
                pass
            raise

    def is_file_done(self, rel_path: str) -> bool:
        return rel_path in self.data["completed_files"]

    def is_chunk_done(self, rel_path: str, part: int) -> bool:
        return part in self.data.get("completed_chunks", {}).get(rel_path, [])

    def mark_chunk_done(self, rel_path: str, part: int, translations: list[dict]) -> None:
        with self._lock:
            chunks = self.data.setdefault("completed_chunks", {})
            chunk_list = chunks.setdefault(rel_path, [])
            if part not in chunk_list:
                chunk_list.append(part)

            # 保存该 chunk 的翻译结果
            results = self.data.setdefault("results", {})
            file_results = results.setdefault(rel_path, [])
            file_results.extend(translations)
            self._dirty += 1
            if self._dirty >= SAVE_INTERVAL:
                self._save_unlocked()
                self._dirty = 0

    def get_file_translations(self, rel_path: str) -> list[dict]:
        """获取文件的所有已完成翻译"""
        return self.data.get("results", {}).get(rel_path, [])

    def mark_file_done(self, rel_path: str) -> None:
        with self._lock:
            if rel_path not in self.data["completed_files"]:
                self.data["completed_files"].append(rel_path)
            # 清理 chunk 级数据（已完成文件不需要保留）
            self.data.get("completed_chunks", {}).pop(rel_path, None)
            self.data.get("results", {}).pop(rel_path, None)
            self._save_unlocked()
            self._dirty = 0

    def update_stats(self, key: str, value: object) -> None:
        with self._lock:
            self.data.setdefault("stats", {})[key] = value
            self._save_unlocked()


# ============================================================
# 会话级翻译缓存
# ============================================================

class TranslationCache:
    """会话级翻译缓存，避免重复 API 调用。

    线程安全。缓存 key 为原文文本，value 为译文。
    同一原文被翻译为相同结果 ≥2 次后视为高置信度。
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._cache: dict[str, str] = {}      # original -> zh
        self._count: dict[str, int] = {}       # original -> 命中/写入次数
        self._hits = 0
        self._misses = 0

    def get(self, original: str) -> str | None:
        """查询缓存。返回译文或 None。"""
        with self._lock:
            zh = self._cache.get(original)
            if zh is not None:
                self._hits += 1
            else:
                self._misses += 1
            return zh

    def put(self, original: str, zh: str) -> None:
        """写入缓存。如果已有相同 original，更新译文并增加计数。"""
        with self._lock:
            self._cache[original] = zh
            self._count[original] = self._count.get(original, 0) + 1

    def confidence(self, original: str) -> int:
        """返回某条原文的翻译置信度（被翻译/确认的次数）。"""
        with self._lock:
            return self._count.get(original, 0)

    def get_high_confidence_entries(self, min_count: int = 2) -> dict[str, str]:
        """返回置信度 ≥ min_count 的所有缓存条目。"""
        with self._lock:
            return {
                k: v for k, v in self._cache.items()
                if self._count.get(k, 0) >= min_count
            }

    @property
    def size(self) -> int:
        with self._lock:
            return len(self._cache)

    def stats(self) -> str:
        with self._lock:
            total = self._hits + self._misses
            rate = self._hits / total * 100 if total else 0
            return f"缓存: {len(self._cache)} 条, 命中 {self._hits}/{total} ({rate:.1f}%)"


# ============================================================
# 公共辅助函数
# ============================================================

# 匹配 AI 返回带角色名前缀的译文，如 mc "你好"
_CHAR_PREFIX_RE = re.compile(r'^[a-zA-Z_]\w*\s+"((?:[^"\\]|\\.)*)"$')


def _strip_char_prefix(translations: list[dict]) -> None:
    """如果 AI 返回的 original/zh 带角色名前缀（如 mc "text"），剥离为纯对话文本。"""
    for t in translations:
        for key in ("original", "zh"):
            val = t.get(key, "") or ""
            m = _CHAR_PREFIX_RE.match(val)
            if m:
                t[key] = m.group(1)


def _restore_placeholders_in_translations(
    translations: list[dict],
    ph_mapping: list[tuple[str, str]],
    extra_keys: tuple[str, ...] = (),
) -> None:
    """将翻译结果中的占位符令牌还原为原始文本。

    默认还原 original 和 zh 字段，extra_keys 可追加额外字段（如 tl-mode 的 id）。
    """
    keys = ("original", "zh") + extra_keys
    for t in translations:
        for key in keys:
            val = t.get(key)
            if val:
                t[key] = restore_placeholders(val, ph_mapping)


_PH_TOKEN_RE = re.compile(r"__RENPY_PH_\d+__")


def _build_fallback_dicts(
    ft: dict[str, str],
) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    """为 StringEntry 四层 fallback 匹配预建 3 个查找 dict（O(1) 查找代替 O(n) 遍历）。"""
    ft_stripped = {}
    ft_clean = {}
    ft_norm = {}
    for k, v in ft.items():
        s = k.strip()
        if s and s not in ft_stripped:
            ft_stripped[s] = v
        c = _PH_TOKEN_RE.sub("", k).strip()
        if c and c not in ft_clean:
            ft_clean[c] = v
        n = k.replace('\\"', '"').replace("\\n", "\n").strip()
        if n and n not in ft_norm:
            ft_norm[n] = v
    return ft_stripped, ft_clean, ft_norm


def _match_string_entry_fallback(
    entry_old: str,
    ft: dict[str, str],
    ft_stripped: dict[str, str],
    ft_clean: dict[str, str],
    ft_norm: dict[str, str],
) -> tuple[str | None, int]:
    """StringEntry 四层 fallback 匹配。返回 (zh, fallback_level)。"""
    # L1: 精确匹配
    zh = ft.get(entry_old)
    if zh:
        return zh, 0
    # L2: strip 空白
    zh = ft_stripped.get(entry_old.strip())
    if zh:
        return zh, 2
    # L3: 去占位符令牌
    clean = _PH_TOKEN_RE.sub("", entry_old).strip()
    if clean:
        zh = ft_clean.get(clean)
        if zh:
            return zh, 3
    # L4: 转义规范化
    norm = entry_old.replace('\\"', '"').replace("\\n", "\n").strip()
    if norm:
        zh = ft_norm.get(norm)
        if zh:
            return zh, 4
    return None, 0


def _filter_checked_translations(
    translations: list[dict],
    line_offset: int = 0,
) -> tuple[list[dict], int, list[dict], list[str]]:
    """对翻译结果逐条执行 checker，分流为 kept / dropped。

    Returns:
        (kept, dropped_count, dropped_items, warnings)
    """
    kept: list[dict] = []
    dropped_items: list[dict] = []
    dropped_count = 0
    warnings: list[str] = []
    for t in translations:
        item_warnings = check_response_item(t, line_offset=line_offset)
        if item_warnings:
            dropped_count += 1
            dropped_items.append(t)
            for w in item_warnings:
                warnings.append(f"[CHECK-DROPPED] {w}")
        else:
            kept.append(t)
    return kept, dropped_count, dropped_items, warnings


def _deduplicate_translations(translations: list[dict]) -> list[dict]:
    """按 (line, original) 去重，保留首次出现的条目。"""
    seen: set[tuple] = set()
    unique: list[dict] = []
    for t in translations:
        key = (t.get("line", 0), t.get("original", ""))
        if key not in seen:
            seen.add(key)
            unique.append(t)
    return unique


# ============================================================
# 进度条（纯标准库，GBK/ASCII 自适应）
# ============================================================

import sys

class ProgressBar:
    """单行覆写式进度条，支持 Unicode（UTF-8）和 ASCII（GBK/CP936）两种模式。

    用法：
        bar = ProgressBar(total=100)
        for i in range(100):
            bar.update(1, cost=0.01)
        bar.finish()
    """

    def __init__(self, total: int, width: int = 40):
        self.total = total
        self.width = width
        self.current = 0
        self.cost = 0.0
        self._start_time = time.time()
        self._use_unicode = self._detect_unicode_support()

    @staticmethod
    def _detect_unicode_support() -> bool:
        """检测终端是否支持 Unicode 进度条字符。"""
        try:
            encoding = getattr(sys.stderr, 'encoding', '') or ''
            if encoding.lower().replace('-', '') in ('utf8', 'utf8sig'):
                return True
            '█░'.encode(encoding)
            return True
        except (UnicodeEncodeError, LookupError):
            return False

    def update(self, n: int = 1, cost: float = 0.0) -> None:
        """更新进度。n=完成的增量，cost=本次花费（美元）。"""
        self.current += n
        self.cost += cost
        self._render()

    def _render(self) -> None:
        pct = self.current / self.total if self.total > 0 else 0
        filled = int(self.width * pct)
        if self._use_unicode:
            bar = '█' * filled + '░' * (self.width - filled)
        else:
            bar = '#' * filled + '-' * (self.width - filled)
        elapsed = time.time() - self._start_time
        if self.current > 0:
            eta = elapsed / self.current * (self.total - self.current)
        else:
            eta = 0
        try:
            sys.stderr.write(
                f"\r[{bar}] {pct:.0%} | {self.current}/{self.total} "
                f"| ${self.cost:.2f} | ETA {eta / 60:.0f}min"
            )
            sys.stderr.flush()
        except (UnicodeEncodeError, OSError):
            pass  # 终端编码异常时静默跳过

    def finish(self) -> None:
        """进度条完成，换行。"""
        try:
            sys.stderr.write('\n')
            sys.stderr.flush()
        except OSError:
            pass
