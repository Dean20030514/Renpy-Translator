"""
autofix.py 单元测试

测试各修复规则
"""



class TestAutofixHelpers:
    """测试 autofix.py 修复规则"""

    def _import_autofix(self):
        from tools import autofix
        return autofix

    def test_to_halfwidth(self):
        af = self._import_autofix()
        # 全角 → 半角
        assert af.to_halfwidth("Ａ") == "A"
        assert af.to_halfwidth("ａ") == "a"
        assert af.to_halfwidth("１") == "1"
        assert af.to_halfwidth("＋") == "+"
        # 全角空格 → 半角空格
        assert af.to_halfwidth("\u3000") == " "
        # 普通字符不变
        assert af.to_halfwidth("Hello") == "Hello"
        assert af.to_halfwidth("你好") == "你好"

    def test_fix_mixed_spacing(self):
        af = self._import_autofix()
        # 中英之间加空格
        result = af.fix_mixed_spacing("你好World")
        assert " " in result
        # 数字与中文之间加空格
        result = af.fix_mixed_spacing("有3个苹果")
        assert " " in result

    def test_zh_end_punct_from_en(self):
        af = self._import_autofix()
        assert af.zh_end_punct_from_en("Hello.") == "。"
        assert af.zh_end_punct_from_en("Really?") == "？"
        assert af.zh_end_punct_from_en("Wow!") == "！"
        assert af.zh_end_punct_from_en("Hello...") == "……"

    def test_fix_end_punct(self):
        af = self._import_autofix()
        # 英文有句号，中文缺少
        result = af.fix_end_punct("Hello.", "你好")
        assert result.endswith("。")
        # 英文有问号，中文缺少
        result = af.fix_end_punct("Really?", "真的吗")
        assert result.endswith("？")

    def test_fix_newline_remove_extra(self):
        af = self._import_autofix()
        # 英文无换行，中文多了换行
        result = af.fix_newline("Hello world", "你好\n世界")
        assert "\n" not in result

    def test_fix_newline_add_missing(self):
        af = self._import_autofix()
        # 英文有一个换行，中文没有，且中文长度 >= 4 才会插入换行
        result = af.fix_newline("Hello\nworld", "你好，世界")
        assert "\n" in result
