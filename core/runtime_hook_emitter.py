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
    *,
    target_lang: str = "zh",
    schema_version: int = 1,
) -> dict:
    """Collapse a ``TranslationDB.entries`` iterable into the runtime hook
    translations JSON payload.

    Deduplication rule (both schemas): the first successful translation wins
    (stable across re-runs because ``translation_db.json`` preserves
    insertion order).  Identical translations across duplicate originals are
    harmless; conflicting translations keep the first one and log a
    debug-level notice so a human can investigate if needed.

    Args:
        entries: ``TranslationDB.entries``-shaped iterable.
        target_lang: Language code used to key the v2 nested dict.  Ignored
            for v1.  Defaults to ``"zh"`` to match ``core.config`` defaults.
        schema_version: 1 → legacy flat ``{original: translation}`` (round
            31 format); 2 → nested ``{original: {lang: translation}}`` with
            an ``_schema_version`` / ``_format`` / ``default_lang`` envelope
            so ``inject_hook.rpy`` can distinguish the two at load time.
            Default stays v1 so existing runs produce byte-identical output.

    Returns:
        dict — either the flat v1 map or the v2 envelope, per
        ``schema_version``.  Callers that serialise the return value
        downstream (``emit_runtime_hook``) do not need to branch.
    """
    if schema_version not in (1, 2):
        raise ValueError(
            "schema_version must be 1 (flat) or 2 (nested); got %r" % (schema_version,)
        )

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

    if schema_version == 1:
        # v1 flat format — byte-identical to round 31's output.
        return mapping

    # v2 nested envelope.  Each original is keyed under its language bucket
    # so future runs for zh-tw / ja can merge their outputs into the same
    # JSON.  This round only populates one bucket (the caller's target_lang).
    nested: dict[str, dict[str, str]] = {
        original: {target_lang: translation}
        for original, translation in mapping.items()
    }
    return {
        "_schema_version": 2,
        "_format": "renpy-translate",
        "default_lang": target_lang,
        "translations": nested,
    }


def _write_json_atomic(path: Path, data: object) -> None:
    """Write ``data`` as pretty UTF-8 JSON atomically via temp + os.replace.

    Shared helper so every artefact emitted by the runtime hook (translations,
    ui whitelist sidecar, and future v2 schema envelopes) uses identical
    crash-safety: an interrupted run never leaves a half-written file.
    Keys are sorted for stable diffs; ``ensure_ascii=False`` keeps CJK
    content readable when users inspect the files.
    """
    import os as _os
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(
        json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2),
        encoding="utf-8",
    )
    _os.replace(str(tmp_path), str(path))


