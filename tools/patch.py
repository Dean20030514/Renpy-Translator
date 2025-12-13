#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Patcher —— 将翻译 JSONL 回填为 .zh.rpy 镜像文件

支持特性:
- 双/单/三引号(含跨行字符串)
- 五级智能匹配策略: 精确位置 -> 邻近区域 -> 上下文锚点 -> 全文唯一 -> 引号包裹
- 占位符安全检查([], {}, %)
- 多译文字段兼容: zh/cn/zh_cn/translation/text_zh/target/tgt
- 干运行模式(--dry-run)和自动备份(--backup)
- 详细的 TSV 报告
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import re
import tempfile
from pathlib import Path
from collections import namedtuple
from typing import List, Optional, Tuple

# 占位符匹配：不将样式标签({i},{/i},{color=...})计入
try:
    from renpy_tools.utils.placeholder import PH_RE as _PH_RE, compute_semantic_signature as _comp_sig, normalize_for_signature as _norm_sig  # type: ignore
except (ImportError, ModuleNotFoundError):
    _PH_RE = None
    _comp_sig = None
    _norm_sig = None
PH_RE = _PH_RE or re.compile(
    r"\[[A-Za-z_][A-Za-z0-9_]*\]"                       # [name]
    r"|%(?:\([^)]+\))?[+#0\- ]?\d*(?:\.\d+)?[sdifeEfgGxXo]"  # %s, %02d, %(name)s, %.2f, %x, %o
    r"|\{\d+(?:![rsa])?(?::[^{}]+)?\}"                  # {0} {0:.2f} {0!r:>8}
    r"|\{[A-Za-z_][A-Za-z0-9_]*(?:![rsa])?(?::[^{}]+)?\}" # {name!r:>8}
)
try:
    from rapidfuzz import fuzz as _fuzz  # type: ignore
except (ImportError, ModuleNotFoundError):  # pragma: no cover - 可选依赖
    _fuzz = None
DQ_RE = re.compile(r'"((?:\\.|[^"\\])*)"')
SQ_RE = re.compile(r"'((?:\\.|[^'\\])*)'")

# 从公共模块导入翻译字段键，保持一致性
try:
    from renpy_tools.utils.common import TRANS_KEYS as _TRANS_KEYS  # type: ignore
except (ImportError, ModuleNotFoundError):
    _TRANS_KEYS = None
TRANS_KEYS = _TRANS_KEYS or ("zh", "cn", "zh_cn", "translation", "text_zh", "target", "tgt", "zh_final")

TRIPLE_QUOTES = {"'''", '"""'}

# 可选：统一文本写入（自动创建父目录，原子写入）
try:
    from renpy_tools.utils.io import write_text_file as _write_text_file  # type: ignore
except (ImportError, ModuleNotFoundError):
    def _write_text_file(path: str | Path, text: str, encoding: str = 'utf-8', atomic: bool = True):
        """写入文本文件，支持原子写入"""
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        if atomic:
            # 原子写入：先写临时文件再重命名
            fd, tmp_path = tempfile.mkstemp(
                dir=p.parent,
                prefix=f".{p.name}.",
                suffix=".tmp"
            )
            try:
                with os.fdopen(fd, 'w', encoding=encoding) as f:
                    f.write(text)
                os.replace(tmp_path, p)
            except Exception:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
                raise
        else:
            p.write_text(text, encoding=encoding)


def _is_safe_path(base_dir: Path, target_path: Path) -> bool:
    """检查路径是否安全（防止路径遍历攻击）"""
    try:
        resolved_base = base_dir.resolve()
        resolved_target = target_path.resolve()
        resolved_target.relative_to(resolved_base)
        return True
    except ValueError:
        return False


def _safe_write_output(
    out_root: Path,
    rel_path: str,
    content: str,
    suffix: str = ".zh.rpy"
) -> bool:
    """安全地写入输出文件

    Args:
        out_root: 输出根目录
        rel_path: 相对路径
        content: 文件内容
        suffix: 文件后缀

    Returns:
        是否成功写入
    """
    out_path = (out_root / rel_path).with_suffix(suffix)

    # 安全检查
    if not _is_safe_path(out_root, out_path):
        print(f"[WARN] 不安全的路径，跳过: {rel_path}")
        return False

    out_path.parent.mkdir(parents=True, exist_ok=True)

    # 流式写出，避免一次性内存占用
    with open(out_path, "w", encoding="utf-8") as wf:
        bs = 1 << 20  # 1MB 块
        for i in range(0, len(content), bs):
            wf.write(content[i:i + bs])

    return True


