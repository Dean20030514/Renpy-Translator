#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
merge.py — 合并 LLM 翻译结果回到 JSONL，并检测缺失/冲突

要求 LLM 输出每行至少包含：id, zh（或 translation/target/tgt）。
特性：
- 兼容目录输入：遍历目录中所有 *.jsonl 合并
- 检测缺失（原始 JSONL 中有、LLM 缺失）
- 检测冲突（同一 id 多个不同译文），输出 conflict.tsv
- 合并策略：仅在原对象无译文时才写入 zh（避免覆盖人工/字典/TM 已有）
"""

import argparse
import json
import csv
from pathlib import Path

# 尝试导入通用工具函数
try:
    from renpy_tools.utils import get_id, get_zh, ph_multiset, TRANS_KEYS  # type: ignore
    _HAS_UTILS = True
except (ImportError, ModuleNotFoundError):
    _HAS_UTILS = False
    # 回退定义
    import re
    
    TRANS_KEYS = ("zh", "cn", "zh_cn", "translation", "text_zh", "target", "tgt")
    _PH_RE = re.compile(
        r"\[[A-Za-z_][A-Za-z0-9_]*\]|%(?:\([^)]+\))?[+#0\- ]?\d*(?:\.\d+)?[sdifeEfgGxXo]|"
        r"\{\d+(?:![rsa])?(?::[^{}]+)?\}|\{[A-Za-z_][A-Za-z0-9_]*(?:![rsa])?(?::[^{}]+)?\}"
    )
    
    def get_id(o: dict):
        if o.get("id"):
            return o["id"]
        if o.get("id_hash"):
            return o["id_hash"]
        if all(k in o for k in ("file", "line", "idx")):
            return f"{o['file']}:{o['line']}:{o['idx']}"
        return None
    
    def get_zh(o: dict):
        for k in TRANS_KEYS:
            v = o.get(k)
            if v is not None and str(v).strip() != "":
                return k, str(v)
        return None, None
    
    def ph_multiset(s: str) -> dict[str, int]:
        """Fallback: Count placeholder occurrences"""
        cnt: dict[str, int] = {}
        for m in _PH_RE.findall(s or ""):
            cnt[m] = cnt.get(m, 0) + 1
        return cnt


def extract_zh(o: dict):
    """提取译文内容（只返回值，不返回字段名）"""
    _, value = get_zh(o)
    return value


def load_llm_dir(p: Path) -> dict:
    """
    Load translations from LLM output directory.
    
    Args:
        p: Path to JSONL file or directory containing JSONL files
        
    Returns:
        Dictionary mapping id to set of translations
    """
    merged = {}
    files = []
    if p.is_dir():
        files = sorted([x for x in p.glob("*.jsonl")])
    else:
        files = [p]
    for f in files:
        with f.open("r", encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                try:
                    o = json.loads(line)
                except (ValueError, json.JSONDecodeError):
                    continue
                _id = o.get("id")
                if not _id:
                    continue
                zh = extract_zh(o)
                if zh is None:
                    continue
                merged.setdefault(_id, set()).add(zh)
    return merged


def main():
    ap = argparse.ArgumentParser(description="Merge LLM translated JSONL into original JSONL, with checks")
    ap.add_argument("source_jsonl", help="原始 JSONL（将据此保留所有字段）")
    ap.add_argument("llm_path", help="LLM 输出的 jsonl 文件或目录")
    ap.add_argument("-o", "--out", required=True, help="合并后的输出 JSONL")
    ap.add_argument("--conflict-tsv", help="冲突明细 TSV 输出路径（可选）")
    ap.add_argument("--rejects-tsv", help="格式/校验失败的行输出 TSV（可选，默认与 out 同名 *_rejects.tsv）")
    args = ap.parse_args()

    src = Path(args.source_jsonl)
    llm = Path(args.llm_path)
    out = Path(args.out)

    # 读取 LLM 结果（id -> {zh...}）
    llm_map = load_llm_dir(llm)

    missing_ids = []
    conflict_rows = []

    rejects: list[tuple[str, str, str]] = []  # (id, reason, sample)
    # 建立源 id -> en 映射，供快检
    src_map = {}
    with src.open("r", encoding="utf-8") as fin0:
        for line in fin0:
            if not line.strip():
                continue
            try:
                o = json.loads(line)
            except (ValueError, json.JSONDecodeError):
                continue
            _id = get_id(o)
            if _id:
                src_map[_id] = o.get("en") or ""

    with src.open("r", encoding="utf-8") as fin, out.open("w", encoding="utf-8") as fout:
        for line in fin:
            if not line.strip():
                continue
            try:
                o = json.loads(line)
            except (ValueError, json.JSONDecodeError):
                continue
            _id = get_id(o)
            if not _id:
                fout.write(json.dumps(o, ensure_ascii=False) + "\n")
                continue
            has_any_zh = extract_zh(o) is not None
            zhs = llm_map.get(_id)
            if not zhs:
                # LLM 未覆盖此 id
                if not has_any_zh:
                    missing_ids.append(_id)
                fout.write(json.dumps(o, ensure_ascii=False) + "\n")
                continue
            if len(zhs) > 1:
                # 冲突：多种译文
                conflict_rows.append((_id, " ; ".join(sorted(zhs))))
            if not has_any_zh:
                # 仅在空译时写入（避免覆盖人工/TM）
                new_o = dict(o)
                cand = sorted(zhs)[0]
                # 快检：占位符与换行数一致
                src_en = src_map.get(_id) or ""
                if src_en:
                    if ph_multiset(src_en) != ph_multiset(cand):
                        rejects.append((_id, "placeholder_multiset_diff", cand))
                        fout.write(json.dumps(o, ensure_ascii=False) + "\n")
                        continue
                    if (src_en or "").count("\n") != (cand or "").count("\n"):
                        rejects.append((_id, "newline_count_diff", cand))
                        fout.write(json.dumps(o, ensure_ascii=False) + "\n")
                        continue
                new_o["zh"] = cand
                new_o["prefilled"] = True
                new_o["prefilled_from"] = "llm"
                fout.write(json.dumps(new_o, ensure_ascii=False) + "\n")
            else:
                fout.write(json.dumps(o, ensure_ascii=False) + "\n")

    print(json.dumps({
        "llm_items": sum(len(v) for v in llm_map.values()),
        "missing_ids": len(missing_ids),
        "conflicts": len(conflict_rows),
    }, ensure_ascii=False))

    if args.conflict_tsv and conflict_rows:
        with Path(args.conflict_tsv).open("w", encoding="utf-8", newline="") as tf:
            w = csv.writer(tf, delimiter='\t')
            w.writerow(["id", "candidates"])
            w.writerows(conflict_rows)

    # 写出 rejects
    if rejects:
        rpath = Path(args.rejects_tsv) if args.rejects_tsv else Path(str(out)).with_name(Path(str(out)).stem + "_rejects.tsv")
        with rpath.open("w", encoding="utf-8", newline="") as tf:
            w = csv.writer(tf, delimiter='\t')
            w.writerow(["id", "reason", "zh_candidate"])
            w.writerows(rejects)


if __name__ == "__main__":
    main()
