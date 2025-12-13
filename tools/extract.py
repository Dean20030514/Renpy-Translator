#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced extractor for Ren'Py .rpy

- 跳过 python 块：python: / init python: / python early
- 抽取双引号、单引号、以及三引号(支持跨行)
- 显式跳过仅注释行；尽量忽略资源路径/文件名误报
- 兼容短 UI 文本(OK/Yes 等)
- 生成行号型 id(back-compat) + 内容锚定 hash id
- 输出：per-file JSONL、combined JSONL、TM 种子 CSV、manifest CSV
"""

import re, csv, json, argparse, hashlib, concurrent.futures, os
from pathlib import Path
from collections import Counter
# 可选：彩色日志与进度
try:
    from rich.console import Console  # type: ignore
    from rich.progress import Progress, BarColumn, TimeElapsedColumn  # type: ignore
    _console = Console()
except ImportError:  # pragma: no cover - 可选依赖
    _console = None
try:
    from renpy_tools.utils.io import write_jsonl_lines as _write_jsonl_lines, ensure_parent_dir as _ensure_parent_dir  # type: ignore
except (ImportError, ModuleNotFoundError):
    _write_jsonl_lines = None
    _ensure_parent_dir = None

ASSET_EXTS = (".png",".jpg",".jpeg",".webp",".ogg",".mp3",".wav",".webm",".mp4",".rpy",".rpa",".zip",".ttf",".otf")
# 占位符匹配/语义签名：尽量复用通用工具
try:
    from renpy_tools.utils.placeholder import ph_set as _ph_set, compute_semantic_signature as _comp_sig  # type: ignore
except (ImportError, ModuleNotFoundError):
    _ph_set = None
    _comp_sig = None

# 作为后备的占位符正则（与 utils 等价覆盖）
PH_RE = re.compile(
    r"\[[A-Za-z_][A-Za-z0-9_]*\]"                       # [name]
    r"|%(?:\([^)]+\))?[+#0\- ]?\d*(?:\.\d+)?[sdifeEfgGxXo]"  # %s, %02d, %(name)s, %.2f, %x, %o, ...
    r"|\{\d+(?:![rsa])?(?::[^{}]+)?\}"                  # {0} {0:.2f} {0!r:>8}
    r"|\{[A-Za-z_][A-Za-z0-9_]*(?:![rsa])?(?::[^{}]+)?\}" # {name!r:>8}
)
LABEL_RE = re.compile(r'^\s*label\s+([A-Za-z0-9_\.]+)\s*:\s*$')
PY_START_RE = re.compile(r'^\s*(init\s+python|python(\s+early)?)\s*:.*$')

# 单行引号（修复：排除缩写如 don't, aren't）
# 双引号：保持原样
DQ_RE = re.compile(r'"((?:\\.|[^"\\])*)"')
# 单引号：前面不能是字母数字（避免 aren't 等缩写）
SQ_RE = re.compile(r"(?<![A-Za-z0-9])'((?:\\.|[^'\\])*)'(?![A-Za-z])")
# 三引号
TRI_OPEN_RE = re.compile(r'("""|\'\'\')')

def leading_spaces(s: str) -> int:
    return len(s) - len(s.lstrip(" "))

def looks_like_asset(s: str) -> bool:
    t = s.strip()
    if not t:
        return False
    # data URI 图像/媒体
    if t.startswith("data:"):
        return True
    if ("/" in t or "\\" in t) and any(t.lower().endswith(ext) for ext in ASSET_EXTS) and " " not in t:
        return True
    # 允许带 query/hash 的资源路径，如 foo.png?v=1#hash
    lower = t.lower()
    for ext in ASSET_EXTS:
        if lower.endswith(ext) or lower.split("?")[0].split("#")[0].endswith(ext):
            if " " not in t:
                return True
    if " " not in t and any(lower.endswith(ext) for ext in ASSET_EXTS):
        return True
    return False

def looks_like_text(s: str, min_len: int) -> bool:
    if len(s.strip()) < min_len:
        return False
    # 有字母或中日韩统一表意文字
    if re.search(r'[A-Za-z\u4e00-\u9fff]', s):
        return True
    # 允许极短 UI 令牌
    return True

def compute_hash_id(file_rel: str, line: int, idx: int, en: str, prev_line: str, next_line: str) -> str:
    """计算条目的唯一哈希 ID（使用 SHA256）"""
    h = hashlib.sha256()
    for part in (file_rel, str(line), str(idx), en, prev_line or "", next_line or ""):
        h.update(part.encode("utf-8"))
    return "sha256:" + h.hexdigest()[:16]


