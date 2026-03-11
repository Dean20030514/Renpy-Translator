#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validator —— 对比抽取 JSONL 与 译文 JSONL，并可输出 QA 细则

- 报告缺失/多余条目
- 报告占位符集合不一致（可扩展为计数差异）
- 识别 id / id_hash / (file,line,idx)
- 译文字段名称多重兼容
- 可选输出 QA 报告（文本标签成对、占位符计数、末尾标点一致、换行数一致、长度比）
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import unicodedata
from pathlib import Path


# 添加 src 到路径
_project_root = Path(__file__).parent.parent
if str(_project_root / "src") not in sys.path:
    sys.path.insert(0, str(_project_root / "src"))

# 统一日志
try:
    from renpy_tools.utils.logger import get_logger
    _logger = get_logger("validate")
except ImportError:
    _logger = None
    ValidationError = ValueError

def _log(level: str, msg: str) -> None:
    """统一日志输出"""
    if _logger:
        getattr(_logger, level, _logger.info)(msg)
    elif level in ("warning", "error"):
        print(f"[{level.upper()}] {msg}", file=sys.stderr)
    else:
        print(f"[{level.upper()}] {msg}")

# 统一导入（优先从 placeholder.py）
try:
    from renpy_tools.utils.placeholder import (
        PH_RE,
        ph_set as _ph_set, strip_renpy_tags as _strip_renpy_tags,
        extract_var_name_counts as _extract_var_name_counts,
        compute_semantic_signature as _compute_semantic_signature,
    )
    from renpy_tools.utils.common import (
        TRANS_KEYS,
        load_jsonl, get_id
    )
except ImportError:
    # Fallback（仅用于独立运行时）
    TRANS_KEYS = ("zh", "cn", "zh_cn", "translation", "text_zh", "target", "tgt", "zh_final")
    RENPY_PAIRED_TAGS = frozenset({"i", "b", "u", "color", "a", "size", "font", "alpha"})
    PH_RE = re.compile(
        r"\[[A-Za-z_][A-Za-z0-9_]*\]"
        r"|%(?:\([^)]+\))?[+#0\- ]?\d*(?:\.\d+)?[sdifeEfgGxXo]"
        r"|\{\d+(?:![rsa])?(?::[^{}]+)?\}"
        r"|\{[A-Za-z_][A-Za-z0-9_]*(?:![rsa])?(?::[^{}]+)?\}"
    )
    _ph_set = None
    _strip_renpy_tags = None
    _extract_var_name_counts = None
    _compute_semantic_signature = None
    load_jsonl = None
    get_id = None

TAG_OPEN_RE = re.compile(r"\{(i|b|u|color(?:=[^}]+)?|a(?:=[^}]+)?|size(?:=[^}]+)?|font(?:=[^}]+)?|alpha(?:=[^}]+)?)\}")
TAG_CLOSE_RE = re.compile(r"\{/(i|b|u|color|a|size|font|alpha)\}")
END_PUNCT_EN = re.compile(r"[\.!?\u2026]\s*$")  # . ! ? …
END_PUNCT_ZH = re.compile(r"[。！？……]\s*$")


