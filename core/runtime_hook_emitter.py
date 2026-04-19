#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Runtime-hook emitter (round 31 Tier C).

Opt-in pipeline tail-step that writes ``translations.json`` plus a copy of
``resources/hooks/inject_hook.rpy`` into the translated output directory.
Pairs with the ``--sandbox`` style ``RENPY_TL_INJECT=1`` launch gate in the
hook file so end-users can choose between:

  * **Default (static-file mode)** — translated ``.rpy`` files are
    written to ``output_dir/game/``; the game runs translated without any
    runtime hook.
  * **Opt-in (runtime-hook mode)** — users who prefer to keep the game's
    original ``.rpy`` files unmodified can ship just the ``translations.json``
    + ``zz_tl_inject_hook.rpy`` produced here alongside the unmodified
    game, and launch with ``RENPY_TL_INJECT=1``.

Activated only when the caller passes ``getattr(args, "emit_runtime_hook",
False)``; silently no-ops otherwise.  Zero third-party dependencies.
"""

from __future__ import annotations

import json
import logging
import shutil
from pathlib import Path
from typing import Iterable, Mapping

logger = logging.getLogger("renpy_translator")


def _iter_translation_pairs(
    entries: Iterable[Mapping[str, object]],
) -> Iterable[tuple[str, str]]:
    """Yield (original, translation) pairs for successful entries only.

    Accepts anything resembling a ``TranslationDB.entries`` list: each item
    must be a dict with ``original`` / ``translation`` / ``status`` fields.
    Entries without a translation or with non-``ok`` status are skipped so
    the runtime hook never ships a failed translation.
    """
    for entry in entries:
        status = str(entry.get("status", "") or "").lower()
        if status and status != "ok":
            continue
        original = entry.get("original")
        translation = entry.get("translation")
        if not isinstance(original, str) or not isinstance(translation, str):
            continue
        if not original or not translation:
            continue
        yield original, translation


def build_translations_map(
    entries: Iterable[Mapping[str, object]],
) -> dict[str, str]:
    """Collapse a ``TranslationDB.entries`` iterable into a flat
    ``{original: translation}`` dict.

    Deduplication rule: the first successful translation wins (stable
    across re-runs because ``translation_db.json`` preserves insertion
    order).  Identical translations across duplicate originals are
    harmless; conflicting translations keep the first one and log a
    debug-level notice so a human can investigate if needed.
    """
    mapping: dict[str, str] = {}
    conflicts = 0
    for original, translation in _iter_translation_pairs(entries):
        existing = mapping.get(original)
        if existing is None:
            mapping[original] = translation
        elif existing != translation:
            conflicts += 1
            logger.debug(
                "[TL-INJECT] translation conflict for %r — kept first (%r), skipped (%r)",
                original, existing, translation,
            )
    if conflicts:
        logger.info(
            "[TL-INJECT] %d original(s) had conflicting translations; kept first occurrence each",
            conflicts,
        )
    return mapping


def emit_runtime_hook(
    output_game_dir: Path,
    translation_db_entries: Iterable[Mapping[str, object]],
    *,
    hook_template_path: Path | None = None,
    hook_filename: str = "zz_tl_inject_hook.rpy",
) -> tuple[Path, Path, int]:
    """Write ``translations.json`` + copy the inject hook into
    ``output_game_dir``.

    Args:
        output_game_dir: Directory to write into (typically
            ``<output>/game`` so users can drop it over their game).
            Created if missing.
        translation_db_entries: Iterable of ``TranslationDB.entries``-shaped
            dicts.  Only ``status == "ok"`` entries contribute to the map.
        hook_template_path: Override for the source ``inject_hook.rpy``.
            Defaults to ``<project_root>/resources/hooks/inject_hook.rpy``.
        hook_filename: Name to save the hook under in ``output_game_dir``.
            Default uses the ``zz_`` prefix so Ren'Py loads it last among
            ``init python early:`` blocks — safest order for a monkey-patch
            shim that depends on other game init running first.

    Returns:
        (translations_json_path, hook_rpy_path, entry_count)

    Raises:
        FileNotFoundError: if ``hook_template_path`` does not exist.
        OSError: on filesystem write failure (caller should log + continue;
            a runtime-hook failure must not abort the main pipeline).
    """
    output_game_dir = Path(output_game_dir)
    output_game_dir.mkdir(parents=True, exist_ok=True)

    if hook_template_path is None:
        project_root = Path(__file__).resolve().parent.parent
        hook_template_path = project_root / "resources" / "hooks" / "inject_hook.rpy"
    hook_template_path = Path(hook_template_path)
    if not hook_template_path.is_file():
        raise FileNotFoundError(
            f"inject hook template missing: {hook_template_path}\n"
            "Ensure resources/hooks/inject_hook.rpy is present."
        )

    # Build map + write translations.json atomically (temp + os.replace)
    # so an interrupted run never leaves a half-written JSON.
    mapping = build_translations_map(translation_db_entries)
    json_path = output_game_dir / "translations.json"
    tmp_path = json_path.with_suffix(json_path.suffix + ".tmp")
    # Sort keys for stable diffs across re-runs; ensure_ascii=False to keep
    # Chinese readable when users inspect the file.
    tmp_path.write_text(
        json.dumps(mapping, ensure_ascii=False, sort_keys=True, indent=2),
        encoding="utf-8",
    )
    import os as _os
    _os.replace(str(tmp_path), str(json_path))

    # Copy the hook .rpy — shutil.copy2 preserves mtime/permissions so
    # Ren'Py's .rpyc cache invalidation still works when the template
    # is updated upstream.
    hook_out = output_game_dir / hook_filename
    shutil.copy2(str(hook_template_path), str(hook_out))

    logger.info(
        "[TL-INJECT] emitted runtime hook: %d translations → %s (+ %s)",
        len(mapping), json_path.name, hook_out.name,
    )
    return json_path, hook_out, len(mapping)


def emit_if_requested(
    args,
    output_dir: Path,
    translation_db,
) -> None:
    """Pipeline tail-step: check ``args.emit_runtime_hook`` and emit.

    Designed to be called from every Ren'Py-facing pipeline
    (``translators.direct.run_pipeline``,
    ``translators.tl_mode.run_tl_pipeline``,
    ``translators.retranslator.run_retranslate_pipeline``,
    ``engines.generic_pipeline.run_generic_pipeline``) at the very end,
    after ``translation_db.save()`` has persisted the session state.

    Args:
        args: argparse ``Namespace`` — the flag is read as
            ``getattr(args, "emit_runtime_hook", False)``.
        output_dir: Pipeline output root; the hook + JSON are written
            under ``output_dir / "game"`` (created if missing).
        translation_db: A ``TranslationDB`` instance.  Only the
            ``.entries`` attribute is read — keeps coupling minimal.

    Never raises into the caller: an emit failure is logged as a
    warning and swallowed, so a broken hook template or a read-only
    output directory cannot abort a successful translation run.
    """
    if not getattr(args, "emit_runtime_hook", False):
        return
    try:
        entries = getattr(translation_db, "entries", None)
        if not entries:
            logger.info("[TL-INJECT] skip emit — translation_db empty")
            return
        output_game_dir = Path(output_dir) / "game"
        emit_runtime_hook(output_game_dir, entries)
    except (OSError, ValueError, FileNotFoundError) as e:
        logger.warning("[TL-INJECT] emit failed, continuing: %s", e)
