"""
Placeholder detection and validation utilities for Ren'Py translation.

This module provides functions to:
- Detect placeholders in text ([name], {0}, %s, etc.)
- Count placeholder occurrences
- Validate placeholder preservation in translations
"""

from __future__ import annotations

import hashlib
import re
from typing import Optional, Callable

from .logger import get_logger

logger = get_logger(__name__)

# 轻量 KV 缓存（可选）
cached: Optional[Callable] = None
try:
    from .cache import cached as _cached  # type: ignore
    cached = _cached
except ImportError:
    # 可选依赖，缓存模块不可用时静默降级
    pass
except RuntimeError as e:  # pragma: no cover
    # 其他异常需要记录以便排查
    logger.warning(f"Failed to import cache module: {e}")

# —— Ren'Py 文本标签与指令 ——
# 单次指令（不成对）
RENPY_SINGLE_TAGS = frozenset({"w","nw","p","fast","k"})
# 成对标签（需闭合/允许嵌套）
RENPY_PAIRED_TAGS = frozenset({"i","b","u","color","a","size","font","alpha"})


# —— 占位符匹配 ——
# 1) 方括号变量: [name]
_PH_SQUARE = re.compile(r"\[[A-Za-z_][A-Za-z0-9_]*\]")
# 2) 百分号格式: %s / %d / %02d / %(name)s / %.2f / %e %g %x %o ...
_PH_PERCENT = re.compile(r"%(?:\([^)]+\))?[+#0\- ]?\d*(?:\.\d+)?[sdifeEfgGxXo]")
# 3) 花括号格式: {0} / {0:.2f} / {name!r:>8}
_PH_BRACE_INDEX = re.compile(r"\{\d+(?:![rsa])?(?::[^{}]+)?\}")
_PH_BRACE_NAME = re.compile(r"\{[A-Za-z_][A-Za-z0-9_]*(?:![rsa])?(?::[^{}]+)?\}")

# 汇总（用于外部快速使用；内部 ph_set 会做进一步过滤以忽略 {{ 和 }} 的转义）
PH_RE = re.compile(
    _PH_SQUARE.pattern + r"|" + _PH_PERCENT.pattern + r"|" + _PH_BRACE_INDEX.pattern + r"|" + _PH_BRACE_NAME.pattern
)

# 变量名匹配（用于 _iter_placeholders 的 brace 变量提取）
_VARNAME_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)(?:![rsa])?(?::[^}]*)?$")

def _is_escaped_brace(s: str, start: int, end: int) -> bool:
    """是否位于 {{...}} 的转义环境中：左侧还有一个 { 或右侧还有一个 }"""
    left = (start-1 >= 0 and s[start-1] == '{')
    right = (end < len(s) and s[end] == '}')
    return left or right

def _iter_placeholders(s: str):
    if not s:
        return
    for rex in (_PH_SQUARE, _PH_PERCENT, _PH_BRACE_INDEX, _PH_BRACE_NAME):
        for m in rex.finditer(s):
            a,b = m.span()
            if _is_escaped_brace(s, a, b):
                continue
            yield m.group(0)

def ph_set(s: str) -> set[str]:
    """
    Extract unique placeholders from text.
    
    Args:
        s: Input text
        
    Returns:
        Set of placeholder strings
    """
    if cached is not None:
        def _comp(x: str) -> str:
            return "\u0001".join(sorted(set(_iter_placeholders(x or ""))))
        v = cached("phset", "v1", s or "", _comp)
        return set((v or "").split("\u0001")) if v else set()
    return set(_iter_placeholders(s or ""))


def ph_multiset(s: str) -> dict[str, int]:
    """
    Count placeholder occurrences in text.
    
    Args:
        s: Input text
        
    Returns:
        Dictionary mapping placeholder to count
        
    Example:
        >>> ph_multiset("Hello [name], score: {0}, {0}")
        {'[name]': 1, '{0}': 2}
    """
    cnt: dict[str, int] = {}
    for ph in _iter_placeholders(s or ""):
        cnt[ph] = cnt.get(ph, 0) + 1
    return cnt


# —— 变量名计数（[name] 与 {name}）——
VAR_BRACKET_RE = re.compile(r"\[\s*([A-Za-z_][A-Za-z0-9_]*)\s*\]")
VAR_BRACE_RE = re.compile(r"\{([^{}]+)\}")

