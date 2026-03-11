"""
split.py 单元测试

测试批次分割、token 计数
"""

import json
import tempfile
from pathlib import Path


class TestSplitHelpers:
    """测试 split.py 的辅助函数"""

    def _import_split(self):
        from tools import split
        return split

    def test_approx_tokens(self):
        s = self._import_split()
        # 近似计算：1 token ≈ 3 字符
        tokens = s.approx_tokens("Hello world")
        assert tokens > 0
        # 较长文本应有更多 token
        assert s.approx_tokens("This is a longer sentence.") > s.approx_tokens("Hi")

    def test_count_tokens_fallback(self):
        s = self._import_split()
        # count_tokens 在无 tiktoken 时应回退到近似值
        tokens = s.count_tokens("Hello world")
        assert isinstance(tokens, int)
        assert tokens > 0

    def test_has_zh(self):
        s = self._import_split()
        assert s.has_zh({"zh": "你好"})
        assert s.has_zh({"cn": "你好"})
        assert s.has_zh({"translation": "你好"})
        assert not s.has_zh({"en": "Hello"})
        assert not s.has_zh({"zh": ""})
        assert not s.has_zh({"zh": "  "})


class TestSplitOutput:
    """测试分割输出"""

    def _import_split(self):
        from tools import split
        return split

    def test_split_creates_batches(self):
        s = self._import_split()
        with tempfile.TemporaryDirectory() as tmpdir:
            src = Path(tmpdir) / "source.jsonl"
            out_dir = Path(tmpdir) / "batches"
            out_dir.mkdir()

            # 生成 20 条数据
            rows = [{"id": f"s:{i}:0", "en": f"Sentence number {i}"} for i in range(20)]
            with src.open("w", encoding="utf-8") as f:
                for r in rows:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")

            # 模拟命令行分割（--max-items 10）
            import sys
            old_argv = sys.argv
            sys.argv = ["split.py", str(src), str(out_dir), "--max-items", "10"]
            try:
                s.main()
            finally:
                sys.argv = old_argv

            # 应生成至少 2 个批次
            batch_files = list(out_dir.glob("batch_*.jsonl"))
            assert len(batch_files) >= 2

            # 所有条目应被保留
            total = 0
            for bf in batch_files:
                with bf.open("r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            total += 1
            assert total == 20
