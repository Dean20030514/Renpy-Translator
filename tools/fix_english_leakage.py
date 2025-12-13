#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fix_english_leakage.py — 检测并修复翻译中残留的英文单词

功能:
1. 检测译文中的英文单词（排除专有名词、变量）
2. 自动重新翻译有问题的句子
3. 生成质量报告
4. 支持批量处理

用法示例:
  # 检测并报告问题
  python tools/fix_english_leakage.py outputs/test_basement/llm_results/batch_0001.jsonl --check-only

  # 自动修复（重新翻译）
  python tools/fix_english_leakage.py outputs/test_basement/llm_results/batch_0001.jsonl --fix --model qwen3:8b

  # 批量处理目录
  python tools/fix_english_leakage.py outputs/test_basement/llm_results --fix --model qwen3:8b
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Optional
from urllib import request as urlreq

# 常见的Ren'Py变量和专有名词模式
ALLOWED_ENGLISH = {
    # Ren'Py 变量
    'pov', 'mom', 'ls', 'mc', 'npc', 'ui',
    # 常见专有名词
    'ok', 'yes', 'no', 'save', 'load', 'menu',
    # 单字母
    'a', 'i',
}

# 检测英文单词的正则（排除占位符）
ENGLISH_WORD_PATTERN = re.compile(
    r'\b[a-zA-Z]{2,}(?:\'[a-z]+)?\b'  # 至少2个字母的英文单词
)

# 占位符模式
PLACEHOLDER_PATTERN = re.compile(
    r'\[[A-Za-z_][A-Za-z0-9_]*\]'  # [name], [pov]
    r'|\{[A-Za-z_][^}]*\}'  # {i}, {color=#fff}
)


def strip_placeholders(text: str) -> str:
    """移除占位符"""
    return PLACEHOLDER_PATTERN.sub('', text)


def detect_english_words(text: str) -> list[str]:
    """
    检测译文中的英文单词
    
    Returns:
        残留的英文单词列表
    """
    # 移除占位符后检测
    clean_text = strip_placeholders(text)
    
    # 查找所有英文单词
    words = ENGLISH_WORD_PATTERN.findall(clean_text)
    
    # 过滤允许的词
    leaked = [
        word for word in words
        if word.lower() not in ALLOWED_ENGLISH
    ]
    
    return leaked


def analyze_jsonl(jsonl_path: Path) -> tuple[list[dict], int, int]:
    """
    分析 JSONL 文件
    
    Returns:
        (有问题的条目, 总数, 问题数)
    """
    problematic: list[dict] = []
    total = 0
    
    with jsonl_path.open('r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            
            total += 1
            try:
                obj = json.loads(line)
                item_id = obj.get('id', '')
                zh = obj.get('zh', '')
                
                if not zh:
                    continue
                
                # 检测英文残留
                leaked = detect_english_words(zh)
                if leaked:
                    problematic.append({
                        'id': item_id,
                        'zh': zh,
                        'leaked_words': leaked,
                    })
            
            except (ValueError, json.JSONDecodeError):
                continue
    
    return problematic, total, len(problematic)


def build_fix_prompt() -> str:
    """构建修复翻译的系统提示词"""
    return (
        "你是专业翻译质量修正员。用户会给你一段中英混合的翻译，你的任务是将其中的英文单词替换为对应的中文。\n\n"
        
        "【修正规则】\n"
        "- 保持原有的中文不变\n"
        "- 只替换英文单词为恰当的中文\n"
        "- 保持占位符（[name], {i} 等）不变\n"
        "- 保持句子结构和语气\n"
        "- 确保修正后的译文完全是中文\n\n"
        
        "【示例】\n"
        "输入: 你 also 也喜欢这个\n"
        "输出: 你也喜欢这个\n\n"
        
        "输入: 享受你的 pleasure\n"
        "输出: 享受你的快感\n\n"
        
        "输入: 一个dirty的小秘密\n"
        "输出: 一个肮脏的小秘密\n\n"
        
        "【输出要求】\n"
        "- 只输出修正后的中文译文\n"
        "- 不要输出任何解释或额外内容"
    )


def fix_translation(
    text: str,
    host: str = "http://127.0.0.1:11434",
    model: str = "qwen3:8b",
    timeout: float = 30.0
) -> Optional[str]:
    """
    使用 Ollama 修复翻译
    
    Args:
        text: 有问题的译文
        host: Ollama 地址
        model: 模型名称
        timeout: 超时时间
    
    Returns:
        修正后的译文，失败返回 None
    """
    url = host.rstrip("/") + "/api/chat"
    
    system_prompt = build_fix_prompt()
    user_prompt = f"请修正以下翻译中的英文单词，将它们替换为恰当的中文：\n\n{text}"
    
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
        "options": {"temperature": 0.1},  # 低温度，保守输出
    }
    
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urlreq.Request(url, data=data, headers={"Content-Type": "application/json"})
        
        with urlreq.urlopen(req, timeout=timeout) as resp:
            result = json.loads(resp.read().decode("utf-8", errors="ignore"))
            fixed = (result.get("message") or {}).get("content") or ""
            return fixed.strip()
    
    except Exception as e:
        print(f"  ✗ 修复失败: {e}")
        return None


