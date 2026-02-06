"""
新增功能测试

测试 v2.0 新增的功能模块:
- 速率限制器 (AdaptiveRateLimiter)
- 质量评分 (calculate_quality_score)
- 翻译缓存 (TranslationCache)
- 翻译配置 (TranslationConfig)
- 翻译记忆 (TranslationMemory)
- 缓存批量操作 (kv_set_batch, kv_get_batch)
- 增强的 Validator 检查规则
"""

import sys
import tempfile
import time
from pathlib import Path

import pytest

# 添加项目根目录
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from renpy_tools.utils.common import (
    PH_RE, ph_set, ph_multiset, strip_renpy_tags,
    AdaptiveRateLimiter, QualityScore, calculate_quality_score,
    TranslationConfig, TranslationCache
)
from renpy_tools.utils.cache import (
    kv_set, kv_get, kv_set_batch, kv_get_batch,
    kv_delete, kv_clear, kv_count, close_all_connections
)
from renpy_tools.utils.tm import (
    TranslationMemory, TMEntry, TMMatch,
    get_global_tm, query_tm
)
from renpy_tools.core.validator import MultiLevelValidator


class TestPlaceholderFunctions:
    """测试占位符相关函数"""
    
    def test_ph_re_matches_brackets(self):
        """测试 PH_RE 匹配方括号占位符"""
        text = "Hello, [name]! Welcome to [place]."
        matches = PH_RE.findall(text)
        assert "[name]" in matches
        assert "[place]" in matches
    
    def test_ph_re_matches_format_strings(self):
        """测试 PH_RE 匹配格式化字符串"""
        text = "Score: %d, Name: %s, Value: {0}"
        matches = PH_RE.findall(text)
        assert "%d" in matches
        assert "%s" in matches
        assert "{0}" in matches
    
    def test_ph_set(self):
        """测试 ph_set 去重"""
        text = "[name] says hello to [name] at [place]"
        result = ph_set(text)
        assert result == {"[name]", "[place]"}
    
    def test_ph_multiset(self):
        """测试 ph_multiset 计数"""
        text = "[name] says hello to [name] at [place]"
        result = ph_multiset(text)
        assert result["[name]"] == 2
        assert result["[place]"] == 1
    
    def test_strip_renpy_tags(self):
        """测试去除 Ren'Py 标签"""
        text = "{i}Hello{/i} {b}World{/b}!"
        result = strip_renpy_tags(text)
        assert result == "Hello World!"


class TestAdaptiveRateLimiter:
    """测试自适应速率限制器"""
    
    def test_basic_rate_limiting(self):
        """测试基本速率限制"""
        limiter = AdaptiveRateLimiter(initial_rps=10.0)
        
        # 获取请求许可
        start = time.time()
        for _ in range(3):
            limiter.acquire()
            limiter.on_success()
        elapsed = time.time() - start
        
        # 应该需要一些时间（但不超过2秒）
        assert elapsed < 2.0
    
    def test_record_error_adjustment(self):
        """测试错误记录调整"""
        limiter = AdaptiveRateLimiter(initial_rps=10.0)
        initial_rps = limiter.rps
        
        # 记录多次速率限制
        for _ in range(3):
            limiter.on_rate_limit()
        
        # RPS 应该降低
        assert limiter.rps < initial_rps
    
    def test_get_stats(self):
        """测试统计信息"""
        limiter = AdaptiveRateLimiter(initial_rps=10.0)
        limiter.acquire()
        limiter.on_success()
        limiter.acquire()
        limiter.on_success()
        limiter.on_rate_limit()
        
        stats = limiter.stats
        assert stats["total_requests"] == 2
        assert stats["rate_limited_count"] == 1


class TestQualityScore:
    """测试质量评分系统"""
    
    def test_calculate_perfect_score(self):
        """测试完美翻译的评分"""
        score = calculate_quality_score(
            source="Hello, [name]!",
            target="你好，[name]！"
        )
        assert score.score >= 80  # 高分
        assert score.is_good
    
    def test_missing_placeholder_penalty(self):
        """测试缺失占位符的惩罚"""
        score = calculate_quality_score(
            source="Hello, [name]!",
            target="你好！"
        )
        assert "placeholder_mismatch" in score.issues
        assert score.score < 80
    
    def test_length_ratio_warning(self):
        """测试长度比例警告"""
        score = calculate_quality_score(
            source="Hello",
            target="这是一个非常非常非常长的翻译，比原文长很多很多倍"
        )
        assert "too_long" in score.issues


