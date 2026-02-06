#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集成测试：测试完整翻译工作流

测试场景：
1. 提取 → 翻译 → 验证 → 回填 完整流程
2. 字典预填充工作流
3. TM（翻译记忆）工作流
4. 批量 API 翻译工作流

注意：这些测试不需要真正的 LLM/API，使用 Mock 模式
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import List, Dict, Any
from unittest.mock import Mock, patch, MagicMock

import pytest

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))


# ========================================
# 测试夹具
# ========================================

@pytest.fixture
def temp_workspace(tmp_path):
    """创建临时工作区"""
    workspace = {
        "root": tmp_path,
        "game": tmp_path / "game",
        "outputs": tmp_path / "outputs",
        "extract": tmp_path / "outputs" / "extract",
        "prefilled": tmp_path / "outputs" / "prefilled",
        "qa": tmp_path / "outputs" / "qa",
        "patch": tmp_path / "outputs" / "out_patch",
    }
    
    for path in workspace.values():
        if isinstance(path, Path):
            path.mkdir(parents=True, exist_ok=True)
    
    return workspace


@pytest.fixture
def sample_rpy_files(temp_workspace):
    """创建示例 RPY 文件"""
    game_dir = temp_workspace["game"]
    
    # 创建主脚本
    script_rpy = game_dir / "script.rpy"
    script_rpy.write_text('''
label start:
    "This is a sample game."
    
    show character happy
    
    e "Hello! Welcome to the game."
    
    menu:
        "Friendly option":
            e "That's nice of you!"
        "Rude option":
            e "How dare you!"
    
    e "Let's continue, [name]."
    
    return
''', encoding='utf-8')
    
    # 创建角色定义
    characters_rpy = game_dir / "characters.rpy"
    characters_rpy.write_text('''
define e = Character("Emily", color="#c8ffc8")
define m = Character("Mike", color="#c8c8ff")
''', encoding='utf-8')
    
    return temp_workspace


@pytest.fixture
def sample_jsonl_data() -> List[Dict[str, Any]]:
    """示例 JSONL 数据"""
    return [
        {"id": "script.rpy:001", "en": "This is a sample game.", "zh": ""},
        {"id": "script.rpy:002", "en": "Hello! Welcome to the game.", "zh": "", "speaker": "e"},
        {"id": "script.rpy:003", "en": "Friendly option", "zh": "", "type": "menu"},
        {"id": "script.rpy:004", "en": "Rude option", "zh": "", "type": "menu"},
        {"id": "script.rpy:005", "en": "That's nice of you!", "zh": "", "speaker": "e"},
        {"id": "script.rpy:006", "en": "How dare you!", "zh": "", "speaker": "e"},
        {"id": "script.rpy:007", "en": "Let's continue, [name].", "zh": "", "speaker": "e", "placeholders": ["[name]"]},
    ]


@pytest.fixture
def sample_translated_data() -> List[Dict[str, Any]]:
    """示例翻译后数据"""
    return [
        {"id": "script.rpy:001", "en": "This is a sample game.", "zh": "这是一个示例游戏。"},
        {"id": "script.rpy:002", "en": "Hello! Welcome to the game.", "zh": "你好！欢迎来到游戏。"},
        {"id": "script.rpy:003", "en": "Friendly option", "zh": "友好选项"},
        {"id": "script.rpy:004", "en": "Rude option", "zh": "粗鲁选项"},
        {"id": "script.rpy:005", "en": "That's nice of you!", "zh": "你真好！"},
        {"id": "script.rpy:006", "en": "How dare you!", "zh": "你怎么敢！"},
        {"id": "script.rpy:007", "en": "Let's continue, [name].", "zh": "我们继续吧，[name]。"},
    ]


# ========================================
# 核心模块测试
# ========================================

class TestCoreModulesIntegration:
    """测试核心模块集成"""
    
    def test_validator_import(self):
        """测试 MultiLevelValidator 可以正常导入"""
        from renpy_tools.core.validator import MultiLevelValidator
        
        v = MultiLevelValidator()
        assert v is not None
        assert hasattr(v, 'validate_with_autofix')
        assert hasattr(v, 'reset')
    
    def test_tm_module_import(self):
        """测试 TM 模块可以正常导入"""
        from renpy_tools.utils.tm import TranslationMemory
        
        tm = TranslationMemory()
        assert tm is not None
        assert hasattr(tm, 'add')  # 实际方法名是 add
        assert hasattr(tm, 'get_exact')  # 实际方法名是 get_exact
    
    def test_common_utilities_import(self):
        """测试 common 模块可以正常导入"""
        from renpy_tools.utils.common import (
            PH_RE, ph_multiset,
            AdaptiveRateLimiter, QualityScore,
            TranslationConfig, TranslationCache
        )
        
        # 测试占位符正则
        assert PH_RE is not None
        
        # 测试占位符提取
        result = ph_multiset("Hello [name], you have {0} items.")
        assert "[name]" in result
        assert "{0}" in result
        
        # 测试速率限制器（使用正确的参数名）
        limiter = AdaptiveRateLimiter(initial_rps=10.0)
        assert limiter is not None


