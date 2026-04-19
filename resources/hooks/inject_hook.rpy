# Inject Hook — Runtime translation injection (round 31, Tier B)
# ===============================================================
#
# Pairs with ``resources/hooks/extract_hook.rpy`` to close the runtime loop:
#
#     extract_hook.rpy  →  extraction_hooked.json  →  translate  →
#     translations.json + inject_hook.rpy          →  translated game
#
# Deployment (manual):
#   1. Produce ``translations.json`` (flat ``{ "English": "中文" }`` map).
#      ``--emit-runtime-hook`` (round 31 Tier C) can generate it from the
#      tool's ``translation_db.json`` output.
#   2. Copy BOTH this file and ``translations.json`` into the game's
#      ``game/`` directory.
#   3. Launch the game with the env var ``RENPY_TL_INJECT=1`` set.
#      Without the env var, the hook is a no-op — the game runs unmodified,
#      so shipping this file is safe by default.
#
# Differences from the competitor's 737-line YOULING hook:
#   - Pure stdlib, no YOULING-brand dependency.
#   - Font-replacement uses only ``config.font_replacement_map`` (the
#     supported Ren'Py API), not style-object monkey-patching.
#   - Explicit Ren'Py 7.x (Python 2) / 8.x (Python 3) compatibility shims.
#   - UI button skip list matches ``file_processor.COMMON_UI_BUTTONS``
#     so static-tool warnings and runtime skips stay consistent.
#   - Placeholder drift fix matches ``file_processor.fix_chinese_placeholder_drift``.
#
# Inspired by:
#   - renpy-translator (MIT, anonymousException 2024)
#   - The 【微信公众号：刺客边风】游戏汉化翻译 v1.5.2 runtime hook
#     template (closed-source; this file is a clean-room reimplementation
#     of the publicly-visible techniques only).
#
# MIT licence — same as the parent project.

python early:
    import os
    import sys
    import json

    # ------------------------------------------------------------------
    # Activation gate: the hook only runs when the deploying tool sets
    # RENPY_TL_INJECT=1 in the game's launch environment.  This keeps
    # the file safe to ship alongside the game — a user opening the
    # game normally sees zero behaviour change.
    # ------------------------------------------------------------------
    _TL_INJECT_ACTIVE = (os.environ.get("RENPY_TL_INJECT") == "1")