def generate_report(problematic: list[dict], total: int, output_path: Path):
    """生成质量报告"""
    with output_path.open('w', encoding='utf-8') as f:
        f.write("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
        f.write("翻译质量检测报告\n")
        f.write("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n")
        
        f.write(f"总翻译数: {total}\n")
        f.write(f"问题数: {len(problematic)}\n")
        f.write(f"问题率: {100 * len(problematic) / total:.2f}%\n\n")
        
        f.write("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
        f.write("问题详情\n")
        f.write("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n")
        
        # 按残留词汇分组
        by_word: dict[str, list[dict]] = {}
        for item in problematic:
            for word in item['leaked_words']:
                word_lower = word.lower()
                if word_lower not in by_word:
                    by_word[word_lower] = []
                by_word[word_lower].append(item)
        
        # 按频率排序
        sorted_words = sorted(by_word.items(), key=lambda x: len(x[1]), reverse=True)
        
        for word, items in sorted_words:
            f.write(f"【{word}】 出现 {len(items)} 次\n")
            f.write("-" * 60 + "\n")
            
            for item in items[:5]:  # 每个词最多显示5个例子
                f.write(f"ID: {item['id']}\n")
                f.write(f"译文: {item['zh']}\n")
                f.write("\n")
            
            if len(items) > 5:
                f.write(f"... 还有 {len(items) - 5} 个相同问题\n")
            
            f.write("\n")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="检测并修复翻译中残留的英文单词",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 只检测，不修复
  python tools/fix_english_leakage.py outputs/llm_results/batch_0001.jsonl --check-only

  # 检测并自动修复
  python tools/fix_english_leakage.py outputs/llm_results/batch_0001.jsonl --fix --model qwen3:8b

  # 批量处理目录
  python tools/fix_english_leakage.py outputs/llm_results --fix --model qwen3:8b

  # 生成详细报告
  python tools/fix_english_leakage.py outputs/llm_results/batch_0001.jsonl --check-only --report quality_report.txt
        """
    )
    
    parser.add_argument(
        "input",
        help="输入 JSONL 文件或目录"
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="只检测问题，不修复"
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="自动修复（重新翻译有问题的句子）"
    )
    parser.add_argument(
        "--model",
        default="qwen3:8b",
        help="修复时使用的模型（默认 qwen3:8b）"
    )
    parser.add_argument(
        "--host",
        default="http://127.0.0.1:11434",
        help="Ollama 地址（默认 http://127.0.0.1:11434）"
    )
    parser.add_argument(
        "--report",
        help="生成详细报告到指定文件"
    )
    parser.add_argument(
        "--output-suffix",
        default="_fixed",
        help="修复后文件的后缀（默认 _fixed）"
    )
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    
    # 收集要处理的文件
    files: list[Path] = []
    if input_path.is_dir():
        files = sorted(input_path.glob("*.jsonl"))
        files = [f for f in files if not f.stem.endswith("_fixed")]
    elif input_path.is_file():
        files = [input_path]
    else:
        print(f"❌ 路径不存在: {input_path}")
        return 1
    
    if not files:
        print(f"❌ 未找到 JSONL 文件")
        return 1
    
    print(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"🔍 翻译质量检测" + (" & 修复" if args.fix else ""))
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
    
    total_files = len(files)
    total_items = 0
    total_problems = 0
    total_fixed = 0
    
    all_problematic: list[dict] = []
    
    for i, jsonl_file in enumerate(files, 1):
        print(f"[{i}/{total_files}] 检测: {jsonl_file.name}")
        
        # 分析文件
        problematic, count, problem_count = analyze_jsonl(jsonl_file)
        total_items += count
        total_problems += problem_count
        all_problematic.extend(problematic)
        
        if problem_count == 0:
            print(f"  ✓ 无问题\n")
            continue
        
        print(f"  ⚠ 发现 {problem_count}/{count} 条有问题 ({100*problem_count/count:.1f}%)")
        
        # 显示前3个问题
        for item in problematic[:3]:
            words = ', '.join(item['leaked_words'])
            print(f"    - 残留词: [{words}]")
            print(f"      译文: {item['zh'][:60]}...")
        
        if problem_count > 3:
            print(f"    ... 还有 {problem_count - 3} 个问题")
        
        # 修复模式
        if args.fix:
            print(f"\n  🔧 开始修复...")
            
            # 读取原始数据
            all_items: list[dict] = []
            with jsonl_file.open('r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        try:
                            all_items.append(json.loads(line))
                        except:
                            pass
            
            # 修复有问题的条目
            fixed_count = 0
            problem_ids = {item['id'] for item in problematic}
            
            for item in all_items:
                if item.get('id') in problem_ids:
                    old_zh = item.get('zh', '')
                    print(f"    修复: {item['id']}")
                    print(f"      旧: {old_zh[:50]}...")
                    
                    # 重新翻译
                    fixed_zh = fix_translation(old_zh, args.host, args.model)
                    
                    if fixed_zh and not detect_english_words(fixed_zh):
                        item['zh'] = fixed_zh
                        fixed_count += 1
                        print(f"      新: {fixed_zh[:50]}...")
                        print(f"      ✓ 修复成功")
                    else:
                        print(f"      ✗ 修复失败，保持原样")
            
            # 保存修复后的文件
            output_file = jsonl_file.parent / f"{jsonl_file.stem}{args.output_suffix}.jsonl"
            with output_file.open('w', encoding='utf-8') as f:
                for item in all_items:
                    f.write(json.dumps(item, ensure_ascii=False) + "\n")
            
            total_fixed += fixed_count
            print(f"\n  ✓ 已修复 {fixed_count}/{problem_count} 条")
            print(f"  保存到: {output_file.name}\n")
        else:
            print()
    
    # 总结
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"📊 汇总统计")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
    print(f"  总文件数: {total_files}")
    print(f"  总翻译数: {total_items}")
    print(f"  问题数: {total_problems} ({100*total_problems/total_items:.2f}%)")
    
    if args.fix:
        print(f"  已修复: {total_fixed}")
        print(f"  修复率: {100*total_fixed/total_problems:.1f}%")
    
    print()
    
    # 生成报告
    if args.report:
        report_path = Path(args.report)
        generate_report(all_problematic, total_items, report_path)
        print(f"✓ 详细报告已保存: {report_path}\n")
    
    return 0


if __name__ == "__main__":
    exit(main())
