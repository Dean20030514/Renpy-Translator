#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Merge multiple v2 ``translations.json`` envelopes into a single
multi-language file (round 33 Subtask 1).

Each input must be a v2 envelope produced by ``core.runtime_hook_emitter``
when the pipeline was run with ``--runtime-hook-schema v2``.  Each input
typically populates exactly one language bucket (matching its ``--target-lang``);
this tool merges N such files into a single envelope whose ``translations``
map has every language bucket seen across all inputs.

Usage::

    python tools/merge_translations_v2.py zh.json ja.json -o merged.json
    python tools/merge_translations_v2.py *.json --default-lang zh --strict

Merge semantics:
    * For each ``(original, lang)`` pair: **first input wins** on conflict.
    * Conflicts log a warning unless ``--strict`` is set (which errors).
    * v1-shaped (flat) inputs are rejected with a clear error — merge is
      only defined for v2.
    * Output ``default_lang`` precedence: ``--default-lang`` flag >
      first input's ``default_lang`` > ``"zh"``.

Exit codes:
    * ``0`` — success
    * ``1`` — any error (missing file / malformed JSON / v1 input / strict
      conflict / output write failure)

Zero third-party dependencies.  Tested by ``tests/test_merge_translations_v2.py``.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Iterable, List, Optional

from core.file_safety import check_fstat_size

logger = logging.getLogger(__name__)

# Round 37 M2: reject v2 envelope input files above 50 MB to bound memory
# usage when the caller passes an attacker-crafted or accidentally huge
# translations.json.  Even a polyglot-translated game DB typically sits
# in the single-digit MB range, so 50 MB is generous headroom.
_MAX_V2_ENVELOPE_SIZE = 50 * 1024 * 1024


class MergeError(Exception):
    """Raised when merge inputs are incompatible (missing, malformed, v1
    schema, or strict-mode conflict)."""


def _load_v2_envelope(path: Path) -> dict:
    """Load a v2 envelope from ``path`` after structural validation.

    Raises ``MergeError`` with an actionable message if the file is missing,
    unreadable, malformed JSON, not an object, or not a v2 envelope.
    """
    if not path.is_file():
        raise MergeError(f"input file not found: {path}")
    # Round 37 M2: bound memory before the full read — raise with an
    # actionable message so the CLI propagates exit=1 to the operator.
    try:
        file_size = path.stat().st_size
    except OSError as e:
        raise MergeError(f"cannot stat {path}: {e}") from e
    if file_size > _MAX_V2_ENVELOPE_SIZE:
        raise MergeError(
            f"{path} too large ({file_size} bytes > {_MAX_V2_ENVELOPE_SIZE} "
            "byte cap); refuse to load to protect memory. If this is "
            "legitimate, split the file into smaller language buckets "
            "before merging."
        )
    try:
        # Round 49 Step 2: TOCTOU defense via check_fstat_size on the open fd.
        with open(path, encoding="utf-8") as f:
            ok, fsize2 = check_fstat_size(f, _MAX_V2_ENVELOPE_SIZE)
            if not ok:
                raise MergeError(
                    f"{path} grew past cap after stat (TOCTOU?): "
                    f"{fsize2} bytes > {_MAX_V2_ENVELOPE_SIZE} byte cap"
                )
            text = f.read()
    except OSError as e:
        raise MergeError(f"cannot read {path}: {e}") from e
    try:
        data = json.loads(text)
    except ValueError as e:
        raise MergeError(f"malformed JSON in {path}: {e}") from e
    if not isinstance(data, dict):
        raise MergeError(f"{path} is not a JSON object")
    if data.get("_schema_version") != 2:
        raise MergeError(
            f"{path} is not a v2 envelope "
            f"(_schema_version={data.get('_schema_version')!r}); "
            "only v2 translations.json files are accepted — generate with "
            "``--runtime-hook-schema v2``"
        )
    translations = data.get("translations")
    if not isinstance(translations, dict):
        raise MergeError(
            f"{path} v2 envelope is missing or has an invalid ``translations`` field"
        )
    return data