if _TL_INJECT_ACTIVE:
    init python early:
        # ------------------------------------------------------------------
        # Load the translation map from the game directory.
        # Empty / missing / malformed file → hook silently degrades to
        # no-op (print once to stderr so developers can diagnose).
        # ------------------------------------------------------------------
        _TL_MAP = {}
        _TL_JSON_PATH = os.path.join(config.gamedir, "translations.json")
        if os.path.exists(_TL_JSON_PATH):
            try:
                with open(_TL_JSON_PATH, "r") as _f:
                    _raw = _f.read()
                # Decode with an explicit utf-8 pass so Py2 and Py3 both get str.
                if isinstance(_raw, bytes):
                    _raw = _raw.decode("utf-8")
                _TL_MAP = json.loads(_raw)
                if not isinstance(_TL_MAP, dict):
                    _TL_MAP = {}
            except (IOError, OSError, ValueError) as _e:
                sys.stderr.write("[TL-INJECT] failed to load translations.json: %s\n" % _e)
                _TL_MAP = {}

        # Precompute a whitespace-collapsed lookup for robustness.
        _TL_MAP_NORM = {}
        for _k, _v in _TL_MAP.items():
            try:
                _n = " ".join(_k.split())
                if _n and _n not in _TL_MAP_NORM:
                    _TL_MAP_NORM[_n] = _v
            except Exception:
                pass

        # ------------------------------------------------------------------
        # UI button whitelist — mirrors file_processor.COMMON_UI_BUTTONS
        # so static warnings and runtime skips stay in lock-step.  When a
        # game string matches, the hook keeps the English original so
        # the screen layout / hotkey wiring doesn't break.
        # ------------------------------------------------------------------
        _UI_BUTTONS = frozenset((
            "yes", "no", "ok", "cancel", "quit", "return", "exit",
            "back", "next", "skip", "continue", "retry",
            "start", "load", "save", "delete", "new game",
            "main menu", "menu", "preferences", "prefs", "options",
            "settings", "about", "help", "credits",
            "auto", "history", "rollback",
            "confirm", "close", "done", "apply", "reset",
            "on", "off", "enable", "disable",
        ))

        def _tl_is_ui_button(s):
            if not isinstance(s, str):
                return False
            try:
                t = " ".join(s.strip().lower().split())
                return bool(t) and t in _UI_BUTTONS
            except Exception:
                return False

        # ------------------------------------------------------------------
        # Chinese placeholder drift fix — mirrors
        # file_processor.fix_chinese_placeholder_drift.  Applied after a
        # lookup succeeds, so stale translations.json files with drift
        # still render correctly.
        # ------------------------------------------------------------------
        _DRIFT_MAP = (
            ("[姓名]", "[name]"), ("[名字]", "[name]"), ("[名称]", "[name]"),
            ("（姓名）", "[name]"), ("（名字）", "[name]"),
            ("(姓名)", "[name]"), ("(名字)", "[name]"),
            ("{{姓名}}", "{{name}}"), ("{{名字}}", "{{name}}"), ("{{名称}}", "{{name}}"),
        )

        def _tl_fix_drift(s):
            if not s:
                return s
            try:
                for _bad, _good in _DRIFT_MAP:
                    if _bad in s:
                        s = s.replace(_bad, _good)
            except Exception:
                pass
            return s

        # ------------------------------------------------------------------
        # Central lookup: exact → whitespace-collapsed fallback → None.
        # ------------------------------------------------------------------
        def _tl_lookup(s):
            if not isinstance(s, str) or not s:
                return None
            try:
                # L1: exact.
                v = _TL_MAP.get(s)
                if v:
                    return _tl_fix_drift(v)
                # L2: whitespace-collapsed fallback.
                n = " ".join(s.split())
                if n and n != s:
                    v = _TL_MAP_NORM.get(n)
                    if v:
                        return _tl_fix_drift(v)
            except Exception:
                pass
            return None

        # ------------------------------------------------------------------
        # Hook point 1: say_menu_text_filter — the Ren'Py-supported callback
        # that every dialogue / menu / textbutton string passes through.
        # We skip UI buttons explicitly so "OK" / "Cancel" stay English,
        # then look up the translation; on miss we return the original to
        # let Ren'Py's own _() mechanism try next.
        # ------------------------------------------------------------------
        def _tl_menu_filter(what):
            if not isinstance(what, str):
                return what
            if _tl_is_ui_button(what):
                return what
            tr = _tl_lookup(what)
            if tr is not None:
                return tr
            return what

        config.say_menu_text_filter = _tl_menu_filter

        # ------------------------------------------------------------------
        # Hook point 2: config.replace_text — a coarser callback that
        # catches strings rendered outside the say/menu path (screen
        # textbutton labels, imagemap tooltips, etc.).  Same UI-button
        # skip + drift-fix rules.
        # ------------------------------------------------------------------
        def _tl_replace_text(s):
            if not isinstance(s, str):
                return s
            if _tl_is_ui_button(s):
                return s
            tr = _tl_lookup(s)
            if tr is not None:
                return tr
            return s

        config.replace_text = _tl_replace_text

        # ------------------------------------------------------------------
        # Hook point 3: Character.__call__ — last-resort wrapper for
        # dialogue paths that bypass the menu filter (rare but observed
        # on custom NVL character subclasses).  Guarded with try/except
        # so a misbehaving subclass cannot break the game.
        # ------------------------------------------------------------------
        try:
            _tl_real_char_call = Character.__call__

            def _tl_character_call(self, what, *args, **kwargs):
                if isinstance(what, str):
                    try:
                        if not _tl_is_ui_button(what):
                            tr = _tl_lookup(what)
                            if tr is not None:
                                what = tr
                    except Exception:
                        pass
                return _tl_real_char_call(self, what, *args, **kwargs)

            Character.__call__ = _tl_character_call
        except (AttributeError, NameError):
            pass

        # ------------------------------------------------------------------
        # Ren'Py 7.x / 8.x compatibility layer.
        # Ren'Py 7 (Python 2) exposes renpy.curry as a *module* with a
        # ``curry`` attribute; Ren'Py 8 made it a *callable* directly.
        # Some third-party .rpy helpers rely on the 7.x shape.  If the
        # runtime looks like 8.x, wrap curry in a proxy object so both
        # ``renpy.curry(...)`` and ``renpy.curry.curry(...)`` resolve.
        # ------------------------------------------------------------------
        try:
            import renpy as _renpy_mod
            _curry_attr = getattr(_renpy_mod, "curry", None)
            if _curry_attr is not None and callable(_curry_attr) and not hasattr(_curry_attr, "curry"):
                class _TLCurryProxy(object):
                    def __init__(self, inner):
                        self._inner = inner
                    def __call__(self, *args, **kwargs):
                        return self._inner(*args, **kwargs)
                    def curry(self, *args, **kwargs):
                        return self._inner(*args, **kwargs)
                _renpy_mod.curry = _TLCurryProxy(_curry_attr)
        except Exception:
            pass

        # ------------------------------------------------------------------
        # Font replacement — only the supported ``config.font_replacement_map``
        # API, no style-object patching.  The map is populated only if
        # ``game/fonts/tl_inject.ttf`` exists alongside this hook; otherwise
        # the game keeps its original fonts (translation still applies).
        # ------------------------------------------------------------------
        _TL_FONT_REL = "fonts/tl_inject.ttf"
        _TL_FONT_ABS = os.path.join(config.gamedir, _TL_FONT_REL)
        if os.path.exists(_TL_FONT_ABS):
            try:
                for _f in renpy.list_files():
                    try:
                        if not _f.lower().endswith((".ttf", ".otf")):
                            continue
                        # Never replace icon fonts — they encode glyphs as
                        # private-use codepoints that a Chinese TTF won't have.
                        _low = _f.lower()
                        if any(_k in _low for _k in (
                            "fontawesome", "material", "mdi", "icon", "emoji", "symbol",
                        )):
                            continue
                        if _f == _TL_FONT_REL:
                            continue
                        # Map the font in all bold / italic combinations.
                        for _bold in (True, False):
                            for _italic in (True, False):
                                config.font_replacement_map[(_f, _bold, _italic)] = (
                                    _TL_FONT_REL, False, False,
                                )
                    except Exception:
                        pass
            except Exception as _e:
                sys.stderr.write("[TL-INJECT] font replacement failed: %s\n" % _e)
