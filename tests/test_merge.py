"""
merge.py 单元测试

测试合并逻辑、冲突检测
"""

import json
import tempfile
from pathlib import Path


class TestMergeHelpers:
    """测试 merge.py 的辅助函数"""

    def _import_merge(self):
        from tools import merge
        return merge

    def test_extract_zh_from_various_keys(self):
        m = self._import_merge()
        assert m.extract_zh({"zh": "你好"}) == "你好"
        assert m.extract_zh({"cn": "你好"}) == "你好"
        assert m.extract_zh({"translation": "你好"}) == "你好"
        assert m.extract_zh({"zh_final": "你好"}) == "你好"
        assert m.extract_zh({"en": "Hello"}) is None

    def test_extract_zh_empty_string(self):
        m = self._import_merge()
        assert m.extract_zh({"zh": ""}) is None
        assert m.extract_zh({"zh": "  "}) is None


class TestLoadLLMDir:
    """测试 LLM 结果目录加载"""

    def _import_merge(self):
        from tools import merge
        return merge

    def test_load_single_file(self):
        m = self._import_merge()
        with tempfile.TemporaryDirectory() as tmpdir:
            f = Path(tmpdir) / "batch_0001.jsonl"
            rows = [
                {"id": "script:1:0", "en": "Hello", "zh": "你好"},
                {"id": "script:2:0", "en": "World", "zh": "世界"},
            ]
            with f.open("w", encoding="utf-8") as fh:
                for r in rows:
                    fh.write(json.dumps(r, ensure_ascii=False) + "\n")
            result = m.load_llm_dir(f)
            assert "script:1:0" in result
            assert any(c["zh"] == "你好" for c in result["script:1:0"])
            assert "script:2:0" in result
            assert any(c["zh"] == "世界" for c in result["script:2:0"])

    def test_load_directory(self):
        m = self._import_merge()
        with tempfile.TemporaryDirectory() as tmpdir:
            d = Path(tmpdir)
            for i, text in enumerate(["你好", "世界"]):
                f = d / f"batch_{i:04d}.jsonl"
                row = {"id": f"script:{i+1}:0", "en": "test", "zh": text}
                f.write_text(json.dumps(row, ensure_ascii=False) + "\n", encoding="utf-8")
            result = m.load_llm_dir(d)
            assert len(result) == 2

    def test_conflict_detection(self):
        m = self._import_merge()
        with tempfile.TemporaryDirectory() as tmpdir:
            d = Path(tmpdir)
            # 两个批次对同一 id 有不同翻译
            f1 = d / "batch_0001.jsonl"
            f2 = d / "batch_0002.jsonl"
            f1.write_text(
                json.dumps({"id": "s:1:0", "en": "Hello", "zh": "你好"}, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            f2.write_text(
                json.dumps({"id": "s:1:0", "en": "Hello", "zh": "您好"}, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            result = m.load_llm_dir(d)
            # 同一 id 应有两个候选
            assert len(result["s:1:0"]) == 2
            zhs = {c["zh"] for c in result["s:1:0"]}
            assert "你好" in zhs
            assert "您好" in zhs