def _load_jsonl(p):
    """加载 JSONL 文件（兼容函数）"""
    if load_jsonl:
        return load_jsonl(p)
    out = []
    with open(p, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            out.append(json.loads(line))
    return out


def any_id(o):
    """获取条目 ID（兼容函数）"""
    if get_id:
        return get_id(o)
    if o.get("id"): return o["id"]
    if o.get("id_hash"): return o["id_hash"]
    if all(k in o for k in ("file","line","idx")):
        return f"{o['file']}:{o['line']}:{o['idx']}"
    return None

def get_tr(o):
    for k in TRANS_KEYS:
        v = o.get(k)
        if v is not None and str(v).strip() != "":
            return str(v)
    return None

def ph_set(s):
    if _ph_set:
        return _ph_set(s)
    return set(PH_RE.findall(s or ""))

def ph_counter(s: str) -> dict:
    cnt = {}
    for m in PH_RE.findall(s or ""):
        cnt[m] = cnt.get(m, 0) + 1
    return cnt

def strip_tags_for_check(s: str) -> str:
    if _strip_renpy_tags:
        return _strip_renpy_tags(s)
    return re.sub(r"\{/?[A-Za-z_][^}]*\}", "", s or "")

def compute_sig(s: str) -> str:
    if _compute_semantic_signature:
        return _compute_semantic_signature(s)
    t = re.sub(r"\s+", " ", (s or "").strip().lower())
    import hashlib
    return "sig0:" + hashlib.sha1(t.encode("utf-8")).hexdigest()[:12]

# 提取变量名占位（区分于样式标签），如 [name] 和 {player}
if _extract_var_name_counts is None:
    VAR_BRACKET_RE = re.compile(r"\[\s*([A-Za-z_][A-Za-z0-9_]*)\s*\]")
    VAR_BRACE_CAND_RE = re.compile(r"\{([^{}]+)\}")
    STYLE_TAG_PREFIXES = ("i","b","u","color","a","size","font","alpha")

    def extract_var_name_counts(s: str):
        s = s or ""
        counts = {}
        # [name]
        for m in VAR_BRACKET_RE.finditer(s):
            k = m.group(1)
            counts[k] = counts.get(k,0) + 1
        # {name} / {name:...} 排除样式/关闭/带=
        for m in VAR_BRACE_CAND_RE.finditer(s):
            inner = m.group(1).strip()
            if not inner or inner.startswith('/'):
                continue
            if '=' in inner:
                continue
            # 允许 {name} 或 {name:...} → 取冒号前的名字
            mname = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)(?::[^}]*)?$", inner)
            if not mname:
                continue
            name = mname.group(1)
            if name in STYLE_TAG_PREFIXES:
                continue
            counts[name] = counts.get(name,0) + 1
        return counts
else:
    extract_var_name_counts = _extract_var_name_counts

def is_ui_token(text: str, max_len: int, max_words: int) -> bool:
    t = (text or '').strip()
    if not t:
        return False
    if len(t) > max_len:
        return False
    # 占位符存在时视为非 UI，避免误分类
    if any(x in t for x in ['[', ']', '{', '}', '%']):
        return False
    words = [w for w in t.replace('\n', ' ').split(' ') if w]
    return len(words) <= max_words


def display_width(s: str) -> int:
    """Approximate display width: treat East Asian Wide/Fullwidth as 2, others as 1."""
    w = 0
    for ch in s or "":
        ea = unicodedata.east_asian_width(ch)
        if ea in ("W", "F"):
            w += 2
        else:
            w += 1
    return w


def parse_args():
    """解析命令行参数。"""
    ap = argparse.ArgumentParser(description="Validate translated JSONL against extracted JSONL.")
    ap.add_argument("source_jsonl")
    ap.add_argument("translated_jsonl")
    # QA 输出与阈值
    ap.add_argument("--qa-json", help="输出 QA 结果 JSON 文件路径")
    ap.add_argument("--qa-tsv", help="输出 QA 结果 TSV 文件路径")
    ap.add_argument("--len-ratio-min", type=float, default=0.30, help="长度比下限(zh/en)，默认 0.30")
    ap.add_argument("--len-ratio-max", type=float, default=3.50, help="长度比上限(zh/en)，默认 3.50")
    # UI 文案宽松 preset / 规则
    ap.add_argument("--ui-max-len", type=int, default=24, help="将长度<=该值的英文短文本视为 UI 候选（默认 24）")
    ap.add_argument("--ui-max-words", type=int, default=4, help="将词数<=该值的英文短文本视为 UI 候选（默认 4）")
    ap.add_argument("--ignore-ui-punct", action="store_true", help="UI 候选忽略末尾标点不一致")
    ap.add_argument("--ui-len-ratio-min", type=float, default=None, help="UI 候选使用更宽松的长度比下限（不设则使用通用阈值）")
    ap.add_argument("--ui-len-ratio-max", type=float, default=None, help="UI 候选使用更宽松的长度比上限（不设则使用通用阈值）")
    ap.add_argument("--qa-html", help="输出 QA 可视化 HTML（本地静态页）")
    # UI 文案中文宽度上限（用于按钮等控件溢出预警）
    ap.add_argument("--ui-max-width", type=int, default=14, help="UI 中文显示宽度上限（按东亚宽字符=2计算），默认 14")
    # 结构一致性（可选，需提供源码与中文镜像目录）
    ap.add_argument("--project-root", help="项目源码根（用于解析 EN .rpy 结构）")
    ap.add_argument("--zh-mirror", help="中文镜像根（patch 输出目录，包含 <rel>.zh.rpy 文件）")
    ap.add_argument("--strict-structure", action="store_true", help="结构不一致直接计为问题（structure_diff）")
    # 术语一致性
    ap.add_argument("--term-dict", help="术语/人名字典（jsonl/csv 或目录）用于强制一致性校验")
    ap.add_argument("--strict-terms", action="store_true", help="术语不在字典或与字典冲突时标记 term_inconsistent")
    # UI 超宽优化建议
    ap.add_argument("--tm", help="TM jsonl/csv（可提供更短的候选译法）")
    # 语义漂移/孤儿译文检测
    ap.add_argument("--detect-orphans", action="store_true", help="基于语义签名检测孤儿译文与 EN 漂移")
    # 目标语言（预留给多语言扩展）
    ap.add_argument("--lang", default="zh_CN", help="目标语言（默认 zh_CN）")
    # 硬约束（可选）：严格占位符计数/换行数一致
    ap.add_argument("--require-ph-count-eq", action="store_true", help="占位符计数必须一致（不一致即非零退出）")
    ap.add_argument("--require-newline-eq", action="store_true", help="换行数必须一致（不一致即非零退出）")
    # 自动修复
    ap.add_argument("--autofix", help="启用自动修复，输出修复后的 JSONL 到指定路径（占位符/换行/重复标点/标签配对）")
    return ap.parse_args()


