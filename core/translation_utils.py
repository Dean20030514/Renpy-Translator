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

logger = logging.getLogger("renpy_translator")

# Round 27 A-H-2: ``_filter_checked_translations`` /
# ``_restore_placeholders_in_translations`` /
# ``_restore_locked_terms_in_translations`` were moved to
# ``file_processor.checker`` to eliminate the reverse dependency
# ``core → file_processor``.  Callers should now import them from
# ``file_processor`` directly (translators/direct_chunk, translators/
# direct_file, translators/tl_mode, translators/retranslator all
# already updated).

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
    locked_terms_map: "dict[str, str]" = field(default_factory=dict)  # {英文术语: 中文译名}，用于预替换保护


# ============================================================
# 进度管理（断点续传）
# ============================================================

class ProgressTracker:
    """追踪翻译进度，支持中断续传。

    并发模型：
    - ``_lock`` 保护 ``self.data`` 的读写和 ``json.dumps`` 的快照生成
    - ``_save_lock`` 串行化磁盘 I/O（tmp 写 + os.replace 重试）
    - 对 ``mark_chunk_done`` 这类热路径，主锁只持有极短时间（dict 更新 + 序列化），
      实际磁盘写在主锁外、``_save_lock`` 内执行，避免 worker 间串行化

    Round 35 C1: 可选 ``language`` kwarg 开启 language-aware namespace。
    当设置时，所有按 ``rel_path`` 索引的 dict key 会变成 ``"<lang>:<rel_path>"``
    形式，让同一游戏在同一输出目录并行跑多语言时不互相污染 progress 状态。
    读路径做向后兼容：如果 namespaced key 不存在但 bare key 存在（pre-r35
    progress 文件），仍能读到，保证 round-34 文件 resume 不失效。写路径始
    终用 namespaced key；遗留 bare key 在 ``mark_file_done`` 时顺便清理。
    ``language=None`` （默认）等价于 round-34 byte-identical 行为。

    Round 36 H1: bare-key fallback is restricted to ``self.language ==
    self._LEGACY_BARE_LANG`` (zh) or ``self.language is None``.  Non-zh
    languages running against pre-r35 bare-key progress files treat the
    data as foreign to avoid cross-language skip bugs (where ja/ko would
    inherit zh's completed chunks and silently leave their DB bucket
    empty).  Mirror guard on ``mark_file_done``: only zh / no-language
    trackers clean the bare bucket on file completion — non-zh trackers
    leave it alone to preserve a future zh resume.
    """

    # Round 36 H1: language that implicitly owns pre-r35 bare-key progress
    # data.  Matches ``core.config.DEFAULTS["target_lang"]`` because pre-r35
    # never supported any other target_lang — the multi-language outer
    # loop (``main._parse_target_langs``) landed in round 35.  See class
    # docstring above for the full H1 rationale.  If a future round changes
    # the project's default target language, update this constant in
    # lockstep.
    _LEGACY_BARE_LANG: str = "zh"

    def __init__(self, progress_file: Path, *, language: "str | None" = None):
        self.path = progress_file
        self.language = language if (isinstance(language, str) and language) else None
        self._lock = threading.Lock()
        self._save_lock = threading.Lock()
        self._dirty = 0  # 未写入磁盘的 mark 操作计数
        self.data: dict = {"completed_files": [], "completed_chunks": {}, "stats": {}}
        self._load()

    def _key(self, rel_path: str) -> str:
        """Round 35 C1: language-namespaced write key for ``rel_path``.

        Returns ``"<lang>:<rel_path>"`` when ``self.language`` is set, else
        the bare ``rel_path`` (round-34 behaviour).  Read-side callers
        should fall back to the bare key on miss for backward compat with
        pre-round-35 ``progress.json`` files.
        """
        if self.language:
            return f"{self.language}:{rel_path}"
        return rel_path

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
        """外部 API：同步写盘。返回时磁盘状态已落。"""
        self._flush_to_disk()
        with self._lock:
            self._dirty = 0

    def _flush_to_disk(self) -> None:
        """生成当前 data 的 JSON 快照并原子落盘。

        并发正确性要点（第 22 轮 P1 修复）：snapshot 生成和磁盘写入必须在
        同一把 ``_save_lock`` 下串行，否则两个线程各自生成快照后按 save_lock
        先后写盘，可能出现"后拿 save_lock 的线程用更旧的快照覆盖新快照"，
        导致盘上进度回退。嵌套 ``_lock`` 仅持 ``json.dumps`` 时长，对 worker
        竞争几乎无影响。
        """
        with self._save_lock:
            with self._lock:
                snapshot_json = json.dumps(self.data, ensure_ascii=False, indent=2)
            self._write_atomic(snapshot_json)

    def _write_atomic(self, json_str: str) -> None:
        """原子写文件：tmp + os.replace + 重试。调用方需持有 _save_lock。"""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix('.tmp')
        try:
            tmp.write_text(json_str, encoding='utf-8')
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
                self.path.write_text(json_str, encoding='utf-8')
                tmp.unlink(missing_ok=True)
                return
            except OSError as fallback_err:
                logger.warning(f"[PROGRESS] 写磁盘最终失败: {fallback_err}")
            if last_err:
                raise last_err
        except BaseException:
            try:
                tmp.unlink(missing_ok=True)
            except OSError:
                pass
            raise

    def is_file_done(self, rel_path: str) -> bool:
        # Round 35 C1 + Round 36 H1: prefer language-namespaced key.
        # Bare-key fallback is restricted to ``_LEGACY_BARE_LANG`` (zh)
        # or unset language — non-zh langs must NOT inherit zh's pre-r35
        # completion state (H1 cross-language skip bug: ja would see zh's
        # completed files as "done" and silently leave its DB bucket empty).
        completed = self.data.get("completed_files", [])
        if self.language:
            if self._key(rel_path) in completed:
                return True
            if self.language != self._LEGACY_BARE_LANG:
                return False
        return rel_path in completed

    def is_chunk_done(self, rel_path: str, part: int) -> bool:
        # Round 35 C1 + Round 36 H1: check namespaced bucket first.
        # Bare-key fallback only for ``_LEGACY_BARE_LANG`` (zh) or unset
        # language — non-zh langs must NOT inherit zh's pre-r35 completed
        # chunks (H1 cross-language skip bug).
        chunks = self.data.get("completed_chunks", {})
        if self.language:
            if part in chunks.get(self._key(rel_path), []):
                return True
            if self.language != self._LEGACY_BARE_LANG:
                return False
        return part in chunks.get(rel_path, [])

    def mark_chunk_done(self, rel_path: str, part: int, translations: list[dict]) -> None:
        should_flush = False
        key = self._key(rel_path)
        with self._lock:
            chunks = self.data.setdefault("completed_chunks", {})
            chunk_list = chunks.setdefault(key, [])
            if part not in chunk_list:
                chunk_list.append(part)

            # 保存该 chunk 的翻译结果
            results = self.data.setdefault("results", {})
            file_results = results.setdefault(key, [])
            file_results.extend(translations)
            self._dirty += 1
            if self._dirty >= SAVE_INTERVAL:
                self._dirty = 0
                should_flush = True
        if should_flush:
            self._flush_to_disk()

    def get_file_translations(self, rel_path: str) -> list[dict]:
        """获取文件的所有已完成翻译.

        Round 35 C1: 合并 namespaced bucket + 旧 bare bucket 的结果，
        让从 round-34 progress.json 接续的 resume 不丢失已翻译条目。

        Round 36 H1: 非 ``_LEGACY_BARE_LANG``（非 zh）的 language-aware
        tracker 跳过 bare bucket 合并，防止 pre-r35 的 zh bare 数据
        污染 ja/ko 等其他语言的 resume 集合。
        """
        results = self.data.get("results", {})
        combined: list[dict] = []
        if self.language:
            combined.extend(results.get(self._key(rel_path), []))
            if self.language != self._LEGACY_BARE_LANG:
                return combined
        combined.extend(results.get(rel_path, []))
        return combined

    def mark_file_done(self, rel_path: str) -> None:
        key = self._key(rel_path)
        with self._lock:
            if key not in self.data["completed_files"]:
                self.data["completed_files"].append(key)
            # 清理 chunk 级数据（已完成文件不需要保留）— namespaced key 始终清。
            self.data.get("completed_chunks", {}).pop(key, None)
            self.data.get("results", {}).pop(key, None)
            # Round 35 C1 + Round 36 H1: bare bucket 只由 owner 语言
            # （zh，或 no-language tracker）清。非 zh language-aware
            # tracker 触碰 bare 会误删另一个语言（隐式 zh）尚未迁移的
            # resume 数据。
            if self.language is None or self.language == self._LEGACY_BARE_LANG:
                self.data.get("completed_chunks", {}).pop(rel_path, None)
                self.data.get("results", {}).pop(rel_path, None)
            self._dirty = 0
        self._flush_to_disk()

    def update_stats(self, key: str, value: object) -> None:
        with self._lock:
            self.data.setdefault("stats", {})[key] = value
        self._flush_to_disk()


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


