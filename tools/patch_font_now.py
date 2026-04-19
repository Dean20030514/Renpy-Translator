#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One-off font patch: apply font to existing translation output without re-running the pipeline.

Run from project root. After running, copy stage2_translated/game contents into the game's game folder.
"""

import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.font_patch import resolve_font, apply_font_patch

# Already-translated output (stage2_translated/game)
OUTPUT_GAME = Path(os.environ.get(
    "PATCH_OUTPUT_GAME",
    r"output\projects\TheTyrant-0.9.4b.with.Official.SAZmod-pc-compressed\stage2_translated\game",
))
# Original game directory (game subdir)
SOURCE_GAME = Path(os.environ.get(
    "TEST_GAME_DIR",
    r"E:\浏览器下载\TheTyrant-0.9.4b.with.Official.SAZmod-pc-compressed\game",
))

if __name__ == "__main__":
    # Round 29 fix: the fonts live under the project root, not under
    # ``tools/``.  ``Path(__file__).parent`` is ``tools/`` so we need
    # one more ``.parent`` to reach the project root (which is where
    # the other entry points — ``main.py`` / ``gui.py`` — compute their
    # resource paths from).  Prior versions silently fell through to the
    # "fonts dir not found" branch of ``resolve_font``.
    project_root = Path(__file__).resolve().parent.parent
    resources_fonts = project_root / "resources" / "fonts"
    font = resolve_font(resources_fonts, None)
    if font:
        apply_font_patch(OUTPUT_GAME, SOURCE_GAME, font)
        print("字体补丁完成")
    else:
        print("未找到字体，请将 .ttf 或 .otf 放入 resources/fonts/ 后重试")