class TestTranslationConfig:
    """测试翻译配置"""
    
    def test_default_values(self):
        """测试默认值"""
        config = TranslationConfig()
        assert config.model == "qwen2.5:14b"
        assert config.temperature == 0.2
        assert config.max_retries == 3
    
    def test_custom_values(self):
        """测试自定义值"""
        config = TranslationConfig(
            model="llama3:8b",
            temperature=0.5,
            max_retries=5
        )
        assert config.model == "llama3:8b"
        assert config.temperature == 0.5
        assert config.max_retries == 5
    
    def test_from_env(self):
        """测试从环境变量创建"""
        import os
        os.environ["RENPY_TRANSLATE_MODEL"] = "test_model"
        config = TranslationConfig.from_env()
        assert config.model == "test_model"
        del os.environ["RENPY_TRANSLATE_MODEL"]


class TestTranslationCache:
    """测试翻译缓存"""
    
    def test_cache_hit(self):
        """测试缓存命中"""
        cache = TranslationCache()
        cache.put("Hello", "你好")
        
        result = cache.get("Hello")
        assert result == "你好"
    
    def test_cache_miss(self):
        """测试缓存未命中"""
        cache = TranslationCache()
        result = cache.get("NotExist")
        assert result is None
    
    def test_cache_persistence(self):
        """测试缓存持久化"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False, encoding='utf-8') as f:
            tmp_path = f.name
        
        try:
            # 写入缓存
            cache1 = TranslationCache(cache_file=tmp_path)
            cache1.put("Hello", "你好")
            cache1.put("World", "世界")
            cache1.save()
            
            # 重新加载
            cache2 = TranslationCache(cache_file=tmp_path)
            assert cache2.get("Hello") == "你好"
            assert cache2.get("World") == "世界"
        finally:
            Path(tmp_path).unlink(missing_ok=True)


class TestSqliteCache:
    """测试 SQLite 缓存"""
    
    @pytest.fixture
    def temp_db(self):
        """创建临时数据库"""
        with tempfile.NamedTemporaryFile(suffix='.sqlite', delete=False) as f:
            db_path = f.name
        yield db_path
        # 清理
        close_all_connections()
        try:
            Path(db_path).unlink(missing_ok=True)
        except PermissionError:
            pass  # Windows 可能还在使用文件
    
    def test_kv_set_get(self, temp_db):
        """测试基本设置获取"""
        kv_set("key1", "value1", temp_db)
        result = kv_get("key1", temp_db)
        assert result == "value1"
    
    def test_kv_set_batch(self, temp_db):
        """测试批量设置"""
        items = [("k1", "v1"), ("k2", "v2"), ("k3", "v3")]
        success, fail = kv_set_batch(items, temp_db)
        assert success == 3
        assert fail == 0
        
        # 验证
        assert kv_get("k1", temp_db) == "v1"
        assert kv_get("k2", temp_db) == "v2"
        assert kv_get("k3", temp_db) == "v3"
    
    def test_kv_get_batch(self, temp_db):
        """测试批量获取"""
        kv_set("a", "1", temp_db)
        kv_set("b", "2", temp_db)
        
        result = kv_get_batch(["a", "b", "c"], temp_db)
        assert result["a"] == "1"
        assert result["b"] == "2"
        assert result["c"] is None
    
    def test_kv_delete(self, temp_db):
        """测试删除"""
        kv_set("key", "value", temp_db)
        kv_delete("key", temp_db)
        assert kv_get("key", temp_db) is None
    
    def test_kv_count(self, temp_db):
        """测试计数"""
        kv_set("k1", "v1", temp_db)
        kv_set("k2", "v2", temp_db)
        assert kv_count(temp_db) == 2


class TestTranslationMemory:
    """测试翻译记忆"""
    
    def test_add_and_get_exact(self):
        """测试添加和精确查询"""
        tm = TranslationMemory()
        tm.add("Hello", "你好")
        
        match = tm.get_exact("Hello")
        assert match is not None
        assert match.target == "你好"
        assert match.score == 100.0
    
    def test_fuzzy_match(self):
        """测试模糊匹配"""
        tm = TranslationMemory()
        tm.add("Hello world", "你好世界")
        
        matches = tm.get_fuzzy("Hello word", threshold=70)  # typo: word vs world
        # 可能匹配（如果安装了 rapidfuzz）
        if matches:
            assert matches[0].score >= 70
    
    def test_query_prefers_exact(self):
        """测试查询优先精确匹配"""
        tm = TranslationMemory()
        tm.add("Hello", "你好")
        tm.add("Hello world", "你好世界")
        
        matches = tm.query("Hello")
        assert len(matches) > 0
        assert matches[0].match_type == "exact"
    
    def test_load_save_jsonl(self):
        """测试 JSONL 加载保存"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False, encoding='utf-8') as f:
            f.write('{"en": "Hello", "zh": "你好"}\n')
            f.write('{"en": "World", "zh": "世界"}\n')
            tmp_path = f.name
        
        try:
            tm = TranslationMemory()
            count = tm.load_jsonl(tmp_path)
            assert count == 2
            
            # 保存到新文件
            out_path = tmp_path + ".out"
            tm.save_jsonl(out_path)
            
            # 验证保存的文件
            tm2 = TranslationMemory()
            count2 = tm2.load_jsonl(out_path)
            assert count2 == 2
            
            Path(out_path).unlink(missing_ok=True)
        finally:
            Path(tmp_path).unlink(missing_ok=True)


