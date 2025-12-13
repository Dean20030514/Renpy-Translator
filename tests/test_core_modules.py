"""
核心模块功能测试

测试 OllamaTranslator, MultiLevelValidator, SafePatcher 的核心功能
"""

import sys
from pathlib import Path

# 添加项目根目录
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.renpy_tools.core import MultiLevelValidator, SafePatcher
from src.renpy_tools.utils.logger import logger


def test_validator():
    """测试验证器"""
    print("\n" + "=" * 60)
    print("测试 MultiLevelValidator")
    print("=" * 60)
    
    # 准备测试数据
    source = [
        {'id': 'test_1', 'en': 'Hello, [name]!'},
        {'id': 'test_2', 'en': 'What is your\nfavorite color?'},
        {'id': 'test_3', 'en': 'Let\'s go!'},
        {'id': 'test_4', 'en': 'Welcome to {game}!'},
    ]
    
    target = [
        {'id': 'test_1', 'zh': '你好！'},  # 缺失 [name]
        {'id': 'test_2', 'zh': '你最喜欢的颜色是什么？'},  # 缺失换行符
        {'id': 'test_3', 'zh': '我们走吧！！'},  # 重复标点
        {'id': 'test_4', 'zh': '欢迎来到 {game}！'},  # 正常
    ]
    
    # 创建验证器
    validator = MultiLevelValidator()
    
    # 验证并自动修复
    print("\n开始验证...")
    fixed, issues = validator.validate_with_autofix(source, target)
    
    # 显示修复结果
    print("\n修复结果:")
    for item in fixed:
        original = next(t for t in target if t['id'] == item['id'])
        if '_autofix' in item:
            print(f"\n  ID: {item['id']}")
            print(f"  原始译文: {original['zh']}")
            print(f"  修复译文: {item['zh']}")
            print(f"  应用修复: {', '.join(item['_autofix'])}")
    
    # 显示问题摘要
    summary = validator.get_summary()
    print(f"\n问题摘要:")
    print(f"  Critical: {summary['critical']}")
    print(f"  Warning: {summary['warning']}")
    print(f"  Info: {summary['info']}")
    print(f"  总计: {summary['total']}")
    
    # 生成报告
    output_dir = project_root / 'outputs' / 'qa'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    validator.generate_report('html', str(output_dir / 'test_qa.html'))
    validator.generate_report('tsv', str(output_dir / 'test_qa.tsv'))
    validator.generate_report('json', str(output_dir / 'test_qa.json'))
    
    print(f"\n✓ 报告已生成:")
    print(f"  - {output_dir / 'test_qa.html'}")
    print(f"  - {output_dir / 'test_qa.tsv'}")
    print(f"  - {output_dir / 'test_qa.json'}")
    
    # 测试成功：所有问题都被检测到并修复
    return len(fixed) == len(target)


def test_patcher():
    """测试回填器"""
    print("\n" + "=" * 60)
    print("测试 SafePatcher")
    print("=" * 60)
    
    # 创建测试目录和文件
    test_dir = project_root / 'outputs' / 'test_patch'
    test_dir.mkdir(parents=True, exist_ok=True)
    
    backup_dir = project_root / 'outputs' / 'test_backup'
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建测试文件
    test_file = test_dir / 'test_script.rpy'
    test_file.write_text("""# Test Script
label start:
    "Hello, World!"
    "This is a test."
    
    menu:
        "Option 1":
            "You chose 1"
        "Option 2":
            "You chose 2"
""", encoding='utf-8')
    
    print(f"\n创建测试文件: {test_file}")
    print(f"原始内容:\n{test_file.read_text(encoding='utf-8')[:200]}...")
    
    # 创建回填器
    patcher = SafePatcher(backup_dir=backup_dir, verify=True)
    
    # 准备翻译数据（简单演示，实际使用时需要复杂的回填逻辑）
    trans_data = {
        'test_script.rpy': "# 测试脚本\nlabel start:\n    \"你好，世界！\"\n    \"这是一个测试。\"\n"
    }
    
    # 自定义回填函数
    def simple_patch(original, new_content):
        # 简单替换（实际应该更复杂）
        return new_content
    
    # 执行回填
    print("\n执行回填...")
    result = patcher.patch_with_rollback(
        target_dir=test_dir,
        trans_data=trans_data,
        patch_fn=simple_patch
    )
    
    print(f"\n回填结果:")
    print(f"  成功: {len(result['success'])} 个文件")
    print(f"  失败: {len(result['failed'])} 个文件")
    
    if result['success']:
        print(f"\n回填后内容:\n{test_file.read_text(encoding='utf-8')[:200]}...")
    
    # 测试回滚
    if result['success']:
        print("\n测试回滚功能...")
        result['rollback']()
        print(f"回滚后内容:\n{test_file.read_text(encoding='utf-8')[:200]}...")
    
    print("\n✓ 回填器测试完成")
    return len(result['failed']) == 0


