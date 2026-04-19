#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Translation DB — store per-line translation metadata for incremental workflows.

Thread-safety: all mutating and reading operations are guarded by a re-entrant
lock so that concurrent workers (e.g. ``engines/generic_pipeline.py`` running
``translation_db.upsert_entry`` from a ``ThreadPoolExecutor``) cannot corrupt
``self.entries`` / ``self._index``.

Durability: ``save()`` writes atomically via a temp file + ``os.replace`` so a
mid-write crash or Windows file-handle contention cannot leave a half-written
JSON payload on disk.

Incremental writes: a ``_dirty`` flag short-circuits ``save()`` when nothing
has changed since the last successful persist (previously every pipeline
report path re-serialised the entire DB regardless of changes).

Round 34 schema v2: entries gain an optional ``language`` field and the
``_index`` key becomes a 4-tuple ``(file, line, original, language_or_None)``.
This unblocks first-class multi-language translation pipelines where one
TranslationDB may legitimately contain ``Hello → 你好`` and ``Hello → こんにちは``
as distinct entries keyed by language.  Construction with
``default_language=args.target_lang`` auto-fills the language on upsert for
callers that don't supply it explicitly; loading a v1 file under a caller
that passed ``default_language`` performs a forced backfill so round-33 DBs
adopt the caller's language on first use (prevents "(file,line,orig,None)"
and "(file,line,orig,zh)" double-bucket drift).
"""

from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class TranslationDB:
    """Lightweight JSON-based translation metadata store.

    Entries are de-duplicated by (file, line, original, language).  Later
    writes override earlier ones.  Thread-safe: callers may invoke
    ``upsert_entry`` / ``save`` from multiple threads concurrently.
    """

    #: On-disk schema version written by ``save()``.  Bumped to 2 in round 34
    #: when per-entry ``language`` fields + 4-tuple index keys were added.
    SCHEMA_VERSION: int = 2

    #: Round 37 M2: reject translation_db.json files above this size to bound
    #: memory usage.  A 50 MB DB would hold tens of thousands of entries even
    #: at verbose status / error_codes fields, so this is orders-of-magnitude
    #: headroom over legitimate use; anything larger is almost certainly
    #: malformed or an attacker-crafted artefact worth rejecting up front.
    _MAX_DB_FILE_SIZE: int = 50 * 1024 * 1024

    def __init__(
        self,
        path: Path,
        *,
        default_language: Optional[str] = None,
    ):
        """Construct a TranslationDB backed by ``path``.

        Args:
            path: JSON file path.  Created on first ``save()``.
            default_language: Round 34 opt-in.  When set, every entry upserted
                without an explicit ``language`` field gets it auto-filled from
                this value.  Also triggers the v1→v2 forced backfill on
                ``load()`` — any entry read from an older DB file without a
                ``language`` field adopts this value.  Leave ``None`` for
                round-33 byte-identical behaviour (entries with no language
                stay in the ``None`` bucket, which is a separate index slot
                from any named-language bucket).
        """
        self.path = path
        self.version: int = 1  # loaded-version; save() always writes SCHEMA_VERSION
        self.default_language: Optional[str] = default_language
        self.entries: List[Dict[str, Any]] = []
        # key: (file, line, original, language_or_None) -> index in entries
        self._index: Dict[Tuple[str, int, str, Optional[str]], int] = {}
        # Re-entrant so ``add_entries`` may call ``upsert_entry`` without
        # deadlocking on the same thread.
        self._lock: threading.RLock = threading.RLock()
        # Skip no-op persistence when nothing has changed since last save/load.
        self._dirty: bool = False

    @staticmethod
    def _entry_language(entry: Dict[str, Any]) -> Optional[str]:
        """Extract the normalised language field from an entry dict.

        Returns None when the field is absent or is set to a non-string /
        empty value, so the index's None bucket groups every legacy entry
        that pre-dates the round-34 schema.
        """
        lang = entry.get("language")
        if isinstance(lang, str) and lang:
            return lang
        return None

    def _rebuild_index(self) -> None:
        """Rebuild the (file, line, original, language) -> position index.

        Caller must already hold ``self._lock``.
        """
        self._index.clear()
        for idx, entry in enumerate(self.entries):
            file = str(entry.get("file", ""))
            raw_line = entry.get("line", 0)
            try:
                line = int(raw_line) if raw_line is not None else None
            except (TypeError, ValueError):
                line = None
            original = str(entry.get("original", ""))
            # Keep entries with line == 0 (generic pipeline uses 0 as a
            # placeholder when the source format has no meaningful line info).
            if file and line is not None and original:
                language = self._entry_language(entry)
                self._index[(file, line, original, language)] = idx

    def load(self) -> None:
        """Load existing DB from disk if present.

        Round 34: when the on-disk schema is v1 (or missing version) AND the
        caller constructed with ``default_language``, every entry without a
        ``language`` field is backfilled with the caller's default.  This
        prevents a subsequent upsert (which auto-fills from the same default)
        from creating a parallel ``(file,line,orig,"zh")`` duplicate of each
        existing ``(file,line,orig,None)`` entry.
        """
        with self._lock:
            if not self.path.exists():
                self.entries = []
                self._index = {}
                self._dirty = False
                return
            # Round 37 M2: bound memory before read.  Reject oversize DB
            # files the same way we treat corruption — drop to an empty
            # in-memory state without overwriting the on-disk copy, so
            # an operator can inspect and recover if needed.
            try:
                file_size = self.path.stat().st_size
            except OSError:
                file_size = 0
            if file_size > self._MAX_DB_FILE_SIZE:
                import logging as _logging
                _logging.getLogger(__name__).warning(
                    "[DB] %s too large (%d bytes > %d-byte cap), "
                    "refusing to load to protect memory",
                    self.path, file_size, self._MAX_DB_FILE_SIZE,
                )
                self.entries = []
                self._index = {}
                self._dirty = False
                return
            try:
                data = json.loads(self.path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError, UnicodeDecodeError):
                # Corrupted or incompatible file; start fresh but do not overwrite immediately.
                self.entries = []
                self._index = {}
                self._dirty = False
                return
            if isinstance(data, dict):
                self.version = int(data.get("version", 1) or 1)
                raw_entries = data.get("entries", [])
                if isinstance(raw_entries, list):
                    self.entries = list(raw_entries)
                else:
                    self.entries = []
            else:
                self.entries = []
            # Round 34 / Round 37 M1: forced backfill for any entry lacking
            # a ``language`` field when caller constructed with
            # ``default_language``.  Originally gated on ``version <
            # SCHEMA_VERSION`` (v1 migration path), but a hand-edited v2 DB
            # or a third-party tool can produce a v2 file whose entries
            # still lack language fields — those must also backfill or
            # they'd stay in the None bucket permanently while subsequent
            # ``upsert_entry`` auto-fills fresh writes to the default
            # bucket, causing ``(file,line,orig,None)`` vs
            # ``(file,line,orig,zh)`` duplicate-bucket drift.  Callers
            # that want to preserve None-bucket behaviour should
            # construct without ``default_language``.
            if self.default_language is not None:
                any_backfilled = False
                for entry in self.entries:
                    if isinstance(entry, dict) and "language" not in entry:
                        entry["language"] = self.default_language
                        any_backfilled = True
                if any_backfilled:
                    # Mark dirty so the next save rewrites at SCHEMA_VERSION
                    # with the backfilled language values persisted — one-
                    # way upgrade.
                    self._dirty = True
            self._rebuild_index()
            if not self._dirty:
                self._dirty = False

    def save(self) -> None:
        """Persist DB to disk atomically (temp file + ``os.replace``).

        No-ops when ``_dirty`` is ``False`` to avoid re-serialising an
        unchanged DB on every report pass.  Always writes ``version = SCHEMA_VERSION``
        so the on-disk file reflects the current code's schema after any
        successful save.
        """
        with self._lock:
            if not self._dirty:
                return
            payload = {
                "version": self.SCHEMA_VERSION,
                "entries": list(self.entries),
            }
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix(self.path.suffix + ".tmp")
            try:
                tmp.write_text(
                    json.dumps(payload, ensure_ascii=False), encoding="utf-8"
                )
                os.replace(str(tmp), str(self.path))
            except OSError:
                # Best-effort cleanup of the temp file; re-raise so the caller
                # (pipeline/report layer) can record the failure.
                if tmp.exists():
                    try:
                        tmp.unlink()
                    except OSError:
                        pass
                raise
            self.version = self.SCHEMA_VERSION
            self._dirty = False

    def upsert_entry(self, entry: Dict[str, Any]) -> None:
        """Insert or update a single entry, de-duplicated by
        ``(file, line, original, language)``.

        Accepts ``line == 0`` (generic pipeline uses 0 as a placeholder).
        Silently drops entries missing file/original or with a non-integer line.

        Round 34: if the entry lacks a ``language`` field and this DB was
        constructed with ``default_language``, the entry is shallow-copied
        and stamped with the default language before storage.  Entries that
        already carry a language pass through unchanged (caller-supplied
        language always wins over the DB-level default).
        """
        file = str(entry.get("file", ""))
        raw_line = entry.get("line", 0)
        try:
            line = int(raw_line) if raw_line is not None else None
        except (TypeError, ValueError):
            line = None
        original = str(entry.get("original", ""))
        if not file or line is None or not original:
            return
        # Round 34: auto-fill language from the DB's default if the caller
        # didn't supply one.  Shallow-copy so we never mutate caller's dict.
        if self.default_language is not None and "language" not in entry:
            entry = dict(entry)
            entry["language"] = self.default_language
        language = self._entry_language(entry)
        key = (file, line, original, language)
        with self._lock:
            idx = self._index.get(key)
            if idx is not None:
                self.entries[idx] = entry
            else:
                self.entries.append(entry)
                self._index[key] = len(self.entries) - 1
            self._dirty = True

    def add_entries(self, entries: List[Dict[str, Any]]) -> None:
        """Bulk insert/update entries."""
        with self._lock:
            for e in entries:
                self.upsert_entry(e)

    def has_entry(
        self,
        file: str,
        line: int,
        original: str,
        language: Optional[str] = None,
    ) -> bool:
        """Check if an entry with given
        ``(file, line, original, language)`` key exists.

        Round 34: ``language`` defaults to ``None`` which is the **exact
        match** for the None bucket (not a wildcard).  Callers that want
        "match any language" must iterate ``entries`` directly or query once
        per language.  Legacy callers that only supply 3 positional args
        keep their round-33 behaviour (matched against the None bucket,
        which is where pre-round-34 entries land).
        """
        with self._lock:
            return (file, line, original, language) in self._index

    def filter_by_status(
        self,
        statuses: Optional[List[str]] = None,
        files: Optional[List[str]] = None,
        language: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Return entries filtered by status, files, and/or language.

        Round 34: ``language`` adds a post-filter.  ``None`` (default) means
        "no language filter" — every entry passes; a non-None string keeps
        only entries whose ``language`` field equals that exact value.

        This is a library-level API for future CLI/GUI tools. It is not
        wired to CLI yet.
        """
        if statuses is not None:
            allowed_status = {s.lower() for s in statuses}
        else:
            allowed_status = None
        if files is not None:
            allowed_files = set(files)
        else:
            allowed_files = None

        with self._lock:
            snapshot = list(self.entries)

        result: List[Dict[str, Any]] = []
        for e in snapshot:
            if allowed_status is not None:
                s = str(e.get("status", "")).lower()
                if s not in allowed_status:
                    continue
            if allowed_files is not None:
                f = str(e.get("file", ""))
                if f not in allowed_files:
                    continue
            if language is not None:
                if self._entry_language(e) != language:
                    continue
            result.append(e)
        return result
