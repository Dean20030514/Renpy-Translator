"""
patch.py 单元测试

测试匹配策略、引号处理
"""


class TestPatchHelpers:
    """测试 patch.py 辅助函数"""

    def _import_patch(self):
        from tools import patch
        return patch

    def test_scan_string_literals(self):
        p = self._import_patch()
        text = '    e "Hello, world!"\n'
        tokens = p.scan_string_literals(text)
        assert len(tokens) >= 1
        # Token 使用 inner_start/inner_end 获取内容
        found = [t for t in tokens if text[t.inner_start:t.inner_end] == "Hello, world!"]
        assert len(found) >= 1

    def test_escape_for_quote_double(self):
        p = self._import_patch()
        result = p.escape_for_quote('He said "hello"', '"')
        assert '\\"' in result or result.count('"') == 0

    def test_escape_for_quote_single(self):
        p = self._import_patch()
        result = p.escape_for_quote("It's a test", "'")
        assert "\\'" in result

    def test_sanitize_triple_content(self):
        p = self._import_patch()
        # 三引号内容不应包含未转义的三引号
        result = p.sanitize_triple_content('contains """ inside', '"""')
        assert '"""' not in result or result != 'contains """ inside'


class TestPatchAdvanced:
    """测试高级回填"""

    def _import_patch(self):
        from tools import patch
        return patch

    def test_apply_patch_exact_position(self):
        p = self._import_patch()
        text = 'label start:\n    e "Hello, world!"\n    "Click here"\n'
        new_text, method, _region = p.apply_patch_advanced(
            text, "Hello, world!", "你好，世界！", 2, 0, "", ""
        )
        assert "你好，世界！" in new_text
        assert method is not None

    def test_apply_patch_preserves_other_lines(self):
        p = self._import_patch()
        text = 'label start:\n    e "Hello"\n    "Continue"\n    "End"\n'
        new_text, _method, _region = p.apply_patch_advanced(
            text, "Continue", "继续", 3, 0, "", ""
        )
        assert "Hello" in new_text  # 其他行不变
        assert "End" in new_text
        assert "继续" in new_text


class TestPatchFileText:
    """测试简单回填"""

    def _import_patch(self):
        from tools import patch
        return patch

    def test_patch_file_text_basic(self):
        p = self._import_patch()
        text = 'label start:\n    e "Hello"\n    "World"\n'
        # patch_file_text 期望 trans 值包含 'obj' 字段
        trans = {
            "game/test.rpy:2:0": {"en": "Hello", "zh": "你好", "obj": {"file": "game/test.rpy", "line": 2, "idx": 0, "en": "Hello"}},
            "game/test.rpy:3:0": {"en": "World", "zh": "世界", "obj": {"file": "game/test.rpy", "line": 3, "idx": 0, "en": "World"}},
        }
        new_text, applied, _warn = p.patch_file_text(text, "game/test.rpy", trans)
        assert "你好" in new_text
        assert "世界" in new_text
        assert applied >= 1