def emit_runtime_hook(
    output_game_dir: Path,
    translation_db_entries: Iterable[Mapping[str, object]],
    *,
    hook_template_path: Path | None = None,
    hook_filename: str = "zz_tl_inject_hook.rpy",
    ui_button_extensions: Iterable[str] | None = None,
    font_path: Path | None = None,
    schema_version: int = 1,
    target_lang: str = "zh",
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
        ui_button_extensions: Optional iterable of UI-button whitelist
            extensions (round 32 Subtask A).  When non-empty, written to a
            sidecar ``ui_button_whitelist.json`` next to ``translations.json``
            so ``inject_hook.rpy`` can mirror the Python-side extensions at
            runtime.  Empty / None → sidecar file is NOT created, keeping
            default output byte-compatible with round 31.
        font_path: Optional path to a ``.ttf`` / ``.otf`` font file (round 32
            Subtask B).  When set and the file exists, the font is copied to
            ``<output_game_dir>/fonts/tl_inject.ttf`` so the hook's font
            replacement block (keyed on the ``_TL_FONT_REL`` constant) fires
            automatically.  None / missing file → fonts directory NOT
            created.  ``shutil.SameFileError`` (caller passes an already-
            correct destination) is tolerated and silently skipped.
        schema_version: 1 (default) → flat ``translations.json`` matching
            round 31 format; 2 → nested multi-language envelope (round 32
            Subtask C).  Hook reader distinguishes the two via the
            ``_schema_version`` key.
        target_lang: Language code used to key v2 buckets.  Ignored for v1.
            Default ``"zh"`` matches ``core.config.DEFAULTS["target_lang"]``.

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
    # so an interrupted run never leaves a half-written JSON.  v1 returns a
    # flat dict; v2 returns an envelope with an ``_schema_version`` key so
    # the hook can route correctly at load time.
    payload = build_translations_map(
        translation_db_entries,
        target_lang=target_lang,
        schema_version=schema_version,
    )
    json_path = output_game_dir / "translations.json"
    _write_json_atomic(json_path, payload)
    # ``len(mapping)`` in the legacy return shape reflected translation
    # count; preserve that for v2 by counting ``translations`` entries.
    if schema_version == 2 and isinstance(payload, dict):
        entry_count = len(payload.get("translations", {}) or {})
    else:
        entry_count = len(payload) if isinstance(payload, dict) else 0

    # Round 32 Subtask A: optional UI-button whitelist sidecar.  Written
    # only when the caller supplied non-empty extensions — default output
    # stays byte-compatible with round 31 (translations.json + hook only).
    if ui_button_extensions is not None:
        ext_sorted = sorted({str(t) for t in ui_button_extensions if isinstance(t, str) and t})
        if ext_sorted:
            ui_json_path = output_game_dir / "ui_button_whitelist.json"
            _write_json_atomic(ui_json_path, {"extensions": ext_sorted})
            logger.info(
                "[TL-INJECT] emitted UI button sidecar: %d extensions → %s",
                len(ext_sorted), ui_json_path.name,
            )

    # Round 32 Subtask B: optional font bundle.  Target filename is fixed
    # to ``tl_inject.ttf`` to match ``inject_hook.rpy``'s hardcoded
    # ``_TL_FONT_REL`` constant.  Kept as a side-effect (not in the return
    # tuple) so callers that only inspect (json_path, hook_path, count) stay
    # byte-compatible with round 31.
    if font_path is not None:
        font_src = Path(font_path)
        if font_src.is_file():
            fonts_dir = output_game_dir / "fonts"
            fonts_dir.mkdir(parents=True, exist_ok=True)
            dst_font = fonts_dir / "tl_inject.ttf"
            # Path pre-check to handle the src == dst case cross-platform:
            # POSIX would raise ``shutil.SameFileError``; Windows raises
            # ``PermissionError [WinError 32]`` instead.  Resolving both
            # paths first lets us skip the copy entirely and stay portable.
            try:
                same = font_src.resolve() == dst_font.resolve()
            except OSError:
                same = False
            if same:
                logger.debug(
                    "[TL-INJECT] skip font copy — src == dst (%s)", dst_font,
                )
            else:
                try:
                    shutil.copy2(str(font_src), str(dst_font))
                    logger.info(
                        "[TL-INJECT] bundled font: %s → %s",
                        font_src.name, dst_font.relative_to(output_game_dir),
                    )
                except shutil.SameFileError:
                    # Belt-and-braces: even if resolve() disagreed, the
                    # POSIX SameFileError path still degrades gracefully.
                    pass

    # Copy the hook .rpy — shutil.copy2 preserves mtime/permissions so
    # Ren'Py's .rpyc cache invalidation still works when the template
    # is updated upstream.
    hook_out = output_game_dir / hook_filename
    shutil.copy2(str(hook_template_path), str(hook_out))

    logger.info(
        "[TL-INJECT] emitted runtime hook (schema v%d): %d translations → %s (+ %s)",
        schema_version, entry_count, json_path.name, hook_out.name,
    )
    return json_path, hook_out, entry_count


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
        # Round 32 Subtask A: mirror the Python-side UI-button whitelist
        # extensions into a sidecar JSON so the inject_hook can read them
        # at runtime.  Returns frozenset (already empty / populated by
        # main.py before engine.run); we pass through unconditionally —
        # emit_runtime_hook treats empty input as "don't emit sidecar".
        ui_ext: Iterable[str] | None = None
        try:
            from file_processor import get_ui_button_whitelist_extensions
            ui_ext = get_ui_button_whitelist_extensions()
        except ImportError:
            ui_ext = None
        # Round 32 Subtask B: resolve the font via the same helper static
        # mode uses (``--font-file`` preferred, ``resources/fonts/`` fallback)
        # and bundle into ``<output>/game/fonts/tl_inject.ttf``.  None result
        # (no flag, no built-in font) → emit_runtime_hook silently skips the
        # fonts directory.
        font_source: Path | None = None
        try:
            from core.font_patch import resolve_font, default_resources_fonts_dir
            explicit = getattr(args, "font_file", "") or None
            font_source = resolve_font(default_resources_fonts_dir(), explicit)
        except (ImportError, OSError):
            font_source = None
        # Round 32 Subtask C: v1 (flat) vs v2 (nested multi-lang) schema.
        # CLI --runtime-hook-schema is restricted to ["v1", "v2"] via
        # argparse choices; this mapping must stay aligned with the
        # argparse default ("v1") so the emitter kwarg default and CLI
        # default agree — default output stays byte-compatible with r31.
        schema_raw = str(getattr(args, "runtime_hook_schema", "v1") or "v1").lower()
        schema_version = 2 if schema_raw == "v2" else 1
        target_lang = str(getattr(args, "target_lang", "") or "zh") or "zh"
        emit_runtime_hook(
            output_game_dir, entries,
            ui_button_extensions=ui_ext,
            font_path=font_source,
            schema_version=schema_version,
            target_lang=target_lang,
        )
    except (OSError, ValueError, FileNotFoundError) as e:
        logger.warning("[TL-INJECT] emit failed, continuing: %s", e)
