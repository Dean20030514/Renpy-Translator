#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UI event handler mixin — split from ``gui.py`` in round 41.

Contains the three pure-UI event handlers that react to combobox /
radiobutton selections by toggling panels, enabling / disabling entry
widgets, or updating the command preview.  Behaviour is byte-identical
to the pre-r41 definitions under ``class App``.

``_PROVIDER_DEFAULTS`` is duplicated here (7 lines) so the mixin stays
self-contained — importing it from ``gui`` would form a cycle
(``gui.py`` imports this module at load time).  The data rarely
changes; the minor DRY violation is preferred over an import graph
complication.

Requires a host class (``gui.App``) that exposes the following
attributes on ``self`` at call time: ``var_engine``, ``var_renpy_mode``,
``var_provider``, ``var_model``, ``lbl_engine_hint``, ``panel_renpy``,
``panel_rpgmaker``, ``panel_csv``, ``entry_tl_lang``, ``frame_pipeline``,
and the ``_update_preview`` method.  The mixin does not own state —
all reads / writes go through ``self``.
"""

from __future__ import annotations

import tkinter as tk


# Duplicated from gui.py to keep this mixin import-cycle-free.  See
# module docstring for rationale.
_PROVIDER_DEFAULTS = {
    "xai": "grok-4-1-fast-reasoning",
    "openai": "gpt-4o-mini",
    "deepseek": "deepseek-chat",
    "claude": "claude-sonnet-4",
    "gemini": "gemini-2.5-flash",
}


class AppHandlersMixin:
    """UI event handlers mixed into :class:`gui.App`."""

    def _on_engine_change(self) -> None:
        engine = self.var_engine.get()
        self.lbl_engine_hint.config(text=f"当前引擎: {engine}")
        # 隐藏所有面板
        for p in (self.panel_renpy, self.panel_rpgmaker, self.panel_csv):
            p.pack_forget()
        # 显示对应面板
        if engine in ("auto", "renpy"):
            self.panel_renpy.pack(fill=tk.BOTH, expand=True)
            self._on_renpy_mode_change()
        elif engine == "rpgmaker":
            self.panel_rpgmaker.pack(fill=tk.BOTH, expand=True)
        elif engine in ("csv", "jsonl"):
            self.panel_csv.pack(fill=tk.BOTH, expand=True)
        self._update_preview()

    def _on_renpy_mode_change(self) -> None:
        mode = self.var_renpy_mode.get()
        is_tl = mode in ("tl", "pipeline")
        self.entry_tl_lang.config(state="normal" if is_tl else "disabled")
        if mode == "pipeline":
            self.frame_pipeline.grid()
        else:
            self.frame_pipeline.grid_remove()
        self._update_preview()

    def _on_provider_change(self) -> None:
        provider = self.var_provider.get()
        default_model = _PROVIDER_DEFAULTS.get(provider, "")
        self.var_model.set(default_model)
        self._update_preview()
