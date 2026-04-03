#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Translation DB — store per-line translation metadata for incremental workflows."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class TranslationDB:
    """Lightweight JSON-based translation metadata store.

    Entries are de-duplicated by (file, line, original). Later writes override earlier ones.
    """

    def __init__(self, path: Path):
        self.path = path
        self.version: int = 1
        self.entries: List[Dict[str, Any]] = []
        # key: (file, line, original) -> index in entries
        self._index: Dict[Tuple[str, int, str], int] = {}

    def _rebuild_index(self) -> None:
        self._index.clear()
        for idx, entry in enumerate(self.entries):
            key = (
                str(entry.get("file", "")),
                int(entry.get("line", 0) or 0),
                str(entry.get("original", "")),
            )
            if key[0] and key[1] and key[2]:
                self._index[key] = idx

    def load(self) -> None:
        """Load existing DB from disk if present."""
        if not self.path.exists():
            self.entries = []
            self._index = {}
            return
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError, UnicodeDecodeError):
            # Corrupted or incompatible file; start fresh but do not overwrite immediately.
            self.entries = []
            self._index = {}
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

    def save(self) -> None:
        """Persist DB to disk using compact JSON (no indentation) to keep file small."""
        payload = {
            "version": self.version,
            "entries": self.entries,
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # Compact JSON, but keep ensure_ascii=False so non-ASCII is readable.
        self.path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    def upsert_entry(self, entry: Dict[str, Any]) -> None:
        """Insert or update a single entry, de-duplicated by (file, line, original)."""
        file = str(entry.get("file", ""))
        line = int(entry.get("line", 0) or 0)
        original = str(entry.get("original", ""))
        if not file or not line or not original:
            return
        key = (file, line, original)
        idx = self._index.get(key)
        if idx is not None:
            self.entries[idx] = entry
        else:
            self.entries.append(entry)
            self._index[key] = len(self.entries) - 1

    def add_entries(self, entries: List[Dict[str, Any]]) -> None:
        """Bulk insert/update entries."""
        for e in entries:
            self.upsert_entry(e)

    def has_entry(self, file: str, line: int, original: str) -> bool:
        """Check if an entry with given (file, line, original) key exists."""
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

        result: List[Dict[str, Any]] = []
        for e in self.entries:
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