def load_and_index_data(args):
    """加载源 JSONL 和译文 JSONL，建立索引。"""
    src = _load_jsonl(args.source_jsonl)
    trn = _load_jsonl(args.translated_jsonl)

    src_map = {}
    for o in src:
        i = any_id(o)
        if i:
            src_map[i] = o

    trn_map = {}
    for o in trn:
        i = any_id(o)
        if not i:
            continue
        t = get_tr(o)
        if t is None:
            continue
        trn_map[i] = o

    missing = [i for i in src_map if i not in trn_map]
    extra = [i for i in trn_map if i not in src_map]
    return src, src_map, trn_map, missing, extra


def load_tm_candidates(tm_path: str | None) -> dict:
    """加载 TM 候选（可选）。"""
    if not tm_path:
        return {}
    tm_cands = {}
    tp = Path(tm_path)
    if tp.suffix.lower() == '.jsonl':
        with tp.open('r', encoding='utf-8', errors='replace') as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    o = json.loads(line)
                except (ValueError, json.JSONDecodeError):
                    continue
                en = (o.get('en') or '').lower()
                cands = o.get('candidates') or []
                if en:
                    tm_cands[en] = [c.get('zh') for c in cands if isinstance(c, dict) and c.get('zh')]
    elif tp.suffix.lower() == '.csv':
        with tp.open('r', encoding='utf-8', newline='', errors='replace') as f:
            r = csv.DictReader(f)
            for row in r:
                en = (row.get('en') or '').lower()
                cj = row.get('candidates_json') or '[]'
                try:
                    cands = json.loads(cj)
                except (ValueError, json.JSONDecodeError):
                    cands = []
                if en:
                    tm_cands[en] = [c.get('zh') for c in cands if isinstance(c, dict) and c.get('zh')]
    return tm_cands


def load_term_dict(term_dict_path: str | None) -> dict:
    """加载术语字典（可选）。"""
    if not term_dict_path:
        return {}
    try:
        from renpy_tools.utils.dict_utils import load_dictionary as _load_dictionary
    except (ImportError, ModuleNotFoundError):
        return {}
    try:
        return _load_dictionary(term_dict_path, case_insensitive=True)
    except (OSError, ValueError, RuntimeError):
        return {}


