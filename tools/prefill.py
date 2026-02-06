#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
预填工具 — 用术语/词典对抽取 JSONL 进行半自动预填

用法:
  python prefill.py <source_jsonl> <dict_path_or_dir> -o <out_jsonl> [--max-len 24] [--max-words 4] [--case-insensitive]

说明:
- 从 source_jsonl (如 project_en_for_grok.jsonl) 读取条目, 若英文 en 满足短文本/UI 令牌条件,
  且与字典完全匹配(variant_en/canonical_en), 则写入 zh 预填字段。
- 保留原 id/id_hash/file/line/idx/anchors 等,
  新增字段 prefilled:true 以标记来源。
- 字典支持 JSONL 或 CSV; 若传入目录, 会读取其中所有 *.jsonl/*.csv。
"""

from __future__ import annotations

import json
import csv
import argparse
import sqlite3
import sys
from pathlib import Path
from typing import Dict, Optional, Any, Callable

# 添加 src 到路径
_project_root = Path(__file__).parent.parent
if str(_project_root / "src") not in sys.path:
    sys.path.insert(0, str(_project_root / "src"))

# 可选：彩色日志与进度
try:
    from rich.console import Console  # type: ignore
    from rich.progress import Progress, BarColumn, TimeElapsedColumn  # type: ignore
    _console = Console()
except ImportError:  # 可选依赖
    _console = None

# 尝试导入统一日志和异常
try:
    from renpy_tools.utils.logger import get_logger, FileOperationError
    logger = get_logger("prefill")
except ImportError:
    logger = None
    class FileOperationError(Exception):
        pass

# 可选：使用重构的公用字典加载模块（若存在）
try:
    from renpy_tools.utils.dict_utils import load_dictionary as _load_dictionary_ext  # type: ignore
except (ImportError, ModuleNotFoundError):  # pragma: no cover - 兼容未迁移阶段
    _load_dictionary_ext = None
try:
    from renpy_tools.utils.io import ensure_parent_dir as _ensure_parent_dir  # type: ignore
except (ImportError, ModuleNotFoundError):
    _ensure_parent_dir = None


def _log(msg: str, level: str = "info") -> None:
    """统一日志输出"""
    if logger:
        getattr(logger, level)(msg)
    elif _console:
        style = {"info": "dim", "warning": "yellow", "error": "red"}.get(level, "")
        _console.print(f"[{style}]{msg}[/]")
    else:
        print(msg)


# 读取字典

def load_dictionary(dict_path: str, case_insensitive: bool = True) -> Dict[str, str]:
    """加载字典文件（JSONL 或 CSV）
    
    Args:
        dict_path: 字典文件或目录路径
        case_insensitive: 是否忽略大小写
        
    Returns:
        英文 -> 中文的映射字典
        
    Raises:
        FileOperationError: 文件不存在或格式不支持
    """
    def norm(s: str) -> str:
        return s.lower() if case_insensitive else s

    mapping: Dict[str, str] = {}

    def add_entry(en: str, zh: str) -> None:
        if not en or not zh:
            return
        mapping.setdefault(norm(en.strip()), zh)

    def load_jsonl(p: Path) -> None:
        with p.open('r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    obj = json.loads(line)
                except (ValueError, json.JSONDecodeError):
                    continue
                en = obj.get('variant_en') or obj.get('canonical_en') or obj.get('en') or obj.get('english')
                # 兼容多种中文字段名（本仓库字典 JSONL 使用 zh；CSV 使用 zh_final）
                zh = obj.get('zh') or obj.get('zh_final') or obj.get('cn') or obj.get('chinese')
                add_entry(en, zh)
                # 如同时存在 canonical 与 variant, 两者都加
                if obj.get('canonical_en') and obj.get('zh'):
                    add_entry(obj['canonical_en'], obj['zh'])

    def load_csv(p: Path) -> None:
        with p.open('r', encoding='utf-8', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                en = row.get('variant_en') or row.get('canonical_en') or row.get('en') or row.get('english')
                # 兼容 CSV 中的 zh_final 字段
                zh = row.get('zh') or row.get('zh_final') or row.get('cn') or row.get('chinese')
                add_entry(en, zh)
                ce = row.get('canonical_en')
                if ce and zh:
                    add_entry(ce, zh)

    path = Path(dict_path)
    if not path.exists():
        raise FileOperationError(f"Dictionary path not found: {dict_path}", file_path=path)
        
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


def is_short_token(text: str, max_len: int, max_words: int) -> bool:
    t = (text or '').strip()
    if not t:
        return False
    if len(t) > max_len:
        return False
    # 占位符存在时避免误填
    if any(x in t for x in ['[', ']', '{', '}', '%']):
        return False
    words = [w for w in t.replace('\n', ' ').split(' ') if w]
    return len(words) <= max_words


def main():
    ap = argparse.ArgumentParser(description='Prefill zh using layered dictionaries and/or TM')
    ap.add_argument('source_jsonl', help='Path to extracted project JSONL (e.g., project_en_for_grok.jsonl)')
    ap.add_argument('dict_path', help='Path to dictionary file or directory (jsonl/csv or a folder). If a directory, will auto-detect names/ui/general.csv')
    ap.add_argument('-o', '--out', required=True, help='Output JSONL path for prefilled result')
    ap.add_argument('--max-len', type=int, default=24, help='Max length of English text to consider UI tokens (default 24)')
    ap.add_argument('--max-words', type=int, default=4, help='Max words of English text to consider UI tokens (default 4)')
    ap.add_argument('--case-insensitive', action='store_true', help='Case-insensitive matching for dictionaries/TM')
    # 分层字典（可覆盖自动检测）
    ap.add_argument('--names', help='Path to names.csv/jsonl (strict priority)')
    ap.add_argument('--ui', help='Path to ui.csv/jsonl (short tokens)')
    ap.add_argument('--general', help='Path to general.csv/jsonl (general phrases)')
    # 别名吸收表（alias_en -> canonical_en），会将 canonical 的译名映射到 alias 变体
    ap.add_argument('--alias', help='Optional alias table (csv/jsonl) with columns alias_en, canonical_en')
    # TM 复用
    ap.add_argument('--tm', help='Path to TM jsonl/csv (from build_tm.py)')
    ap.add_argument('--tm-min-len', type=int, default=6, help='Minimum EN length to apply TM exact-match (default 6)')
    # 大字典优化
    ap.add_argument('--dict-backend', choices=['memory','sqlite'], default='memory', help='字典后端：memory(默认) 或 sqlite（只读查询，适合超大词典）')
    ap.add_argument('--sqlite-path', help='当 --dict-backend=sqlite 时，指定 sqlite 路径（默认与输出同目录，文件名 out.jsonl.dict.sqlite）')
    # 可选：使用 Aho-Corasick 对 UI 短词做子串快速匹配（默认关闭，谨慎使用）
    ap.add_argument('--ac-ui-substrings', action='store_true', help='启用 Aho-Corasick 对 UI 字典短词进行子串匹配（可能引入误填，默认关闭）')
    args = ap.parse_args()

    # 优先使用外部模块，未安装则回退到本地实现
    # 加载分层字典
    names_map = {}
    ui_map = {}
    general_map = {}

    def _load_map(p: str | None):
        if not p:
            return {}
        if _load_dictionary_ext is not None:
            return _load_dictionary_ext(p, case_insensitive=args.case_insensitive)
        return load_dictionary(p, case_insensitive=args.case_insensitive)

    dict_path = Path(args.dict_path)
    ui_automaton = None  # optional Aho-Corasick automaton (only for memory backend)
    # sqlite 后端准备
    sqlite_db = None
    def sqlite_put_many(conn, rows, layer):
        with conn:
            conn.executemany("INSERT OR REPLACE INTO dict_entries(layer, key, zh) VALUES(?,?,?)", ((layer, k, v) for k,v in rows))

    def build_sqlite_from_sources(conn, sources: list[tuple[str,str]]):
        conn.execute("CREATE TABLE IF NOT EXISTS dict_entries(layer TEXT, key TEXT, zh TEXT, PRIMARY KEY(layer,key))")
        for layer, path in sources:
            p = Path(path)
            if not p.exists():
                continue
            # 流式读取并落库
            if p.suffix.lower() == '.jsonl':
                batch = []
                with p.open('r', encoding='utf-8', errors='replace') as f:
                    for line in f:
                        if not line.strip():
                            continue
                        try:
                            obj = json.loads(line)
                        except (ValueError, json.JSONDecodeError):
                            continue
                        en = obj.get('variant_en') or obj.get('canonical_en') or obj.get('en') or obj.get('english')
                        zh = obj.get('zh') or obj.get('zh_final') or obj.get('cn') or obj.get('chinese')
                        if en and zh:
                            k = norm(str(en).strip())
                            batch.append((k, str(zh)))
                            if obj.get('canonical_en') and obj.get('zh'):
                                batch.append((norm(str(obj['canonical_en'])), str(obj['zh'])))
                        if len(batch) >= 2000:
                            sqlite_put_many(conn, batch, layer)
                            batch.clear()
                if batch:
                    sqlite_put_many(conn, batch, layer)
            elif p.suffix.lower() == '.csv':
                batch = []
                with p.open('r', encoding='utf-8', newline='', errors='replace') as f:
                    r = csv.DictReader(f)
                    for row in r:
                        en = row.get('variant_en') or row.get('canonical_en') or row.get('en') or row.get('english')
                        zh = row.get('zh') or row.get('zh_final') or row.get('cn') or row.get('chinese')
                        if en and zh:
                            batch.append((norm(str(en).strip()), str(zh)))
                            ce = row.get('canonical_en')
                            if ce and zh:
                                batch.append((norm(str(ce)), str(zh)))
                        if len(batch) >= 2000:
                            sqlite_put_many(conn, batch, layer)
                            batch.clear()
                if batch:
                    sqlite_put_many(conn, batch, layer)

    # 根据后端加载或构建
    if args.dict_backend == 'memory':
        if args.names or args.ui or args.general:
            names_map = _load_map(args.names)
            ui_map = _load_map(args.ui)
            general_map = _load_map(args.general)
        else:
            if dict_path.is_dir():
                cand = {p.name.lower(): str(p) for p in dict_path.iterdir() if p.suffix.lower() in ('.csv','.jsonl')}
                names_map = _load_map(cand.get('names.csv') or cand.get('names.jsonl'))
                ui_map = _load_map(cand.get('ui.csv') or cand.get('ui.jsonl'))
                general_map = _load_map(cand.get('general.csv') or cand.get('general.jsonl'))
                if not (names_map or ui_map or general_map):
                    general_map = _load_map(str(dict_path))
            else:
                general_map = _load_map(str(dict_path))
        # 别名吸收：将 canonical→zh 的映射复制到 alias→zh
        if args.alias:
            alias_p = Path(args.alias)
            alias_pairs: list[tuple[str,str]] = []  # (alias_en, canonical_en)
            def _load_alias_jsonl(p: Path):
                with p.open('r', encoding='utf-8', errors='replace') as f:
                    for line in f:
                        if not line.strip():
                            continue
                        try:
                            o = json.loads(line)
                        except (ValueError, json.JSONDecodeError):
                            continue
                        a = (o.get('alias_en') or o.get('alias') or '').strip()
                        c = (o.get('canonical_en') or o.get('canonical') or '').strip()
                        if a and c:
                            alias_pairs.append((a, c))
            def _load_alias_csv(p: Path):
                with p.open('r', encoding='utf-8', newline='', errors='replace') as f:
                    r = csv.DictReader(f)
                    for row in r:
                        a = (row.get('alias_en') or row.get('alias') or '').strip()
                        c = (row.get('canonical_en') or row.get('canonical') or '').strip()
                        if a and c:
                            alias_pairs.append((a, c))
            if alias_p.exists():
                if alias_p.is_dir():
                    for p in alias_p.iterdir():
                        if p.suffix.lower() == '.jsonl': _load_alias_jsonl(p)
                        elif p.suffix.lower() == '.csv': _load_alias_csv(p)
                else:
                    if alias_p.suffix.lower() == '.jsonl': _load_alias_jsonl(alias_p)
                    elif alias_p.suffix.lower() == '.csv': _load_alias_csv(alias_p)
            # 应用：若 canonical 在任一层存在，复制到 alias
            def _absorb_alias(layer_map: dict[str,str]):
                if not layer_map or not alias_pairs:
                    return
                for a, c in alias_pairs:
                    cv = layer_map.get(norm(c))
                    if cv and norm(a) not in layer_map:
                        layer_map[norm(a)] = cv
            _absorb_alias(names_map)
            _absorb_alias(ui_map)
            _absorb_alias(general_map)

        # 可选：为 UI 构建 Aho-Corasick 自动机（仅内存后端可用）
        ui_automaton = None
        if args.ac_ui_substrings:
            try:
                import ahocorasick  # type: ignore
            except (ImportError, ModuleNotFoundError):
                ahocorasick = None  # type: ignore
            if ui_map and 'ahocorasick' in locals() and ahocorasick is not None:  # type: ignore
                A = ahocorasick.Automaton()  # type: ignore
                for k in ui_map.keys():
                    if k:
                        A.add_word(k, k)  # type: ignore
                A.make_automaton()  # type: ignore
                ui_automaton = A
    else:
        # sqlite 模式：将词典索引到 sqlite，按需查
        sqlite_path = Path(args.sqlite_path) if args.sqlite_path else (Path(args.out).with_suffix('.dict.sqlite'))
        sqlite_db = sqlite3.connect(str(sqlite_path))
        # 汇总来源路径
        sources: list[tuple[str,str]] = []
        def add_src(layer_name, pth):
            if pth:
                sources.append((layer_name, pth))
        if args.names or args.ui or args.general:
            add_src('names', args.names)
            add_src('ui', args.ui)
            add_src('general', args.general if args.general else (str(dict_path) if dict_path.exists() else None))
        else:
            if dict_path.is_dir():
                cand = {p.name.lower(): str(p) for p in dict_path.iterdir() if p.suffix.lower() in ('.csv','.jsonl')}
                add_src('names', cand.get('names.csv') or cand.get('names.jsonl'))
                add_src('ui', cand.get('ui.csv') or cand.get('ui.jsonl'))
                g = cand.get('general.csv') or cand.get('general.jsonl')
                add_src('general', g if g else str(dict_path))
            else:
                add_src('general', str(dict_path))
        build_sqlite_from_sources(sqlite_db, sources)

    def norm(s: str) -> str:
        return s.lower() if args.case_insensitive else s

    # 加载 TM（可选）
    tm_top: dict[str, tuple[str, list[dict]] ] = {}
    if args.tm:
        tp = Path(args.tm)
        if tp.suffix.lower() == '.jsonl':
            with tp.open('r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        o = json.loads(line)
                    except (ValueError, json.JSONDecodeError):
                        continue
                    en = str(o.get('en','')).strip()
                    zh = o.get('top_zh')
                    cands = o.get('candidates') or []
                    if en and zh:
                        tm_top[norm(en)] = (str(zh), cands)
        elif tp.suffix.lower() == '.csv':
            with tp.open('r', encoding='utf-8', newline='') as f:
                r = csv.DictReader(f)
                for row in r:
                    en = (row.get('en') or '').strip()
                    zh = (row.get('top_zh') or '').strip()
                    cj = row.get('candidates_json') or '[]'
                    try:
                        cands = json.loads(cj)
                    except (ValueError, json.JSONDecodeError):
                        cands = []
                    if en and zh:
                        tm_top[norm(en)] = (zh, cands)

    src = Path(args.source_jsonl)
    out = Path(args.out)
    count_total = 0
    count_prefilled = 0
    src_names = 0
    src_ui = 0
    src_general = 0
    src_tm = 0

    # 确保输出目录存在
    if _ensure_parent_dir is not None:
        _ensure_parent_dir(out)
    else:
        out.parent.mkdir(parents=True, exist_ok=True)

    if _console:
        _console.print(f"[bold cyan]Prefilling[/] from [magenta]{src}[/] using dict [magenta]{Path(args.dict_path)}[/]")

    # 预读行数以更好展示进度（若文件极大亦可按流式计数）
    lines = src.read_text(encoding='utf-8', errors='replace').splitlines()
    with out.open('w', encoding='utf-8') as fout:
        iterator = lines
        if _console:
            prog = Progress("{task.description}", BarColumn(), "{task.completed}/{task.total}", TimeElapsedColumn(), console=_console)
            prog.start()
            task = prog.add_task("Scanning", total=len(lines))
        else:
            prog = None
            task = None
        for line in iterator:
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except (ValueError, json.JSONDecodeError):
                continue
            count_total += 1
            en = obj.get('en', '')
            key = norm(en)
            # 若已有译文，跳过
            if any(k in obj and str(obj.get(k) or '').strip() != '' for k in ('zh','cn','zh_cn','translation','text_zh','target','tgt')):
                fout.write(json.dumps(obj, ensure_ascii=False) + "\n")
                if prog is not None and task is not None:
                    prog.advance(task)
                continue
            applied = False
            # 1) 专名表（强制一致）
            if args.dict_backend == 'sqlite' and sqlite_db is not None:
                cur = sqlite_db.execute("SELECT zh FROM dict_entries WHERE layer=? AND key=?", ('names', key))
                row = cur.fetchone()
                zh = row[0] if row else None
            else:
                zh = names_map.get(key) if names_map else None
                if zh:
                    obj['zh'] = zh
                    obj['prefilled'] = True
                    obj['prefilled_from'] = 'names'
                    count_prefilled += 1; src_names += 1; applied = True
            # 2) UI 表（仅短令牌）。若启用 AC，额外尝试子串覆盖为全词匹配
            if (not applied) and is_short_token(en, args.max_len, args.max_words):
                if args.dict_backend == 'sqlite' and sqlite_db is not None:
                    cur = sqlite_db.execute("SELECT zh FROM dict_entries WHERE layer=? AND key=?", ('ui', key))
                    row = cur.fetchone()
                    zh = row[0] if row else None
                else:
                    zh = ui_map.get(key) if ui_map else None
                if zh:
                    obj['zh'] = zh
                    obj['prefilled'] = True
                    obj['prefilled_from'] = 'ui'
                    count_prefilled += 1; src_ui += 1; applied = True
                elif args.dict_backend == 'memory' and ui_automaton is not None:
                    # 查找是否存在一个词条完全覆盖整个短文本
                    full_hit = None
                    for end_idx, k in ui_automaton.iter(norm(en)):
                        start_idx = end_idx - len(k) + 1
                        if start_idx == 0 and end_idx + 1 == len(norm(en)):
                            full_hit = k; break
                    if full_hit:
                        zh2 = ui_map.get(full_hit)
                        if zh2:
                            obj['zh'] = zh2
                            obj['prefilled'] = True
                            obj['prefilled_from'] = 'ui'
                            count_prefilled += 1; src_ui += 1; applied = True
            # 3) 通用表（精确匹配）
            if (not applied):
                if args.dict_backend == 'sqlite' and sqlite_db is not None:
                    cur = sqlite_db.execute("SELECT zh FROM dict_entries WHERE layer=? AND key=?", ('general', key))
                    row = cur.fetchone()
                    zh = row[0] if row else None
                else:
                    zh = general_map.get(key) if general_map else None
                if zh:
                    obj['zh'] = zh
                    obj['prefilled'] = True
                    obj['prefilled_from'] = 'general'
                    count_prefilled += 1; src_general += 1; applied = True
            # 4) TM（长度阈值 + 精确匹配，选高频首选；保留候选供人工参考）
            if (not applied) and tm_top and len((en or '').strip()) >= args.tm_min_len:
                t = tm_top.get(key)
                if t:
                    zh, cands = t
                    obj['zh'] = zh
                    obj['prefilled'] = True
                    obj['prefilled_from'] = 'tm'
                    # 仅在存在多候选时附带（避免膨胀）
                    if isinstance(cands, list) and len(cands) > 1:
                        obj['tm_candidates'] = cands[:5]
                    count_prefilled += 1; src_tm += 1; applied = True
            fout.write(json.dumps(obj, ensure_ascii=False) + "\n")
            if prog is not None and task is not None:
                prog.advance(task)
        if prog is not None:
            prog.stop()

    summary = {
        "source_items": count_total,
        "prefilled": count_prefilled,
        "by_source": {"names": src_names, "ui": src_ui, "general": src_general, "tm": src_tm},
        "output": str(out)
    }
    if _console:
        _console.print("\n[bold green]Prefill Summary[/]")
        _console.print(summary)
    else:
        print(f"Source items: {count_total}")
        print(f"Prefilled:    {count_prefilled}")
        print(f"Output:       {out}")


if __name__ == '__main__':
    main()
