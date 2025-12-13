"""
核心模块功能测试

测试 OllamaTranslator, MultiLevelValidator, SafePatcher 的核心功能
使用 pytest 风格的断言
"""

import sys
import shutil
import tempfile
from pathlib import Path

import pytest

# 添加项目根目录
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from renpy_tools.core import MultiLevelValidator, SafePatcher
from renpy_tools.core.patcher import IncrementalBuilder


class TestMultiLevelValidator:
    """测试 MultiLevelValidator"""

    def setup_method(self):
        """每个测试方法前执行"""
        self.validator = MultiLevelValidator()

    def test_empty_translation_detected(self):
        """测试空翻译检测"""
        source = [{'id': 'test_1', 'en': 'Hello!'}]
        target = [{'id': 'test_1', 'zh': ''}]

        fixed, issues = self.validator.validate_with_autofix(source, target)

        assert len(issues['critical']) > 0
        assert any(i['type'] == 'empty' for i in issues['critical'])

    def test_placeholder_mismatch_detected(self):
        """测试占位符不匹配检测"""
        source = [{'id': 'test_1', 'en': 'Hello, [name]!'}]
        target = [{'id': 'test_1', 'zh': '你好！'}]

        fixed, issues = self.validator.validate_with_autofix(source, target)

        assert len(issues['critical']) > 0
        assert any(i['type'] == 'placeholder' for i in issues['critical'])

    def test_placeholder_autofix(self):
        """测试占位符自动修复"""
        source = [{'id': 'test_1', 'en': 'Hello, [name]!'}]
        target = [{'id': 'test_1', 'zh': '你好！'}]

        fixed, issues = self.validator.validate_with_autofix(source, target)

        # 检查是否添加了缺失的占位符
        assert '[name]' in fixed[0]['zh']

    def test_newline_mismatch_detected(self):
        """测试换行符不匹配检测"""
        source = [{'id': 'test_1', 'en': 'Line 1\nLine 2'}]
        target = [{'id': 'test_1', 'zh': '第一行第二行'}]

        fixed, issues = self.validator.validate_with_autofix(source, target)

        assert len(issues['critical']) > 0
        assert any(i['type'] == 'newline' for i in issues['critical'])

    def test_duplicate_punct_detected(self):
        """测试重复标点检测"""
        source = [{'id': 'test_1', 'en': 'Hello!'}]
        target = [{'id': 'test_1', 'zh': '你好！！'}]

        fixed, issues = self.validator.validate_with_autofix(source, target)

        assert any(i['type'] == 'duplicate_punct' for i in issues['info'])

    def test_duplicate_punct_autofix(self):
        """测试重复标点自动修复"""
        source = [{'id': 'test_1', 'en': 'Hello!'}]
        target = [{'id': 'test_1', 'zh': '你好。。'}]

        fixed, issues = self.validator.validate_with_autofix(source, target)

        # 检查是否修复了重复标点
        assert '。。' not in fixed[0]['zh']

    def test_correct_translation_passes(self):
        """测试正确翻译不产生问题"""
        source = [{'id': 'test_1', 'en': 'Welcome to {game}!'}]
        target = [{'id': 'test_1', 'zh': '欢迎来到 {game}！'}]

        fixed, issues = self.validator.validate_with_autofix(source, target)

        assert len(issues['critical']) == 0

    def test_get_summary(self):
        """测试获取摘要"""
        source = [
            {'id': 'test_1', 'en': 'Hello, [name]!'},
            {'id': 'test_2', 'en': 'OK'},
        ]
        target = [
            {'id': 'test_1', 'zh': '你好！'},  # 缺失占位符
            {'id': 'test_2', 'zh': '确定'},  # 正确
        ]

        self.validator.validate_with_autofix(source, target)
        summary = self.validator.get_summary()

        assert 'critical' in summary
        assert 'warning' in summary
        assert 'info' in summary
        assert 'total' in summary

    def test_generate_html_report(self):
        """测试生成 HTML 报告"""
        source = [{'id': 'test_1', 'en': 'Hello!'}]
        target = [{'id': 'test_1', 'zh': '你好！'}]

        self.validator.validate_with_autofix(source, target)
        report = self.validator.generate_report('html')

        assert '<!DOCTYPE html>' in report
        assert 'Translation Quality Report' in report

    def test_generate_tsv_report(self):
        """测试生成 TSV 报告"""
        source = [{'id': 'test_1', 'en': 'Hello, [name]!'}]
        target = [{'id': 'test_1', 'zh': '你好！'}]

        self.validator.validate_with_autofix(source, target)
        report = self.validator.generate_report('tsv')

        assert 'Level\tID\tType\tMessage' in report


