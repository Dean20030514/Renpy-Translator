#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 translate.py 与优化翻译器的集成
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_import():
    """测试模块导入"""
    print("测试模块导入...")
    try:
        from tools import translate
        print("  ✓ tools.translate 导入成功")
    except ImportError as e:
        print(f"  ✗ 导入失败: {e}")
        return False
    
    # 检查优化模块
    try:
        from src.renpy_tools.core.translator import OllamaTranslator
        print("  ✓ OllamaTranslator 可用")
        has_optimized = True
    except ImportError:
        print("  ⚠ OllamaTranslator 不可用（这是正常的，如果你没有创建该模块）")
        has_optimized = False
    
    # 检查标志
    if hasattr(translate, '_HAS_OPTIMIZED_TRANSLATOR'):
        status = translate._HAS_OPTIMIZED_TRANSLATOR
        print(f"  ✓ _HAS_OPTIMIZED_TRANSLATOR = {status}")
        if status != has_optimized:
            print(f"  ⚠ 警告: 标志不一致 (期望={has_optimized}, 实际={status})")
    else:
        print("  ✗ 缺少 _HAS_OPTIMIZED_TRANSLATOR 标志")
        return False
    
    return True


def test_functions():
    """测试函数存在性"""
    print("\n测试函数存在性...")
    from tools import translate
    
    required_funcs = [
        'process_file',
        'process_file_optimized',
        'extract_placeholders',
        'restore_placeholders',
        'translate_one',
        'is_non_dialog_text',
        'build_system_prompt',
        'build_user_prompt',
    ]
    
    all_ok = True
    for func_name in required_funcs:
        if hasattr(translate, func_name):
            print(f"  ✓ {func_name} 存在")
        else:
            print(f"  ✗ {func_name} 缺失")
            all_ok = False
    
    return all_ok


def test_placeholder_extraction():
    """测试占位符提取和恢复"""
    print("\n测试占位符提取和恢复...")
    from tools.translate import extract_placeholders, restore_placeholders
    
    test_cases = [
        ("Hello [name]!", 1),
        ("{i}Italic{/i} text", 2),
        ("Value: {0:.2f}", 1),
        ("%(name)s is here", 1),
        ("No placeholders", 0),
        ("{color=#fff}Colored{/color} [name]", 3),
    ]
    
    all_ok = True
    for text, expected_count in test_cases:
        clean, phs = extract_placeholders(text)
        if len(phs) == expected_count:
            # 测试恢复
            restored = restore_placeholders(clean, phs)
            if restored == text:
                print(f"  ✓ '{text}' -> {len(phs)} 占位符 -> 恢复正确")
            else:
                print(f"  ✗ '{text}' 恢复失败: '{restored}' != '{text}'")
                all_ok = False
        else:
            print(f"  ✗ '{text}' 期望 {expected_count} 占位符，实际 {len(phs)}")
            all_ok = False
    
    return all_ok


def test_non_dialog_filter():
    """测试非台词过滤"""
    print("\n测试非台词过滤...")
    from tools.translate import is_non_dialog_text
    
    should_skip = [
        "images/bg.png",
        "True",
        "False",
        "mcroom_hover_icon",
        "7am009ancl2jpg",
        "sazmod",
    ]
    
    should_keep = [
        "Hello world!",
        "OK",
        "Yes",
        "Save Game",
        "I love you.",
    ]
    
    all_ok = True
    for text in should_skip:
        if is_non_dialog_text(text):
            print(f"  ✓ 正确跳过: '{text}'")
        else:
            print(f"  ✗ 应该跳过但未跳过: '{text}'")
            all_ok = False
    
    for text in should_keep:
        if not is_non_dialog_text(text):
            print(f"  ✓ 正确保留: '{text}'")
        else:
            print(f"  ✗ 应该保留但跳过了: '{text}'")
            all_ok = False
    
    return all_ok


def main():
    """运行所有测试"""
    print("=" * 50)
    print("translate.py 集成测试")
    print("=" * 50)
    
    tests = [
        ("模块导入", test_import),
        ("函数存在性", test_functions),
        ("占位符提取", test_placeholder_extraction),
        ("非台词过滤", test_non_dialog_filter),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ {name} 测试异常: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # 总结
    print("\n" + "=" * 50)
    print("测试结果总结")
    print("=" * 50)
    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{name:20s}: {status}")
    
    all_passed = all(r for _, r in results)
    if all_passed:
        print("\n✓ 所有测试通过！")
        return 0
    else:
        print("\n✗ 部分测试失败")
        return 1


if __name__ == "__main__":
    exit(main())