def compute_semantic(en_text: str) -> str:
    """计算语义签名（用于去重）"""
    if _comp_sig:
        return _comp_sig(en_text)
    # 简易后备：去除花括号标签（粗略）与空白归一化
    t = re.sub(r"\{/?[A-Za-z_][^}]*\}", "", en_text or "")
    t = re.sub(r"\s+", " ", t).strip().lower()
    return "sig0:" + hashlib.sha256(t.encode("utf-8")).hexdigest()[:16]

def extract_from_file(path: Path, root: Path, include_single=True, include_triple=True, skip_comments=True, min_len=1):
    rel = path.relative_to(root).as_posix()
    items = []
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    n = len(lines)

    def prev_nonempty(i):
        j = i-1
        while j >= 0 and not lines[j].strip():
            j -= 1
        return lines[j] if j >= 0 else ""

    def next_nonempty(i):
        j = i+1
        while j < n and not lines[j].strip():
            j += 1
        return lines[j] if j < n else ""

    in_python = False
    py_base = 0
    current_label = ""
    i = 0

    while i < n:
        line = lines[i]

        # 记录 label
        m_lab = LABEL_RE.match(line)
        if m_lab:
            current_label = m_lab.group(1)

        # 进入/退出 python 块
        if not in_python and PY_START_RE.match(line):
            in_python = True
            py_base = leading_spaces(line)
            i += 1
            continue
        if in_python:
            if line.strip() and leading_spaces(line) <= py_base:
                in_python = False
            i += 1
            continue

        # 跳过纯注释行
        if skip_comments and line.lstrip().startswith("#"):
            i += 1
            continue

        # —— 三引号（含跨行）——
        if include_triple:
            mo = TRI_OPEN_RE.search(line)
            valid_triple_start = False
            if mo:
                # 不在注释后的三引号
                cpos = line.find("#")
                if cpos == -1 or mo.start() < cpos:
                    valid_triple_start = True
            if valid_triple_start:
                q = mo.group(1)  # ''' 或 """
                buf = [line[mo.end():]]
                start_line = i+1
                i += 1
                closed = False
                while i < n:
                    l2 = lines[i]
                    pos = l2.find(q)
                    if pos != -1:
                        content = "\n".join(buf + [l2[:pos]])
                        en_text = content
                        if looks_like_text(en_text, min_len) and not looks_like_asset(en_text):
                            ph = sorted(set(PH_RE.findall(en_text)))
                            ap = prev_nonempty(start_line-1)
                            an = next_nonempty(i)
                            items.append({
                                "id": f"{rel}:{start_line}:0",
                                "id_hash": compute_hash_id(rel, start_line, 0, en_text, ap, an),
                                "id_semantic": compute_semantic(en_text),
                                "file": rel, "line": start_line, "col": 0, "idx": 0,
                                "label": current_label, "en": en_text,
                                "placeholders": ph, "anchor_prev": ap, "anchor_next": an,
                                "quote": q*3, "is_triple": True
                            })
                        # 处理收尾后的剩余部分（继续本行单行扫描）
                        tail = l2[pos+3:]
                        line = tail
                        closed = True
                        break
                    else:
                        buf.append(l2)
                        i += 1
                if not closed:
                    # 到 EOF 未闭合，仍然记录
                    en_text = "\n".join(buf)
                    if looks_like_text(en_text, min_len) and not looks_like_asset(en_text):
                        ph = sorted(set(PH_RE.findall(en_text)))
                        ap = prev_nonempty(start_line-1)
                        items.append({
                            "id": f"{rel}:{start_line}:0",
                            "id_hash": compute_hash_id(rel, start_line, 0, en_text, ap, ""),
                            "id_semantic": compute_semantic(en_text),
                            "file": rel, "line": start_line, "col": 0, "idx": 0,
                            "label": current_label, "en": en_text,
                            "placeholders": ph, "anchor_prev": ap, "anchor_next": "",
                            "quote": q*3, "is_triple": True
                        })
                    break  # EOF
                # 有 tail 时,继续往下执行单行引号扫描（line 已覆盖为 tail）

        # —— 单行引号扫描（去掉行内注释后的部分）——
        non_comment = line
        hash_pos = non_comment.find("#")
        if hash_pos != -1:
            non_comment = non_comment[:hash_pos]

        idx_in_line = 0
        for m in DQ_RE.finditer(non_comment):
            en_text = m.group(1)
            if looks_like_text(en_text, min_len) and not looks_like_asset(en_text):
                ph = sorted((_ph_set(en_text) if _ph_set else set(PH_RE.findall(en_text))))
                ap = prev_nonempty(i)
                an = next_nonempty(i)
                # 尝试推断说话者（如：e "Hello"）
                before = non_comment[:m.start()].rstrip()
                spk = ""
                if before:
                    msp = re.search(r"([A-Za-z_][A-Za-z0-9_]*)\s*$", before)
                    if msp:
                        spk = msp.group(1)
                items.append({
                    "id": f"{rel}:{i+1}:{idx_in_line}",
                    "id_hash": compute_hash_id(rel, i+1, idx_in_line, en_text, ap, an),
                    "id_semantic": compute_semantic(en_text),
                    "file": rel, "line": i+1, "col": m.start(1), "idx": idx_in_line,
                    "label": current_label, "speaker": spk, "en": en_text,
                    "placeholders": ph, "anchor_prev": ap, "anchor_next": an,
                    "quote": '"', "is_triple": False
                })
            idx_in_line += 1

        if include_single:
            for m in SQ_RE.finditer(non_comment):
                en_text = m.group(1)
                if looks_like_text(en_text, min_len) and not looks_like_asset(en_text):
                    ph = sorted((_ph_set(en_text) if _ph_set else set(PH_RE.findall(en_text))))
                    ap = prev_nonempty(i)
                    an = next_nonempty(i)
                    before = non_comment[:m.start()].rstrip()
                    spk = ""
                    if before:
                        msp = re.search(r"([A-Za-z_][A-Za-z0-9_]*)\s*$", before)
                        if msp:
                            spk = msp.group(1)
                    items.append({
                        "id": f"{rel}:{i+1}:{idx_in_line}",
                        "id_hash": compute_hash_id(rel, i+1, idx_in_line, en_text, ap, an),
                        "id_semantic": compute_semantic(en_text),
                        "file": rel, "line": i+1, "col": m.start(1), "idx": idx_in_line,
                        "label": current_label, "speaker": spk, "en": en_text,
                        "placeholders": ph, "anchor_prev": ap, "anchor_next": an,
                        "quote": "'", "is_triple": False
                    })
                idx_in_line += 1

        i += 1

    return items

