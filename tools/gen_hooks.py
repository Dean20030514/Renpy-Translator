#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_hooks.py — 生成 Ren'Py 运行时 Hook 脚本

借鉴 RenpyTranslator 的 Hook 设计，生成以下 .rpy 脚本：
  1. hook_extract.rpy     — 运行时提取翻译字符串（支持 .rpyc 编译文件）
  2. hook_language.rpy     — 动态语言切换器（自动扫描 game/tl/ 目录）
  3. hook_font.rpy         — 按语言配置字体（支持 RTL）
  4. hook_default_lang.rpy — 设置默认语言

用法示例：
  # 生成所有 Hook 文件
  python tools/gen_hooks.py -o hooks/ --lang zh_CN --font "SourceHanSansCN-Regular.otf"

  # 仅生成提取 Hook
  python tools/gen_hooks.py -o hooks/ --only extract

  # 生成后复制到游戏目录
  python tools/gen_hooks.py -o "E:\\MyGame\\game" --lang zh_CN --font "fonts/zh.ttf"
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# 添加 src 到路径
_project_root = Path(__file__).parent.parent
if str(_project_root / "src") not in sys.path:
    sys.path.insert(0, str(_project_root / "src"))

try:
    from rich.console import Console
    _console = Console()
except ImportError:
    _console = None


def _log(msg: str, level: str = "info") -> None:
    if _console:
        style = {"info": "dim", "warning": "yellow", "error": "red"}.get(level, "")
        _console.print(f"[{style}]{msg}[/]")
    else:
        print(msg)


# ═══════════════════════════════════════════════════════════
# Hook 模板
# ═══════════════════════════════════════════════════════════

HOOK_EXTRACT_RPY = r'''# hook_extract.rpy — 运行时提取翻译字符串
# 将此文件放入 game/ 目录，启动游戏后自动提取所有对话到 JSON
# 提取完成后游戏自动退出，输出 extraction_hooked.json

init python:
    import os
    import io
    import json

    renpy_runtime_extract_hook_file_name = 'extraction_hooked.json'
    translator = renpy.game.script.translator
    default_translates = translator.default_translates
    dic = dict()

    for identifier, value in default_translates.items():
        if hasattr(value, "block"):
            say = value.block[0]
            if not hasattr(say, 'what'):
                continue
            what = say.what
            who = say.who
        else:
            if not hasattr(value, 'what') or not hasattr(value, "who"):
                continue
            what = value.what
            who = value.who

        filename = value.filename
        linenumber = value.linenumber

        if filename not in dic:
            dic[filename] = [(identifier, who, what, linenumber)]
        else:
            dic[filename].append((identifier, who, what, linenumber))

    with io.open(renpy_runtime_extract_hook_file_name, 'w', encoding="utf-8") as outfile:
        outfile.write(json.dumps(dic, ensure_ascii=False, indent=2))

    renpy.notify("Extraction complete: " + renpy_runtime_extract_hook_file_name)
    renpy.quit()
'''


def _gen_language_hook(lang: str = "zh_CN") -> str:
    """生成语言切换器 Hook"""
    return f'''# hook_language.rpy — 动态语言切换器
# 将此文件放入 game/ 目录，在设置界面添加语言切换按钮

init python early hide:
    import os
    import importlib
    import inspect

    def check_function_exists(module_name, function_name):
        try:
            module = importlib.import_module(module_name)
            function = getattr(module, function_name)
            return inspect.isfunction(function)
        except (ImportError, AttributeError):
            return False

    global my_old_show_screen
    my_old_show_screen = renpy.show_screen

    def my_show_screen(_screen_name, *_args, **kwargs):
        if _screen_name == 'preferences':
            _screen_name = 'my_preferences'
        return my_old_show_screen(_screen_name, *_args, **kwargs)

    renpy.show_screen = my_show_screen

screen my_preferences():
    python:
        global os
        import os

        def traverse_first_dir(path):
            translator = renpy.game.script.translator
            languages = translator.languages
            l = set(languages) if languages else set()
            if os.path.exists(path):
                for file in os.listdir(path):
                    m = os.path.join(path, file)
                    if os.path.isdir(m):
                        l.add(os.path.split(m)[1])
            return l

        l = traverse_first_dir('game/tl')

    tag menu
    use preferences

    vbox:
        align(.99, .99)
        hbox:
            box_wrap True
            vbox:
                label _("Language")
                textbutton "Default" action Language(None)
                for i in sorted(l):
                    if i is not None and i != 'None':
                        textbutton "%s" % i action Language(i)
'''


