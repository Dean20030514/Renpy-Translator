# Language Switcher — In-game language selection UI
# ==================================================
# Place this file in the game's `game/` directory to add a language
# switcher to the Preferences screen.
#
# It monkey-patches `renpy.show_screen` to replace the default
# "preferences" screen with a custom version that includes language
# buttons for all available translations in `game/tl/`.
#
# Inspired by renpy-translator (MIT, anonymousException 2024).
# Pure Ren'Py script — no external dependencies.

init python early hide:
    import os
    import importlib
    import inspect

    # Save original show_screen to chain calls
    global my_old_show_screen
    my_old_show_screen = renpy.show_screen

    def my_show_screen(_screen_name, *_args, **kwargs):
        if _screen_name == "preferences":
            _screen_name = "my_preferences_with_language"
        return my_old_show_screen(_screen_name, *_args, **kwargs)

    renpy.show_screen = my_show_screen


screen my_preferences_with_language():
    python:
        import os

        def _get_available_languages():
            """Scan tl/ directory for available language folders."""
            translator = renpy.game.script.translator
            languages = set(translator.languages) if hasattr(translator, "languages") else set()
            tl_path = os.path.join(renpy.config.gamedir, "tl")
            if os.path.isdir(tl_path):
                for name in os.listdir(tl_path):
                    full = os.path.join(tl_path, name)
                    if os.path.isdir(full):
                        languages.add(name)
            return sorted(lang for lang in languages if lang and lang != "None")

        available_langs = _get_available_languages()

    tag menu

    # Show the original preferences screen
    use preferences

    # Add language selector in bottom-right corner
    vbox:
        align (0.99, 0.99)
        spacing 5

        label _("Language")

        textbutton "Default" action Language(None)

        for lang in available_langs:
            textbutton "[lang]" action Language(lang)