class TestEnhancedValidator:
    """测试增强的 Validator"""
    
    def setup_method(self):
        """每个测试方法前执行"""
        self.validator = MultiLevelValidator()
    
    def test_tag_mismatch_detected(self):
        """测试标签不匹配检测"""
        source = [{'id': 'test_1', 'en': '{i}Hello{/i}'}]
        target = [{'id': 'test_1', 'zh': '{i}你好'}]  # 缺少闭标签
        
        fixed, issues = self.validator.validate_with_autofix(source, target)
        
        # 应该检测到标签不匹配
        assert any(i['type'] == 'tag_mismatch' for i in issues['critical'])
    
    def test_tag_autofix(self):
        """测试标签自动修复"""
        source = [{'id': 'test_1', 'en': '{i}Hello{/i}'}]
        target = [{'id': 'test_1', 'zh': '{i}你好'}]  # 缺少闭标签
        
        fixed, issues = self.validator.validate_with_autofix(source, target)
        
        # 应该自动添加闭标签
        assert '{/i}' in fixed[0]['zh']
    
    def test_english_leakage_detected(self):
        """测试英文泄露检测"""
        source = [{'id': 'test_1', 'en': 'Hello, how are you today?'}]
        target = [{'id': 'test_1', 'zh': 'Hello, how are you today?'}]  # 未翻译
        
        fixed, issues = self.validator.validate_with_autofix(source, target)
        
        # 应该检测到英文泄露
        assert any(i['type'] == 'english_leakage' for i in issues['warning'])
    
    def test_number_mismatch_detected(self):
        """测试数字不匹配检测"""
        source = [{'id': 'test_1', 'en': 'You have 100 gold coins.'}]
        target = [{'id': 'test_1', 'zh': '你有50个金币。'}]  # 数字变了
        
        fixed, issues = self.validator.validate_with_autofix(source, target)
        
        # 应该检测到数字不匹配
        assert any(i['type'] == 'number_mismatch' for i in issues['warning'])
    
    def test_term_consistency(self):
        """测试术语一致性检查"""
        # 创建新的 validator 配置，包含 term_consistency
        config = MultiLevelValidator.DEFAULT_CHECKS.copy()
        config['term_consistency'] = {'level': 'info', 'autofix': False}
        
        validator = MultiLevelValidator(config=config)
        validator.set_term_dict({'Player': '玩家'})
        
        source = [{'id': 'test_1', 'en': 'The Player wins!'}]
        target = [{'id': 'test_1', 'en': 'The Player wins!', 'zh': '那个人赢了！'}]  # 应该用"玩家"
        
        fixed, issues = validator.validate_with_autofix(source, target)
        
        # 应该检测到术语不一致
        assert any(i['type'] == 'term_inconsistent' for i in issues['info'])


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
