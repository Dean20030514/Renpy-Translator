#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_dict.py — 自动生成游戏术语字典

功能:
1. 从已翻译的 JSONL 中提取高频词汇
2. 识别游戏特定术语（角色名、地点名、道具名等）
3. 生成 CSV 格式的术语字典
4. 支持合并现有字典和新生成的内容

用法示例:
  # 从提取的文件生成字典
  python tools/generate_dict.py outputs/extract/project_en.jsonl -o outputs/dictionaries

  # 指定游戏名称（用于分组）
  python tools/generate_dict.py outputs/extract/project_en.jsonl -o outputs/dictionaries --game-name "MyGame"

  # 从已翻译的文件生成（更准确）
  python tools/generate_dict.py outputs/prefilled/translated.jsonl -o outputs/dictionaries --from-translated

  # 合并现有字典
  python tools/generate_dict.py outputs/extract/project_en.jsonl -o outputs/dictionaries --merge data/dictionaries/common_terms.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


# ========================================
# 术语识别规则
# ========================================

class TermExtractor:
    """术语提取器"""
    
    # 常见的角色名称模式
    NAME_PATTERNS = [
        r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\b',  # John, Mary Smith
        r'\b[A-Z]{2,}\b',  # MC, NPC
    ]
    
    # 需要跳过的常见词
    SKIP_WORDS = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
        'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
        'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this',
        'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
        'my', 'your', 'his', 'her', 'its', 'our', 'their', 'me', 'him', 'us',
        'them', 'what', 'which', 'who', 'when', 'where', 'why', 'how',
        'all', 'each', 'every', 'both', 'few', 'more', 'most', 'other',
        'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so',
        'than', 'too', 'very', 'just', 'now', 'then',
        # Ren'Py 常见关键词
        'scene', 'show', 'hide', 'menu', 'jump', 'call', 'return',
        'elif', 'while', 'pass', 'break', 'continue',
        'True', 'False', 'None',
    }
    
    # 游戏特定术语类型
    TERM_TYPES = {
        'character': r'\b(?:mom|dad|sister|brother|son|daughter|wife|husband|girlfriend|boyfriend|friend|teacher|student|boss|neighbor|landlord|landlady|roommate)\b',
        'location': r'\b(?:room|bedroom|bathroom|kitchen|living room|office|school|classroom|gym|pool|beach|park|store|shop|restaurant|bar|club|hospital|hotel)\b',
        'item': r'\b(?:key|phone|wallet|bag|book|note|letter|photo|picture|gift|drink|food|clothes|dress|shirt|pants|shoes|hat|glasses|ring|necklace|bracelet)\b',
        'action': r'\b(?:love|lust|corruption|submission|dominance|affection|relationship|quest|event|scene|route|ending)\b',
        'stat': r'\b(?:level|points|stats|money|cash|gold|energy|stamina|health|mana|experience|exp)\b',
    }
    
    def __init__(self, min_freq: int = 3, min_length: int = 3):
        """
        初始化术语提取器
        
        Args:
            min_freq: 最小出现频率
            min_length: 最小词长
        """
        self.min_freq = min_freq
        self.min_length = min_length
        self.term_counter: Counter[str] = Counter()
        self.term_types: dict[str, set[str]] = defaultdict(set)
    
    def extract_from_text(self, text: str):
        """从文本中提取术语"""
        if not text:
            return
        
        # 移除 Ren'Py 标签
        clean = re.sub(r'\{[/a-z_]+\}', '', text, flags=re.IGNORECASE)
        clean = re.sub(r'\[[a-z_]+\]', '', clean, flags=re.IGNORECASE)
        
        # 提取单词
        words = re.findall(r'\b[A-Za-z]+(?:[A-Za-z\-\']*[A-Za-z]+)?\b', clean)
        
        for word in words:
            word_lower = word.lower()
            
            # 跳过常见词和短词
            if word_lower in self.SKIP_WORDS or len(word) < self.min_length:
                continue
            
            # 统计词频
            self.term_counter[word] += 1
            
            # 识别术语类型
            for term_type, pattern in self.TERM_TYPES.items():
                if re.search(pattern, word_lower):
                    self.term_types[term_type].add(word)
    
    def extract_names(self, text: str):
        """提取可能的角色名称"""
        names: set[str] = set()
        
        for pattern in self.NAME_PATTERNS:
            matches = re.findall(pattern, text)
            for match in matches:
                if match.lower() not in self.SKIP_WORDS and len(match) >= 2:
                    names.add(match)
                    self.term_counter[match] += 1
                    self.term_types['character'].add(match)
        
        return names
    
    def get_high_freq_terms(self) -> list[tuple[str, int]]:
        """获取高频术语"""
        return [
            (term, count)
            for term, count in self.term_counter.most_common()
            if count >= self.min_freq
        ]
    
    def get_terms_by_type(self, term_type: str) -> list[str]:
        """获取特定类型的术语"""
        return sorted(self.term_types.get(term_type, set()))


