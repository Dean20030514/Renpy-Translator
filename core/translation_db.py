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
"""

from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class TranslationDB:
    """Lightweight JSON-based translation metadata store.

    Entries are de-duplicated by (file, line, original). Later writes override earlier ones.
    Thread-safe: callers may invoke ``upsert_entry`` / ``save`` from multiple
    threads concurrently.
    """

    def __init__(self, path: Path):
        self.path = path
        self.version: int = 1
        self.entries: List[Dict[str, Any]] = []
        # key: (file, line, original) -> index in entries
        self._index: Dict[Tuple[str, int, str], int] = {}
        # Re-entrant so ``add_entries`` may call ``upsert_entry`` without
        # deadlocking on the same thread.
        self._lock: threading.RLock = threading.RLock()
        # Skip no-op persistence when nothing has changed since last save/load.
        self._dirty: bool = False

    def _rebuild_index(self) -> None:
        """Rebuild the (file, line, original) -> position index.

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
                self._index[(file, line, original)] = idx

    def load(self) -> None:
        """Load existing DB from disk if present."""
        with self._lock:
            if not self.path.exists():
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
            self._rebuild_index()
            self._dirty = False

    def save(self) -> None:
        """Persist DB to disk atomically (temp file + ``os.replace``).

        No-ops when ``_dirty`` is ``False`` to avoid re-serialising an
        unchanged DB on every report pass.
        """
        with self._lock:
            if not self._dirty:
                return
            payload = {
                "version": self.version,
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
            self._dirty = False

    def upsert_entry(self, entry: Dict[str, Any]) -> None:
        """Insert or update a single entry, de-duplicated by (file, line, original).

        Accepts ``line == 0`` (generic pipeline uses 0 as a placeholder).
        Silently drops entries missing file/original or with a non-integer line.
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
        key = (file, line, original)
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

    def has_entry(self, file: str, line: int, original: str) -> bool:
        """Check if an entry with given (file, line, original) key exists."""
        with self._lock:
            return (file, line, original) in self._index

    def filter_by_status(
        self,
        statuses: Optional[List[str]] = None,
        files: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Return entries filtered by status and/or file list.

        This is a library-level API for future CLI/GUI tools. It is not wired to CLI yet.
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
            result.append(e)
        return result