def validate_item(item_id: str, src_obj: dict, trn_obj: dict, args,
                  tm_cands: dict) -> tuple[dict | None, dict | None, bool]:
    """验证单条译文，返回 (ph_viol_entry, qa_row, hard_fail)。"""
    src_en = src_obj.get("en", "")
    tgt = get_tr(trn_obj) or ""

    ph_viol_entry = None
    hard_fail = False

    # 占位符集合差异
    if ph_set(src_en) != ph_set(tgt):
        ph_viol_entry = {"id": item_id, "src_ph": sorted(ph_set(src_en)), "tgt_ph": sorted(ph_set(tgt))}

    # QA 细则
    issues: list[str] = []

    # 1) 文本标签成对与嵌套合法性
    opens = TAG_OPEN_RE.finditer(tgt)
    closes = TAG_CLOSE_RE.finditer(tgt)
    if len(list(opens)) != len(list(closes)):
        issues.append("tag_pair_mismatch")
    # 栈式校验嵌套
    stack: list[str] = []
    pos = 0
    while True:
        mo = re.search(
            r"\{/(i|b|u|color|a|size|font|alpha)\}"
            r"|\{(i|b|u|color(?:=[^}]+)?|a(?:=[^}]+)?|size(?:=[^}]+)?|font(?:=[^}]+)?|alpha(?:=[^}]+)?)\}",
            tgt[pos:],
        )
        if not mo:
            break
        end = pos + mo.end()
        if tgt[pos + mo.start() + 1] == '/':
            tag = mo.group(1)
            if not stack or stack[-1] != tag:
                issues.append("tag_nesting_invalid")
                break
            stack.pop()
        else:
            name = mo.group(2)
            name = name.split('=', 1)[0] if '=' in name else name
            stack.append(name)
        pos = end
    if stack and "tag_pair_mismatch" not in issues:
        issues.append("tag_pair_mismatch")

    # 2) 占位符计数一致
    src_ph_all = list(PH_RE.findall(src_en))
    tgt_ph_all = list(PH_RE.findall(tgt))
    if len(src_ph_all) != len(tgt_ph_all):
        issues.append("placeholder_count_diff")
        if args.require_ph_count_eq:
            hard_fail = True

    # 2.1) 变量名计数一致（[name] 与 {name}）
    src_vars = extract_var_name_counts(src_en)
    tgt_vars = extract_var_name_counts(tgt)
    if src_vars != tgt_vars:
        issues.append("var_name_count_diff")

    # 3) 末尾标点类别一致
    en_end = bool(END_PUNCT_EN.search(src_en or ""))
    zh_end = bool(END_PUNCT_ZH.search(tgt or ""))
    is_ui = is_ui_token(src_en, args.ui_max_len, args.ui_max_words)
    if not (is_ui and args.ignore_ui_punct):
        if en_end != zh_end:
            issues.append("end_punct_mismatch")

    # 4) 换行数一致
    if (src_en or "").count("\n") != (tgt or "").count("\n"):
        issues.append("newline_count_diff")
        if args.require_newline_eq:
            hard_fail = True

    # 5) 长度比
    en_len = max(1, len(src_en))
    ratio = len(tgt) / en_len
    if is_ui and (args.ui_len_ratio_min is not None or args.ui_len_ratio_max is not None):
        lo = args.ui_len_ratio_min if args.ui_len_ratio_min is not None else args.len_ratio_min
        hi = args.ui_len_ratio_max if args.ui_len_ratio_max is not None else args.len_ratio_max
        if not (lo <= ratio <= hi):
            issues.append("length_ratio_out_of_range")
    else:
        if not (args.len_ratio_min <= ratio <= args.len_ratio_max):
            issues.append("length_ratio_out_of_range")

    # 6) 中英混排空格与全角/半角统一
    if re.search(r"[\u4e00-\u9fff][A-Za-z0-9]", tgt) or re.search(r"[A-Za-z0-9][\u4e00-\u9fff]", tgt):
        issues.append("mixed_spacing_missing")
    if re.search(r"\d(?:[A-Za-z%℃℉°])", tgt) or re.search(r"(?:[A-Za-z%℃℉°])\d", tgt):
        issues.append("mixed_spacing_missing")
    if re.search(r"[\uFF01-\uFF5E]", tgt):
        issues.append("fullwidth_forms_present")
    if re.search(r"[\u4e00-\u9fff][:;,\.!\?][\u4e00-\u9fff]", tgt):
        issues.append("halfwidth_punct_adjacent_cn")

    # 7) 超长中文 UI
    if is_ui:
        zh_width = display_width(tgt)
        if zh_width > args.ui_max_width:
            issues.append("ui_overlong_zh_width")

    # 8) 占位符多重集一致
    spc = ph_counter(src_en)
    tpc = ph_counter(tgt)
    if spc != tpc:
        issues.append("placeholder_multiset_diff")

    # 9) 关键元素保留率
    st = strip_tags_for_check(src_en)
    tt = strip_tags_for_check(tgt)
    pres_fields = _check_preservation(st, tt, issues)

    # 构建 qa_row
    qa_row = None
    if issues:
        qa_row = {
            "id": item_id,
            "issues": ";".join(issues),
            "en_len": len(src_en),
            "zh_len": len(tgt),
            "ratio": round(ratio, 3),
        }
        qa_row.update(pres_fields)
        # UI 超宽：提供短同义词候选 + 折行建议
        if "ui_overlong_zh_width" in issues and src_en:
            _add_ui_suggestions(qa_row, src_en, tgt, tm_cands)

    return ph_viol_entry, qa_row, hard_fail