# ========================================
# 字典生成
# ========================================

class DictionaryGenerator:
    """字典生成器"""
    
    def __init__(
        self,
        game_name: str = "game",
        min_freq: int = 3,
        min_length: int = 3
    ):
        """
        初始化字典生成器
        
        Args:
            game_name: 游戏名称（用于分组）
            min_freq: 最小词频
            min_length: 最小词长
        """
        self.game_name = game_name
        self.extractor = TermExtractor(min_freq, min_length)
        self.existing_dict: dict[str, dict[str, str]] = {}
    
    def load_existing_dict(self, dict_path: Path):
        """加载现有字典"""
        if not dict_path.exists():
            return
        
        print(f"  加载现有字典: {dict_path}")
        
        with dict_path.open('r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                en = row.get('variant_en', '') or row.get('canonical_en', '')
                if en:
                    self.existing_dict[en.lower()] = row
        
        print(f"  已加载 {len(self.existing_dict)} 条术语")
    
    def process_jsonl(self, jsonl_path: Path, _has_translation: bool = False):
        """
        处理 JSONL 文件
        
        Args:
            jsonl_path: JSONL 文件路径
            _has_translation: 是否包含翻译（zh 字段），预留参数
        """
        print(f"  分析文件: {jsonl_path}")
        
        count = 0
        with jsonl_path.open('r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                
                try:
                    obj = json.loads(line)
                    text = obj.get('en', '')
                    
                    if text:
                        self.extractor.extract_from_text(text)
                        self.extractor.extract_names(text)
                        count += 1
                
                except (ValueError, json.JSONDecodeError):
                    continue
        
        print(f"  已分析 {count} 条文本")
    
    def generate_dict_entries(self) -> list[dict[str, str]]:
        """生成字典条目"""
        entries: list[dict[str, str]] = []
        high_freq = self.extractor.get_high_freq_terms()
        
        print(f"\n  找到 {len(high_freq)} 个高频术语")
        
        # 按类型组织术语
        for term, count in high_freq:
            term_lower = term.lower()
            
            # 跳过已存在的术语
            if term_lower in self.existing_dict:
                continue
            
            # 判断术语类型
            term_type = self._classify_term(term)
            canonical = self._get_canonical_form(term)
            
            entry = {
                'group': f"{self.game_name}_{term_type}",
                'canonical_en': canonical,
                'variant_en': term,
                'zh_final': '',  # 留空，待人工填写
                'source': 'auto_generated',
                'freq': str(count),
                'type': term_type,
            }
            
            entries.append(entry)
        
        # 按频率排序
        entries.sort(key=lambda x: int(x.get('freq', 0)), reverse=True)
        
        return entries
    
    def _classify_term(self, term: str) -> str:
        """分类术语"""
        term_lower = term.lower()
        
        for term_type, pattern in self.extractor.TERM_TYPES.items():
            if re.search(pattern, term_lower):
                return term_type
        
        # 默认类型
        if term[0].isupper():
            return 'character'  # 首字母大写可能是人名
        
        return 'general'
    
    def _get_canonical_form(self, term: str) -> str:
        """获取规范形式"""
        # 简单处理：使用小写作为规范形式
        return term.lower()
    
    def save_dict(self, output_path: Path, entries: list[dict[str, str]]):
        """保存字典"""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # CSV 字段
        fieldnames = ['group', 'canonical_en', 'variant_en', 'zh_final', 'source', 'freq', 'type']
        
        with output_path.open('w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(entries)
        
        print(f"\n  ✓ 字典已保存: {output_path}")
        print(f"  共 {len(entries)} 条新术语")
    
    def save_summary(self, output_path: Path, entries: list[dict[str, str]]):
        """保存摘要（按类型分组）"""
        summary_path = output_path.parent / (output_path.stem + '_summary.txt')
        
        # 按类型分组
        by_type: dict[str, list[dict[str, str]]] = defaultdict(list)
        for entry in entries:
            by_type[entry['type']].append(entry)
        
        with summary_path.open('w', encoding='utf-8') as f:
            f.write("游戏字典生成摘要\n")
            f.write(f"游戏: {self.game_name}\n")
            f.write(f"总计: {len(entries)} 条术语\n")
            f.write(f"\n{'='*60}\n\n")
            
            for term_type in sorted(by_type.keys()):
                terms = by_type[term_type]
                f.write(f"【{term_type.upper()}】 ({len(terms)} 条)\n")
                f.write(f"{'-'*60}\n")
                
                for entry in terms[:20]:  # 每类最多显示20个
                    freq = entry.get('freq', '0')
                    f.write(f"  {entry['variant_en']:20s}  (频率: {freq:>3s})\n")
                
                if len(terms) > 20:
                    f.write(f"  ... 还有 {len(terms) - 20} 个术语\n")
                
                f.write("\n")
        
        print(f"  摘要已保存: {summary_path}")


# ========================================
# 主函数
# ========================================

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="自动生成游戏术语字典",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 基本用法
  python tools/generate_dict.py outputs/extract/project_en.jsonl -o outputs/dictionaries

  # 指定游戏名称
  python tools/generate_dict.py outputs/extract/project_en.jsonl -o outputs/dictionaries --game-name "MyGame"

  # 从已翻译的文件生成（更准确）
  python tools/generate_dict.py outputs/prefilled/translated.jsonl -o outputs/dictionaries --from-translated

  # 合并现有字典
  python tools/generate_dict.py outputs/extract/project_en.jsonl -o outputs/dictionaries \\
    --merge data/dictionaries/common_terms.csv

注意:
  - 生成的字典中 zh_final 字段为空，需要人工填写翻译
  - 自动生成的术语按频率排序，频率越高越重要
  - 建议结合游戏内容和上下文手动审核和完善字典
        """
    )
    
    parser.add_argument(
        "input",
        help="输入 JSONL 文件（包含 en 字段）"
    )
    parser.add_argument(
        "-o", "--output",
        required=True,
        help="输出目录"
    )
    parser.add_argument(
        "--game-name",
        default="game",
        help="游戏名称（用于分组，默认 'game'）"
    )
    parser.add_argument(
        "--min-freq",
        type=int,
        default=3,
        help="最小词频（默认 3）"
    )
    parser.add_argument(
        "--min-length",
        type=int,
        default=3,
        help="最小词长（默认 3）"
    )
    parser.add_argument(
        "--from-translated",
        action="store_true",
        help="输入文件包含翻译（zh 字段）"
    )
    parser.add_argument(
        "--merge",
        help="合并现有字典文件（CSV 格式）"
    )
    
    args = parser.parse_args()
    
    # 路径
    input_path = Path(args.input)
    output_dir = Path(args.output)
    
    if not input_path.exists():
        print(f"❌ 输入文件不存在: {input_path}")
        return 1
    
    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("🔍 自动生成游戏字典")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
    
    print(f"游戏名称: {args.game_name}")
    print(f"最小词频: {args.min_freq}")
    print(f"最小词长: {args.min_length}\n")
    
    # 创建生成器
    generator = DictionaryGenerator(
        game_name=args.game_name,
        min_freq=args.min_freq,
        min_length=args.min_length
    )
    
    # 加载现有字典
    if args.merge:
        merge_path = Path(args.merge)
        if merge_path.exists():
            generator.load_existing_dict(merge_path)
        else:
            print(f"  ⚠ 合并字典不存在: {merge_path}")
    
    # 处理输入文件
    generator.process_jsonl(input_path, args.from_translated)
    
    # 生成字典条目
    entries = generator.generate_dict_entries()
    
    if not entries:
        print("\n  ⚠ 未找到新的高频术语")
        print("  建议:")
        print("    1. 降低 --min-freq 参数")
        print("    2. 检查输入文件是否包含有效的英文文本")
        return 0
    
    # 保存字典
    output_file = output_dir / f"{args.game_name}_dict.csv"
    generator.save_dict(output_file, entries)
    
    # 保存摘要
    generator.save_summary(output_file, entries)
    
    print(f"\n{'='*60}")
    print("✓ 字典生成完成!")
    print(f"{'='*60}\n")
    print("下一步:")
    print(f"  1. 编辑 {output_file.name}")
    print("  2. 填写 zh_final 列的中文翻译")
    print("  3. 将字典用于 prefill 步骤")
    print()
    
    return 0


if __name__ == "__main__":
    exit(main())