Token = namedtuple("Token", ["start", "end", "inner_start", "inner_end", "quote", "is_triple", "start_line", "end_line"])

# 自定义异常：命中了 python 区域，按策略应跳过并记录 warn
class PythonRegionMatch(Exception):
    def __init__(self, method: str):
        super().__init__(method)
        self.method = method

def escape_for_quote(s: str, q: str) -> str:
    return s.replace(q, '\\' + q)

def sanitize_triple_content(s: str, triple_q: str) -> str:
    # 避免译文中直接出现与包裹用的三引号完全相同的序列（例如连续三个双引号或连续三个单引号），
    # 通过在第三个引号前插入反斜杠打破闭合标记。
    return s.replace(triple_q, triple_q[:2] + '\\' + triple_q[2:])

def _newline_positions(text: str) -> List[int]:
    pos = [0]
    i = text.find('\n')
    while i != -1:
        pos.append(i + 1)
        i = text.find('\n', i + 1)
    return pos

def _line_from_index(line_starts: List[int], idx: int) -> int:
    lo, hi = 0, len(line_starts) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if line_starts[mid] <= idx and (mid + 1 == len(line_starts) or idx < line_starts[mid + 1]):
            return mid + 1
        elif idx < line_starts[mid]:
            hi = mid - 1
        else:
            lo = mid + 1
    return 1

def scan_string_literals(text: str) -> List[Token]:
    """扫描所有字符串字面量(单/双/三引号,支持跨行)"""
    n = len(text)
    tokens: List[Token] = []
    i = 0
    line_starts = _newline_positions(text)
    while i < n:
        ch = text[i]
        if ch == "'" or ch == '"':
            # 三引号
            if i + 2 < n and text[i:i+3] in TRIPLE_QUOTES:
                q = text[i:i+3]
                start = i
                i += 3
                while i < n:
                    if text[i:i+3] == q:
                        end = i + 3
                        inner_start = start + 3
                        inner_end = end - 3
                        start_line = _line_from_index(line_starts, start)
                        end_line = _line_from_index(line_starts, end - 1)
                        tokens.append(Token(start, end, inner_start, inner_end, q, True, start_line, end_line))
                        i = end
                        break
                    i += 1
                else:
                    # 未闭合三引号
                    end = n
                    inner_start = start + 3
                    inner_end = end
                    start_line = _line_from_index(line_starts, start)
                    end_line = _line_from_index(line_starts, end - 1)
                    tokens.append(Token(start, end, inner_start, inner_end, q, True, start_line, end_line))
                    i = n
                continue
            else:
                # 单/双引号(单行)
                q = ch
                start = i
                i += 1
                escaped = False
                while i < n:
                    c = text[i]
                    if escaped:
                        escaped = False
                        i += 1
                        continue
                    if c == '\\':
                        escaped = True
                        i += 1
                        continue
                    if c == q:
                        end = i + 1
                        inner_start = start + 1
                        inner_end = end - 1
                        start_line = _line_from_index(line_starts, start)
                        end_line = start_line
                        tokens.append(Token(start, end, inner_start, inner_end, q, False, start_line, end_line))
                        i = end
                        break
                    i += 1
                else:
                    # 未闭合
                    end = n
                    inner_start = start + 1
                    inner_end = end
                    start_line = _line_from_index(line_starts, start)
                    end_line = _line_from_index(line_starts, end - 1)
                    tokens.append(Token(start, end, inner_start, inner_end, q, False, start_line, end_line))
                    i = n
                continue
        else:
            i += 1
    return tokens

_PY_BLOCK_RE = re.compile(r"^\s*(?:init\s+python|python(?:\s+early)?(?:\s+hide)?(?:\s+in\s+\w+)?)\s*:\s*$")
_LABEL_RE = re.compile(r"^\s*label\s+[A-Za-z_][A-Za-z0-9_]*\s*:\s*$")
_SCREEN_RE = re.compile(r"^\s*screen\s+[A-Za-z_][A-Za-z0-9_]*.*:\s*$")

