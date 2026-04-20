#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extracted HTML template for ``tools.translation_editor``.

Round 34 Commit 3 split: the raw HTML + inline JS template was 350 lines
of single-purpose constant living at the top of ``tools/translation_editor.py``.
Moving it into this leaf module keeps the main editor file under the
CLAUDE.md 800-line soft limit while preserving byte-identical behaviour —
``translation_editor`` imports ``HTML_TEMPLATE`` and uses it verbatim.

Underscore prefix on the filename marks this as an **internal** helper
module; operators should still run ``python -m tools.translation_editor``
as the public entry point.
"""

from __future__ import annotations


HTML_TEMPLATE = r"""<!DOCTYPE html>
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
/* Round 35 C3: side-by-side multi-language columns (injected dynamically
 * when the operator ticks the checkbox).  Width divides the 38% footprint
 * evenly across N languages; narrow viewports collapse gracefully via
 * word-break but operators should prefer dropdown mode on mobile.
 */
.col-trans-multi { width: 13%; white-space: pre-wrap; word-break: break-word; }
.col-trans-multi[contenteditable] { outline: none; border: 1px solid transparent; border-radius: 3px; min-height: 1.4em; }
.col-trans-multi[contenteditable]:focus { border-color: #1976d2; background: #e3f2fd; }
.col-trans-multi[contenteditable].dirty { background: #fff8e1; }
.col-trans-multi.empty-trans { color: #e53935; font-style: italic; }
th.col-trans-multi, td.col-trans-multi { font-size: 13px; }
.empty-trans { color: #e53935; font-style: italic; }
.file-header { background: #eceff1; padding: 6px 10px; font-weight: bold; font-size: 13px; border-top: 2px solid #b0bec5; }
.file-header td { padding: 6px 10px; }
#no-results { display: none; text-align: center; padding: 40px; color: #999; font-size: 16px; }
#v2-banner { display: none; background: #fff3e0; border-bottom: 2px solid #ffb74d; color: #e65100; padding: 8px 16px; font-size: 13px; position: sticky; top: 49px; z-index: 60; }
#v2-banner code { background: #fff; padding: 1px 6px; border-radius: 3px; font-size: 12px; }

/* Round 38 C4: mobile / narrow-viewport adaptation for side-by-side
 * multi-column mode.  Below 800px the fixed 13% width per language
 * collapses to sub-75px cells at 6 languages — too narrow to edit
 * comfortably on a phone.  This @media block gives each side-by-side
 * cell a readable ``min-width: 120px`` and lets the table scroll
 * horizontally so the rest of the page stays anchored.
 */
@media (max-width: 800px) {
  table { display: block; overflow-x: auto; -webkit-overflow-scrolling: touch; }
  thead, tbody { display: table; width: 100%; }
  .col-trans-multi { min-width: 120px; width: auto; }
  /* File column takes too much space on narrow screens — trim back. */
  .col-file { width: 120px; }
}
</style>
</head>
<body>
<div id="v2-banner"></div>
<div class="toolbar">
  <input type="text" id="search" placeholder="Search original or translation..." autocomplete="off">
  <button class="btn-primary" onclick="doSearch()">Search</button>
  <button onclick="clearSearch()">Clear</button>
  <label><input type="checkbox" id="only-empty" onchange="doSearch()"> Untranslated only</label>
  <label><input type="checkbox" id="only-modified" onchange="doSearch()"> Modified only</label>
  <label id="v2-lang-switch-label" style="display:none;">Language:&nbsp;<select id="v2-lang-switch"></select></label>
  <label id="v2-side-by-side-label" style="display:none;" title="Empty cells are skipped on import (not treated as a delete). To remove a translation bucket, edit the v2 JSON file directly."><input type="checkbox" id="v2-side-by-side" onchange="toggleSideBySide(this.checked)"> Side-by-side</label>
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

// Round 34 C3: currently-selected v2 language.  Empty string means either
// non-v2 mode, or v2 with the envelope's default lang (pre-dropdown init).
let _currentV2Lang = "";

// Round 34 C3: per-row per-lang edit state.  Shape: _edits[idx][lang] = text.
// Populated by the input handler; read by the dropdown switch + exportEdits.
const _edits = {};

function esc(s) { const d = document.createElement("div"); d.textContent = s; return d.innerHTML; }

function initV2UI() {
  // Round 33 Subtask 3 + Round 34 C3: show banner AND populate the in-page
  // language-switch dropdown so the operator can edit multiple buckets
  // without re-invoking the CLI.
  const v2Entry = META.find(e => e.source === "v2");
  if (!v2Entry) return;
  _currentV2Lang = v2Entry.v2_lang || "";
  const langsSeen = v2Entry.v2_langs_seen || [];
  const banner = document.getElementById("v2-banner");
  const other = langsSeen.filter(l => l !== v2Entry.v2_lang);
  const otherHtml = other.length
    ? " | Other buckets in file: " + other.map(l => "<code>" + esc(l) + "</code>").join(", ")
    : " | This is the only language bucket in the file.";
  banner.innerHTML =
    "<b>v2 envelope mode</b> — editing <code id=\"v2-banner-lang\">" + esc(v2Entry.v2_lang) +
    "</code> bucket of <code>" + esc(v2Entry.v2_path) + "</code>" + otherHtml +
    " &nbsp;(use the Language dropdown above to switch without leaving the page)";
  banner.style.display = "block";

  // Populate dropdown.
  if (langsSeen.length > 0) {
    const sel = document.getElementById("v2-lang-switch");
    langsSeen.forEach(function(lang) {
      const opt = document.createElement("option");
      opt.value = lang;
      opt.textContent = lang;
      if (lang === v2Entry.v2_lang) opt.selected = true;
      sel.appendChild(opt);
    });
    sel.addEventListener("change", function() { switchV2Language(this.value); });
    document.getElementById("v2-lang-switch-label").style.display = "inline-flex";
    // Round 35 C3: expose side-by-side toggle only when 2+ languages
    // exist (single-bucket envelopes don't benefit from multi-column view).
    if (langsSeen.length >= 2) {
      document.getElementById("v2-side-by-side-label").style.display = "inline-flex";
    }
  }
}

// Round 35 C3: side-by-side mode state.  When ON, extra per-language
// ``<th>`` / ``<td>`` cells are injected alongside (actually replacing)
// the single ``.col-trans`` column; when OFF, the original round-34
// dropdown mode is restored.
let _sideBySideOn = false;

function _v2LangsForSideBySide() {
  // Returns the language list (from the first v2 entry's v2_langs_seen).
  // All v2 entries share the same envelope so it's safe to read from [0].
  const e = META.find(function(x) { return x.source === "v2"; });
  return (e && e.v2_langs_seen) ? e.v2_langs_seen : [];
}

function toggleSideBySide(on) {
  _sideBySideOn = !!on;
  const langs = _v2LangsForSideBySide();
  if (langs.length === 0) return;

  // First: flush any in-flight DOM edit in the currently-visible lang
  // into _edits so the rebuild below preserves pending work.
  if (_currentV2Lang) {
    rows.forEach(function(tr) {
      const idx = parseInt(tr.dataset.idx);
      const m = META[idx];
      if (!m || m.source !== "v2") return;
      // In dropdown mode, the single .col-trans cell holds the current
      // value.  In side-by-side mode, each .col-trans-multi holds its
      // own lang's value — no flush needed (handlers write directly).
      if (!_sideBySideOn) {
        const tdT = tr.querySelector(".col-trans");
        if (!tdT) return;
        const cur = tdT.textContent.trim();
        const baseline = _getRowBaseline(idx, _currentV2Lang);
        if (cur !== baseline) {
          if (!_edits[idx]) _edits[idx] = {};
          _edits[idx][_currentV2Lang] = cur;
        }
      }
    });
  }

  // Rebuild the header row based on the mode.
  const theadTr = document.querySelector("thead tr");
  // Remove any previously-injected per-lang th cells.
  Array.prototype.slice.call(theadTr.querySelectorAll(".col-trans-multi")).forEach(function(n) {
    n.remove();
  });
  const origHeaderTh = theadTr.querySelector("th.col-trans");
  if (_sideBySideOn) {
    // Hide the single Translation header; inject one th per language.
    origHeaderTh.style.display = "none";
    langs.forEach(function(lang) {
      const th = document.createElement("th");
      th.className = "col-trans-multi";
      th.textContent = lang;
      theadTr.appendChild(th);
    });
  } else {
    origHeaderTh.style.display = "";
  }

  // Rebuild body cells for every v2 row.
  rows.forEach(function(tr) {
    const idx = parseInt(tr.dataset.idx);
    const m = META[idx];
    if (!m || m.source !== "v2") return;
    // Clear any previously-injected per-lang td cells.
    Array.prototype.slice.call(tr.querySelectorAll(".col-trans-multi")).forEach(function(n) {
      n.remove();
    });
    const singleTd = tr.querySelector(".col-trans");
    if (_sideBySideOn) {
      singleTd.style.display = "none";
      langs.forEach(function(lang) {
        const td = document.createElement("td");
        td.className = "col-trans-multi";
        td.setAttribute("contenteditable", "true");
        td.dataset.lang = lang;
        const baseline = _getRowBaseline(idx, lang);
        const pending = (_edits[idx] || {})[lang];
        const value = (pending !== undefined) ? pending : baseline;
        td.textContent = value || "(empty)";
        td.classList.toggle("empty-trans", !value);
        const dirty = (pending !== undefined) && (pending !== baseline);
        td.classList.toggle("dirty", dirty);
        _bindSideBySideCellEvents(td, tr, idx, lang);
        tr.appendChild(td);
      });
    } else {
      singleTd.style.display = "";
      // Restore dropdown-mode rendering using _currentV2Lang as baseline.
      _applyRowFromEdits(tr, idx, _currentV2Lang);
    }
  });

  // Dropdown switch is meaningless when all langs are visible at once;
  // disable (but don't hide — it still shows which lang feeds the
  // single-col view).
  const sel = document.getElementById("v2-lang-switch");
  if (sel) sel.disabled = _sideBySideOn;

  updateStats();
}

function _bindSideBySideCellEvents(td, tr, idx, lang) {
  // Round 35 C3: per-cell input handler writes to _edits[idx][lang]
  // directly — no shared ``_currentV2Lang`` to race against because
  // each cell owns its lang via ``td.dataset.lang``.
  td.addEventListener("input", function() {
    const cur = this.textContent.trim();
    const baseline = _getRowBaseline(idx, lang);
    const changed = cur !== baseline;
    this.classList.toggle("dirty", changed);
    this.classList.toggle("empty-trans", !cur);
    if (!_edits[idx]) _edits[idx] = {};
    if (changed) {
      _edits[idx][lang] = cur;
    } else {
      delete _edits[idx][lang];
    }
    // Row-level modified flag = ANY of its cells is dirty.
    const anyDirty = Array.prototype.slice.call(
      tr.querySelectorAll(".col-trans-multi.dirty")
    ).length > 0;
    tr.classList.toggle("modified", anyDirty);
    tr.dataset.modified = anyDirty ? "1" : "0";
    updateStats();
  });
  td.addEventListener("paste", function(ev) {
    ev.preventDefault();
    const text = (ev.clipboardData || window.clipboardData).getData("text/plain");
    document.execCommand("insertText", false, text);
  });
  td.addEventListener("keydown", function(ev) {
    if (ev.key === "Enter" && !ev.shiftKey) { ev.preventDefault(); }
  });
}

function _getRowBaseline(idx, lang) {
  // Returns the original (un-edited) translation string for (idx, lang).
  // For v2 rows reads from META[idx].languages; for non-v2 rows reads the
  // single-bucket data-orig-trans-map under the empty-string key.
  const m = META[idx];
  if (m.source === "v2") {
    const langs = m.languages || {};
    return langs[lang] || "";
  }
  return m.translation || "";
}

function _applyRowFromEdits(tr, idx, lang) {
  // Rewrite col-trans cell content from either an in-flight edit in
  // _edits[idx][lang] (if present) or the META baseline for (idx, lang).
  // Updates the dirty flag based on diff against the baseline.
  const tdT = tr.querySelector(".col-trans");
  const baseline = _getRowBaseline(idx, lang);
  const pending = (_edits[idx] || {})[lang];
  const value = (pending !== undefined) ? pending : baseline;
  tdT.textContent = value || "(empty)";
  tdT.classList.toggle("empty-trans", !value);
  const dirty = (pending !== undefined) && (pending !== baseline);
  tdT.classList.toggle("dirty", dirty);
  tr.classList.toggle("modified", dirty);
  tr.dataset.modified = dirty ? "1" : "0";
  tr.dataset.trans = (value || "").toLowerCase();
  tr.dataset.empty = value ? "0" : "1";
}

function switchV2Language(newLang) {
  // Round 34 C3: in-page language switch.  (1) flush in-flight edit from
  // the DOM to _edits under the OLD lang so it survives the swap; (2) for
  // every v2 row re-render col-trans using the new language's baseline or
  // pending edit; (3) refresh banner + stats.
  const oldLang = _currentV2Lang;
  if (oldLang && oldLang !== newLang) {
    rows.forEach(function(tr) {
      const idx = parseInt(tr.dataset.idx);
      const m = META[idx];
      if (!m || m.source !== "v2") return;
      const tdT = tr.querySelector(".col-trans");
      const cur = tdT.textContent.trim();
      const baseline = _getRowBaseline(idx, oldLang);
      if (cur !== baseline) {
        // Something was typed in this cell for oldLang; persist before swap.
        if (!_edits[idx]) _edits[idx] = {};
        _edits[idx][oldLang] = cur;
      }
    });
  }
  _currentV2Lang = newLang;
  const bannerLang = document.getElementById("v2-banner-lang");
  if (bannerLang) bannerLang.textContent = newLang;
  rows.forEach(function(tr) {
    const idx = parseInt(tr.dataset.idx);
    const m = META[idx];
    if (!m || m.source !== "v2") return;
    _applyRowFromEdits(tr, idx, newLang);
  });
  updateStats();
}

function init() {
  initV2UI();
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

    // Track edits — round 34 C3: for v2 rows, also persist to _edits under
    // the current v2 language so language switches preserve pending work.
    const tdT = tr.querySelector(".col-trans");
    tdT.addEventListener("input", function() {
      const cur = this.textContent.trim();
      const baseline = e.source === "v2"
        ? _getRowBaseline(i, _currentV2Lang)
        : (this.dataset.origTrans || "");
      const changed = cur !== baseline;
      this.classList.toggle("dirty", changed);
      tr.classList.toggle("modified", changed);
      tr.dataset.modified = changed ? "1" : "0";
      if (e.source === "v2" && _currentV2Lang) {
        if (!_edits[i]) _edits[i] = {};
        _edits[i][_currentV2Lang] = cur;
      }
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
  // Round 34 C3: flush any in-flight DOM-level edit in the currently-
  // visible language into _edits first so the per-(idx, lang) iteration
  // below sees it.  Non-v2 rows continue to read from the DOM directly.
  rows.forEach(function(r) {
    const idx = parseInt(r.dataset.idx);
    const m = META[idx];
    if (!m || m.source !== "v2" || !_currentV2Lang) return;
    const cur = r.querySelector(".col-trans").textContent.trim();
    const baseline = _getRowBaseline(idx, _currentV2Lang);
    if (cur !== baseline) {
      if (!_edits[idx]) _edits[idx] = {};
      _edits[idx][_currentV2Lang] = cur;
    }
  });

  const edits = [];

  // v2 edits: iterate _edits per (idx, lang) so a row edited under three
  // languages produces three separate records (each routed to the correct
  // language bucket in _apply_v2_edits).
  Object.keys(_edits).forEach(function(idxKey) {
    const idx = parseInt(idxKey);
    const m = META[idx];
    if (!m || m.source !== "v2") return;
    const byLang = _edits[idx] || {};
    Object.keys(byLang).forEach(function(lang) {
      const newTrans = byLang[lang];
      const baseline = _getRowBaseline(idx, lang);
      if (newTrans === baseline) return;  // no-op after switch-back
      edits.push({
        source: "v2",
        file: m.file,
        line: m.line,
        original: m.original,
        old_translation: baseline,
        new_translation: newTrans,
        identifier: m.identifier || "",
        v2_path: m.v2_path,
        v2_lang: lang,
      });
    });
  });

  // Non-v2 edits (tl / db source): keep the per-row DOM-read path —
  // _edits is only populated for v2 rows.
  rows.forEach(function(r) {
    if (r.dataset.modified !== "1") return;
    const idx = parseInt(r.dataset.idx);
    const m = META[idx];
    if (!m || m.source === "v2") return;  // v2 already handled above
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