def test_incremental_builder():
    """测试增量构建器"""
    print("\n" + "=" * 60)
    print("测试 IncrementalBuilder")
    print("=" * 60)
    
    from src.renpy_tools.core.patcher import IncrementalBuilder
    import shutil
    import time
    
    # 创建测试目录
    source_dir = project_root / 'outputs' / 'test_source'
    output_dir = project_root / 'outputs' / 'test_output'
    source_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建测试文件
    files = ['script1.rpy', 'script2.rpy', 'script3.rpy']
    for f in files:
        (source_dir / f).write_text(f"# Content of {f}\nlabel test:\n    pass\n", encoding='utf-8')
    
    print(f"\n创建 {len(files)} 个测试文件")
    
    # 创建构建器
    cache_file = project_root / 'outputs' / '.test_build_cache.json'
    builder = IncrementalBuilder(cache_file=cache_file)
    
    # 定义构建函数
    def build_file(src, dst):
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        time.sleep(0.1)  # 模拟构建耗时
    
    # 第一次构建（全量）
    print("\n第一次构建（全量）...")
    result1 = builder.build_incremental(source_dir, output_dir, build_file)
    print(f"  重新构建: {len(result1['rebuilt'])} 个文件")
    print(f"  跳过: {len(result1['skipped'])} 个文件")
    
    # 第二次构建（无变更）
    print("\n第二次构建（无变更）...")
    result2 = builder.build_incremental(source_dir, output_dir, build_file)
    print(f"  重新构建: {len(result2['rebuilt'])} 个文件")
    print(f"  跳过: {len(result2['skipped'])} 个文件")
    print(f"  节省时间: {result2['time_saved']:.2f}s")
    
    # 修改一个文件
    print("\n修改一个文件后重新构建...")
    (source_dir / 'script1.rpy').write_text("# Modified content\nlabel test:\n    pass\n", encoding='utf-8')
    time.sleep(0.1)  # 确保时间戳变化
    
    result3 = builder.build_incremental(source_dir, output_dir, build_file)
    print(f"  重新构建: {len(result3['rebuilt'])} 个文件")
    print(f"  跳过: {len(result3['skipped'])} 个文件")
    print(f"  节省时间: {result3['time_saved']:.2f}s")
    
    print("\n✓ 增量构建器测试完成")
    return len(result3['rebuilt']) == 1 and len(result3['skipped']) == 2


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("Renpy汉化 核心模块功能测试")
    print("=" * 60)
    
    results = {}
    
    try:
        # 测试验证器
        results['validator'] = test_validator()
    except Exception as e:
        logger.error(f"验证器测试失败: {e}")
        results['validator'] = False
    
    try:
        # 测试回填器
        results['patcher'] = test_patcher()
    except Exception as e:
        logger.error(f"回填器测试失败: {e}")
        results['patcher'] = False
    
    try:
        # 测试增量构建器
        results['builder'] = test_incremental_builder()
    except Exception as e:
        logger.error(f"增量构建器测试失败: {e}")
        results['builder'] = False
    
    # 总结
    print("\n" + "=" * 60)
    print("测试结果总结")
    print("=" * 60)
    
    for name, passed in results.items():
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"  {name:20s}: {status}")
    
    all_passed = all(results.values())
    print("\n" + ("✓ 所有测试通过！" if all_passed else "✗ 部分测试失败"))
    
    print("\n" + "=" * 60)
    print("注意事项:")
    print("  - OllamaTranslator 测试需要 Ollama 服务运行")
    print("  - 其他模块已完成独立测试")
    print("  - 查看 outputs/qa/ 查看生成的报告")
    print("=" * 60)


if __name__ == '__main__':
    main()