def extract_var_name_counts(s: str) -> dict[str, int]:
    s = s or ""
    counts: dict[str, int] = {}
    # [name]
    for m in VAR_BRACKET_RE.finditer(s):
        k = m.group(1)
        counts[k] = counts.get(k,0) + 1
    # {name} / {name:...} / {name!r} —— 排除关闭、含=、以及 Ren'Py 文本标签
    for m in VAR_BRACE_RE.finditer(s):
        a,b = m.span()
        if _is_escaped_brace(s, a, b):
            continue
        inner = m.group(1).strip()
        if not inner or inner.startswith('/'):
            continue
        if '=' in inner:
            # {color=...} {a=...} {size=...} 视作文本标签/指令，不计为占位变量
            continue
        mname = _VARNAME_RE.match(inner)
        if not mname:
            continue
        name = mname.group(1)
        if name in RENPY_PAIRED_TAGS or name in RENPY_SINGLE_TAGS:
            continue
        counts[name] = counts.get(name,0) + 1
    return counts


# —— 语义稳定签名 ——
_TAG_OPEN_RE = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)(?:=[^}]*)?\}")
_TAG_CLOSE_RE = re.compile(r"\{/([A-Za-z_][A-Za-z0-9_]*)\}")

def strip_renpy_tags(s: str) -> str:
    """去除 Ren'Py 文本标签（单次与成对的开闭标签），保留文本与占位符。"""
    if not s:
        return ""
    out = []
    i = 0
    n = len(s)
    while i < n:
        ch = s[i]
        if ch == '{':
            # 尝试识别标签；若为 {{ 或 }} 的一部分则保留一个 { 并跳过
            if i+1 < n and s[i+1] == '{':
                out.append('{')
                i += 2
                continue
            m1 = _TAG_OPEN_RE.match(s, i)
            if m1:
                name = m1.group(1)
                if name in RENPY_SINGLE_TAGS or name in RENPY_PAIRED_TAGS:
                    i = m1.end()
                    continue  # 丢弃标签本身
            m2 = _TAG_CLOSE_RE.match(s, i)
            if m2:
                name = m2.group(1)
                if name in RENPY_PAIRED_TAGS:
                    i = m2.end()
                    continue
        out.append(ch)
        i += 1
    return ''.join(out)

_WS_RE = re.compile(r"\s+")

def normalize_for_signature(s: str) -> str:
    s = strip_renpy_tags(s or "")
    s = _WS_RE.sub(" ", s).strip().lower()
    return s

def compute_semantic_signature(s: str) -> str:
    """语义签名 v2：加入更稳健的规范化（保留占位符，归一空白与大小写）。

    返回形如：sig:v2:<sha12>
    """
    norm = normalize_for_signature(s)
    if cached is not None:
        return cached("sig", "v2", norm, lambda x: "sig:v2:" + hashlib.sha256(x.encode('utf-8')).hexdigest()[:12])
    h = hashlib.sha256(norm.encode('utf-8')).hexdigest()
    return "sig:v2:" + h[:12]


# —— 占位符提取 / 恢复（用于翻译引擎） ——
_EXTRACT_PH_RE = re.compile(
    r'\{[/a-z_][^}]*\}'           # {i}, {/i}, {color=#fff}
    r'|\[[a-z_][^\]]*\]'          # [name], [pov]
    r'|%\([^)]+\)[sdifeEfgGxXo]'  # %(name)s
    r'|%[sdifeEfgGxXo]'           # %s, %d
    r'|\{\d+(?:![rsa])?(?::[^{}]+)?\}'           # {0}, {0:.2f}
    r'|\{[A-Za-z_][A-Za-z0-9_]*(?:![rsa])?(?::[^{}]+)?\}',  # {name}
    flags=re.IGNORECASE
)


def extract_placeholders(text: str) -> tuple[str, list[tuple[str, int]]]:
    """提取占位符，用 〔n〕 全角标记替换。

    提取的占位符类型：
    1. Ren'Py 标签：{i} {/i} {b} {color=#...}
    2. 方括号变量：[name] [pov] [ls]
    3. 格式化占位符：%(name)s %s {0} {name}

    Args:
        text: 原始英文文本

    Returns:
        (替换后的纯文本, [(占位符原文, 索引)])
    """
    matches = list(_EXTRACT_PH_RE.finditer(text))
    placeholders: list[tuple[str, int]] = []
    result = text

    # 从后往前替换，避免位置偏移
    for i in range(len(matches) - 1, -1, -1):
        match = matches[i]
        ph = match.group(0)
        pos = match.start()
        tag = f'〔{i}〕'
        placeholders.insert(0, (ph, i))
        result = result[:pos] + tag + result[pos + len(ph):]

    return result, placeholders


def restore_placeholders(text: str, placeholders: list[tuple[str, int]]) -> str:
    """将 〔n〕 标记替换回原始占位符。

    Args:
        text: 含 〔n〕 标记的译文
        placeholders: extract_placeholders 返回的占位符列表

    Returns:
        替换回占位符后的译文
    """
    result = text
    for ph, idx in placeholders:
        tag = f'〔{idx}〕'
        result = result.replace(tag, ph)
    return result
