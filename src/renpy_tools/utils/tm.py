"""
翻译记忆 (Translation Memory) 模块

支持:
- 从已翻译 JSONL 构建 TM
- 精确匹配查询
- 模糊匹配查询（使用 rapidfuzz）
- TM 导入/导出
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional
from collections import defaultdict
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# 尝试导入 rapidfuzz
try:
    from rapidfuzz import fuzz, process
    _HAS_RAPIDFUZZ = True
except ImportError:
    _HAS_RAPIDFUZZ = False
    logger.warning("rapidfuzz not installed, fuzzy matching disabled")


@dataclass
class TMEntry:
    """TM 条目"""
    source: str
    target: str
    context: str = ""
    quality: float = 1.0
    count: int = 1  # 出现次数（用于投票）


@dataclass
class TMMatch:
    """TM 匹配结果"""
    source: str
    target: str
    score: float  # 匹配分数 (0-100)
    context: str = ""
    match_type: str = "exact"  # exact, fuzzy


class TranslationMemory:
    """翻译记忆库"""
    
    def __init__(self, min_length: int = 3):
        """
        初始化 TM
        
        Args:
            min_length: 最小源文本长度（过滤太短的条目）
        """
        self.min_length = min_length
        # 精确匹配索引: source -> [TMEntry, ...]
        self._exact_index: dict[str, list[TMEntry]] = defaultdict(list)
        # 所有源文本（用于模糊匹配）
        self._sources: list[str] = []
        # 源文本到条目的映射
        self._source_to_entries: dict[str, list[TMEntry]] = defaultdict(list)
        
    def add(
        self, 
        source: str, 
        target: str, 
        context: str = "",
        quality: float = 1.0
    ) -> bool:
        """
        添加条目到 TM
        
        Args:
            source: 源文本（英文）
            target: 目标文本（中文）
            context: 上下文信息
            quality: 翻译质量分数
            
        Returns:
            是否成功添加
        """
        # 跳过太短的条目
        if len(source.strip()) < self.min_length:
            return False
        
        # 标准化
        source = source.strip()
        target = target.strip()
        
        if not source or not target:
            return False
        
        # 检查是否已存在相同的翻译
        existing = self._exact_index.get(source, [])
        for entry in existing:
            if entry.target == target:
                entry.count += 1  # 增加计数
                return True
        
        # 添加新条目
        entry = TMEntry(
            source=source,
            target=target,
            context=context,
            quality=quality
        )
        self._exact_index[source].append(entry)
        
        # 更新模糊匹配索引
        if source not in self._source_to_entries:
            self._sources.append(source)
        self._source_to_entries[source].append(entry)
        
        return True
    
    def get_exact(self, source: str) -> Optional[TMMatch]:
        """
        精确匹配查询
        
        Args:
            source: 源文本
            
        Returns:
            匹配结果，如果没有则返回 None
        """
        source = source.strip()
        entries = self._exact_index.get(source)
        
        if not entries:
            return None
        
        # 选择最佳条目（按质量和出现次数）
        best = max(entries, key=lambda e: (e.quality, e.count))
        
        return TMMatch(
            source=best.source,
            target=best.target,
            score=100.0,
            context=best.context,
            match_type="exact"
        )
    
    def get_fuzzy(
        self, 
        source: str, 
        threshold: float = 80.0,
        limit: int = 3
    ) -> list[TMMatch]:
        """
        模糊匹配查询
        
        Args:
            source: 源文本
            threshold: 最小匹配分数（0-100）
            limit: 最大返回数量
            
        Returns:
            匹配结果列表（按分数降序）
        """
        if not _HAS_RAPIDFUZZ:
            logger.warning("Fuzzy matching requires rapidfuzz")
            return []
        
        if not self._sources:
            return []
        
        source = source.strip()
        
        # 使用 rapidfuzz 进行模糊匹配
        results = process.extract(
            source,
            self._sources,
            scorer=fuzz.ratio,
            limit=limit * 2  # 获取更多候选以便过滤
        )
        
        matches = []
        for matched_source, score, _ in results:
            if score < threshold:
                continue
            
            # 获取对应的翻译
            entries = self._source_to_entries.get(matched_source, [])
            if not entries:
                continue
            
            # 选择最佳翻译
            best = max(entries, key=lambda e: (e.quality, e.count))
            
            matches.append(TMMatch(
                source=best.source,
                target=best.target,
                score=score,
                context=best.context,
                match_type="fuzzy"
            ))
            
            if len(matches) >= limit:
                break
        
        return matches
    
    def query(
        self, 
        source: str,
        fuzzy_threshold: float = 80.0,
        fuzzy_limit: int = 3
    ) -> list[TMMatch]:
        """
        查询 TM（先精确后模糊）
        
        Args:
            source: 源文本
            fuzzy_threshold: 模糊匹配阈值
            fuzzy_limit: 模糊匹配最大数量
            
        Returns:
            匹配结果列表
        """
        results = []
        
        # 先尝试精确匹配
        exact = self.get_exact(source)
        if exact:
            results.append(exact)
            return results  # 精确匹配就直接返回
        
        # 否则模糊匹配
        fuzzy = self.get_fuzzy(source, fuzzy_threshold, fuzzy_limit)
        results.extend(fuzzy)
        
        return results
    
    def load_jsonl(self, path: str | Path) -> int:
        """
        从 JSONL 文件加载 TM
        
        Args:
            path: JSONL 文件路径
            
        Returns:
            加载的条目数
        """
        path = Path(path)
        if not path.exists():
            logger.warning(f"TM file not found: {path}")
            return 0
        
        count = 0
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    source = data.get('en', data.get('source', ''))
                    target = data.get('zh', data.get('target', ''))
                    context = data.get('context', data.get('speaker', ''))
                    quality = data.get('quality', 1.0)
                    
                    if source and target:
                        if self.add(source, target, context, quality):
                            count += 1
                except json.JSONDecodeError:
                    continue
        
        logger.info(f"Loaded {count} entries from {path}")
        return count
    
    def save_jsonl(self, path: str | Path) -> int:
        """
        保存 TM 到 JSONL 文件
        
        Args:
            path: 输出文件路径
            
        Returns:
            保存的条目数
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        count = 0
        with open(path, 'w', encoding='utf-8') as f:
            for source, entries in self._exact_index.items():
                for entry in entries:
                    data = {
                        'en': entry.source,
                        'zh': entry.target,
                        'context': entry.context,
                        'quality': entry.quality,
                        'count': entry.count
                    }
                    f.write(json.dumps(data, ensure_ascii=False) + '\n')
                    count += 1
        
        logger.info(f"Saved {count} entries to {path}")
        return count
    
    def __len__(self) -> int:
        """返回唯一源文本数量"""
        return len(self._sources)
    
    def stats(self) -> dict:
        """返回 TM 统计信息"""
        total_entries = sum(len(entries) for entries in self._exact_index.values())
        return {
            'unique_sources': len(self._sources),
            'total_entries': total_entries,
            'avg_translations_per_source': total_entries / len(self._sources) if self._sources else 0
        }


# 全局 TM 实例（单例模式）
_global_tm: Optional[TranslationMemory] = None


def get_global_tm() -> TranslationMemory:
    """获取全局 TM 实例"""
    global _global_tm
    if _global_tm is None:
        _global_tm = TranslationMemory()
    return _global_tm


def load_tm_from_file(path: str | Path) -> TranslationMemory:
    """
    从文件加载 TM 到全局实例
    
    Args:
        path: TM 文件路径
        
    Returns:
        全局 TM 实例
    """
    tm = get_global_tm()
    tm.load_jsonl(path)
    return tm


def query_tm(source: str, fuzzy_threshold: float = 80.0) -> Optional[str]:
    """
    查询全局 TM 获取翻译
    
    Args:
        source: 源文本
        fuzzy_threshold: 模糊匹配阈值
        
    Returns:
        翻译结果，如果没有匹配则返回 None
    """
    tm = get_global_tm()
    matches = tm.query(source, fuzzy_threshold)
    
    if matches:
        # 返回最佳匹配
        return matches[0].target
    
    return None