# ==================== 全局辅助函数（用于多进程） ====================

# 全局变量，用于在多进程中共享配置
_global_config = {}

def _process_one_file(file_path_tuple):
    """处理单个文件 - 全局函数以支持多进程"""
    p, root, include_single, include_triple, skip_comments, min_len, per_file_dir = file_path_tuple
    p = Path(p)
    root = Path(root)
    per_file_dir = Path(per_file_dir)
    
    items = extract_from_file(
        p, root,
        include_single=include_single,
        include_triple=include_triple,
        skip_comments=skip_comments,
        min_len=min_len
    )
    
    # per-file JSONL
    pf = per_file_dir / (p.relative_to(root).as_posix().replace("/", "__") + ".jsonl")
    pf.parent.mkdir(parents=True, exist_ok=True)
    if _write_jsonl_lines:
        _write_jsonl_lines(pf, items)
    else:
        with pf.open("w", encoding="utf-8") as f:
            for it in items:
                f.write(json.dumps(it, ensure_ascii=False) + "\n")
    return p, items

def _process_chunk_files(chunk_tuple):
    """处理文件块 - 全局函数以支持多进程"""
    chunk_files, root, include_single, include_triple, skip_comments, min_len, per_file_dir, parts_dir = chunk_tuple
    
    root = Path(root)
    per_file_dir = Path(per_file_dir)
    parts_dir = Path(parts_dir)
    
    part_path = parts_dir / (f"part_{os.getpid()}_{hash(tuple(str(p) for p in chunk_files)) & 0xfffffff}.jsonl")
    local_rows = []
    local_tm_counter = {}
    local_tm_sample = {}
    
    with part_path.open("w", encoding="utf-8") as pf_comb:
        for p_str in chunk_files:
            p = Path(p_str)
            file_tuple = (p, root, include_single, include_triple, skip_comments, min_len, per_file_dir)
            _p, items = _process_one_file(file_tuple)
            
            for it in items:
                pf_comb.write(json.dumps(it, ensure_ascii=False) + "\n")
                # tm
                cnt = local_tm_counter.get(it["en"], 0) + 1
                local_tm_counter[it["en"]] = cnt
                if it["en"] not in local_tm_sample:
                    local_tm_sample[it["en"]] = {"file": it["file"], "line": it["line"], "label": it.get("label", "")}
            
            local_rows.append({
                "file": p.relative_to(root).as_posix(),
                "extracted_strings": len(items),
                "empty": ("yes" if len(items)==0 else "no")
            })
    
    return str(part_path), local_rows, local_tm_counter, local_tm_sample

