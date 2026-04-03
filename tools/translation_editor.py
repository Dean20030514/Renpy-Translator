#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Translation Editor — Interactive HTML Review & Edit Tool
=========================================================

Export translated Ren'Py files to an interactive HTML page where reviewers
can search, filter, and **edit** translations in a browser, then import the
changes back into the ``.rpy`` files.

Supports two data sources:
    - **tl-mode**: Reads ``tl/<lang>/*.rpy`` via ``tl_parser`` (DialogueEntry /
      StringEntry with precise ``tl_line`` positioning).
    - **translation_db**: Reads ``translation_db.json`` produced by direct-mode
      or the one-click pipeline (entries with file / line / original / translation).

Export produces a self-contained HTML file; import reads a JSON file that the
HTML page's "Export Edits" button generates.

Usage::

    # Export (tl-mode)
    python -m tools.translation_editor --export --tl-dir game/tl/chinese --output review.html

    # Export (from translation_db.json)
    python -m tools.translation_editor --export --db translation_db.json --output review.html

    # Import edits back
    python -m tools.translation_editor --import-json edits.json

Pure standard library — no external dependencies.
"""

from __future__ import annotations

import argparse
import html
import json
import logging
import re
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


# ============================================================
# Data extraction
# ============================================================

def _extract_from_tl_dir(tl_dir: Path) -> List[Dict[str, Any]]:
    """Extract translation entries from tl/<lang>/ directory using tl_parser."""
    from translators.tl_parser import parse_tl_file, DialogueEntry

    entries: List[Dict[str, Any]] = []
    rpy_files = sorted(tl_dir.rglob("*.rpy"))
    if not rpy_files:
        logger.warning("No .rpy files found in %s", tl_dir)
        return entries

    for rpy in rpy_files:
        result = parse_tl_file(str(rpy))
        for d in result.dialogues:
            entries.append({
                "source": "tl",
                "file": str(rpy),
                "line": d.tl_line,
                "original": d.original,
                "translation": d.translation,
                "character": d.character,
                "identifier": d.identifier,
                "source_file": d.source_file,
                "source_line": d.source_line,
            })
        for s in result.strings:
            entries.append({
                "source": "tl",
                "file": str(rpy),
                "line": s.tl_line,
                "original": s.old,
                "translation": s.new,
                "character": "",
                "identifier": "",
                "source_file": s.source_file,
                "source_line": s.source_line,
            })
    return entries


def _extract_from_db(db_path: Path) -> List[Dict[str, Any]]:
    """Extract translation entries from translation_db.json."""
    data = json.loads(db_path.read_text(encoding="utf-8"))
    raw_entries = data.get("entries", [])
    entries: List[Dict[str, Any]] = []
    for e in raw_entries:
        entries.append({
            "source": "db",
            "file": e.get("file", ""),
            "line": e.get("line", 0),
            "original": e.get("original", ""),
            "translation": e.get("translation", ""),
            "character": "",
            "identifier": "",
            "source_file": e.get("file", ""),
            "source_line": e.get("line", 0),
        })
    return entries


# ============================================================
# HTML generation
# ============================================================

_HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>Translation Editor</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, "Segoe UI", Roboto, "Noto Sans SC", sans-serif; background: #f5f5f5; color: #333; }
.toolbar { position: sticky; top: 0; z-index: 100; background: #fff; padding: 8px 16px; border-bottom: 1px solid #ddd; display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
.toolbar input[type=text] { padding: 6px 10px; border: 1px solid #ccc; border-radius: 4px; width: 260px; font-size: 14px; }
.toolbar button { padding: 6px 14px; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; }
.btn-primary { background: #1976d2; color: #fff; }
.btn-primary:hover { background: #1565c0; }
.btn-warn { background: #f57c00; color: #fff; }
.btn-warn:hover { background: #e65100; }
.stats { font-size: 13px; color: #666; margin-left: auto; }
table { width: 100%; border-collapse: collapse; background: #fff; margin: 0 auto; }
th { background: #e3f2fd; padding: 8px 10px; text-align: left; font-size: 13px; position: sticky; top: 49px; z-index: 50; border-bottom: 2px solid #90caf9; }
td { padding: 6px 10px; border-bottom: 1px solid #eee; font-size: 14px; vertical-align: top; }
tr.modified td { background: #fff8e1; }
tr.hidden { display: none; }
.col-idx { width: 40px; color: #999; font-size: 12px; text-align: center; }
.col-file { width: 180px; font-size: 12px; color: #666; word-break: break-all; }
.col-char { width: 60px; font-size: 12px; color: #9c27b0; }
.col-orig { width: 38%; white-space: pre-wrap; word-break: break-word; }
.col-trans { width: 38%; white-space: pre-wrap; word-break: break-word; }
.col-trans[contenteditable] { outline: none; border: 1px solid transparent; border-radius: 3px; min-height: 1.4em; }
.col-trans[contenteditable]:focus { border-color: #1976d2; background: #e3f2fd; }
.col-trans[contenteditable].dirty { background: #fff8e1; }
.empty-trans { color: #e53935; font-style: italic; }
.file-header { background: #eceff1; padding: 6px 10px; font-weight: bold; font-size: 13px; border-top: 2px solid #b0bec5; }
.file-header td { padding: 6px 10px; }
#no-results { display: none; text-align: center; padding: 40px; color: #999; font-size: 16px; }
</style>
</head>
<body>
<div class="toolbar">
  <input type="text" id="search" placeholder="Search original or translation..." autocomplete="off">
  <button class="btn-primary" onclick="doSearch()">Search</button>
  <button onclick="clearSearch()">Clear</button>
  <label><input type="checkbox" id="only-empty" onchange="doSearch()"> Untranslated only</label>
  <label><input type="checkbox" id="only-modified" onchange="doSearch()"> Modified only</label>
  <button class="btn-warn" onclick="exportEdits()">Export Edits</button>
  <span class="stats" id="stats"></span>
</div>
<table>
<thead><tr>
  <th class="col-idx">#</th>
  <th class="col-file">File</th>
  <th class="col-char">Speaker</th>
  <th class="col-orig">Original</th>
  <th class="col-trans">Translation</th>
</tr></thead>
<tbody id="tbody"></tbody>
</table>
<div id="no-results">No matching entries</div>
<script type="application/json" id="metadata">__METADATA__</script>
<script>
"use strict";
const META = JSON.parse(document.getElementById("metadata").textContent);
const tbody = document.getElementById("tbody");
const rows = [];
let totalModified = 0;

function esc(s) { const d = document.createElement("div"); d.textContent = s; return d.innerHTML; }

function init() {
  let lastFile = "";
  META.forEach((e, i) => {
    if (e.file !== lastFile) {
      lastFile = e.file;
      const fh = document.createElement("tr");
      fh.className = "file-header";
      fh.innerHTML = '<td colspan="5">' + esc(e.file) + '</td>';
      tbody.appendChild(fh);
    }
    const tr = document.createElement("tr");
    tr.dataset.idx = i;
    tr.dataset.orig = e.original.toLowerCase();
    tr.dataset.trans = (e.translation || "").toLowerCase();
    tr.dataset.empty = e.translation ? "0" : "1";

    const tdIdx = '<td class="col-idx">' + (i + 1) + '</td>';
    const shortFile = e.file.split(/[/\\]/).slice(-2).join("/");
    const tdFile = '<td class="col-file" title="' + esc(e.file) + '">' + esc(shortFile) + ':' + e.line + '</td>';
    const tdChar = '<td class="col-char">' + esc(e.character || "") + '</td>';
    const tdOrig = '<td class="col-orig">' + esc(e.original) + '</td>';

    let transHtml;
    if (e.translation) {
      transHtml = '<td class="col-trans" contenteditable="true" data-orig-trans="' + esc(e.translation) + '">' + esc(e.translation) + '</td>';
    } else {
      transHtml = '<td class="col-trans empty-trans" contenteditable="true" data-orig-trans="">(empty)</td>';
    }
    tr.innerHTML = tdIdx + tdFile + tdChar + tdOrig + transHtml;
    tbody.appendChild(tr);
    rows.push(tr);

    // Track edits
    const tdT = tr.querySelector(".col-trans");
    tdT.addEventListener("input", function() {
      const cur = this.textContent.trim();
      const orig = this.dataset.origTrans;
      const changed = cur !== orig;
      this.classList.toggle("dirty", changed);
      tr.classList.toggle("modified", changed);
      tr.dataset.modified = changed ? "1" : "0";
      updateStats();
    });
    tdT.addEventListener("paste", function(ev) {
      ev.preventDefault();
      const text = (ev.clipboardData || window.clipboardData).getData("text/plain");
      document.execCommand("insertText", false, text);
    });
    tdT.addEventListener("keydown", function(ev) {
      if (ev.key === "Enter" && !ev.shiftKey) { ev.preventDefault(); }
    });
    tr.dataset.modified = "0";
  });
  updateStats();
}

function updateStats() {
  totalModified = rows.filter(r => r.dataset.modified === "1").length;
  const visible = rows.filter(r => !r.classList.contains("hidden")).length;
  const empty = rows.filter(r => r.dataset.empty === "1").length;
  document.getElementById("stats").textContent =
    "Total: " + rows.length + " | Visible: " + visible + " | Untranslated: " + empty + " | Modified: " + totalModified;
}

function doSearch() {
  const q = document.getElementById("search").value.toLowerCase();
  const onlyEmpty = document.getElementById("only-empty").checked;
  const onlyMod = document.getElementById("only-modified").checked;
  let visCount = 0;
  // Also hide/show file headers
  const fileHeaders = tbody.querySelectorAll(".file-header");
  const fileVis = {};
  rows.forEach(r => {
    let show = true;
    if (q && r.dataset.orig.indexOf(q) === -1 && r.dataset.trans.indexOf(q) === -1) show = false;
    if (onlyEmpty && r.dataset.empty !== "1") show = false;
    if (onlyMod && r.dataset.modified !== "1") show = false;
    r.classList.toggle("hidden", !show);
    if (show) visCount++;
  });
  document.getElementById("no-results").style.display = visCount ? "none" : "block";
  updateStats();
}
function clearSearch() {
  document.getElementById("search").value = "";
  document.getElementById("only-empty").checked = false;
  document.getElementById("only-modified").checked = false;
  doSearch();
}

function exportEdits() {
  const edits = [];
  rows.forEach(r => {
    if (r.dataset.modified !== "1") return;
    const idx = parseInt(r.dataset.idx);
    const m = META[idx];
    const newTrans = r.querySelector(".col-trans").textContent.trim();
    edits.push({
      source: m.source,
      file: m.file,
      line: m.line,
      original: m.original,
      old_translation: m.translation,
      new_translation: newTrans,
      identifier: m.identifier || "",
    });
  });
  if (!edits.length) { alert("No modifications to export."); return; }
  const blob = new Blob([JSON.stringify(edits, null, 2)], {type: "application/json"});
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "translation_edits.json";
  a.click();
  URL.revokeObjectURL(a.href);
  alert("Exported " + edits.length + " edits to translation_edits.json");
}

init();
</script>
</body>
</html>"""


def export_html(
    entries: List[Dict[str, Any]],
    output_path: Path,
) -> int:
    """Generate an interactive HTML editor from translation entries.

    Returns the number of entries written.
    """
    if not entries:
        logger.warning("No entries to export")
        return 0

    # Sanitize entries for JSON embedding
    safe_entries = []
    for e in entries:
        safe_entries.append({
            "source": e.get("source", ""),
            "file": e.get("file", ""),
            "line": e.get("line", 0),
            "original": e.get("original", ""),
            "translation": e.get("translation", ""),
            "character": e.get("character", ""),
            "identifier": e.get("identifier", ""),
            "source_file": e.get("source_file", ""),
            "source_line": e.get("source_line", 0),
        })

    metadata_json = json.dumps(safe_entries, ensure_ascii=False)
    html_content = _HTML_TEMPLATE.replace("__METADATA__", metadata_json)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html_content, encoding="utf-8")
    logger.info("Exported %d entries to %s", len(safe_entries), output_path)
    return len(safe_entries)


# ============================================================
# Import edits
# ============================================================

def import_edits(
    edits_path: Path,
    *,
    create_backup: bool = True,
) -> Dict[str, int]:
    """Import edits from the JSON file exported by the HTML editor.

    Supports two modes based on ``source`` field:
        - ``"tl"``: Uses ``tl_parser.fill_translation`` approach — replaces
          the string at exact ``tl_line`` in the file.
        - ``"db"``: Uses ``patcher.apply_translations`` approach — matches
          by line number and original text in the source .rpy file.

    Args:
        edits_path: Path to the ``translation_edits.json`` file.
        create_backup: Whether to create ``.bak`` backups before modifying.

    Returns:
        ``{"applied": N, "skipped": N, "files_modified": N}``
    """
    edits = json.loads(edits_path.read_text(encoding="utf-8"))
    if not edits:
        return {"applied": 0, "skipped": 0, "files_modified": 0}

    # Group edits by file
    by_file: Dict[str, List[Dict[str, Any]]] = {}
    for edit in edits:
        f = edit.get("file", "")
        if not f:
            continue
        by_file.setdefault(f, []).append(edit)

    applied = 0
    skipped = 0
    files_modified = 0

    for filepath_str, file_edits in sorted(by_file.items()):
        filepath = Path(filepath_str)
        if not filepath.is_file():
            logger.warning("File not found, skipping %d edits: %s", len(file_edits), filepath)
            skipped += len(file_edits)
            continue

        # Backup
        if create_backup:
            bak = filepath.with_suffix(filepath.suffix + ".bak")
            if not bak.exists():
                shutil.copy2(filepath, bak)

        content = filepath.read_text(encoding="utf-8-sig")
        lines = content.splitlines()
        has_trailing_nl = content.endswith("\n")
        file_changed = False

        for edit in file_edits:
            new_trans = edit.get("new_translation", "").strip()
            if not new_trans:
                skipped += 1
                continue

            line_idx = edit.get("line", 0) - 1  # 1-based → 0-based
            if line_idx < 0 or line_idx >= len(lines):
                logger.warning("Line %d out of range in %s", edit.get("line", 0), filepath)
                skipped += 1
                continue

            source = edit.get("source", "tl")
            line = lines[line_idx]

            if source == "tl":
                # tl-mode: replace the quoted string at tl_line
                old_trans = edit.get("old_translation", "")
                if old_trans:
                    # Replace old translation with new
                    target = f'"{old_trans}"'
                    replacement = f'"{_escape_for_rpy(new_trans)}"'
                    if target in line:
                        lines[line_idx] = line.replace(target, replacement, 1)
                        applied += 1
                        file_changed = True
                        continue
                # Fallback: replace empty "" or any first quoted string
                if '""' in line:
                    lines[line_idx] = line.replace('""', f'"{_escape_for_rpy(new_trans)}"', 1)
                    applied += 1
                    file_changed = True
                else:
                    # Try replacing first quoted string
                    m = re.search(r'"([^"]*)"', line)
                    if m:
                        old_q = f'"{m.group(1)}"'
                        lines[line_idx] = line.replace(old_q, f'"{_escape_for_rpy(new_trans)}"', 1)
                        applied += 1
                        file_changed = True
                    else:
                        logger.warning("Cannot find quoted string at line %d in %s", edit.get("line", 0), filepath)
                        skipped += 1

            else:
                # db/direct-mode: match original text and replace
                original = edit.get("original", "")
                if original and original in line:
                    escaped = _escape_for_rpy(new_trans)
                    lines[line_idx] = line.replace(original, escaped, 1)
                    applied += 1
                    file_changed = True
                else:
                    logger.warning("Original text not found at line %d in %s", edit.get("line", 0), filepath)
                    skipped += 1

        if file_changed:
            result = "\n".join(lines)
            if has_trailing_nl:
                result += "\n"
            filepath.write_text(result, encoding="utf-8")
            files_modified += 1

    return {"applied": applied, "skipped": skipped, "files_modified": files_modified}


def _escape_for_rpy(text: str) -> str:
    """Escape text for safe embedding in a Ren'Py quoted string."""
    return text.replace("\\", "\\\\").replace('"', '\\"')


# ============================================================
# CLI
# ============================================================

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Interactive HTML translation editor — export, edit in browser, import back",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--export", action="store_true", help="Export translations to interactive HTML")
    group.add_argument("--import-json", type=str, metavar="PATH", help="Import edits from JSON file")

    parser.add_argument("--tl-dir", type=str, help="tl/<lang>/ directory for tl-mode export")
    parser.add_argument("--db", type=str, help="translation_db.json path for direct-mode export")
    parser.add_argument("--output", "-o", default="translation_editor.html", help="Output HTML path")
    parser.add_argument("--no-backup", action="store_true", help="Skip .bak backup on import")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    if args.export:
        entries: List[Dict[str, Any]] = []
        if args.tl_dir:
            entries = _extract_from_tl_dir(Path(args.tl_dir))
        elif args.db:
            entries = _extract_from_db(Path(args.db))
        else:
            parser.error("--export requires --tl-dir or --db")
            return

        if not entries:
            print("No entries found to export", file=sys.stderr)
            sys.exit(1)

        count = export_html(entries, Path(args.output))
        print(f"Exported {count} entries to {args.output}")

    elif args.import_json:
        result = import_edits(Path(args.import_json), create_backup=not args.no_backup)
        print(
            f"Import complete: {result['applied']} applied, "
            f"{result['skipped']} skipped, {result['files_modified']} files modified"
        )


if __name__ == "__main__":
    main()
