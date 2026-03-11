"""
cli.py 单元测试

测试命令发现、参数验证
"""



class TestCLI:
    """测试 CLI 入口"""

    def test_get_available_tools(self):
        from renpy_tools.cli import get_available_tools
        tools = get_available_tools()
        assert isinstance(tools, dict)
        # 至少应发现这些核心工具
        expected = ["extract", "patch", "merge", "split", "validate"]
        for name in expected:
            assert name in tools, f"缺少工具: {name}"

    def test_validate_args_normal(self):
        from renpy_tools.cli import _validate_args
        assert _validate_args(["--help"]) is True
        assert _validate_args(["test.jsonl", "-o", "out.jsonl"]) is True

    def test_validate_args_too_long(self):
        from renpy_tools.cli import _validate_args
        # 超长参数应被拒绝（Windows CMD 限制 32768 字符）
        long_arg = "x" * 40000
        assert _validate_args([long_arg]) is False

    def test_tool_paths_exist(self):
        from renpy_tools.cli import get_available_tools
        tools = get_available_tools()
        for name, path in tools.items():
            assert path.exists(), f"工具脚本不存在: {name} -> {path}"