def _indent(s: str) -> int:
    i = 0
    for ch in s:
        if ch in (' ', '\t'):
            i += 1
        else:
            break
    return i

def detect_block_spans(text: str):
    """检测脚本中的主要块区域，返回：
    - python_spans: [(start_line, end_line)]
    - label_spans: [(start_line, end_line)]
    - screen_spans: [(start_line, end_line)]
    均为 1-based 行号闭区间。
    """
    lines = normalize_newlines(text).split('\n')
    n = len(lines)
    def scan_with(rex):
        spans = []
        i = 0
        while i < n:
            ln = lines[i]
            m = rex.match(ln)
            if m:
                base_indent = _indent(ln)
                start = i + 1
                j = i + 1
                while j < n:
                    l2 = lines[j]
                    if l2.strip() == '':
                        j += 1; continue
                    if _indent(l2) <= base_indent:
                        break
                    j += 1
                end = j
                spans.append((start, end))
                i = j
                continue
            i += 1
        return spans
    py_spans = scan_with(_PY_BLOCK_RE)
    label_spans = scan_with(_LABEL_RE)
    screen_spans = scan_with(_SCREEN_RE)
    return py_spans, label_spans, screen_spans

def _line_in_spans(line_no: int, spans: list[tuple[int,int]]) -> bool:
    for a,b in spans:
        if a <= line_no <= b:
            return True
    return False

def _region_of_token(tok: Token, py_spans, label_spans, screen_spans) -> str:
    if _line_in_spans(tok.start_line, py_spans):
        return 'python'
    if _line_in_spans(tok.start_line, screen_spans):
        return 'screen'
    if _line_in_spans(tok.start_line, label_spans):
        return 'label'
    return 'root'

def normalize_newlines(s: str) -> str:
    return s.replace('\r\n', '\n').replace('\r', '\n')