def _gen_font_hook(lang: str = "zh_CN", font_path: str = "SourceHanSansCN-Regular.otf", rtl: bool = False) -> str:
    """生成字体配置 Hook"""
    rtl_str = "True" if rtl else "False"
    return f'''# hook_font.rpy — 按语言动态配置字体
# 将此文件放入 game/ 目录

init python early hide:
    import renpy

    if 'tl_font_dic' not in globals():
        global tl_font_dic
        tl_font_dic = dict()
        global old_load_face
        old_load_face = renpy.text.font.load_face

        def my_load_face(fn, *args):
            renpy.text.font.free_memory()
            for key, value in tl_font_dic.items():
                if renpy.game.preferences.language == key:
                    fn = value[0]
                    renpy.config.rtl = value[1]
            return old_load_face(fn, *args)

        renpy.text.font.load_face = my_load_face

    global tl_font_dic
    tl_font_dic["{lang}"] = "{font_path}", {rtl_str}

    old_reload_all = renpy.reload_all

    def my_reload_all():
        renpy.text.font.free_memory()
        renpy.text.font.load_face = old_load_face
        ret = old_reload_all()
        renpy.reload_all = old_reload_all
        return ret

    renpy.reload_all = my_reload_all
'''


def _gen_default_lang_hook(lang: str = "zh_CN") -> str:
    """生成默认语言设置 Hook"""
    return f'''# hook_default_lang.rpy — 设置默认语言
# 将此文件放入 game/ 目录，游戏启动时自动切换到指定语言

init 1000 python:
    renpy.game.preferences.language = "{lang}"
'''


def main():
    parser = argparse.ArgumentParser(description="生成 Ren'Py 运行时 Hook 脚本")
    parser.add_argument("-o", "--output", required=True, help="输出目录")
    parser.add_argument("--lang", default="zh_CN", help="目标语言（默认 zh_CN）")
    parser.add_argument("--font", default="SourceHanSansCN-Regular.otf", help="字体文件路径")
    parser.add_argument("--rtl", action="store_true", help="是否 RTL（从右到左）语言")
    parser.add_argument(
        "--only",
        choices=["extract", "language", "font", "default_lang"],
        help="仅生成指定 Hook"
    )
    args = parser.parse_args()

    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    generated = []

    hooks = {
        "extract": ("hook_extract.rpy", HOOK_EXTRACT_RPY),
        "language": ("hook_language.rpy", _gen_language_hook(args.lang)),
        "font": ("hook_font.rpy", _gen_font_hook(args.lang, args.font, args.rtl)),
        "default_lang": ("hook_default_lang.rpy", _gen_default_lang_hook(args.lang)),
    }

    for key, (filename, content) in hooks.items():
        if args.only and args.only != key:
            continue
        out_path = out_dir / filename
        out_path.write_text(content, encoding="utf-8")
        generated.append(filename)
        _log(f"生成: {out_path}")

    if _console:
        _console.print(f"\n[bold green]完成[/]：生成 {len(generated)} 个 Hook 文件到 {out_dir}")
    else:
        print(f"\n完成：生成 {len(generated)} 个 Hook 文件到 {out_dir}")

    if not args.only:
        _log("提示: 将 hook 文件复制到游戏的 game/ 目录即可使用")
        _log("  hook_extract.rpy    — 启动游戏自动提取（提取后删除此文件）")
        _log("  hook_language.rpy   — 设置界面添加语言切换")
        _log("  hook_font.rpy       — 动态字体配置")
        _log("  hook_default_lang.rpy — 默认语言")


if __name__ == "__main__":
    main()