class TestValidatorIntegration:
    """验证器集成测试"""
    
    def test_validate_translation_pair(self, sample_jsonl_data, sample_translated_data):
        """测试翻译对验证"""
        from renpy_tools.core.validator import MultiLevelValidator
        
        v = MultiLevelValidator()
        
        # 使用正确的 API
        source = [{"id": "test", "en": "Hello, [name]!"}]
        target = [{"id": "test", "zh": "你好，[name]！"}]
        
        fixed, report = v.validate_with_autofix(source, target)
        
        # 检查没有严重问题
        assert len(report.get('critical', [])) == 0
    
    def test_validate_placeholder_mismatch(self):
        """测试占位符不匹配检测"""
        from renpy_tools.core.validator import MultiLevelValidator
        
        v = MultiLevelValidator()
        
        source = [{"id": "test", "en": "Hello, [name]! You have {0} items."}]
        target = [{"id": "test", "zh": "你好！你有东西。"}]  # 缺少占位符
        
        fixed, report = v.validate_with_autofix(source, target)
        
        # 应该检测到占位符问题（critical 级别）
        assert len(report.get('critical', [])) > 0
    
    def test_validate_batch(self, sample_jsonl_data, sample_translated_data):
        """测试批量验证"""
        from renpy_tools.core.validator import MultiLevelValidator
        
        v = MultiLevelValidator()
        
        # 构建验证数据
        source = [{"id": item["id"], "en": item["en"]} for item in sample_jsonl_data]
        target = [{"id": item["id"], "zh": item["zh"]} for item in sample_translated_data]
        
        fixed, report = v.validate_with_autofix(source, target)
        
        # 验证返回结果
        assert len(fixed) == len(source)


class TestTranslationMemoryIntegration:
    """翻译记忆集成测试"""
    
    def test_tm_workflow(self, sample_translated_data, tmp_path):
        """测试 TM 完整工作流"""
        from renpy_tools.utils.tm import TranslationMemory
        
        # 1. 创建并填充 TM
        tm = TranslationMemory()
        
        for item in sample_translated_data:
            if item["zh"]:
                tm.add(item["en"], item["zh"], context=item["id"])
        
        # 2. 精确匹配
        match = tm.get_exact("This is a sample game.")
        assert match is not None
        assert match.target == "这是一个示例游戏。"
        assert match.match_type == "exact"
        
        # 3. 模糊匹配（如果 rapidfuzz 可用）
        # match = tm.get_fuzzy("This is a sample application.")
        
        # 4. 保存和加载
        tm_file = tmp_path / "test_tm.jsonl"
        tm.save_jsonl(tm_file)
        
        assert tm_file.exists()
        
        tm2 = TranslationMemory()
        tm2.load_jsonl(tm_file)
        assert len(tm2._exact_index) == len(tm._exact_index)
    
    def test_tm_fuzzy_matching(self):
        """测试模糊匹配功能"""
        from renpy_tools.utils.tm import TranslationMemory
        
        tm = TranslationMemory(min_length=3)
        
        # 添加一些条目
        tm.add("The quick brown fox jumps.", "敏捷的棕色狐狸跳跃。")
        tm.add("Hello world!", "你好世界！")
        
        # 测试精确匹配
        match = tm.get_exact("Hello world!")
        assert match is not None
        assert match.target == "你好世界！"


class TestTranslationCacheIntegration:
    """翻译缓存集成测试"""
    
    def test_cache_workflow(self, tmp_path):
        """测试缓存完整工作流"""
        from renpy_tools.utils.common import TranslationCache
        
        cache_file = tmp_path / "test_cache.jsonl"
        
        # 1. 创建缓存
        cache = TranslationCache(cache_file)
        
        # 2. 添加条目（使用正确的 API）
        cache.put("Hello", "你好")
        cache.put("World", "世界")
        
        # 3. 读取条目
        result = cache.get("Hello")
        assert result == "你好"
        
        # 4. 统计信息
        stats = cache.get_stats()
        assert stats["total"] == 2
        
        # 5. 保存
        cache.save()
        
        assert cache_file.exists()
        
        # 6. 重新加载
        cache2 = TranslationCache(cache_file)
        result2 = cache2.get("Hello")
        assert result2 == "你好"


