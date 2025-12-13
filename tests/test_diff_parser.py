import unittest, tempfile
from pathlib import Path

# 允许直接从源码包导入（不要求已安装）
import sys
ROOT = Path(__file__).resolve().parents[1]
src_path = ROOT / 'src'
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import importlib


class TestDiffParser(unittest.TestCase):
    def test_parse_rpy_basic_blocks_and_dialogues(self):
        sample = """
label start:
    mc "Hello"
    "Narration"

screen ui():
    text "Click Here"
        """.strip("\n")
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / 'sample.rpy'
            p.write_text(sample, encoding='utf-8')
            mod = importlib.import_module('renpy_tools.diff.parser')
            parse_rpy = getattr(mod, 'parse_rpy')
            parsed = parse_rpy(str(p))
            # blocks
            self.assertIn('start', parsed.labels)
            self.assertIn('ui', parsed.screens)
            # dialogues in label start
            start_blk = parsed.labels['start']
            self.assertEqual(len(start_blk.dialogues), 2)
            self.assertEqual(start_blk.dialogues[0].kind, 'speaker')
            self.assertEqual(start_blk.dialogues[0].speaker, 'mc')
            self.assertEqual(start_blk.dialogues[0].text, 'Hello')
            self.assertEqual(start_blk.dialogues[1].kind, 'narration')
            self.assertIsNone(start_blk.dialogues[1].speaker)
            self.assertEqual(start_blk.dialogues[1].text, 'Narration')
            # dialogues in screen ui
            ui_blk = parsed.screens['ui']
            self.assertEqual(len(ui_blk.dialogues), 1)
            self.assertEqual(ui_blk.dialogues[0].kind, 'text')
            self.assertEqual(ui_blk.dialogues[0].text, 'Click Here')

    def test_align_by_speaker_minimal(self):
        mod = importlib.import_module('renpy_tools.diff.parser')
        Dialogue = getattr(mod, 'Dialogue')
        align_by_speaker = getattr(mod, 'align_by_speaker')
        en = [
            Dialogue(kind='speaker', speaker='a', text='X', line_no=1),
            Dialogue(kind='speaker', speaker='b', text='Y', line_no=2),
            Dialogue(kind='narration', speaker=None, text='...', line_no=3),
        ]
        cn = [
            Dialogue(kind='speaker', speaker='a', text='XX', line_no=10),
            Dialogue(kind='narration', speaker=None, text='...', line_no=11),
        ]
        mapping = align_by_speaker(en, cn)
        # 期望: 第0对齐，第1删除为 None，第2对齐到 cn 索引1
        self.assertEqual(mapping[0], (0, 0))
        self.assertEqual(mapping[1], (1, None))
        self.assertEqual(mapping[2], (2, 1))


if __name__ == '__main__':
    unittest.main()
