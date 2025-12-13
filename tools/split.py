#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
split.py — 将抽取/待翻译的 JSONL 切分为多包，便于交给本地/云端 LLM 处理

特性：
- 支持按条数 --max-items，或按近似 tokens --max-tokens（默认启用简易估算，若安装 tiktoken 则优先使用）
- 可选择仅导出必要字段（id, en, context）
- 支持跳过已存在译文的条目（--skip-has-zh）
- 输出到指定目录，生成 batch_0001.jsonl, batch_0002.jsonl ...
"""

import argparse, json, math, hashlib
from pathlib import Path
try:
    from renpy_tools.utils.cache import cached  # type: ignore
except (ImportError, ModuleNotFoundError):
    cached = None  # type: ignore


def approx_tokens(s: str) -> int:
    # 简易估算：英文近似 1 token ≈ 4 chars；中文近似 1 token ≈ 1.6 chars，取折中 3
    if not s:
        return 0
    return max(1, math.ceil(len(s) / 3))


def count_tokens(s: str) -> int:
    try:
        import tiktoken  # type: ignore
    except (ImportError, ModuleNotFoundError):
        # 缓存近似统计
        if cached is not None:
            return int(cached("tok", "v1", s, lambda x: str(approx_tokens(x))))
        return approx_tokens(s)
    try:
        enc = tiktoken.get_encoding("cl100k_base")
        n = len(enc.encode(s))
        if cached is not None:
            # 命中后续可直接返回
            cached("tok", "v1", s, lambda _x: str(n))
        return n
    except (ValueError, RuntimeError):
        if cached is not None:
            return int(cached("tok", "v1", s, lambda x: str(approx_tokens(x))))
        return approx_tokens(s)


def has_zh(o: dict) -> bool:
    for k in ("zh", "cn", "zh_cn", "translation", "text_zh", "target", "tgt"):
        v = o.get(k)
        if v is not None and str(v).strip() != "":
            return True
    return False


def main():
    ap = argparse.ArgumentParser(description="Split JSONL into LLM-friendly batches")
    ap.add_argument("source_jsonl", help="抽取或预填后的 JSONL")
    ap.add_argument("out_dir", help="输出目录")
    ap.add_argument("--max-items", type=int, default=0, help="每包最大条数（0 表示不按条数限制）")
    ap.add_argument("--max-tokens", type=int, default=2000, help="每包最大近似 tokens（默认 2000）")
    ap.add_argument("--skip-has-zh", action="store_true", help="跳过已有译文的条目，仅导出未译或空译")
    ap.add_argument("--include-context", action="store_true", default=True, help="导出基础上下文字段（label/anchor_prev/anchor_next），默认开启")
    ap.add_argument("--include-speaker", action="store_true", help="导出 speaker 字段（若存在）")
    ap.add_argument("--bundle-window", type=int, default=0, help="同 label 内前后各拼接 N 句上下文，提供给 LLM 参考（默认 0 不拼接）")
    # LLM 批次元数据
    ap.add_argument("--model", default=None, help="（可选）LLM 模型名，写入批次元数据")
    ap.add_argument("--temperature", type=float, default=None, help="（可选）采样温度，写入批次元数据")
    ap.add_argument("--system-prompt-file", default=None, help="（可选）系统提示词文件路径，将记录 hash")
    args = ap.parse_args()

    src = Path(args.source_jsonl)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    batch = []
    batch_items = 0
    batch_tokens = 0
    batch_idx = 1

    def flush():
        nonlocal batch, batch_items, batch_tokens, batch_idx
        if not batch:
            return
        p = out_dir / f"batch_{batch_idx:04d}.jsonl"
        with p.open("w", encoding="utf-8") as f:
            for o in batch:
                f.write(json.dumps(o, ensure_ascii=False) + "\n")
        # 写入元数据
        meta = {"count": batch_items, "tokens": batch_tokens}
        if args.model:
            meta["model"] = args.model
        if args.temperature is not None:
            meta["temperature"] = args.temperature
        if args.system_prompt_file:
            sp = Path(args.system_prompt_file)
            if sp.exists():
                try:
                    content = sp.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    content = ""
                meta["system_prompt_sha1"] = hashlib.sha1(content.encode("utf-8")).hexdigest()
        (out_dir / f"batch_{batch_idx:04d}.meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        batch = []
        batch_items = 0
        batch_tokens = 0
        batch_idx += 1

    # 预读全部，便于同 label 内构建上下文窗口
    rows = []
    with src.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except (ValueError, json.JSONDecodeError):
                continue
            if args.skip_has_zh and has_zh(obj):
                continue
            rows.append(obj)

    # 按 (file,label,line,idx) 排序并分组
    def _key(o):
        return (
            o.get("file") or "",
            o.get("label") or "",
            int(o.get("line") or 0),
            int(o.get("idx") or 0),
        )
    rows.sort(key=_key)

    # 构造 bundle 窗口
    from collections import defaultdict
    groups = defaultdict(list)
    for o in rows:
        groups[(o.get("file") or "", o.get("label") or "")].append(o)

    for (_file_unused, _label_unused), seq in groups.items():
        n = len(seq)
        for i, obj in enumerate(seq):
            item = {
                "id": obj.get("id") or obj.get("id_hash") or (f"{obj.get('file')}:{obj.get('line')}:{obj.get('idx')}")
            }
            item["en"] = obj.get("en", "")
            if args.include_context:
                for k in ("label", "anchor_prev", "anchor_next"):
                    if k in obj:
                        item[k] = obj[k]
            if args.include_speaker and (obj.get("speaker") is not None):
                item["speaker"] = obj.get("speaker")
            bw = max(0, int(args.bundle_window))
            if bw > 0:
                # 仅同 label 内相邻句
                left = []
                right = []
                # 前 bw 句
                li = i - 1
                while li >= 0 and len(left) < bw:
                    enp = seq[li].get("en") or ""
                    if enp:
                        left.append(enp)
                    li -= 1
                # 后 bw 句
                ri = i + 1
                while ri < n and len(right) < bw:
                    enn = seq[ri].get("en") or ""
                    if enn:
                        right.append(enn)
                    ri += 1
                if left:
                    item["ctx_prev"] = list(reversed(left))
                if right:
                    item["ctx_next"] = right
            tks = count_tokens(item.get("en", ""))
            # 估算将上下文也计入 tokens（粗略）
            if "ctx_prev" in item:
                tks += sum(count_tokens(s) for s in item["ctx_prev"]) // 2
            if "ctx_next" in item:
                tks += sum(count_tokens(s) for s in item["ctx_next"]) // 2
            limit_items = (args.max_items > 0 and batch_items + 1 > args.max_items)
            limit_tokens = (args.max_tokens > 0 and batch_tokens + tks > args.max_tokens)
            if limit_items or limit_tokens:
                flush()
            batch.append(item)
            batch_items += 1
            batch_tokens += tks
    flush()

    print(f"Batches written to: {out_dir}")


if __name__ == "__main__":
    main()
