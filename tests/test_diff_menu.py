import tempfile
from pathlib import Path
import importlib


class TestDiffMenu:
    def test_menu_count_in_label(self):
        sample = """
label start:
    "Before"
    menu:
        "Go outside":
            jump outside
        "Stay home":
            "Okay"
label outside:
    "You went out"
        """.strip("\n")
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / 'menu.rpy'
            p.write_text(sample, encoding='utf-8')
            mod = importlib.import_module('renpy_tools.diff.parser')
            parse_rpy = getattr(mod, 'parse_rpy')
            parsed = parse_rpy(str(p))
            assert 'start' in parsed.labels
            start_blk = parsed.labels['start']
            # 菜单被统计一次
            assert start_blk.counts.get('menu', 0) == 1
            # 选择文本（带冒号）不会被当作台词收集
            texts = [d.text for d in start_blk.dialogues]
            assert 'Go outside' not in texts
            assert 'Stay home' not in texts

    def test_menu_choice_ignored_as_dialogue(self):
        sample = """
label start:
    menu:
        "A choice":
            pass
        "Another choice":
            pass
        """.strip("\n")
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / 'menu_only.rpy'
            p.write_text(sample, encoding='utf-8')
            mod = importlib.import_module('renpy_tools.diff.parser')
            parse_rpy = getattr(mod, 'parse_rpy')
            parsed = parse_rpy(str(p))
            start_blk = parsed.labels['start']
            # 纯菜单不应产生对话条目
            assert len(start_blk.dialogues) == 0
