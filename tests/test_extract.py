"""
extract.py 单元测试

测试文本提取逻辑、资产过滤、编码处理
"""

import tempfile
from pathlib import Path


class TestExtractHelpers:
    """测试 extract.py 的辅助函数"""

    def _import_extract(self):
        from tools import extract
        return extract

    def test_looks_like_text_valid(self):
        ext = self._import_extract()
        assert ext.looks_like_text("Hello, world!", 1)
        assert ext.looks_like_text("你好", 1)
        assert ext.looks_like_text("Save Game", 1)

    def test_looks_like_text_rejects_short(self):
        ext = self._import_extract()
        assert not ext.looks_like_text("", 1)
        assert not ext.looks_like_text("x", 2)

    def test_looks_like_text_rejects_non_text(self):
        ext = self._import_extract()
        # 纯数字
        assert not ext.looks_like_text("12345", 1)
        # 纯符号
        assert not ext.looks_like_text("---", 1)

    def test_looks_like_asset(self):
        ext = self._import_extract()
        assert ext.looks_like_asset("images/bg.png")
        assert ext.looks_like_asset("audio/bgm.ogg")
        assert ext.looks_like_asset("gui/textbox.webp")
        assert not ext.looks_like_asset("Hello, world!")
        assert not ext.looks_like_asset("Save Game")

    def test_compute_hash_id_deterministic(self):
        ext = self._import_extract()
        h1 = ext.compute_hash_id("game/script.rpy", 10, 0, "Hello", "prev", "next")
        h2 = ext.compute_hash_id("game/script.rpy", 10, 0, "Hello", "prev", "next")
        assert h1 == h2
        assert h1.startswith("sha256:")

    def test_compute_hash_id_different_for_different_input(self):
        ext = self._import_extract()
        h1 = ext.compute_hash_id("game/script.rpy", 10, 0, "Hello", "", "")
        h2 = ext.compute_hash_id("game/script.rpy", 10, 0, "World", "", "")
        assert h1 != h2


class TestExtractFromFile:
    """测试从 .rpy 文件提取文本"""

    def _import_extract(self):
        from tools import extract
        return extract

    def test_extract_basic_dialogue(self):
        ext = self._import_extract()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            rpy = root / "game" / "script.rpy"
            rpy.parent.mkdir(parents=True)
            rpy.write_text(
                'label start:\n'
                '    e "Hello, world!"\n'
                '    "Click to continue"\n',
                encoding="utf-8",
            )
            items = ext.extract_from_file(rpy, root)
            texts = [it["en"] for it in items]
            assert "Hello, world!" in texts
            assert "Click to continue" in texts

    def test_extract_skips_assets(self):
        ext = self._import_extract()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            rpy = root / "game" / "script.rpy"
            rpy.parent.mkdir(parents=True)
            rpy.write_text(
                'label start:\n'
                '    scene "images/bg.png"\n'
                '    e "Hello"\n',
                encoding="utf-8",
            )
            items = ext.extract_from_file(rpy, root)
            texts = [it["en"] for it in items]
            assert "images/bg.png" not in texts
            assert "Hello" in texts

    def test_extract_skips_comments(self):
        ext = self._import_extract()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            rpy = root / "game" / "script.rpy"
            rpy.parent.mkdir(parents=True)
            rpy.write_text(
                'label start:\n'
                '    # "This is a comment"\n'
                '    e "Real dialogue"\n',
                encoding="utf-8",
            )
            items = ext.extract_from_file(rpy, root)
            texts = [it["en"] for it in items]
            assert "This is a comment" not in texts
            assert "Real dialogue" in texts

    def test_extract_preserves_placeholders(self):
        ext = self._import_extract()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            rpy = root / "game" / "script.rpy"
            rpy.parent.mkdir(parents=True)
            rpy.write_text(
                'label start:\n'
                '    e "Hello, [name]! You have [count] items."\n',
                encoding="utf-8",
            )
            items = ext.extract_from_file(rpy, root)
            assert len(items) >= 1
            item = [it for it in items if "[name]" in it["en"]][0]
            assert "[name]" in item["en"]
            assert "[count]" in item["en"]

    def test_extract_output_fields(self):
        ext = self._import_extract()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            rpy = root / "game" / "script.rpy"
            rpy.parent.mkdir(parents=True)
            rpy.write_text(
                'label start:\n'
                '    e "Hello"\n',
                encoding="utf-8",
            )
            items = ext.extract_from_file(rpy, root)
            assert len(items) >= 1
            item = items[0]
            # 必要字段
            assert "en" in item
            assert "file" in item
            assert "line" in item
