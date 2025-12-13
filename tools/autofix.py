#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
autofix.py — 批量自动修复常见中英混排/标点/全角问题，并尽量对齐换行数。

支持修复：
- mixed_spacing_missing：中英/数字与中文之间自动插入空格
- fullwidth_forms_present：全角 ASCII 转半角
- end_punct_mismatch：按英文结尾标点映射中文标点
- newline_count_diff：在简单场景对齐换行（0↔0、1↔1），多行复杂场景保守跳过

用法：
  python tools/autofix.py <source_jsonl> -o <out_jsonl> --tsv <changes.tsv>
可选：--enable <列表> 限定修复类型
"""
from __future__ import annotations
import argparse, json, csv, re
from pathlib import Path

# 尝试导入通用工具函数
try:
    from renpy_tools.utils.common import get_zh, TRANS_KEYS  # type: ignore
except (ImportError, ModuleNotFoundError):
    TRANS_KEYS = ("zh","cn","zh_cn","translation","text_zh","target","tgt")
    
    def get_zh(o: dict):
        for k in TRANS_KEYS:
            v = o.get(k)
            if v is not None and str(v).strip() != "":
                return k, str(v)
        return None, None

FW_START, FW_END = ord('\uFF01'), ord('\uFF5E')

def to_halfwidth(s: str) -> str:
    out = []
    for ch in s:
        code = ord(ch)
        if 0xFF01 <= code <= 0xFF5E:
            out.append(chr(code - 0xFEE0))
        elif code == 0x3000:  # 全角空格
            out.append(' ')
        else:
            out.append(ch)
    return ''.join(out)

def fix_mixed_spacing(s: str) -> str:
    # 中文与英文/数字/单位之间补空格（两向）
    s = re.sub(r"([\u4e00-\u9fff])([A-Za-z0-9%℃℉°])", r"\1 \2", s)
    s = re.sub(r"([A-Za-z0-9%℃℉°])([\u4e00-\u9fff])", r"\1 \2", s)
    return s

def zh_end_punct_from_en(en: str) -> str | None:
    en = en.strip()
    if not en:
        return None
    if en.endswith('...') or en.endswith('\u2026'):
        return '……'
    if en.endswith('!'): return '！'
    if en.endswith('?'): return '？'
    if en.endswith('.') : return '。'
    return None

def fix_end_punct(en: str, zh: str) -> str:
    need = zh_end_punct_from_en(en)
    if not need:
        return zh
    z = zh.rstrip()
    if not z:
        return zh
    # 若已是中文结尾，跳过
    if z.endswith(('。','！','？','……')):
        return zh
    # 若以半角 .!? 结尾，替换为中文
    if z.endswith('.'):
        z = z[:-1] + '。'
    elif z.endswith('!'):
        z = z[:-1] + '！'
    elif z.endswith('?'):
        z = z[:-1] + '？'
    else:
        z = z + need
    # 保留原末尾空白
    return z + zh[len(zh.rstrip()):]

def fix_newline(en: str, zh: str) -> str:
    en_n = en.count('\n')
    zh_n = zh.count('\n')
    if en_n == zh_n:
        return zh
    # 若英文无换行，中文有 → 合并为一行
    if en_n == 0 and zh_n > 0:
        return re.sub(r"\s*\n\s*", " ", zh)
    # 若英文 1 行内含 1 个换行，中文无 → 尝试插入一个换行
    if en_n == 1 and zh_n == 0 and len(zh) >= 4:
        mid = len(zh)//2
        # 在最近的标点或空格处断开
        punct = [m.start() for m in re.finditer(r"[，、。：；！？\s]", zh)]
        if punct:
            cut = min(punct, key=lambda p: abs(p-mid))
            return zh[:cut+1].rstrip() + "\n" + zh[cut+1:].lstrip()
        return zh
    # 其他多换行复杂场景 → 保守不动
    return zh

def main():
    ap = argparse.ArgumentParser(description="Autofix common QA issues in translated JSONL")
    ap.add_argument("translated_jsonl")
    ap.add_argument("-o","--out", required=True)
    ap.add_argument("--tsv", help="输出变更明细 TSV")
    ap.add_argument("--enable", nargs="*", default=[
        "mixed_spacing_missing","fullwidth_forms_present","end_punct_mismatch","newline_count_diff"
    ], help="启用的修复类别")
    args = ap.parse_args()

    src = Path(args.translated_jsonl)
    out = Path(args.out)
    report_rows = []
    applied = 0

    with src.open('r', encoding='utf-8', errors='ignore') as fin, out.open('w', encoding='utf-8') as fout:
        for line in fin:
            if not line.strip():
                continue
            try:
                o = json.loads(line)
            except (ValueError, json.JSONDecodeError):
                continue
            k, zh = get_zh(o)
            if not k or not zh:
                fout.write(json.dumps(o, ensure_ascii=False) + "\n")
                continue
            before = zh
            en = o.get('en') or ''
            fixes = []
            s = zh
            if "fullwidth_forms_present" in args.enable:
                ns = to_halfwidth(s)
                if ns != s:
                    s = ns; fixes.append('fullwidth_forms_present')
            if "mixed_spacing_missing" in args.enable:
                ns = fix_mixed_spacing(s)
                if ns != s:
                    s = ns; fixes.append('mixed_spacing_missing')
            if "end_punct_mismatch" in args.enable:
                ns = fix_end_punct(en, s)
                if ns != s:
                    s = ns; fixes.append('end_punct_mismatch')
            if "newline_count_diff" in args.enable:
                ns = fix_newline(en, s)
                if ns != s:
                    s = ns; fixes.append('newline_count_diff')
            if s != zh:
                o[k] = s
                applied += 1
                report_rows.append([o.get('id') or o.get('id_hash') or '', before, s, ';'.join(fixes)])
            fout.write(json.dumps(o, ensure_ascii=False) + "\n")

    print(json.dumps({"applied": applied, "out": str(out)}, ensure_ascii=False))
    if args.tsv and report_rows:
        with Path(args.tsv).open('w', encoding='utf-8', newline='') as tf:
            w = csv.writer(tf, delimiter='\t')
            w.writerow(["id","before","after","fixes"])
            w.writerows(report_rows)

if __name__ == '__main__':
    main()