def _check_preservation(src_stripped: str, tgt_stripped: str,
                        issues: list[str]) -> dict:
    """检查数字/缩写/URL/邮箱保留率，在 issues 中追加问题，返回保留率字段。"""
    fields: dict[str, str] = {}
    nums = re.findall(r"\b\d+(?:[.,]\d+)?\b", src_stripped)
    acrs = re.findall(r"\b[A-Z]{2,}\b", src_stripped)
    urls = re.findall(r"(?:https?://|www\.)\S+", src_stripped)
    emails = re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", src_stripped)

    def _preserved(tokens, hay):
        total = len(tokens)
        hit = sum(1 for t in tokens if t and t in hay)
        return hit, total

    checks = [
        (nums, "number_preserve_incomplete", "preserve_numbers"),
        (acrs, "acronym_preserve_incomplete", "preserve_acronyms"),
        (urls, "url_preserve_incomplete", "preserve_urls"),
        (emails, "email_preserve_incomplete", "preserve_emails"),
    ]
    for tokens, issue_key, field_key in checks:
        if tokens:
            hit, total = _preserved(tokens, tgt_stripped)
            if hit < total:
                issues.append(issue_key)
                fields[field_key] = f"{hit}/{total}"
    return fields


def _add_ui_suggestions(qa_row: dict, src_en: str, tgt: str,
                        tm_cands: dict):
    """为 UI 超宽项添加短候选和折行建议。"""
    key = src_en.lower()
    alts = []
    cur_w = display_width(tgt)
    for cand in (tm_cands.get(key) or [])[:8]:
        if cand and display_width(cand) < cur_w:
            alts.append(cand)
    if alts:
        qa_row["alt_candidates"] = ";".join(sorted(set(alts))[:5])

    # 折行建议
    points = []
    for ch in "·、，。：；！？ （）() /-":
        for pos in [m.start() for m in re.finditer(re.escape(ch), tgt)]:
            points.append(pos)
    if not points and len(tgt) >= 6:
        points = [len(tgt) // 2]
    if points:
        picks = []
        for kk in (1, 2, 3):
            target_pos = int(len(tgt) * kk / (kk + 1))
            nearest = min(points, key=lambda p, tp=target_pos: abs(p - tp))
            picks.append(nearest)
        picks = sorted(set(picks))[:3]
        demo = tgt
        offset = 0
        for p in picks:
            demo = demo[:p + offset] + "▏" + demo[p + offset:]
            offset += 1
        qa_row["wrap_points"] = demo


def validate_terms(trn_map: dict, src_map: dict, term_map: dict,
                   qa_rows: list[dict]):
    """术语一致性检查。"""
    if not term_map:
        return
    for item_id, trn_obj in trn_map.items():
        src_obj = src_map.get(item_id)
        if not src_obj:
            continue
        src_en = src_obj.get("en", "")
        tgt = get_tr(trn_obj) or ""
        if not tgt:
            continue
        key = (src_en or "").lower()
        en_len = max(1, len(src_en))
        if key in term_map:
            exp = term_map[key]
            if exp and str(tgt) != str(exp):
                qa_rows.append({
                    "id": item_id,
                    "issues": "term_inconsistent",
                    "en_len": len(src_en),
                    "zh_len": len(tgt),
                    "ratio": round(len(tgt) / en_len, 3),
                })
        else:
            qa_rows.append({
                "id": item_id,
                "issues": "term_inconsistent",
                "en_len": len(src_en),
                "zh_len": len(tgt),
                "ratio": round(len(tgt) / en_len, 3),
            })


def validate_structure(args, qa_rows: list[dict]):
    """结构一致性校验（可选，需 project-root 与 zh-mirror）。"""
    if not args.project_root or not args.zh_mirror:
        return
    try:
        from renpy_tools.diff.parser import parse_rpy
    except (ImportError, ModuleNotFoundError):
        return

    root = Path(args.project_root)
    zh_root = Path(args.zh_mirror)
    for p in root.rglob("*.rpy"):
        try:
            rel = p.relative_to(root).as_posix()
        except (ValueError, OSError):
            rel = p.name
        zh_path = (zh_root / rel).with_suffix(".zh.rpy")
        if not zh_path.exists():
            qa_rows.append({
                "id": rel,
                "issues": "structure_diff:file_missing_in_zh",
                "en_len": 0, "zh_len": 0, "ratio": 0.0
            })
            continue
        try:
            en_p = parse_rpy(str(p))
            zh_p = parse_rpy(str(zh_path))
        except (OSError, ValueError, RuntimeError):
            continue
        _cmp_blocks('label', en_p.labels, zh_p.labels, rel, zh_p, qa_rows)
        _cmp_blocks('screen', en_p.screens, zh_p.screens, rel, zh_p, qa_rows)


def _cmp_blocks(kind: str, en_map: dict, zh_map: dict,
                rel_path: str, zh_parsed, qa_rows: list[dict]):
    """比较 EN/ZH 的同名 label/screen 块。"""
    for name in sorted(set(en_map.keys()) - set(zh_map.keys())):
        qa_rows.append({
            "id": f"{rel_path}::{kind}::{name}",
            "issues": "structure_diff:block_missing_in_zh",
            "en_len": 0, "zh_len": 0, "ratio": 0.0
        })
    for name in sorted(set(en_map.keys()) & set(zh_map.keys())):
        e = en_map[name]
        z = zh_map[name]
        em = getattr(e, 'menus', []) or []
        zm = getattr(z, 'menus', []) or []
        if len(em) != len(zm):
            qa_rows.append({
                "id": f"{rel_path}::{kind}::{name}",
                "issues": "structure_diff:menu_count_mismatch",
                "en_len": len(em), "zh_len": len(zm), "ratio": 0.0
            })
        for k in ("jump", "call", "call_screen", "menu", "imagebutton_jumps"):
            ce = e.counts.get(k, 0)
            cz = z.counts.get(k, 0)
            if ce != cz:
                qa_rows.append({
                    "id": f"{rel_path}::{kind}::{name}",
                    "issues": f"structure_diff:{k}_count_mismatch",
                    "en_len": ce, "zh_len": cz, "ratio": 0.0
                })
        for tgt_label, _line in z.imagebutton_jumps:
            if tgt_label not in zh_parsed.labels and tgt_label not in zh_parsed.screens:
                qa_rows.append({
                    "id": f"{rel_path}::{kind}::{name}",
                    "issues": "structure_diff:imagebutton_jump_target_missing",
                    "en_len": 0, "zh_len": 0, "ratio": 0.0
                })


def detect_orphans_and_drift(src_map: dict, trn_map: dict, extra: list[str]):
    """基于语义签名检测孤儿译文与 EN 漂移。"""
    src_sig_to_id: dict[str, set] = {}
    for sid, so in src_map.items():
        sig = compute_sig(so.get("en") or "")
        src_sig_to_id.setdefault(sig, set()).add(sid)

    orphan_rows = []
    for oid in extra:
        to = trn_map.get(oid)
        if not to:
            continue
        sig = compute_sig(to.get('en') or '')
        cand = sorted(src_sig_to_id.get(sig, []))
        if cand:
            orphan_rows.append({"old_id": oid, "new_ids": cand})

    drift_rows = []
    for cid in sorted(set(src_map.keys()) & set(trn_map.keys())):
        so = src_map[cid]
        to = trn_map[cid]
        if not so or not to:
            continue
        if compute_sig(so.get('en') or '') != compute_sig(to.get('en') or ''):
            drift_rows.append({"id": cid})

    if orphan_rows or drift_rows:
        print(json.dumps({
            "semantic_orphans": orphan_rows,
            "semantic_drifts": drift_rows,
        }, ensure_ascii=False, indent=2))


def generate_reports(qa_rows: list[dict], summary: dict, args):
    """生成 QA 报告（JSON / TSV / HTML）。"""
    print(json.dumps(summary, ensure_ascii=False, indent=2))

    if args.qa_json:
        with open(args.qa_json, 'w', encoding='utf-8') as jf:
            json.dump({"qa_rows": qa_rows}, jf, ensure_ascii=False, indent=2)

    if args.qa_tsv:
        with open(args.qa_tsv, 'w', encoding='utf-8', newline='') as tf:
            w = csv.writer(tf, delimiter='\t')
            w.writerow([
                "id", "issues", "en_len", "zh_len", "ratio",
                "preserve_numbers", "preserve_acronyms", "preserve_urls", "preserve_emails",
                "alt_candidates", "wrap_points",
            ])
            for r in qa_rows:
                w.writerow([
                    r["id"], r["issues"], r["en_len"], r["zh_len"], r["ratio"],
                    r.get("preserve_numbers", ""), r.get("preserve_acronyms", ""),
                    r.get("preserve_urls", ""), r.get("preserve_emails", ""),
                    r.get("alt_candidates", ""), r.get("wrap_points", ""),
                ])

    if getattr(args, "qa_html", None):
        _write_qa_html(args.qa_html, qa_rows, summary)


def _write_qa_html(html_path: str, qa_rows: list[dict], summary: dict):
    """生成纯静态 HTML QA 报表。"""
    issue_types = sorted(set(
        i for row in qa_rows for i in row.get("issues", "").split(";") if i
    ))
    html_template = """<!doctype html>
<html lang=zh>
<meta charset=utf-8>
<title>QA 报表</title>
<style>
body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial,'Noto Sans',sans-serif; margin:16px}
.pill{display:inline-block;margin:0 6px 6px 0;padding:4px 8px;border-radius:12px;border:1px solid #ccc;cursor:pointer}
.pill.active{background:#2563eb;color:#fff;border-color:#2563eb}
table{border-collapse:collapse;width:100%}
th,td{border:1px solid #e5e7eb;padding:6px 8px;text-align:left;font-size:13px}
thead th{background:#f8fafc;position:sticky;top:0}
.muted{color:#6b7280}
</style>
<h2>QA 报表</h2>
<div class=muted>总条目：__TOTAL__ | 缺失：__MISSING__ | 多余：__EXTRA__ | 占位符告警：__PH__</div>
<h3>筛选</h3>
<div id=filters>
  <div id=issues></div>
  <div style="margin:8px 0">
    文件/ID 包含：<input id=kw type=text placeholder="关键字" style="padding:4px 8px;width:280px"> 
    <button id=clear>清空</button>
  </div>
  <div class=muted>提示：issues 可多选；支持按文件名、目录或完整 id 子串过滤。</div>
  <hr>
</div>
<table id=tbl>
  <thead>
    <tr><th>ID</th><th>Issues</th><th>en_len</th><th>zh_len</th><th>ratio</th></tr>
  </thead>
  <tbody></tbody>
</table>
<script>
const ALL_ROWS = __DATA__;
let activeIssues = new Set();
const byId = (s)=>document.getElementById(s);
function renderPills(){
  const wrap = byId('issues');
  wrap.innerHTML = '';
  const types = __TYPES__;
  for (const t of types){
    const span = document.createElement('span');
    span.className = 'pill' + (activeIssues.has(t)?' active':'');
    span.textContent = t;
    span.onclick = ()=>{ if(activeIssues.has(t)) activeIssues.delete(t); else activeIssues.add(t); renderPills(); renderTable(); };
    wrap.appendChild(span);
  }
}
function matches(row){
  if (activeIssues.size){
    const set = new Set((row.issues||'').split(';').filter(Boolean));
    let ok=false; for(const t of activeIssues){ if(set.has(t)){ ok=true; break; } }
    if(!ok) return false;
  }
  const kw = byId('kw').value.trim();
  if (kw){ return (row.id||'').includes(kw); }
  return true;
}
function renderTable(){
  const tb = byId('tbl').querySelector('tbody');
  tb.innerHTML = '';
  const rows = ALL_ROWS.filter(matches);
  for (const r of rows){
    const tr = document.createElement('tr');
    tr.innerHTML = `<td>${r.id||''}</td><td>${r.issues||''}</td><td>${r.en_len||''}</td><td>${r.zh_len||''}</td><td>${r.ratio||''}</td>`;
    tb.appendChild(tr);
  }
}
byId('kw').addEventListener('input', ()=> renderTable());
byId('clear').onclick = ()=>{ byId('kw').value=''; activeIssues.clear(); renderPills(); renderTable(); };
renderPills();
renderTable();
</script>
</html>"""
    html = (html_template
            .replace("__TOTAL__", str(len(qa_rows)))
            .replace("__MISSING__", str(summary['missing_count']))
            .replace("__EXTRA__", str(summary['extra_count']))
            .replace("__PH__", str(summary['placeholder_violation_count']))
            .replace("__DATA__", json.dumps(qa_rows, ensure_ascii=False))
            .replace("__TYPES__", json.dumps(issue_types, ensure_ascii=False)))
    with open(html_path, 'w', encoding='utf-8') as hf:
        hf.write(html)
    print(f"QA HTML: {html_path}")


def main():
    args = parse_args()
    src, src_map, trn_map, missing, extra = load_and_index_data(args)
    tm_cands = load_tm_candidates(getattr(args, 'tm', None))
    term_map = load_term_dict(getattr(args, 'term_dict', None))

    ph_viol: list[dict] = []
    qa_rows: list[dict] = []
    hard_fail = False

    for item_id, trn_obj in trn_map.items():
        src_obj = src_map.get(item_id)
        if not src_obj:
            continue
        pv, qr, hf = validate_item(item_id, src_obj, trn_obj, args, tm_cands)
        if pv:
            ph_viol.append(pv)
        if qr:
            qa_rows.append(qr)
        if hf:
            hard_fail = True

    # 术语一致性
    if args.strict_terms and term_map:
        validate_terms(trn_map, src_map, term_map, qa_rows)

    # 结构一致性
    validate_structure(args, qa_rows)

    # 汇总
    summary = {
        "total_src_items": len(src),
        "total_translated_nonempty": len(trn_map),
        "missing_count": len(missing),
        "extra_count": len(extra),
        "placeholder_violation_count": len(ph_viol),
        "qa_issue_count": len(qa_rows),
        "missing_sample": missing[:50],
        "extra_sample": extra[:50],
        "placeholder_violation_sample": ph_viol[:30],
    }

    # 输出报告
    generate_reports(qa_rows, summary, args)

    # 自动修复
    if getattr(args, "autofix", None):
        try:
            from renpy_tools.core.validator import MultiLevelValidator
        except ImportError:
            _log("error", "无法导入 MultiLevelValidator，跳过自动修复")
        else:
            validator = MultiLevelValidator()
            # 构建 source 和 target 列表
            src_list = []
            tgt_list = []
            trn_full = _load_jsonl(args.translated_jsonl)
            trn_by_id = {}
            for o in trn_full:
                i = any_id(o)
                if i:
                    trn_by_id[i] = o
            for item_id in trn_by_id:
                src_obj = src_map.get(item_id)
                if not src_obj:
                    continue
                tgt_val = get_tr(trn_by_id[item_id])
                if tgt_val is None:
                    continue
                src_list.append({"id": item_id, "en": src_obj.get("en", "")})
                tgt_list.append({"id": item_id, "zh": tgt_val})
            
            fixed_target, fix_report = validator.validate_with_autofix(src_list, tgt_list)
            
            # 将修复后的值写回完整对象
            fixed_by_id = {f["id"]: f.get("zh", "") for f in fixed_target}
            autofix_path = Path(args.autofix)
            autofix_path.parent.mkdir(parents=True, exist_ok=True)
            fix_count = 0
            with autofix_path.open("w", encoding="utf-8") as af:
                for o in trn_full:
                    i = any_id(o)
                    if i and i in fixed_by_id:
                        old_zh = get_tr(o)
                        new_zh = fixed_by_id[i]
                        if old_zh != new_zh:
                            fix_count += 1
                        out_o = dict(o)
                        out_o["zh"] = new_zh
                        af.write(json.dumps(out_o, ensure_ascii=False) + "\n")
                    else:
                        af.write(json.dumps(o, ensure_ascii=False) + "\n")
            
            fix_summary = fix_report.get("summary", {})
            _log("info", f"自动修复完成: {fix_count} 条已修改 → {autofix_path}")
            if fix_summary:
                _log("info", f"  修复统计: {json.dumps(fix_summary, ensure_ascii=False)}")

    # 孤儿/漂移检测
    if getattr(args, "detect_orphans", False):
        detect_orphans_and_drift(src_map, trn_map, extra)

    # 退出码
    if args.strict_structure:
        if any((r.get("issues") or "").startswith("structure_diff") for r in qa_rows):
            raise SystemExit(3)
    if hard_fail:
        raise SystemExit(2)

if __name__ == "__main__":
    main()