_PH_TOKEN_RE = re.compile(r"__RENPY_PH_\d+__")

# Round 31 Tier A-3: Ren'Py inline-tag stripper for fallback key matching.
# Matches ``{color=#f00}...{/color}``, ``{b}``, ``{size=-10}``, ``{#id}`` etc.
# Ported in spirit from ``renpy_hook_template_py3.rpy::_strip_tags`` (lines
# 279-294) — the competitor's bracket-state-machine version is simpler but
# this regex-driven variant reuses Python's compiled-pattern cache and
# handles nested cases cleanly.
_RENPY_TAG_RE = re.compile(r"\{/?[a-zA-Z#!][^}]*\}")


def _strip_renpy_tags(text: str) -> str:
    """Strip Ren'Py inline control tags (``{color}...{/color}``, ``{b}`` …)
    leaving only the human-readable text.  Used as a 5th-level fallback
    key when a String entry's tags differ slightly from the translation
    file (e.g. the AI added a ``{b}`` emphasis wrapper or closed with the
    short form ``{/}``).  Idempotent and safe on strings with no tags.
    """
    if not text:
        return text
    return _RENPY_TAG_RE.sub("", text)


def _build_fallback_dicts(
    ft: dict[str, str],
) -> tuple[dict[str, str], dict[str, str], dict[str, str], dict[str, str]]:
    """为 StringEntry 五层 fallback 匹配预建 4 个查找 dict（O(1) 查找代替 O(n) 遍历）。

    Round 31 Tier A-3: the 4th dict (``ft_tagstripped``) keys every entry
    by its tag-stripped + whitespace-collapsed form, enabling an extra
    fallback layer for AI outputs that add / remove / reshape ``{color}`` /
    ``{b}`` / ``{size}`` wrappers relative to the translation file.
    """
    ft_stripped: dict[str, str] = {}
    ft_clean: dict[str, str] = {}
    ft_norm: dict[str, str] = {}
    ft_tagstripped: dict[str, str] = {}
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
        t = _strip_renpy_tags(k).strip()
        # Normalise whitespace so "Hello world" matches "Hello  world"
        # after tag-stripping collapses spacing.
        t = " ".join(t.split()) if t else t
        if t and t not in ft_tagstripped:
            ft_tagstripped[t] = v
    return ft_stripped, ft_clean, ft_norm, ft_tagstripped


def _match_string_entry_fallback(
    entry_old: str,
    ft: dict[str, str],
    ft_stripped: dict[str, str],
    ft_clean: dict[str, str],
    ft_norm: dict[str, str],
    ft_tagstripped: dict[str, str] | None = None,
) -> tuple[str | None, int]:
    """StringEntry 五层 fallback 匹配。返回 (zh, fallback_level)。

    ``ft_tagstripped`` defaults to ``None`` for backward compatibility with
    pre-round-31 callers that only passed 4 dicts; when provided, enables
    the level-5 tag-stripped match.
    """
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
    # L5 (round 31 Tier A-3): strip Ren'Py tags + whitespace-normalise.
    if ft_tagstripped:
        tag_stripped = _strip_renpy_tags(entry_old).strip()
        tag_stripped = " ".join(tag_stripped.split()) if tag_stripped else tag_stripped
        if tag_stripped:
            zh = ft_tagstripped.get(tag_stripped)
            if zh:
                return zh, 5
    return None, 0


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
