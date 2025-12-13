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
import unicodedata
from pathlib import Path

# 从公共模块导入翻译字段键
try:
    from renpy_tools.utils.common import TRANS_KEYS as _TRANS_KEYS  # type: ignore
except (ImportError, ModuleNotFoundError):
    _TRANS_KEYS = None
TRANS_KEYS = _TRANS_KEYS or ("zh", "cn", "zh_cn", "translation", "text_zh", "target", "tgt", "zh_final")

# 可选：复用通用占位符/变量/签名工具
try:
    from renpy_tools.utils.placeholder import (
        PH_RE as _PH_RE,
        ph_set as _ph_set,
        extract_var_name_counts as _extract_var_name_counts,
        strip_renpy_tags as _strip_renpy_tags,
        compute_semantic_signature as _compute_semantic_signature,
    )  # type: ignore
except (ImportError, ModuleNotFoundError):
    _PH_RE = None
    _ph_set = None
    _extract_var_name_counts = None
    _strip_renpy_tags = None
    _compute_semantic_signature = None

PH_RE = _PH_RE or re.compile(
    r"\[[A-Za-z_][A-Za-z0-9_]*\]"                       # [name]
    r"|%(?:\([^)]+\))?[+#0\- ]?\d*(?:\.\d+)?[sdifeEfgGxXo]"  # %s, %02d, %(name)s, %.2f, %x, %o, ...
    r"|\{\d+(?:![rsa])?(?::[^{}]+)?\}"                             # {0} / {0:...} / {0!r}
    r"|\{[A-Za-z_][A-Za-z0-9_]*(?:![rsa])?(?::[^{}]+)?\}"                # {name!r:>8}
)

TAG_OPEN_RE = re.compile(r"\{(i|b|u|color(?:=[^}]+)?|a(?:=[^}]+)?|size(?:=[^}]+)?|font(?:=[^}]+)?|alpha(?:=[^}]+)?)\}")
TAG_CLOSE_RE = re.compile(r"\{/(i|b|u|color|a|size|font|alpha)\}")
END_PUNCT_EN = re.compile(r"[\.!?\u2026]\s*$")  # . ! ? …
END_PUNCT_ZH = re.compile(r"[。！？……]\s*$")