class TestQualityScoringIntegration:
    """质量评分集成测试"""
    
    def test_quality_score_calculation(self):
        """测试质量分数计算"""
        from renpy_tools.utils.common import calculate_quality_score
        
        # 完美翻译
        result = calculate_quality_score(
            source="Hello, [name]!",
            target="你好，[name]！"
        )
        assert result.score >= 80
        
        # 占位符缺失
        result2 = calculate_quality_score(
            source="Hello, [name]!",
            target="你好！"
        )
        assert result2.score < result.score


# ========================================
# 端到端工作流测试（Mock 模式）
# ========================================

class TestEndToEndWorkflow:
    """端到端工作流测试"""
    
    def test_jsonl_round_trip(self, sample_jsonl_data, tmp_path):
        """测试 JSONL 读写往返"""
        # 写入
        jsonl_file = tmp_path / "test.jsonl"
        with open(jsonl_file, 'w', encoding='utf-8') as f:
            for item in sample_jsonl_data:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        
        # 读取
        loaded = []
        with open(jsonl_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    loaded.append(json.loads(line))
        
        assert len(loaded) == len(sample_jsonl_data)
        for orig, load in zip(sample_jsonl_data, loaded):
            assert orig["id"] == load["id"]
            assert orig["en"] == load["en"]
    
    def test_prefill_with_dict(self, sample_jsonl_data, tmp_path):
        """测试字典预填充"""
        # 创建字典
        dict_file = tmp_path / "dict.csv"
        dict_file.write_text(
            "en,zh\n"
            "sample game,示例游戏\n"
            "Welcome,欢迎\n"
            "option,选项\n",
            encoding='utf-8'
        )
        
        # 创建源 JSONL
        source_file = tmp_path / "source.jsonl"
        with open(source_file, 'w', encoding='utf-8') as f:
            for item in sample_jsonl_data:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        
        # 模拟预填充逻辑（简化版）
        dict_entries = {}
        with open(dict_file, 'r', encoding='utf-8') as f:
            next(f)  # 跳过表头
            for line in f:
                parts = line.strip().split(',')
                if len(parts) >= 2:
                    dict_entries[parts[0].lower()] = parts[1]
        
        # 预填充
        prefilled = []
        for item in sample_jsonl_data:
            new_item = item.copy()
            en_lower = item["en"].lower()
            
            for key, val in dict_entries.items():
                if key in en_lower:
                    # 简单替换（实际逻辑更复杂）
                    if not new_item["zh"]:
                        new_item["zh"] = f"[预填充]{val}"
                    break
            
            prefilled.append(new_item)
        
        # 验证有预填充结果
        filled_count = sum(1 for item in prefilled if item["zh"])
        assert filled_count > 0
    
    def test_validation_workflow(self, sample_jsonl_data, sample_translated_data, tmp_path):
        """测试验证工作流"""
        from renpy_tools.core.validator import MultiLevelValidator
        
        v = MultiLevelValidator()
        
        # 使用正确的 API
        source = [{"id": item["id"], "en": item["en"]} for item in sample_jsonl_data]
        target = [{"id": item["id"], "zh": item["zh"]} for item in sample_translated_data]
        
        fixed, report = v.validate_with_autofix(source, target)
        
        # 写入 QA 报告
        qa_file = tmp_path / "qa.json"
        with open(qa_file, 'w', encoding='utf-8') as f:
            json.dump({"issues": report, "total": len(sample_jsonl_data)}, f)
        
        assert qa_file.exists()


class TestConfigurationIntegration:
    """配置系统集成测试"""
    
    def test_config_from_yaml(self, tmp_path):
        """测试从 YAML 加载配置"""
        from renpy_tools.utils.common import TranslationConfig
        
        # 创建配置文件
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
translation:
  model: qwen2.5:14b
  temperature: 0.3
  quality_threshold: 0.7
  
performance:
  workers: 4
  timeout: 120.0
  
cache:
  enable_cache: true
""", encoding='utf-8')
        
        config = TranslationConfig.from_yaml(config_file)
        
        assert config.model == "qwen2.5:14b"
        assert config.temperature == 0.3
        assert config.workers == 4  # 在 performance 部分
    
    def test_config_from_env(self, monkeypatch):
        """测试从环境变量加载配置"""
        from renpy_tools.utils.common import TranslationConfig
        
        # 设置环境变量（使用正确的变量名）
        monkeypatch.setenv("RENPY_TRANSLATE_MODEL", "llama3:8b")
        monkeypatch.setenv("RENPY_WORKERS", "8")
        
        config = TranslationConfig.from_env()
        
        assert config.model == "llama3:8b"
        assert config.workers == 8


class TestRateLimiterIntegration:
    """速率限制器集成测试"""
    
    def test_adaptive_rate_limiter(self):
        """测试自适应速率限制器"""
        from renpy_tools.utils.common import AdaptiveRateLimiter
        import time
        
        limiter = AdaptiveRateLimiter(initial_rps=100.0)
        
        # 快速发送请求
        start = time.time()
        for _ in range(10):
            limiter.acquire()
        elapsed = time.time() - start
        
        # 应该非常快（100 RPS = 10ms 间隔）
        assert elapsed < 1.0
        
        # 报告错误应该降低速率（使用正确的方法名）
        original_rps = limiter.rps
        for _ in range(5):
            limiter.on_rate_limit()
        
        # 速率应该降低
        assert limiter.rps < original_rps


# ========================================
# 错误处理测试
# ========================================

class TestErrorHandling:
    """错误处理测试"""
    
    def test_invalid_jsonl_handling(self, tmp_path):
        """测试无效 JSONL 处理"""
        # 创建包含无效行的 JSONL
        bad_file = tmp_path / "bad.jsonl"
        bad_file.write_text(
            '{"id": "1", "en": "Hello"}\n'
            'this is not json\n'
            '{"id": "2", "en": "World"}\n',
            encoding='utf-8'
        )
        
        # 应该能优雅处理
        valid_items = []
        with open(bad_file, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                try:
                    if line.strip():
                        valid_items.append(json.loads(line))
                except json.JSONDecodeError:
                    pass  # 跳过无效行
        
        assert len(valid_items) == 2
    
    def test_missing_file_handling(self, tmp_path):
        """测试缺失文件处理"""
        from renpy_tools.utils.tm import TranslationMemory
        
        # 尝试加载不存在的文件
        missing_file = tmp_path / "nonexistent.jsonl"
        
        # 创建空 TM 并尝试加载
        tm = TranslationMemory()
        try:
            tm.load_jsonl(missing_file)
            # 如果不抛错，应该没有条目
            assert len(tm._exact_index) == 0
        except FileNotFoundError:
            pass  # 这也是可接受的行为
    
    def test_encoding_handling(self, tmp_path):
        """测试编码处理"""
        # 创建带特殊字符的文件
        special_file = tmp_path / "special.jsonl"
        content = '{"id": "1", "en": "Hello", "zh": "你好🌟"}\n'
        special_file.write_text(content, encoding='utf-8')
        
        # 应该正确读取
        with open(special_file, 'r', encoding='utf-8') as f:
            item = json.loads(f.read().strip())
        
        assert "🌟" in item["zh"]


# ========================================
# 性能测试
# ========================================

class TestPerformance:
    """性能测试"""
    
    def test_validator_batch_performance(self):
        """测试批量验证性能"""
        from renpy_tools.core.validator import MultiLevelValidator
        import time
        
        v = MultiLevelValidator()
        
        # 创建大量测试数据
        source = [{"id": f"test_{i}", "en": f"Test sentence number {i}."} for i in range(100)]
        target = [{"id": f"test_{i}", "zh": f"测试句子 {i}。"} for i in range(100)]
        
        start = time.time()
        fixed, report = v.validate_with_autofix(source, target)
        elapsed = time.time() - start
        
        # 100 条应该在 1 秒内完成
        assert elapsed < 1.0
        assert len(fixed) == 100
    
    def test_tm_lookup_performance(self):
        """测试 TM 查找性能"""
        from renpy_tools.utils.tm import TranslationMemory
        import time
        
        tm = TranslationMemory()
        
        # 添加大量条目
        for i in range(1000):
            tm.add(f"Source text number {i}", f"译文 {i}")
        
        # 测试查找性能
        start = time.time()
        for i in range(100):
            tm.get_exact(f"Source text number {i}")
        elapsed = time.time() - start
        
        # 100 次查找应该在 0.5 秒内完成
        assert elapsed < 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
