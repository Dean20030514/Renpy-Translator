import tempfile, json
from pathlib import Path

from renpy_tools.utils.dict_utils import load_dictionary  # type: ignore
from renpy_tools.utils.io import read_jsonl_lines, write_jsonl_lines  # type: ignore


class TestDictUtils:
    def test_load_dictionary_from_jsonl_and_csv(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            d = Path(tmpdir)
            # JSONL
            jpath = d / 'd.jsonl'
            rows = [
                {"variant_en": "Start", "zh": "开始"},
                {"canonical_en": "Exit", "zh": "退出"},
                {"en": "Save", "zh_final": "保存"},
            ]
            with jpath.open('w', encoding='utf-8') as f:
                for r in rows:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
            # CSV
            cpath = d / 'd.csv'
            with cpath.open('w', encoding='utf-8', newline='') as f:
                f.write('variant_en,canonical_en,en,english,zh,zh_final\n')
                f.write(',,Load,,加载,\n')
                f.write(',,Settings,,设置,\n')

            # 目录整体加载
            m = load_dictionary(d, case_insensitive=True)
            assert m.get('start') == '开始'
            assert m.get('exit') == '退出'
            assert m.get('save') == '保存'
            assert m.get('load') == '加载'
            assert m.get('settings') == '设置'

    def test_jsonl_io_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / 'x.jsonl'
            rows = [{"id": 1, "en": "Hello"}, {"id": 2, "zh": "你好"}]
            write_jsonl_lines(p, rows)
            loaded = read_jsonl_lines(p)
            assert loaded == rows
