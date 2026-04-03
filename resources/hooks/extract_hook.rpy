# Extract Hook — Runtime text extraction from Ren'Py AST
# ======================================================
# Place this file in the game's `game/` directory, then launch the game.
# It will extract all translatable dialogue (say statements) into a JSON
# file and immediately quit.
#
# Output: extraction_hooked.json in the game's working directory.
#
# This is useful when static .rpy parsing cannot correctly handle complex
# or non-standard Ren'Py scripts.
#
# Inspired by renpy-translator (MIT, anonymousException 2024).
# Pure Ren'Py script — no external dependencies.

init python:
    import os
    import io
    import json

    translator = renpy.game.script.translator
    default_translates = translator.default_translates

    result = dict()

    for identifier, value in default_translates.items():
        # Extract dialogue from translate blocks
        if hasattr(value, "block"):
            say = value.block[0]
            if not hasattr(say, "what"):
                continue
            what = say.what
            who = say.who
        else:
            if not hasattr(value, "what") or not hasattr(value, "who"):
                continue
            what = value.what
            who = value.who

        filename = value.filename
        linenumber = value.linenumber

        entry = {
            "identifier": str(identifier),
            "who": str(who) if who else None,
            "what": str(what),
            "linenumber": linenumber,
        }

        if filename not in result:
            result[filename] = [entry]
        else:
            result[filename].append(entry)

    # Sort entries within each file by line number
    for filename in result:
        result[filename].sort(key=lambda e: e["linenumber"])

    output_path = "extraction_hooked.json"
    with io.open(output_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(result, ensure_ascii=False, indent=2))

    renpy.notify("Extraction complete: " + output_path)
    renpy.quit()