def _chunks(lst, n):
    """分块辅助函数"""
    for i in range(0, len(lst), n):
        yield lst[i:i+n]

def main():
    ap = argparse.ArgumentParser(description="Extract visible strings from Ren'Py .rpy files.")
    ap.add_argument("project_root", help="Path to Ren'Py project root")
    ap.add_argument("-o","--out", default="out_extract", help="Output directory")
    ap.add_argument("--glob", default="**/*.rpy", help="Glob for files to include")
    ap.add_argument("--exclude-dirs", default="tl,saves,cache", help="Comma-separated dir names to exclude (default 'tl,saves,cache')")
    ap.add_argument("--no-single", action="store_true", help="Do NOT extract single-quoted strings")
    ap.add_argument("--no-triple", action="store_true", help="Do NOT extract triple-quoted strings")
    ap.add_argument("--no-skip-comments", action="store_true", help="Do NOT skip comment-only lines")
    ap.add_argument("--min-len", type=int, default=1, help="Minimum trimmed length to keep")
    ap.add_argument("--workers", default="auto", help="并行进程数，可设为整数或 auto (=cpu-1)，0 表示不并行；默认 auto")
    ap.add_argument("--chunk-size", type=int, default=64, help="每个进程处理的文件数（>0 启用分片聚合，适合超大量文件），默认 64")
    args = ap.parse_args()

    root = Path(args.project_root).resolve()
    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    per_file_dir = out_dir / "per_file_jsonl"
    per_file_dir.mkdir(parents=True, exist_ok=True)

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

    combined = out_dir / "project_en_for_grok.jsonl"
    manifest_rows = []
    tm_counter = Counter()
    tm_sample = {}

    # 准备参数供全局函数使用
    include_single = not args.no_single
    include_triple = not args.no_triple
    skip_comments = not args.no_skip_comments

    # workers 解析
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
    if _console:
        _console.print(f"[bold cyan]Scanning[/] {len(files)} .rpy files from [magenta]{root}[/] ...")
    if workers_val and workers_val > 0:
        # 并行不易精准显示进度，简要提示
        if _console:
            _console.print(f"[dim]Using {workers_val} workers[/]")
        # 若未指定 chunk, 直接逐文件；若指定，则每块聚合并写入分片 combined，主进程最后合并
        if args.chunk_size and args.chunk_size > 0:
            parts_dir = out_dir / "combined_parts"
            parts_dir.mkdir(parents=True, exist_ok=True)

            # 准备参数
            include_single = not args.no_single
            include_triple = not args.no_triple
            skip_comments = not args.no_skip_comments
            
            # 将文件路径转为字符串（Path对象无法序列化）
            file_strs = [str(f) for f in files]
            chunks_list = list(_chunks(file_strs, args.chunk_size))
            
            # 为每个chunk准备参数元组
            chunk_args = [
                (chunk, str(root), include_single, include_triple, skip_comments, args.min_len, str(per_file_dir), str(parts_dir))
                for chunk in chunks_list
            ]

            manifest_rows = []
            tm_counter_map = Counter()
            tm_sample_map = {}
            part_paths = []
            with concurrent.futures.ProcessPoolExecutor(max_workers=workers_val) as ex:
                for part_path, mrows, tmc, tms in ex.map(_process_chunk_files, chunk_args):
                    part_paths.append(part_path)
                    manifest_rows.extend(mrows)
                    for k,v in tmc.items():
                        tm_counter_map[k] = tm_counter_map.get(k,0) + v
                    for k,v in tms.items():
                        if k not in tm_sample_map:
                            tm_sample_map[k] = v
            # 合并分片到 combined
            with combined.open("w", encoding="utf-8") as cf:
                for pp in part_paths:
                    with Path(pp).open("r", encoding="utf-8") as inf:
                        for line in inf:
                            cf.write(line)
                    try:
                        Path(pp).unlink()
                    except OSError:
                        pass
            # 写 TM 与 manifest
            tm_counter = tm_counter_map
            tm_sample = tm_sample_map
        else:
            # 准备文件参数元组
            file_args = [
                (str(p), str(root), include_single, include_triple, skip_comments, args.min_len, str(per_file_dir))
                for p in files
            ]
            with concurrent.futures.ProcessPoolExecutor(max_workers=workers_val) as ex:
                for p, items in ex.map(_process_one_file, file_args):
                    results.append((Path(p), items))
    else:
        if _console:
            with Progress("{task.description}", BarColumn(), "{task.completed}/{task.total}", TimeElapsedColumn(), console=_console) as prog:
                task = prog.add_task("Extracting", total=len(files))
                for p in files:
                    p_str, items = _process_one_file((str(p), str(root), include_single, include_triple, skip_comments, args.min_len, str(per_file_dir)))
                    results.append((Path(p_str), items))
                    prog.advance(task)
        else:
            for p in files:
                p_str, items = _process_one_file((str(p), str(root), include_single, include_triple, skip_comments, args.min_len, str(per_file_dir)))
                results.append((Path(p_str), items))

    def _combined_iter():
        for _p, items in results:
            for it in items:
                yield it
    # 写 combined，同时累计 TM 与 manifest
    if not (workers_val and args.chunk_size and args.chunk_size > 0):
        # 非分片模式：按旧路径聚合
        if _write_jsonl_lines:
            _write_jsonl_lines(combined, _combined_iter())
            for p, items in results:
                for it in items:
                    tm_counter[it["en"]] = tm_counter.get(it["en"],0) + 1
                    if it["en"] not in tm_sample:
                        tm_sample[it["en"]] = {"file": it["file"], "line": it["line"], "label": it.get("label","")}
                manifest_rows.append({
                    "file": p.relative_to(root).as_posix(),
                    "extracted_strings": len(items),
                    "empty": ("yes" if len(items)==0 else "no")
                })
        else:
            with combined.open("w", encoding="utf-8") as cf:
                for p, items in results:
                    for it in items:
                        cf.write(json.dumps(it, ensure_ascii=False) + "\n")
                        tm_counter[it["en"]] = tm_counter.get(it["en"],0) + 1
                        if it["en"] not in tm_sample:
                            tm_sample[it["en"]] = {"file": it["file"], "line": it["line"], "label": it.get("label","")}
                    manifest_rows.append({
                        "file": p.relative_to(root).as_posix(),
                        "extracted_strings": len(items),
                        "empty": ("yes" if len(items)==0 else "no")
                    })

    # TM 种子
    tm_rows = []
    for text, cnt in sorted(tm_counter.items(), key=lambda kv:(-kv[1], kv[0])):
        s = tm_sample[text]
        tm_rows.append({"text_en": text, "count": cnt, "sample_file": s["file"], "sample_line": s["line"], "sample_label": s["label"]})
    with (out_dir / "tm_seed_all_en.csv").open("w", newline="", encoding="utf-8") as tf:
        w = csv.DictWriter(tf, fieldnames=["text_en","count","sample_file","sample_line","sample_label"])
        w.writeheader(); w.writerows(tm_rows)

    # Manifest
    with (out_dir / "manifest.csv").open("w", newline="", encoding="utf-8") as mf:
        w = csv.DictWriter(mf, fieldnames=["file","extracted_strings","empty"])
        w.writeheader(); w.writerows(manifest_rows)

    total = sum(m['extracted_strings'] for m in manifest_rows)
    summary = {
        "files": len(files),
        "strings": total,
        "per_file_jsonl": str(per_file_dir),
        "combined_jsonl": str(combined),
        "tm_seed_csv": str(out_dir / 'tm_seed_all_en.csv'),
        "manifest_csv": str(out_dir / 'manifest.csv'),
    }
    if _console:
        _console.print("\n[bold green]Extraction Summary[/]")
        _console.print(summary)
    else:
        print(f"Scanned {len(files)} files. Extracted {total} strings.")
        print(f"Per-file JSONL: {per_file_dir}")
        print(f"Combined JSONL: {combined}")
        print(f"TM seed CSV:    {out_dir / 'tm_seed_all_en.csv'}")
        print(f"Manifest CSV:   {out_dir / 'manifest.csv'}")

if __name__ == "__main__":
    main()