def apply_patch_advanced(text: str, en: str, zh: str,
                        line_hint: Optional[int], idx_hint: Optional[int],
                        anchor_prev: Optional[str], anchor_next: Optional[str]) -> Tuple[str, str, str]:
    """
    高级模式: 五级智能匹配策略
    返回 (new_text, method), 找不到时抛 ValueError
    """
    text = normalize_newlines(text)
    en_norm = normalize_newlines(en)
    tokens = scan_string_literals(text)
    py_spans, label_spans, screen_spans = detect_block_spans(text)

    def replace_in_token(tok: Token) -> str:
        # 按字面量类型安全转义
        if tok.is_triple:
            safe_zh = sanitize_triple_content(zh, tok.quote)
        else:
            # tok.quote 为 ' 或 "
            safe_zh = escape_for_quote(zh, tok.quote)
        return text[:tok.inner_start] + safe_zh + text[tok.inner_end:]

    # S1: (line, idx) 精确命中
    if line_hint is not None and idx_hint is not None:
        candidates = [t for t in tokens if t.start_line <= line_hint <= t.end_line]
        on_line = [t for t in candidates if t.start_line == line_hint == t.end_line]
        if on_line and 0 <= idx_hint < len(on_line):
            t = on_line[idx_hint]
            inner = text[t.inner_start:t.inner_end]
            if normalize_newlines(inner) == en_norm:
                region = _region_of_token(t, py_spans, label_spans, screen_spans)
                if region == 'python':
                    raise PythonRegionMatch("S1-line-idx")
                return replace_in_token(t), "S1-line-idx", region
        exact = [t for t in candidates if normalize_newlines(text[t.inner_start:t.inner_end]) == en_norm]
        if len(exact) == 1:
            region = _region_of_token(exact[0], py_spans, label_spans, screen_spans)
            if region == 'python':
                raise PythonRegionMatch("S1-line-exact")
            return replace_in_token(exact[0]), "S1-line-exact", region

    # S2: 以 line 为中心 ±200 行窗口
    if line_hint is not None:
        window = 200
        nearby = [t for t in tokens if abs(((t.start_line + t.end_line)//2) - line_hint) <= window]
        exact = [t for t in nearby if normalize_newlines(text[t.inner_start:t.inner_end]) == en_norm]
        if len(exact) == 1:
            region = _region_of_token(exact[0], py_spans, label_spans, screen_spans)
            if region == 'python':
                raise PythonRegionMatch("S2-nearby")
            return replace_in_token(exact[0]), "S2-nearby", region

    # S3: 通过 anchor_prev / anchor_next 锚定区域
    if anchor_prev or anchor_next:
        start_idx = 0
        end_idx = len(text)
        if anchor_prev:
            i = text.find(anchor_prev)
            if i != -1:
                start_idx = i + len(anchor_prev)
        if anchor_next:
            j = text.find(anchor_next, start_idx)
            if j != -1:
                end_idx = j
        region_tokens = [t for t in tokens if t.start < end_idx and t.end > start_idx]
        exact = [t for t in region_tokens if normalize_newlines(text[t.inner_start:t.inner_end]) == en_norm]
        if len(exact) == 1:
            region = _region_of_token(exact[0], py_spans, label_spans, screen_spans)
            if region == 'python':
                raise PythonRegionMatch("S3-anchors")
            return replace_in_token(exact[0]), "S3-anchors", region
        if len(exact) > 1:
            mid = (start_idx + end_idx) // 2
            t = min(exact, key=lambda x: abs((x.inner_start + x.inner_end)//2 - mid))
            region = _region_of_token(t, py_spans, label_spans, screen_spans)
            if region == 'python':
                raise PythonRegionMatch("S3-anchors-closest")
            return replace_in_token(t), "S3-anchors-closest", region

        # S3.5: 基于语义签名的匹配（仅当提供 id_semantic 时）
        # 在锚定区域内对所有 token 的内容计算语义签名，唯一命中则采用
        # 说明：签名旨在跨轻微样式/空白改动保持稳定
        if _norm_sig is not None and _comp_sig is not None:
            target_sig = _comp_sig(en)
            cand = []
            for t in region_tokens:
                inner = text[t.inner_start:t.inner_end]
                sig = _comp_sig(inner)
                if sig == target_sig:
                    cand.append(t)
            if len(cand) == 1:
                region = _region_of_token(cand[0], py_spans, label_spans, screen_spans)
                if region == 'python':
                    raise PythonRegionMatch("S3.5-semantic")
                return replace_in_token(cand[0]), "S3.5-semantic", region

    # S4: 全文件唯一精确匹配
    exact_all = [t for t in tokens if normalize_newlines(text[t.inner_start:t.inner_end]) == en_norm]
    if len(exact_all) == 1:
        region = _region_of_token(exact_all[0], py_spans, label_spans, screen_spans)
        if region == 'python':
            raise PythonRegionMatch("S4-unique")
        return replace_in_token(exact_all[0]), "S4-unique", region

    # S5: 引号包裹的一次性替换
    # S5: 在非 python 区域内按引号类型唯一命中
    def _tok_by_quote(tokens_list: list[Token], quote: str, triple: bool):
        cand = []
        for t in tokens_list:
            if t.quote == quote and bool(t.is_triple) == bool(triple):
                inner = normalize_newlines(text[t.inner_start:t.inner_end])
                if inner == en_norm:
                    r = _region_of_token(t, py_spans, label_spans, screen_spans)
                    if r != 'python':
                        cand.append((t, r))
        return cand
    # 三引号优先，再普通引号
    tlist = _tok_by_quote(tokens, '"""', True)
    if len(tlist) == 1:
        t, region = tlist[0]
        new_text = text[:t.inner_start] + sanitize_triple_content(zh, '"""') + text[t.inner_end:]
        return new_text, "S5-replace-once", region
    tlist = _tok_by_quote(tokens, "'''", True)
    if len(tlist) == 1:
        t, region = tlist[0]
        new_text = text[:t.inner_start] + sanitize_triple_content(zh, "'''") + text[t.inner_end:]
        return new_text, "S5-replace-once", region
    tlist = _tok_by_quote(tokens, '"', False)
    if len(tlist) == 1:
        t, region = tlist[0]
        new_text = text[:t.inner_start] + escape_for_quote(zh, '"') + text[t.inner_end:]
        return new_text, "S5-replace-once", region
    tlist = _tok_by_quote(tokens, "'", False)
    if len(tlist) == 1:
        t, region = tlist[0]
        new_text = text[:t.inner_start] + escape_for_quote(zh, "'") + text[t.inner_end:]
        return new_text, "S5-replace-once", region

    # S6: 轻量模糊匹配（近邻窗口，唯一且高分）
    if _fuzz is not None and line_hint is not None:
        window = 200
        nearby = [t for t in tokens if abs(((t.start_line + t.end_line)//2) - line_hint) <= window]
        scores: list[tuple[int, Token]] = []
        for t in nearby:
            inner = normalize_newlines(text[t.inner_start:t.inner_end])
            score = _fuzz.token_set_ratio(en_norm, inner)
            if score >= 92:
                # 仅在非 python 区块评分
                if _region_of_token(t, py_spans, label_spans, screen_spans) != 'python':
                    scores.append((score, t))
        # 唯一最高且差值明显（避免同分多处）
        if scores:
            scores.sort(key=lambda x: (-x[0], x[1].inner_start))
            top = scores[0]
            if len(scores) == 1 or (len(scores) >= 2 and top[0] - scores[1][0] >= 3):
                t = top[1]
                region = _region_of_token(t, py_spans, label_spans, screen_spans)
                new_text = replace_in_token(t)
                return new_text, f"S6-fuzzy-nearby({top[0]})", region

    raise ValueError("not_found_or_ambiguous")

def load_translations(path: Path):
    trans = {}
    with path.open("r", encoding="utf-8") as f:
        for ln, line in enumerate(f,1):
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except (json.JSONDecodeError, ValueError) as e:
                print(f"[WARN] bad JSON at line {ln}: {e}")
                continue
            _id = obj.get("id") or obj.get("id_hash")
            if not _id and all(k in obj for k in ("file","line","idx")):
                _id = f"{obj['file']}:{obj['line']}:{obj['idx']}"
            if not _id:
                continue
            zh = None
            for k in TRANS_KEYS:
                v = obj.get(k)
                if v is not None and str(v).strip() != "":
                    zh = str(v); break
            if zh is None:
                continue
            en = obj.get("en","")
            trans[_id] = {"zh": zh, "en": en, "obj": obj}
    return trans

def replace_nth_on_line(line: str, idx: int, zh: str) -> tuple[str, bool]:
    """替换行中第 idx 个字符串字面量

    Args:
        line: 源代码行
        idx: 字符串字面量索引（0-based）
        zh: 替换的中文文本

    Returns:
        (新行内容, 是否成功替换)
    """
    # 验证索引有效性
    if idx < 0:
        return line, False

    # 先双引号,再单引号 —— 与抽取顺序一致
    m = list(DQ_RE.finditer(line))
    if idx < len(m):
        a, b = m[idx].start(1), m[idx].end(1)
        return line[:a] + escape_for_quote(zh, '"') + line[b:], True

    idx2 = idx - len(m)
    m2 = list(SQ_RE.finditer(line))
    if 0 <= idx2 < len(m2):
        a, b = m2[idx2].start(1), m2[idx2].end(1)
        return line[:a] + escape_for_quote(zh, "'") + line[b:], True

    return line, False

def patch_file_text(text: str, rel: str, trans: dict):
    # 选出属于本文件的翻译项
    items = []
    for _id, rec in trans.items():
        if isinstance(_id, str) and _id.startswith(rel + ":"):
            items.append((_id, rec))
        elif rec["obj"].get("file") == rel:
            items.append((_id, rec))
    if not items:
        return text, 0, 0

    lines = text.splitlines(keepends=False)
    applied = 0
    warn = 0

    # 第一轮：按 (line, idx) 精确替换
    for _id, rec in items:
        o = rec["obj"]
        line_no, idx = None, None
        if "line" in o and "idx" in o:
            line_no, idx = int(o["line"]), int(o["idx"])
        else:
            parts = _id.split(":")
            try:
                line_no, idx = int(parts[-2]), int(parts[-1])
            except (ValueError, IndexError):
                line_no, idx = None, None

        if line_no is not None and 1 <= line_no <= len(lines):
            new_line, ok = replace_nth_on_line(lines[line_no-1], idx, rec["zh"])
            if ok:
                if rec.get("en"):
                    if set(PH_RE.findall(rec["en"])) != set(PH_RE.findall(rec["zh"])):
                        warn += 1
                lines[line_no-1] = new_line
                applied += 1

    # 第二轮：对没有位置信息的项,用 en + 引号 做精确一次替换(防误爆)
    for _id, rec in items:
        o = rec["obj"]
        has_loc = ("line" in o and "idx" in o) or (isinstance(_id, str) and _id.startswith(rel + ":"))
        if has_loc:
            continue
        en = rec.get("en","")
        if not en:
            continue
        zh = rec["zh"]
        done = False
        for q in ['"', "'"]:
            needle = q + en + q
            for i, ln in enumerate(lines):
                pos = ln.find(needle)
                if pos != -1:
                    lines[i] = ln.replace(needle, q + escape_for_quote(zh, q) + q, 1)
                    if set(PH_RE.findall(en)) != set(PH_RE.findall(zh)):
                        warn += 1
                    applied += 1
                    done = True
                    break
            if done:
                break

    return "\n".join(lines), applied, warn

def patch_file_advanced(text: str, rel: str, trans: dict, report_rows: list):
    """高级模式: 按文件分组,使用五级匹配策略"""
    items = []
    for _id, rec in trans.items():
        if isinstance(_id, str) and _id.startswith(rel + ":"):
            items.append((_id, rec))
        elif rec["obj"].get("file") == rel:
            items.append((_id, rec))
    if not items:
        return text, 0

    file_modified = False

    def sort_key(x):
        return (x[1]["obj"].get("line", 10**9), x[1]["obj"].get("idx", 10**9), x[0])
    items_sorted = sorted(items, key=sort_key)

    for _id, rec in items_sorted:
        o = rec["obj"]
        en = rec.get("en", "")
        zh = rec["zh"]
        line_hint = o.get("line", None)
        idx_hint = o.get("idx", None)
        anchor_prev = o.get("anchor_prev", None)
        anchor_next = o.get("anchor_next", None)

        # 占位符检查
        en_pl = set(PH_RE.findall(en))
        zh_pl = set(PH_RE.findall(zh))
        if en_pl != zh_pl:
            report_rows.append((_id, rel, "WARN", "placeholder_mismatch", f"{sorted(en_pl)} vs {sorted(zh_pl)}"))

        try:
            new_text, method, region = apply_patch_advanced(text, en, zh, line_hint, idx_hint, anchor_prev, anchor_next)
            if new_text != text:
                text = new_text
                file_modified = True
                report_rows.append((_id, rel, "OK", method, f"region={region}"))
            else:
                report_rows.append((_id, rel, "NOOP", "unchanged", f"region={region}"))
        except PythonRegionMatch as e:
            report_rows.append((_id, rel, "WARN", "python_region_skip", e.method))
        except ValueError:
            report_rows.append((_id, rel, "FAIL", "not_found_or_ambiguous", ""))

    return text, 1 if file_modified else 0

def main():
    ap = argparse.ArgumentParser(description="Patch translated JSONL back into .zh.rpy files.")
    ap.add_argument("project_root", help="Ren'Py project root")
    ap.add_argument("translated_jsonl", help="Translated JSONL")
    ap.add_argument("-o","--out", default="out_patch", help="Output directory (mirror tree with .zh.rpy)")
    ap.add_argument("--glob", default="**/*.rpy", help="Glob for files to include")
    ap.add_argument("--exclude-dirs", default="tl", help="Comma-separated dir names to exclude (e.g. 'tl,saves,cache')")
    ap.add_argument("--advanced", action="store_true", help="使用高级五级匹配策略(支持三引号/上下文锚点)")
    ap.add_argument("--dry-run", action="store_true", help="只生成报告,不写文件")
    ap.add_argument("--backup", action="store_true", help="修改前写入 .bak 备份")
    ap.add_argument("--workers", default=0, help="并行进程数(仅用于高级模式；可设为整数或 auto；0 表示不并行)")
    ap.add_argument("--chunk-size", type=int, default=0, help="高级模式分片大小：每个进程处理的文件数（>0 启用）")
    # TL 模式参数（官方 i18n）
    ap.add_argument("--tl-mode", action="store_true", help="输出到 tl/<lang>/strings.rpy 的官方翻译格式，而不是生成 .zh.rpy 镜像")
    ap.add_argument("--lang", default="zh_CN", help="TL 语言目录名（默认 zh_CN）")
    ap.add_argument("--tl-per-file", action="store_true", default=True, help="将 strings 分拆为 tl/<lang>/<相对路径>.rpy（默认开启；取消请显式传 --no-tl-per-file）")
    ap.add_argument("--no-tl-per-file", action="store_false", dest="tl_per_file", help="禁用按源文件拆分，输出单一 strings.rpy")
    args = ap.parse_args()

    root = Path(args.project_root).resolve()
    out_root = Path(args.out).resolve()
    out_root.mkdir(parents=True, exist_ok=True)

    trans = load_translations(Path(args.translated_jsonl).resolve())
    exclude_dirs = set([d.strip() for d in args.exclude_dirs.split(",") if d.strip()])
    def is_excluded(path: Path) -> bool:
        try:
            rel_parts = path.relative_to(root).parts
        except ValueError:
            rel_parts = path.parts
        return any(part in exclude_dirs for part in rel_parts)

    files = sorted([
        p for p in root.glob(args.glob)
        if p.is_file() and p.suffix.lower()==".rpy" and not is_excluded(p)
    ])
    
    count_files = 0
    total_applied = 0
    total_warn = 0
    report_rows = []

    # TL 模式：收集 old→new 映射，统一生成 tl/<lang>/strings.rpy
    if args.tl_mode:
        # 收集本工程所有与译文匹配的项（按文件可选分组）
        grouped = {}
        for _id, rec in trans.items():
            o = rec["obj"]
            rel = o.get("file")
            en = rec.get("en", "")
            zh = rec["zh"]
            if not rel:
                # 兼容 id: file:line:idx
                if isinstance(_id, str) and ":" in _id:
                    rel = _id.split(":", 1)[0]
            if not rel:
                continue
            grouped.setdefault(rel if args.tl_per_file else "__ALL__", []).append((en, zh, _id))

        def quote_block(s: str) -> str:
            # 多行/包含换行 → 三引号；否则双引号并转义内双引号
            if "\n" in s:
                # 使用三引号，避免常见转义；极端包含 """ 的情况较罕见
                return '"""' + s.replace('\\', '\\\\') + '"""'
            else:
                return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'

        def build_strings_content(pairs: list, lang: str) -> str:
            # 去重，保留首次出现；冲突（同 old 多译）以注释标记
            seen = {}
            conflicts = {}
            for en, zh, _id in pairs:
                key = en
                if key not in seen:
                    seen[key] = (zh, [_id])
                else:
                    if seen[key][0] != zh:
                        conflicts.setdefault(key, set()).add(seen[key][0])
                        conflicts[key].add(zh)
                        seen[key][1].append(_id)
            lines = []
            lines.append(f"translate {lang} strings:")
            for en, (zh, _ids) in seen.items():
                if en.strip() == "":
                    continue
                if en in conflicts:
                    lines.append(f"    # CONFLICT for old: {en!r} → {sorted(list(conflicts[en]))}")
                lines.append(f"    old {quote_block(en)}")
                lines.append(f"    new {quote_block(zh)}")
                lines.append("")
            return "\n".join(lines) + "\n"

        lang = args.lang
        if args.tl_per_file:
            written = 0
            for rel, pairs in sorted(grouped.items()):
                if rel == "__ALL__":
                    continue
                out_path = out_root / "game" / "tl" / lang / (rel + ".rpy")
                content = build_strings_content(pairs, lang)
                if not args.dry_run:
                    _write_text_file(out_path, content, encoding="utf-8")
                written += 1
            print(f"[TL] 写入 {written} 个 per-file strings 脚本到: {out_root / 'game' / 'tl' / lang}")
        else:
            # 单一 strings.rpy
            pairs = grouped.get("__ALL__", [])
            # 如果按文件分组为空，也汇总其余
            if not pairs:
                for k,v in grouped.items():
                    if k != "__ALL__":
                        pairs.extend(v)
            out_path = out_root / "game" / "tl" / lang / "strings.rpy"
            content = build_strings_content(pairs, lang)
            if not args.dry_run:
                _write_text_file(out_path, content, encoding="utf-8")
            print(f"[TL] 写入 strings 脚本: {out_path}")

        print(f"Output root: {out_root}")
        if args.dry_run:
            print("[干运行模式] 未实际写入 tl 文件")
        return

    if args.advanced:
        # 高级模式
        print("[高级模式] 使用五级智能匹配策略")

        # 仅处理有翻译项的文件
        targets = []
        for p in files:
            rel = p.relative_to(root).as_posix()
            if any((isinstance(_id, str) and _id.startswith(rel + ":")) or 
                   (rec["obj"].get("file") == rel) for _id, rec in trans.items()):
                targets.append(p)

        def do_one(p: Path):
            rel = p.relative_to(root).as_posix()
            local_reports = []
            orig_text = p.read_text(encoding="utf-8", errors="ignore")
            patched_text, modified = patch_file_advanced(orig_text, rel, trans, local_reports)
            return rel, orig_text, patched_text, modified, local_reports

        # 解析 workers
        workers_val: int = 0
        if isinstance(args.workers, str):
            if args.workers == "auto":
                c = os.cpu_count() or 1
                workers_val = max(1, c - 1)
            else:
                try:
                    workers_val = int(args.workers)
                except ValueError:
                    workers_val = 0
        else:
            workers_val = int(args.workers)

        results = []
        if workers_val and workers_val > 0:
            if args.chunk_size and args.chunk_size > 0:
                def chunks(lst, n):
                    for i in range(0, len(lst), n):
                        yield lst[i:i+n]

                def do_chunk(chunk_files):
                    local_rows = []
                    modified_count = 0
                    for p in chunk_files:
                        rel = p.relative_to(root).as_posix()
                        orig_text = p.read_text(encoding="utf-8", errors="ignore")
                        patched_text, modified = patch_file_advanced(orig_text, rel, trans, local_rows)
                        if modified:
                            if not args.dry_run:
                                if _safe_write_output(out_root, rel, patched_text):
                                    modified_count += 1
                            else:
                                modified_count += 1
                    return local_rows, modified_count

                with concurrent.futures.ProcessPoolExecutor(max_workers=workers_val) as ex:
                    for lrows, mcnt in ex.map(do_chunk, list(chunks(targets, args.chunk_size))):
                        report_rows.extend(lrows)
                        count_files += mcnt
            else:
                with concurrent.futures.ProcessPoolExecutor(max_workers=workers_val) as ex:
                    for res in ex.map(do_one, targets):
                        results.append(res)
        else:
            for p in targets:
                results.append(do_one(p))

        for rel, _orig_text, patched_text, modified, local_reports in results:
            report_rows.extend(local_reports)
            if modified:
                if not args.dry_run:
                    if _safe_write_output(out_root, rel, patched_text):
                        count_files += 1
                else:
                    count_files += 1

        # 写出报告
        tsv_path = Path(args.translated_jsonl).with_suffix(".patch_report.tsv")
        with tsv_path.open("w", encoding="utf-8", newline="") as rep:
            rep.write("id\tfile\tstatus\tmethod\tmessage\n")
            for r in report_rows:
                rep.write(f"{r[0]}\t{r[1]}\t{r[2]}\t{r[3]}\t{r[4]}\n")
        print(f"详细报告: {tsv_path}")
    else:
        # 简单模式(向后兼容)
        for p in files:
            rel = p.relative_to(root).as_posix()
            text = p.read_text(encoding="utf-8", errors="ignore")
            patched_text, applied, warn = patch_file_text(text, rel, trans)
            if applied or warn:
                if not args.dry_run:
                    if args.backup:
                        p.with_suffix(".bak.rpy").write_text(text, encoding="utf-8")
                    if _safe_write_output(out_root, rel, patched_text):
                        count_files += 1
                else:
                    count_files += 1
            total_applied += applied
            total_warn += warn

        print(f"Patched files written: {count_files}")
        print(f"Applied replacements: {total_applied}, warnings: {total_warn}")

    print(f"Output root: {out_root}")
    if args.dry_run:
        print("[干运行模式] 未实际修改文件")

if __name__ == "__main__":
    main()
