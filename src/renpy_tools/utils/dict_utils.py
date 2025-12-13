from __future__ import annotations
import json, csv
from pathlib import Path
from typing import Dict


def load_dictionary(dict_path: str | Path, case_insensitive: bool = True) -> Dict[str, str]:
    """
    读取 JSONL/CSV（或目录）中的术语/短 UI 文案映射，返回 {en->zh} 字典。
    - JSONL 字段优先：variant_en/canonical_en/en/english → zh/zh_final/cn/chinese
    - CSV 字段优先：variant_en/canonical_en/en/english → zh/zh_final/cn/chinese
    - 若传入目录，将合并其中所有 *.jsonl/*.csv
    """
    def norm(s: str) -> str:
        return s.lower() if case_insensitive else s

    mapping: Dict[str, str] = {}

    def add_entry(en: str | None, zh: str | None):
        if not en or not zh:
            return
        key = norm(en.strip())
        if key and zh:
            mapping.setdefault(key, zh)

    def load_jsonl(p: Path):
        with p.open('r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    obj = json.loads(line)
                except (ValueError, json.JSONDecodeError):
                    continue
                en = obj.get('variant_en') or obj.get('canonical_en') or obj.get('en') or obj.get('english')
                zh = obj.get('zh') or obj.get('zh_final') or obj.get('cn') or obj.get('chinese')
                add_entry(en, zh)
                if obj.get('canonical_en') and obj.get('zh'):
                    add_entry(obj['canonical_en'], obj['zh'])

    def load_csv(p: Path):
        with p.open('r', encoding='utf-8', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                en = row.get('variant_en') or row.get('canonical_en') or row.get('en') or row.get('english')
                zh = row.get('zh') or row.get('zh_final') or row.get('cn') or row.get('chinese')
                add_entry(en, zh)
                ce = row.get('canonical_en')
                if ce and zh:
                    add_entry(ce, zh)

    path = Path(dict_path)
    if path.is_dir():
        for p in path.iterdir():
            if p.suffix.lower() == '.jsonl':
                load_jsonl(p)
            elif p.suffix.lower() == '.csv':
                load_csv(p)
    else:
        if path.suffix.lower() == '.jsonl':
            load_jsonl(path)
        elif path.suffix.lower() == '.csv':
            load_csv(path)
        else:
            raise ValueError(f"Unsupported dictionary format: {path}")

    return mapping