def merge_v2_translations(
    input_paths: Iterable[Path],
    *,
    default_lang: Optional[str] = None,
    strict: bool = False,
) -> dict:
    """Merge one or more v2 envelopes into a fresh v2 envelope dict.

    Args:
        input_paths: iterable of paths to v2 envelope JSON files.  At least
            one is required; typical use is two or more with disjoint
            ``target_lang`` buckets.
        default_lang: override for the output envelope's ``default_lang``.
            When ``None``, uses the first input's ``default_lang``, falling
            back to ``"zh"``.
        strict: when True, conflicting translations (same ``original`` +
            same ``lang`` with differing values) raise ``MergeError``.
            When False (default), the first occurrence wins and the
            conflict is logged at ``warning`` level.

    Returns:
        A fresh v2 envelope dict with ``_schema_version``, ``_format``,
        ``default_lang``, and merged ``translations``.

    Raises:
        MergeError: on input validation failure or strict-mode conflict.
    """
    paths = [Path(p) for p in input_paths]
    if not paths:
        raise MergeError("merge needs at least one input file")

    merged_translations: dict[str, dict[str, str]] = {}
    first_default_lang: Optional[str] = None
    seen_langs: set[str] = set()
    conflict_count = 0

    for p in paths:
        env = _load_v2_envelope(p)
        src_default = env.get("default_lang")
        if (
            first_default_lang is None
            and isinstance(src_default, str)
            and src_default
        ):
            first_default_lang = src_default

        for original, bucket in env["translations"].items():
            if not isinstance(original, str) or not original:
                logger.warning(
                    "[MERGE] %s: skipping non-string or empty key", p,
                )
                continue
            if not isinstance(bucket, dict):
                logger.warning(
                    "[MERGE] %s: non-dict bucket for %r — skipping",
                    p, original,
                )
                continue
            dst_bucket = merged_translations.setdefault(original, {})
            for lang, trans in bucket.items():
                if not isinstance(lang, str) or not lang:
                    continue
                if not isinstance(trans, str):
                    continue
                seen_langs.add(lang)
                existing = dst_bucket.get(lang)
                if existing is None:
                    dst_bucket[lang] = trans
                elif existing != trans:
                    conflict_count += 1
                    if strict:
                        raise MergeError(
                            f"conflict in {p} for {original!r}[{lang!r}]: "
                            f"already have {existing!r}, would overwrite with "
                            f"{trans!r} — use non-strict mode to accept first-wins"
                        )
                    logger.warning(
                        "[MERGE] conflict for %r[%r] — kept first (%r), "
                        "skipped (%r from %s)",
                        original, lang, existing, trans, p,
                    )

    out_default_lang = default_lang or first_default_lang or "zh"

    if conflict_count:
        logger.info(
            "[MERGE] merged %d original(s) across %d language(s); "
            "%d conflict(s) resolved by first-wins rule",
            len(merged_translations), len(seen_langs), conflict_count,
        )
    else:
        sorted_langs = ", ".join(sorted(seen_langs)) or "(none)"
        logger.info(
            "[MERGE] merged %d original(s) across %d language(s): %s",
            len(merged_translations), len(seen_langs), sorted_langs,
        )

    return {
        "_schema_version": 2,
        "_format": "renpy-translate",
        "default_lang": out_default_lang,
        "translations": merged_translations,
    }


def _write_json_atomic(path: Path, data: object) -> None:
    """Write ``data`` as pretty UTF-8 JSON atomically (temp + os.replace).

    Mirrors the crash-safety pattern used by ``core/runtime_hook_emitter.py``
    so interrupted runs never leave a half-written merged output file.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(
        json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2),
        encoding="utf-8",
    )
    os.replace(str(tmp_path), str(path))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "将多个 v2 translations.json envelope 合并成一个多语言文件（round 33 Subtask 1）"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例:\n"
            "  python tools/merge_translations_v2.py zh.json ja.json -o merged.json\n"
            "  python tools/merge_translations_v2.py *.json --default-lang zh --strict\n"
            "\n"
            "注意：所有输入必须是 v2 envelope（--runtime-hook-schema v2 生成）。"
        ),
    )
    parser.add_argument(
        "inputs",
        nargs="+",
        metavar="INPUT.json",
        help="v2 translations.json 文件路径（至少 1 个，典型 2+）",
    )
    parser.add_argument(
        "-o", "--output",
        default="merged_translations.json",
        metavar="PATH",
        help="输出文件路径（默认: merged_translations.json）",
    )
    parser.add_argument(
        "--default-lang",
        default=None,
        metavar="LANG",
        help="覆盖输出的 default_lang（默认: 第一个输入的 default_lang，否则 zh）",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="冲突翻译时立即报错退出（默认: 警告 + first-wins 保留首次）",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """CLI entry point.  Returns 0 on success, 1 on error."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
    )

    try:
        merged = merge_v2_translations(
            [Path(p) for p in args.inputs],
            default_lang=args.default_lang,
            strict=args.strict,
        )
    except MergeError as e:
        logger.error("[MERGE] %s", e)
        return 1

    try:
        out_path = Path(args.output)
        _write_json_atomic(out_path, merged)
    except OSError as e:
        logger.error("[MERGE] cannot write %s: %s", args.output, e)
        return 1

    lang_count = len(
        {lang for bucket in merged["translations"].values() for lang in bucket}
    )
    logger.info(
        "[MERGE] wrote %s (%d originals, %d languages)",
        out_path, len(merged["translations"]), lang_count,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