def load_jsonl(p):
    out = []
    with open(p, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            out.append(json.loads(line))
    return out

def any_id(o):
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


def main():
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
    args = ap.parse_args()

    src = load_jsonl(args.source_jsonl)
    trn = load_jsonl(args.translated_jsonl)

    src_map = {}
    for o in src:
        i = any_id(o)
        if i: src_map[i] = o

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

    # 语义签名索引（用于孤儿/漂移检测）
    src_sig_to_id = {}
    if getattr(args, "detect_orphans", False):
        for sid, so in src_map.items():
            sig = compute_sig(so.get("en") or "")
            src_sig_to_id.setdefault(sig, set()).add(sid)

    ph_viol = []
    qa_rows = []
    # 读取 TM 候选（可选）
    tm_cands = {}
    if getattr(args, "tm", None):
        tp = Path(args.tm)
        if tp.suffix.lower() == '.jsonl':
            with tp.open('r', encoding='utf-8', errors='ignore') as f:
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
            with tp.open('r', encoding='utf-8', newline='', errors='ignore') as f:
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
    term_map = {}
    if args.term_dict:
        try:
            from renpy_tools.utils.dict_utils import load_dictionary as _load_dictionary  # type: ignore
        except (ImportError, ModuleNotFoundError):
            _load_dictionary = None
        if _load_dictionary is not None:
            try:
                term_map = _load_dictionary(args.term_dict, case_insensitive=True)
            except (OSError, ValueError, RuntimeError):
                term_map = {}
    hard_fail = False
    for i, to in trn_map.items():
        so = src_map.get(i)
        if not so: 
            continue
        src_en = so.get("en","")
        tgt = get_tr(to) or ""
        # 占位符集合差异
        if ph_set(src_en) != ph_set(tgt):
            ph_viol.append({"id": i, "src_ph": sorted(ph_set(src_en)), "tgt_ph": sorted(ph_set(tgt))})
        # QA 细则
        issues = []
        # 1) 文本标签成对与嵌套合法性
        opens = TAG_OPEN_RE.finditer(tgt)
        closes = TAG_CLOSE_RE.finditer(tgt)
        # 简单数量检查
        if len(list(opens)) != len(list(closes)):
            issues.append("tag_pair_mismatch")
        # 栈式校验嵌套
        stack = []
        i = 0
        while True:
            mo = re.search(r"\{/(i|b|u|color|a|size|font|alpha)\}|\{(i|b|u|color(?:=[^}]+)?|a(?:=[^}]+)?|size(?:=[^}]+)?|font(?:=[^}]+)?|alpha(?:=[^}]+)?)\}", tgt[i:])
            if not mo:
                break
            s = i + mo.start()
            e = i + mo.end()
            if tgt[s+1] == '/':
                tag = mo.group(1)
                if not stack or stack[-1] != tag:
                    issues.append("tag_nesting_invalid")
                    break
                stack.pop()
            else:
                name = mo.group(2)
                name = name.split('=',1)[0] if '=' in name else name
                stack.append(name)
            i = e
        if stack:
            # 仍有未闭合
            if "tag_pair_mismatch" not in issues:
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
        # 3) 末尾标点类别一致（英 vs 中）
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
        # UI 使用更宽松的长度比（若提供）
        if is_ui and (args.ui_len_ratio_min is not None or args.ui_len_ratio_max is not None):
            lo = args.ui_len_ratio_min if args.ui_len_ratio_min is not None else args.len_ratio_min
            hi = args.ui_len_ratio_max if args.ui_len_ratio_max is not None else args.len_ratio_max
            if not (lo <= ratio <= hi):
                issues.append("length_ratio_out_of_range")
        else:
            if not (args.len_ratio_min <= ratio <= args.len_ratio_max):
                issues.append("length_ratio_out_of_range")
        # 6) 中英混排空格与全角/半角统一（仅 WARN，不自动更改）
        # 6.1) 缺少中英/数字与中文之间的空格
        # - 中文紧邻英文或数字（无空格）
        if re.search(r"[\u4e00-\u9fff][A-Za-z0-9]", tgt) or re.search(r"[A-Za-z0-9][\u4e00-\u9fff]", tgt):
            issues.append("mixed_spacing_missing")
        # - 数字与单位/百分号等紧邻（如 50kg / 100%），建议留空格
        if re.search(r"\d(?:[A-Za-z%℃℉°])", tgt) or re.search(r"(?:[A-Za-z%℃℉°])\d", tgt):
            issues.append("mixed_spacing_missing")
        # 6.2) 存在全角 ASCII 形式（＂，：，Ａ，１ 等），建议统一为半角
        if re.search(r"[\uFF01-\uFF5E]", tgt):
            issues.append("fullwidth_forms_present")
        # 6.3) 半角英文标点紧邻中文（如 ： ; , . ! ? 之间无空格且夹在中文中间），建议用全角或调整排版
        if re.search(r"[\u4e00-\u9fff][:;,\.!\?][\u4e00-\u9fff]", tgt):
            issues.append("halfwidth_punct_adjacent_cn")
        # 7) 超长中文 UI（以显示宽度估算）
        if is_ui:
            zh_width = display_width(tgt)
            if zh_width > args.ui_max_width:
                issues.append("ui_overlong_zh_width")
        # 8) 占位符多重集一致（严格计数比较）
        spc = ph_counter(src_en)
        tpc = ph_counter(tgt)
        if spc != tpc:
            issues.append("placeholder_multiset_diff")
        # 9) 关键元素保留率（数字/大写缩写/URL/邮箱）
        st = strip_tags_for_check(src_en)
        tt = strip_tags_for_check(tgt)
        nums = re.findall(r"\b\d+(?:[.,]\d+)?\b", st)
        acrs = re.findall(r"\b[A-Z]{2,}\b", st)
        urls = re.findall(r"(?:https?://|www\.)\S+", st)
        emails = re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", st)
        def _preserved(tokens, hay):
            if not tokens:
                return (0,0)
            total = len(tokens)
            hit = 0
            for tkn in tokens:
                if tkn and (tkn in hay):
                    hit += 1
            return (hit, total)
        pres_numbers = None
        pres_acronyms = None
        pres_urls = None
        pres_emails = None
        if nums:
            h, tot = _preserved(nums, tt)
            pres_numbers = (h, tot)
            if h < tot:
                issues.append("number_preserve_incomplete")
        if acrs:
            h, tot = _preserved(acrs, tt)
            pres_acronyms = (h, tot)
            if h < tot:
                issues.append("acronym_preserve_incomplete")
        if urls:
            h, tot = _preserved(urls, tt)
            pres_urls = (h, tot)
            if h < tot:
                issues.append("url_preserve_incomplete")
        if emails:
            h, tot = _preserved(emails, tt)
            pres_emails = (h, tot)
            if h < tot:
                issues.append("email_preserve_incomplete")
        row = None
        if issues:
            row = {
                "id": i,
                "issues": ";".join(issues),
                "en_len": len(src_en),
                "zh_len": len(tgt),
                "ratio": round(ratio, 3)
            }
            # UI 超宽：提供短同义词候选（来自 TM）和折行建议
            if "ui_overlong_zh_width" in issues and src_en:
                key = (src_en or "").lower()
                alts = []
                cur_w = display_width(tgt)
                for cand in (tm_cands.get(key) or [])[:8]:
                    if cand and display_width(cand) < cur_w:
                        alts.append(cand)
                if alts:
                    row["alt_candidates"] = ";".join(sorted(set(alts))[:5])
            # 保留率字段（仅在有对应该类问题时附带输出）
            if pres_numbers is not None and "number_preserve_incomplete" in issues:
                row["preserve_numbers"] = f"{pres_numbers[0]}/{pres_numbers[1]}"
            if pres_acronyms is not None and "acronym_preserve_incomplete" in issues:
                row["preserve_acronyms"] = f"{pres_acronyms[0]}/{pres_acronyms[1]}"
            if pres_urls is not None and "url_preserve_incomplete" in issues:
                row["preserve_urls"] = f"{pres_urls[0]}/{pres_urls[1]}"
            if pres_emails is not None and "email_preserve_incomplete" in issues:
                row["preserve_emails"] = f"{pres_emails[0]}/{pres_emails[1]}"
                # 折行建议：按中文标点优先 + 中点/空格，其次中间位置
                s = tgt
                points = []
                for ch in "·、，。：；！？ （）() /-":
                    for pos in [m.start() for m in re.finditer(re.escape(ch), s)]:
                        points.append(pos)
                if not points and len(s) >= 6:
                    points = [len(s)//2]
                if points:
                    # 选择 1-3 个靠近等分的位置
                    picks = []
                    for kk in (1,2,3):
                        idx_pos = int(len(s)*kk/(kk+1))
                        # 手写最小值，避免闭包变量警告
                        nearest = points[0]
                        bestd = abs(points[0]-idx_pos)
                        for pnt in points[1:]:
                            d = abs(pnt - idx_pos)
                            if d < bestd:
                                bestd = d
                                nearest = pnt
                        picks.append(nearest)
                    picks = sorted(set(picks))[:3]
                    # 用 ▏ 标注建议点
                    demo = s
                    offset = 0
                    for p in picks:
                        demo = demo[:p+offset] + "▏" + demo[p+offset:]
                        offset += 1
                    row["wrap_points"] = demo
            qa_rows.append(row)
        # 术语一致性（可选）
        if args.strict_terms and term_map is not None:
            key = (src_en or "").lower()
            if key in term_map:
                exp = term_map.get(key)
                if exp and tgt and str(tgt) != str(exp):
                    qa_rows.append({
                        "id": i,
                        "issues": "term_inconsistent",
                        "en_len": len(src_en),
                        "zh_len": len(tgt),
                        "ratio": round(ratio, 3)
                    })
            else:
                if tgt:
                    qa_rows.append({
                        "id": i,
                        "issues": "term_inconsistent",
                        "en_len": len(src_en),
                        "zh_len": len(tgt),
                        "ratio": round(ratio, 3)
                    })

    # 结构一致性（可选）
    if args.project_root and args.zh_mirror:
        try:
            from renpy_tools.diff.parser import parse_rpy  # type: ignore
        except (ImportError, ModuleNotFoundError):
            parse_rpy = None  # type: ignore
        if parse_rpy is not None:
            root = Path(args.project_root)
            zh_root = Path(args.zh_mirror)
            # 遍历源码下的 .rpy，与 zh 镜像对应 <rel>.zh.rpy
            for p in root.rglob("*.rpy"):
                try:
                    rel = p.relative_to(root).as_posix()
                except (ValueError, OSError):
                    rel = p.name
                zh_path = (zh_root / rel).with_suffix(".zh.rpy")
                if not zh_path.exists():
                    # 中文缺失整个文件，结构差异
                    qa_rows.append({
                        "id": rel,
                        "issues": "structure_diff:file_missing_in_zh",
                        "en_len": 0,
                        "zh_len": 0,
                        "ratio": 0.0
                    })
                    continue
                try:
                    en_p = parse_rpy(str(p))
                    zh_p = parse_rpy(str(zh_path))
                except (OSError, ValueError, RuntimeError):
                    continue
                # 比较每个同名块
                def cmp_blocks(kind: str, en_map: dict, zh_map: dict, rel_path: str, zh_parsed):
                    # 缺失块
                    for name in sorted(set(en_map.keys()) - set(zh_map.keys())):
                        qa_rows.append({
                            "id": f"{rel_path}::{kind}::{name}",
                            "issues": "structure_diff:block_missing_in_zh",
                            "en_len": 0, "zh_len": 0, "ratio": 0.0
                        })
                    # 对齐块
                    for name in sorted(set(en_map.keys()) & set(zh_map.keys())):
                        e = en_map[name]; z = zh_map[name]
                        # 菜单数量对比
                        em = getattr(e, 'menus', []) or []
                        zm = getattr(z, 'menus', []) or []
                        if len(em) != len(zm):
                            qa_rows.append({
                                "id": f"{rel_path}::{kind}::{name}",
                                "issues": "structure_diff:menu_count_mismatch",
                                "en_len": len(em), "zh_len": len(zm), "ratio": 0.0
                            })
                        # 各指令计数
                        for k in ("jump","call","call_screen","menu","imagebutton_jumps"):
                            ce = e.counts.get(k,0)
                            cz = z.counts.get(k,0)
                            if ce != cz:
                                qa_rows.append({
                                    "id": f"{rel_path}::{kind}::{name}",
                                    "issues": f"structure_diff:{k}_count_mismatch",
                                    "en_len": ce, "zh_len": cz, "ratio": 0.0
                                })
                        # imagebutton Jump 目标存在性（在 zh 中检查）
                        for tgt, _line in z.imagebutton_jumps:
                            if tgt not in zh_parsed.labels and tgt not in zh_parsed.screens:
                                qa_rows.append({
                                    "id": f"{rel_path}::{kind}::{name}",
                                    "issues": "structure_diff:imagebutton_jump_target_missing",
                                    "en_len": 0, "zh_len": 0, "ratio": 0.0
                                })
                cmp_blocks('label', en_p.labels, zh_p.labels, rel, zh_p)
                cmp_blocks('screen', en_p.screens, zh_p.screens, rel, zh_p)

    summary = {
        "total_src_items": len(src),
        "total_translated_nonempty": len(trn_map),
        "missing_count": len(missing),
        "extra_count": len(extra),
        "placeholder_violation_count": len(ph_viol),
        "qa_issue_count": len(qa_rows),
        "missing_sample": missing[:50],
        "extra_sample": extra[:50],
        "placeholder_violation_sample": ph_viol[:30]
    }

    print(json.dumps(summary, ensure_ascii=False, indent=2))

    # 输出 QA 报告（可选）
    if args.qa_json:
        with open(args.qa_json, 'w', encoding='utf-8') as jf:
            json.dump({"qa_rows": qa_rows}, jf, ensure_ascii=False, indent=2)
    if args.qa_tsv:
        with open(args.qa_tsv, 'w', encoding='utf-8', newline='') as tf:
            w = csv.writer(tf, delimiter='\t')
            # 扩展列：保留率 + UI 超宽候选与折行
            w.writerow([
                "id","issues","en_len","zh_len","ratio",
                "preserve_numbers","preserve_acronyms","preserve_urls","preserve_emails",
                "alt_candidates","wrap_points"
            ])
            for r in qa_rows:
                w.writerow([
                    r["id"], r["issues"], r["en_len"], r["zh_len"], r["ratio"],
                    r.get("preserve_numbers",""), r.get("preserve_acronyms",""), r.get("preserve_urls",""), r.get("preserve_emails",""),
                    r.get("alt_candidates", ""), r.get("wrap_points", "")
                ])
    if getattr(args, "qa_html", None):
        # 生成纯静态 HTML（内嵌数据 + 过滤交互）
        html_path = args.qa_html
        issue_types = sorted(set(i for row in qa_rows for i in row.get("issues","" ).split(";") if i))
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
                 .replace("__TYPES__", json.dumps(issue_types, ensure_ascii=False))
                 )
        with open(html_path, 'w', encoding='utf-8') as hf:
            hf.write(html)
        print(f"QA HTML: {html_path}")

    # 孤儿译文 + 语义漂移摘要（可选输出到控制台）
    if getattr(args, "detect_orphans", False):
        orphan_rows = []
        drift_rows = []
        # 孤儿：译文中存在但源文中不存在，且其 EN 语义签名在源文出现在其他 id
        for oid in extra:
            to = trn_map.get(oid)
            if not to:
                continue
            sig = compute_sig(to.get('en') or '')
            cand = sorted(src_sig_to_id.get(sig, []))
            if cand:
                orphan_rows.append({"old_id": oid, "new_ids": cand})
        # 漂移：同 id，但 trn.en 与 src.en 的签名不同
        for cid in sorted(set(src_map.keys()) & set(trn_map.keys())):
            so = src_map[cid]; to = trn_map[cid]
            if not so or not to:
                continue
            if compute_sig(so.get('en') or '') != compute_sig(to.get('en') or ''):
                drift_rows.append({"id": cid})
        if orphan_rows or drift_rows:
            print(json.dumps({
                "semantic_orphans": orphan_rows,
                "semantic_drifts": drift_rows
            }, ensure_ascii=False, indent=2))

    # 严格结构模式：发现结构问题时以非零退出
    if args.strict_structure:
        if any((r.get("issues") or "").startswith("structure_diff") for r in qa_rows):
            raise SystemExit(3)

    # 硬约束触发时返回非零
    if hard_fail:
        raise SystemExit(2)

if __name__ == "__main__":
    main()
