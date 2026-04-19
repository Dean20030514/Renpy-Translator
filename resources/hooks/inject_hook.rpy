# Inject Hook — Runtime translation injection (round 31, Tier B)
# ===============================================================
#
# Pairs with ``resources/hooks/extract_hook.rpy`` to close the runtime loop:
#
#     extract_hook.rpy  →  extraction_hooked.json  →  translate  →
#     translations.json + inject_hook.rpy          →  translated game
#
# Deployment (manual):
#   1. Produce ``translations.json`` using ``--emit-runtime-hook``
#      (round 31 Tier C, round 32 Subtask C):
#        v1 schema (default): flat ``{ "English": "中文" }`` map
#        v2 schema (``--runtime-hook-schema v2``): nested multi-language
#          envelope ``{"_schema_version": 2, "_format": "renpy-translate",
#          "default_lang": "zh", "translations": {"English": {"zh": "中文"}}}``
#   2. (optional, v2) Run additional translation passes with different
#      ``--target-lang`` values and merge their ``translations`` dicts to
#      get a single file with ``{zh, zh-tw, ja}`` buckets per string.
#   3. Copy this file, ``translations.json``, and (optionally)
#      ``ui_button_whitelist.json`` + ``fonts/tl_inject.ttf`` into the
#      game's ``game/`` directory.
#   4. Launch the game with the env var ``RENPY_TL_INJECT=1`` set.
#      Without the env var, the hook is a no-op — the game runs unmodified,
#      so shipping this file is safe by default.
#
# Runtime environment variables:
#   RENPY_TL_INJECT       Required; set to "1" to activate the hook.
#   RENPY_TL_INJECT_LANG  v2 schema only; optional language override
#                         ("zh" / "zh-tw" / "ja" / ...).  Falls back to
#                         ``renpy.preferences.language`` then to the JSON's
#                         ``default_lang``.
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

        # ------------------------------------------------------------------
        # Round 32 Subtask C: schema detection.  v1 (legacy) is a flat
        # ``{english: chinese}`` map; v2 wraps the translations in an
        # envelope with a ``_schema_version`` key so future multi-language
        # payloads can coexist with the hook.  For v2, ``_TL_TRANSLATIONS``
        # maps ``english -> {lang: translation}`` instead of directly to the
        # translation string — all downstream lookups route through
        # ``_tl_resolve_bucket`` so the language-pick policy lives in one
        # place.  Behaviour when no envelope is present is byte-identical
        # to round 31.
        # ------------------------------------------------------------------
        _TL_SCHEMA = 1
        _TL_TRANSLATIONS = _TL_MAP
        _TL_DEFAULT_LANG = None
        if isinstance(_TL_MAP, dict) and _TL_MAP.get("_schema_version") == 2:
            _TL_SCHEMA = 2
            _nested = _TL_MAP.get("translations")
            _TL_TRANSLATIONS = _nested if isinstance(_nested, dict) else {}
            _dl = _TL_MAP.get("default_lang")
            if isinstance(_dl, str) and _dl:
                _TL_DEFAULT_LANG = _dl

        # Precompute a whitespace-collapsed lookup for robustness.
        # Value type matches ``_TL_TRANSLATIONS`` — str for v1, dict for v2.
        _TL_MAP_NORM = {}
        for _k, _v in _TL_TRANSLATIONS.items():
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

        # ------------------------------------------------------------------
        # Round 32 Subtask A: optional user-supplied UI-button extensions.
        # Mirrors ``file_processor._ui_button_extensions`` via the sidecar
        # ``ui_button_whitelist.json`` emitted alongside ``translations.json``
        # when ``--ui-button-whitelist`` was set on the translate side.  Same
        # degradation rules as ``_TL_MAP`` — missing / malformed file → empty
        # set, never aborts hook load.
        # ------------------------------------------------------------------
        _TL_UI_EXT = set()
        _TL_UI_EXT_PATH = os.path.join(config.gamedir, "ui_button_whitelist.json")
        if os.path.exists(_TL_UI_EXT_PATH):
            try:
                with open(_TL_UI_EXT_PATH, "r") as _f:
                    _raw_ui = _f.read()
                if isinstance(_raw_ui, bytes):
                    _raw_ui = _raw_ui.decode("utf-8")
                _data_ui = json.loads(_raw_ui)
                if isinstance(_data_ui, dict) and isinstance(_data_ui.get("extensions"), list):
                    for _tok in _data_ui["extensions"]:
                        try:
                            if isinstance(_tok, bytes):
                                _tok = _tok.decode("utf-8")
                            if isinstance(_tok, str):
                                _n = " ".join(_tok.strip().lower().split())
                                if _n:
                                    _TL_UI_EXT.add(_n)
                        except Exception:
                            pass
            except (IOError, OSError, ValueError) as _e:
                sys.stderr.write("[TL-INJECT] failed to load ui_button_whitelist.json: %s\n" % _e)
                _TL_UI_EXT = set()

        def _tl_is_ui_button(s):
            if not isinstance(s, str):
                return False
            try:
                t = " ".join(s.strip().lower().split())
                if not t:
                    return False
                return t in _UI_BUTTONS or t in _TL_UI_EXT
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
        # Round 32 Subtask C: runtime language resolver for v2 schema.
        # Priority: RENPY_TL_INJECT_LANG env var > renpy.preferences.language
        # (if set and not the string "None") > default_lang from JSON > None.
        # Defensive around preferences: at init python early: time on some
        # Ren'Py builds renpy.preferences may not yet be constructed.
        # ------------------------------------------------------------------
        def _tl_resolve_lang():
            try:
                _env = os.environ.get("RENPY_TL_INJECT_LANG")
                if _env:
                    return _env
            except Exception:
                pass
            try:
                _prefs = getattr(renpy, "preferences", None)
                _lang = getattr(_prefs, "language", None) if _prefs is not None else None
                if _lang and _lang != "None":
                    return _lang
            except Exception:
                pass
            return _TL_DEFAULT_LANG

        def _tl_resolve_bucket(bucket):
            """Pick a translation string from a v2 ``{lang: text}`` dict.

            Falls back to ``_TL_DEFAULT_LANG`` if the resolved runtime lang
            has no entry; returns None if nothing matches (so the caller can
            degrade to returning the original English).
            """
            if not isinstance(bucket, dict):
                return None
            try:
                _lang = _tl_resolve_lang()
                if _lang and isinstance(bucket.get(_lang), str):
                    return bucket[_lang]
                if _TL_DEFAULT_LANG and isinstance(bucket.get(_TL_DEFAULT_LANG), str):
                    return bucket[_TL_DEFAULT_LANG]
            except Exception:
                pass
            return None

        # ------------------------------------------------------------------
        # Central lookup: exact → whitespace-collapsed fallback → None.
        # For v1 the map values are strings; for v2 they are ``{lang: text}``
        # dicts that route through ``_tl_resolve_bucket``.
        # ------------------------------------------------------------------
        def _tl_lookup(s):
            if not isinstance(s, str) or not s:
                return None
            try:
                # L1: exact.
                v = _TL_TRANSLATIONS.get(s)
                if v is not None:
                    if _TL_SCHEMA == 2:
                        _r = _tl_resolve_bucket(v)
                        if _r:
                            return _tl_fix_drift(_r)
                    elif isinstance(v, str) and v:
                        return _tl_fix_drift(v)
                # L2: whitespace-collapsed fallback.
                n = " ".join(s.split())
                if n and n != s:
                    v = _TL_MAP_NORM.get(n)
                    if v is not None:
                        if _TL_SCHEMA == 2:
                            _r = _tl_resolve_bucket(v)
                            if _r:
                                return _tl_fix_drift(_r)
                        elif isinstance(v, str) and v:
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
