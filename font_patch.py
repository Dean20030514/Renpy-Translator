#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Font patch — copy font into output game dir and set gui.*_font in gui.rpy."""

from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import Optional


# Only .ttf and .otf are accepted; no hardcoded font names.
FONT_EXTENSIONS = (".ttf", ".otf")


def resolve_font(
    resources_fonts_dir: Path,
    explicit_file: Optional[str] = None,
) -> Optional[Path]:
    """Resolve font file: use --font-file if given, else first .ttf/.otf in resources/fonts/.

    Returns Path to font file, or None on failure (warnings printed).
    """
    if explicit_file:
        path = Path(explicit_file).resolve()
        if not path.exists():
            print("[WARN] --font-file 指向的文件不存在，跳过字体补丁: " + str(path))
            return None
        if path.suffix.lower() not in FONT_EXTENSIONS:
            print("[WARN] --font-file 须为 .ttf 或 .otf，跳过字体补丁: " + str(path))
            return None
        return path

    if not resources_fonts_dir.exists():
        print("[WARN] resources/fonts/ 不存在，跳过字体补丁")
        return None
    candidates: list[Path] = []
    # 优先选择 .ttf 再考虑 .otf，以兼容旧版 Ren'Py
    for ext in (".ttf", ".otf"):
        candidates.extend(resources_fonts_dir.glob("*" + ext))
    # .ttf 排前面（0），.otf 排后面（1），同扩展名内按文件名排序
    _ext_order = {".ttf": 0, ".otf": 1}
    candidates.sort(key=lambda p: (_ext_order.get(p.suffix.lower(), 9), p.name))
    if not candidates:
        print("[WARN] resources/fonts/ 下未找到 .ttf 或 .otf 文件，跳过字体补丁")
        return None
    return candidates[0]


def apply_font_patch(
    output_game_dir: Path,
    source_game_dir: Path,
    font_path: Path,
) -> None:
    """Copy font into output_game_dir and patch gui.*_font in gui.rpy.

    Only replaces define gui.XXX_font = "..." lines; other content unchanged.
    If gui.rpy is missing in output, copy from source_game_dir first.
    """
    output_game_dir = output_game_dir.resolve()
    source_game_dir = source_game_dir.resolve()
    font_path = font_path.resolve()
    font_basename = font_path.name

    # Copy font
    output_game_dir.mkdir(parents=True, exist_ok=True)
    dst_font = output_game_dir / font_basename
    shutil.copy2(font_path, dst_font)
    print(f"[FONT ] 已复制字体: {font_basename} -> {output_game_dir}")

    gui_rpy = output_game_dir / "gui.rpy"
    if not gui_rpy.exists():
        source_gui = source_game_dir / "gui.rpy"
        if not source_gui.exists():
            print("[WARN] 输出目录与源目录均无 gui.rpy，无法写入字体变量")
            return
        shutil.copy2(source_gui, gui_rpy)
        print("[FONT ] 已从源目录复制 gui.rpy 至输出目录")

    # Replace only define gui.XXX_font = "..." (any quote, value unchanged except replaced with font_basename)
    pattern = re.compile(
        r'^(\s*define\s+gui\.\w+_font\s*=\s*)["\']([^"\']*)["\'](\s*)$',
        re.MULTILINE,
    )
    text = gui_rpy.read_text(encoding="utf-8")
    new_text, count = pattern.subn(
        lambda m: m.group(1) + '"' + font_basename + '"' + m.group(3),
        text,
    )
    if count == 0:
        print("[WARN] gui.rpy 中未找到 gui.*_font 变量定义，未修改任何内容")
        return
    gui_rpy.write_text(new_text, encoding="utf-8")
    print(f"[FONT ] 已更新 gui.rpy 中 {count} 处 gui.*_font 为 {font_basename}")
