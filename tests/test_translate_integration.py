#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 translate.py 与优化翻译器的集成
使用 pytest 风格的断言
"""

import sys
from pathlib import Path

import pytest

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))


class TestTranslateModuleImport:
    """测试 translate 模块导入"""

    def test_translate_module_imports(self):
        """测试 tools.translate 模块可以导入"""
        from tools import translate
        assert translate is not None

    def test_has_optimized_translator_flag(self):
        """测试 _HAS_OPTIMIZED_TRANSLATOR 标志存在"""
        from tools import translate
        assert hasattr(translate, '_HAS_OPTIMIZED_TRANSLATOR')

    def test_required_functions_exist(self):
        """测试必需的函数存在"""
        from tools import translate

        required_funcs = [
            'extract_placeholders',
            'restore_placeholders',
            'is_non_dialog_text',
            'build_system_prompt',
            'build_user_prompt',
        ]

        for func_name in required_funcs:
            assert hasattr(translate, func_name), f"{func_name} 缺失"


class TestPlaceholderExtraction:
    """测试占位符提取和恢复"""

    def test_square_bracket_placeholder(self):
        """测试方括号占位符"""
        from tools.translate import extract_placeholders, restore_placeholders

        text = "Hello [name]!"
        clean, phs = extract_placeholders(text)

        assert len(phs) == 1
        assert phs[0][0] == "[name]"

        restored = restore_placeholders(clean, phs)
        assert restored == text

    def test_renpy_tags(self):
        """测试 Ren'Py 标签"""
        from tools.translate import extract_placeholders, restore_placeholders

        text = "{i}Italic{/i} text"
        clean, phs = extract_placeholders(text)

        assert len(phs) == 2
        restored = restore_placeholders(clean, phs)
        assert restored == text

    def test_format_placeholder(self):
        """测试格式占位符"""
        from tools.translate import extract_placeholders, restore_placeholders

        text = "Value: {0:.2f}"
        clean, phs = extract_placeholders(text)

        assert len(phs) == 1
        restored = restore_placeholders(clean, phs)
        assert restored == text

    def test_percent_placeholder(self):
        """测试百分号占位符"""
        from tools.translate import extract_placeholders, restore_placeholders

        text = "%(name)s is here"
        clean, phs = extract_placeholders(text)

        assert len(phs) == 1
        restored = restore_placeholders(clean, phs)
        assert restored == text

    def test_no_placeholders(self):
        """测试没有占位符的文本"""
        from tools.translate import extract_placeholders, restore_placeholders

        text = "No placeholders"
        clean, phs = extract_placeholders(text)

        assert len(phs) == 0
        restored = restore_placeholders(clean, phs)
        assert restored == text

    def test_multiple_placeholders(self):
        """测试多个占位符"""
        from tools.translate import extract_placeholders, restore_placeholders

        text = "{color=#fff}Colored{/color} [name]"
        clean, phs = extract_placeholders(text)

        assert len(phs) == 3
        restored = restore_placeholders(clean, phs)
        assert restored == text


class TestNonDialogFilter:
    """测试非台词过滤"""

    def test_skip_boolean_values(self):
        """测试跳过布尔值"""
        from tools.translate import is_non_dialog_text

        assert is_non_dialog_text("True")
        assert is_non_dialog_text("False")
        assert is_non_dialog_text("None")

    def test_skip_resource_paths(self):
        """测试跳过资源路径"""
        from tools.translate import is_non_dialog_text

        assert is_non_dialog_text("images/bg.png")
        assert is_non_dialog_text("audio/music.ogg")

    def test_keep_normal_text(self):
        """测试保留正常文本"""
        from tools.translate import is_non_dialog_text

        assert not is_non_dialog_text("Hello world!")
        assert not is_non_dialog_text("Save Game")
        assert not is_non_dialog_text("I love you.")

    def test_keep_short_ui_text(self):
        """测试保留短 UI 文本"""
        from tools.translate import is_non_dialog_text

        assert not is_non_dialog_text("OK")
        assert not is_non_dialog_text("Yes")
        assert not is_non_dialog_text("No")


class TestPromptBuilding:
    """测试提示词构建"""

    def test_system_prompt_not_empty(self):
        """测试系统提示词不为空"""
        from tools.translate import build_system_prompt

        prompt = build_system_prompt()
        assert len(prompt) > 100
        assert "翻译" in prompt or "中文" in prompt

    def test_user_prompt_contains_text(self):
        """测试用户提示词包含文本"""
        from tools.translate import build_user_prompt

        text = "Hello, world!"
        context = {"label": "start"}
        prompt = build_user_prompt(text, context)

        assert text in prompt
        assert "start" in prompt

    def test_user_prompt_includes_context(self):
        """测试用户提示词包含上下文"""
        from tools.translate import build_user_prompt

        text = "Hello!"
        context = {
            "label": "scene_1",
            "anchor_prev": "Previous line",
            "anchor_next": "Next line",
        }
        prompt = build_user_prompt(text, context)

        assert "scene_1" in prompt
        assert "Previous line" in prompt
        assert "Next line" in prompt


class TestTranslationValidation:
    """测试翻译验证"""

    def test_valid_translation_passes(self):
        """测试有效翻译通过验证"""
        from tools.translate import ensure_valid_translation

        source = "Hello!"
        translation = "你好！"

        valid, error = ensure_valid_translation(source, translation)
        assert valid
        assert error == ""

    def test_empty_translation_fails(self):
        """测试空翻译失败"""
        from tools.translate import ensure_valid_translation

        source = "Hello!"
        translation = ""

        valid, error = ensure_valid_translation(source, translation)
        assert not valid
        assert "empty" in error

    def test_newline_mismatch_fails(self):
        """测试换行符不匹配失败"""
        from tools.translate import ensure_valid_translation

        source = "Line 1\nLine 2"
        translation = "第一行第二行"

        valid, error = ensure_valid_translation(source, translation)
        assert not valid
        assert "newline" in error

    def test_placeholder_mismatch_fails(self):
        """测试占位符不匹配失败"""
        from tools.translate import ensure_valid_translation

        source = "Hello [name]!"
        translation = "你好！"

        valid, error = ensure_valid_translation(source, translation)
        assert not valid
        assert "placeholder" in error


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