class TestSafePatcher:
    """测试 SafePatcher"""

    def setup_method(self):
        """每个测试方法前执行"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.target_dir = self.temp_dir / "target"
        self.backup_dir = self.temp_dir / "backup"
        self.target_dir.mkdir()
        self.backup_dir.mkdir()

    def teardown_method(self):
        """每个测试方法后执行"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_patch_creates_backup(self):
        """测试回填创建备份"""
        # 创建测试文件
        test_file = self.target_dir / "test.rpy"
        test_file.write_text('label start:\n    "Hello!"\n', encoding='utf-8')

        patcher = SafePatcher(backup_dir=self.backup_dir, verify=False)
        trans_data = {'test.rpy': 'label start:\n    "你好！"\n'}

        result = patcher.patch_with_rollback(
            target_dir=self.target_dir,
            trans_data=trans_data,
            patch_fn=lambda orig, new: new
        )

        # 检查备份是否创建
        backup_file = self.backup_dir / "test.rpy"
        assert backup_file.exists()
        assert 'Hello' in backup_file.read_text(encoding='utf-8')

    def test_patch_applies_changes(self):
        """测试回填应用更改"""
        test_file = self.target_dir / "test.rpy"
        test_file.write_text('label start:\n    "Hello!"\n', encoding='utf-8')

        patcher = SafePatcher(backup_dir=self.backup_dir, verify=False)
        trans_data = {'test.rpy': 'label start:\n    "你好！"\n'}

        patcher.patch_with_rollback(
            target_dir=self.target_dir,
            trans_data=trans_data,
            patch_fn=lambda orig, new: new
        )

        # 检查文件是否更新
        content = test_file.read_text(encoding='utf-8')
        assert '你好' in content

    def test_rollback_restores_original(self):
        """测试回滚恢复原始内容"""
        test_file = self.target_dir / "test.rpy"
        original_content = 'label start:\n    "Hello!"\n'
        test_file.write_text(original_content, encoding='utf-8')

        patcher = SafePatcher(backup_dir=self.backup_dir, verify=False)
        trans_data = {'test.rpy': 'label start:\n    "你好！"\n'}

        result = patcher.patch_with_rollback(
            target_dir=self.target_dir,
            trans_data=trans_data,
            patch_fn=lambda orig, new: new
        )

        # 执行回滚
        result['rollback']()

        # 检查文件是否恢复
        content = test_file.read_text(encoding='utf-8')
        assert content == original_content

    def test_missing_file_reported(self):
        """测试缺失文件报告"""
        patcher = SafePatcher(backup_dir=self.backup_dir, verify=False)
        trans_data = {'nonexistent.rpy': 'some content'}

        result = patcher.patch_with_rollback(
            target_dir=self.target_dir,
            trans_data=trans_data,
            patch_fn=lambda orig, new: new
        )

        assert len(result['failed']) == 1
        assert 'nonexistent.rpy' in result['failed'][0]['file']

    def test_path_traversal_blocked(self):
        """测试路径遍历攻击被阻止"""
        test_file = self.target_dir / "test.rpy"
        test_file.write_text('content', encoding='utf-8')

        patcher = SafePatcher(backup_dir=self.backup_dir, verify=False)
        trans_data = {'../../../etc/passwd': 'malicious content'}

        result = patcher.patch_with_rollback(
            target_dir=self.target_dir,
            trans_data=trans_data,
            patch_fn=lambda orig, new: new
        )

        # 应该失败，路径不安全
        assert len(result['failed']) == 1
        assert 'Unsafe path' in result['failed'][0]['error']


class TestIncrementalBuilder:
    """测试 IncrementalBuilder"""

    def setup_method(self):
        """每个测试方法前执行"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.source_dir = self.temp_dir / "source"
        self.output_dir = self.temp_dir / "output"
        self.cache_file = self.temp_dir / ".build_cache.json"
        self.source_dir.mkdir()
        self.output_dir.mkdir()

    def teardown_method(self):
        """每个测试方法后执行"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_first_build_processes_all(self):
        """测试首次构建处理所有文件"""
        # 创建测试文件
        for i in range(3):
            (self.source_dir / f"script{i}.rpy").write_text(
                f"# Script {i}\nlabel test:\n    pass\n",
                encoding='utf-8'
            )

        builder = IncrementalBuilder(cache_file=self.cache_file)

        def build_fn(src, dst):
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

        result = builder.build_incremental(
            self.source_dir, self.output_dir, build_fn
        )

        assert len(result['rebuilt']) == 3
        assert len(result['skipped']) == 0

    def test_second_build_skips_unchanged(self):
        """测试第二次构建跳过未更改文件"""
        # 创建测试文件
        for i in range(3):
            (self.source_dir / f"script{i}.rpy").write_text(
                f"# Script {i}\nlabel test:\n    pass\n",
                encoding='utf-8'
            )

        builder = IncrementalBuilder(cache_file=self.cache_file)

        def build_fn(src, dst):
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

        # 第一次构建
        builder.build_incremental(self.source_dir, self.output_dir, build_fn)

        # 第二次构建（无更改）
        result = builder.build_incremental(
            self.source_dir, self.output_dir, build_fn
        )

        assert len(result['rebuilt']) == 0
        assert len(result['skipped']) == 3

    def test_modified_file_rebuilt(self):
        """测试修改的文件被重新构建"""
        import time

        # 创建测试文件
        for i in range(3):
            (self.source_dir / f"script{i}.rpy").write_text(
                f"# Script {i}\nlabel test:\n    pass\n",
                encoding='utf-8'
            )

        builder = IncrementalBuilder(cache_file=self.cache_file)

        def build_fn(src, dst):
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

        # 第一次构建
        builder.build_incremental(self.source_dir, self.output_dir, build_fn)

        # 等待一小段时间确保时间戳变化
        time.sleep(0.1)

        # 修改一个文件
        (self.source_dir / "script0.rpy").write_text(
            "# Modified\nlabel test:\n    pass\n",
            encoding='utf-8'
        )

        # 第二次构建
        result = builder.build_incremental(
            self.source_dir, self.output_dir, build_fn
        )

        assert len(result['rebuilt']) == 1
        assert len(result['skipped']) == 2
        assert 'script0.rpy' in result['rebuilt'][0]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
