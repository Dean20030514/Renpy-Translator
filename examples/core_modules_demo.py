"""
Renpy汉化 - 核心优化模块使用示例

演示如何使用新的 OllamaTranslator, MultiLevelValidator, SafePatcher
"""

import sys
from pathlib import Path

# 添加项目根目录
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.renpy_tools.core import OllamaTranslator, MultiLevelValidator, SafePatcher


def example_translator():
    """示例：使用 OllamaTranslator 翻译"""
    print("=== OllamaTranslator 示例 ===\n")
    
    # 初始化翻译器
    with OllamaTranslator(
        host="http://localhost:11434",
        model="qwen2.5:14b",
        quality_threshold=0.7,
        max_retries=3
    ) as translator:
        
        # 翻译单个文本
        result = translator.translate_with_validation(
            text="Hello, [name]! What's your favorite color?",
            context={'type': 'dialog'}
        )
        
        print(f"原文: Hello, [name]! What's your favorite color?")
        print(f"译文: {result['text']}")
        print(f"质量分数: {result['quality_score']:.2f}")
        print(f"问题: {result['issues']}")
        print(f"重试次数: {result['retries']}")
        print(f"耗时: {result['time']:.2f}s\n")
        
        # 批量翻译
        texts = [
            "New Game",
            "Load Game",
            "Preferences",
            "About"
        ]
        
        for text in texts:
            result = translator.translate_with_validation(text)
            print(f"{text} → {result['text']}")
        
        # 获取统计
        stats = translator.get_stats()
        print(f"\n统计信息:")
        print(f"  总计: {stats['total']}")
        print(f"  成功: {stats['success']}")
        print(f"  重试: {stats['retry']}")
        print(f"  失败: {stats['failed']}")
        print(f"  成功率: {stats['success_rate']:.1%}")
        print(f"  平均耗时: {stats['avg_time']:.2f}s")


def example_validator():
    """示例：使用 MultiLevelValidator 验证"""
    print("\n\n=== MultiLevelValidator 示例 ===\n")
    
    # 模拟数据
    source = [
        {'id': 'line_1', 'en': 'Hello, [name]!'},
        {'id': 'line_2', 'en': 'What is your\nfavorite color?'},
        {'id': 'line_3', 'en': 'Let\'s go!'},
    ]
    
    target = [
        {'id': 'line_1', 'zh': '你好！'},  # 缺失占位符
        {'id': 'line_2', 'zh': '你最喜欢的颜色是什么？'},  # 缺失换行符
        {'id': 'line_3', 'zh': '我们走吧！！'},  # 重复标点
    ]
    
    # 初始化验证器
    validator = MultiLevelValidator()
    
    # 验证并自动修复
    fixed, issues = validator.validate_with_autofix(source, target)
    
    # 显示修复结果
    print("修复后的译文:")
    for item in fixed:
        original = next(t for t in target if t['id'] == item['id'])
        if '_autofix' in item:
            print(f"  {item['id']}:")
            print(f"    原始: {original['zh']}")
            print(f"    修复: {item['zh']}")
            print(f"    应用修复: {item['_autofix']}")
    
    # 显示问题摘要
    summary = validator.get_summary()
    print(f"\n问题摘要:")
    print(f"  Critical: {summary['critical']}")
    print(f"  Warning: {summary['warning']}")
    print(f"  Info: {summary['info']}")
    print(f"  总计: {summary['total']}")
    
    # 生成报告（实际使用时取消注释）
    # validator.generate_report('html', 'outputs/qa/qa.html')
    # validator.generate_report('tsv', 'outputs/qa/qa.tsv')
    # validator.generate_report('json', 'outputs/qa/qa.json')
    print("\n（HTML/TSV/JSON 报告已生成到 outputs/qa/）")


def example_patcher():
    """示例：使用 SafePatcher 回填"""
    print("\n\n=== SafePatcher 示例 ===\n")
    
    # 初始化回填器
    patcher = SafePatcher(
        backup_dir=Path('outputs/backups'),
        verify=True
    )
    
    # 模拟翻译数据（实际使用时从 JSONL 加载）
    trans_data = {
        'script.rpy': {
            'line_10': '    "你好，[name]！"',
            'line_15': '    "你最喜欢的颜色是什么？"',
        }
    }
    
    # 自定义回填函数（实际使用时根据文件格式定义）
    def custom_patch(original_text, trans):
        lines = original_text.splitlines()
        for line_id, new_line in trans.items():
            if isinstance(line_id, str) and line_id.startswith('line_'):
                idx = int(line_id.split('_')[1])
                if 0 <= idx < len(lines):
                    lines[idx] = new_line
        return '\n'.join(lines)
    
    # 执行回填（注释掉以避免实际修改文件）
    # result = patcher.patch_with_rollback(
    #     target_dir=Path('game'),
    #     trans_data=trans_data,
    #     patch_fn=custom_patch
    # )
    
    # print(f"成功回填: {len(result['success'])} 个文件")
    # print(f"失败: {len(result['failed'])} 个文件")
    
    # if result['failed']:
    #     print("回填失败，执行回滚...")
    #     result['rollback']()
    
    print("（示例代码，未实际执行回填）")
    print("使用方法:")
    print("  1. 准备翻译数据（JSONL）")
    print("  2. 调用 patch_with_rollback()")
    print("  3. 如果失败，调用 result['rollback']() 恢复")


def example_incremental_build():
    """示例：使用 IncrementalBuilder 增量构建"""
    print("\n\n=== IncrementalBuilder 示例 ===\n")
    
    from src.renpy_tools.core.patcher import IncrementalBuilder
    import shutil
    
    # 初始化构建器
    builder = IncrementalBuilder(
        cache_file=Path('.build_cache.json')
    )
    
    # 自定义构建函数
    def build_file(source_file, output_file):
        """简单复制（实际使用时替换为实际构建逻辑）"""
        output_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_file, output_file)
    
    # 执行增量构建（注释掉以避免实际构建）
    # result = builder.build_incremental(
    #     source_dir=Path('game'),
    #     output_dir=Path('outputs/build_cn'),
    #     build_fn=build_file
    # )
    
    # print(f"重新构建: {len(result['rebuilt'])} 个文件")
    # print(f"跳过: {len(result['skipped'])} 个文件")
    # print(f"节省时间: {result['time_saved']:.1f}s")
    
    print("（示例代码，未实际执行构建）")
    print("使用方法:")
    print("  1. 定义构建函数 build_fn(source, output)")
    print("  2. 调用 build_incremental()")
    print("  3. 构建器自动检测变更文件，只处理变更部分")


if __name__ == '__main__':
    print("Renpy汉化 - 核心优化模块演示\n")
    print("=" * 60)
    
    # 运行示例
    try:
        # example_translator()  # 需要 Ollama 服务运行
        example_validator()
        example_patcher()
        example_incremental_build()
    except Exception as e:
        print(f"\n错误: {e}")
        print("\n注意:")
        print("  - example_translator() 需要 Ollama 服务运行")
        print("  - 其他示例使用模拟数据，可安全运行")
    
    print("\n" + "=" * 60)
    print("\n完整使用文档: CODE_OPTIMIZATION_IMPLEMENTATION.md")
    print("详细计划: CODE_ENHANCEMENT_PLAN.md")
