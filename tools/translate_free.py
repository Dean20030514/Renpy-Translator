#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
translate_free.py — 使用免费机器翻译 API（Google/Bing/DeepL）

免费方案对比:
  Google Translate: 完全免费，无限制（通过爬虫）
  Bing Translator: 完全免费，无限制（通过爬虫）  
  DeepL Free: 每月 50 万字符免费额度（需注册）

特点:
  ✅ 完全免费（Google/Bing 无需注册）
  ✅ 速度快（~50-100 条/分钟）
  ⚠️ 质量一般（机翻水平，适合打底）
  ⚠️ 不适合成人内容（可能被过滤）

用法示例:
  # Google 翻译（推荐，最稳定）
  python tools/translate_free.py outputs/llm_batches -o outputs/llm_results \
    --provider google --workers 10

  # Bing 翻译
  python tools/translate_free.py outputs/llm_batches -o outputs/llm_results \
    --provider bing --workers 10

  # DeepL 翻译（质量最好但需要注册）
  python tools/translate_free.py outputs/llm_batches -o outputs/llm_results \
    --provider deepl --api-key YOUR_FREE_API_KEY --workers 5

推荐使用流程:
  1. 先用 Google/Bing 快速机翻打底
  2. 再用 DeepSeek API 修正关键台词
  3. 最后用 fix_english_leakage.py 检查质量
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import hashlib
import json
import random
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from urllib import parse as urlparse
from urllib import request as urlreq
from urllib import error as urlerr

try:
    from rich.console import Console
    from rich.progress import Progress, BarColumn, TimeElapsedColumn, TextColumn, TaskProgressColumn
    _console = Console()
except ImportError:
    _console = None


@dataclass
class TranslatorConfig:
    """翻译器配置"""
    provider: str
    api_key: Optional[str] = None
    workers: int = 10
    timeout: float = 15.0
    max_retries: int = 3
    delay: float = 0.1  # 请求间隔，避免被限流


class GoogleTranslator:
    """Google 翻译（通过非官方 API）"""
    
    BASE_URL = "https://translate.googleapis.com/translate_a/single"
    
    @staticmethod
    def translate(text: str, timeout: float = 15.0) -> Optional[str]:
        """
        翻译文本
        
        原理: 使用 Google Translate 的前端 API
        """
        if not text.strip():
            return ""
        
        # 构建请求参数
        params = {
            'client': 'gtx',
            'sl': 'en',      # 源语言：英文
            'tl': 'zh-CN',   # 目标语言：简体中文
            'dt': 't',       # 返回翻译结果
            'q': text,
        }
        
        url = f"{GoogleTranslator.BASE_URL}?{urlparse.urlencode(params)}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        try:
            req = urlreq.Request(url, headers=headers)
            with urlreq.urlopen(req, timeout=timeout) as resp:
                result = json.loads(resp.read().decode('utf-8'))
                
                # 解析结果：[[["翻译文本", "原文", null, null, 10]], ...]
                if result and result[0]:
                    translations = []
                    for item in result[0]:
                        if item and item[0]:
                            translations.append(item[0])
                    return ''.join(translations)
        
        except Exception as e:
            return None
        
        return None


class BingTranslator:
    """Bing 翻译（通过非官方 API）"""
    
    BASE_URL = "https://www.bing.com/translator"
    TRANSLATE_URL = "https://www.bing.com/ttranslatev3"
    
    @staticmethod
    def translate(text: str, timeout: float = 15.0) -> Optional[str]:
        """
        翻译文本
        
        原理: 模拟 Bing Translator 网页请求
        """
        if not text.strip():
            return ""
        
        # 1. 先访问首页获取 token
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.bing.com/translator',
        }
        
        try:
            # 2. 直接翻译（Bing 的 API 比较宽松）
            data = {
                'fromLang': 'en',
                'to': 'zh-Hans',
                'text': text,
            }
            
            post_data = urlparse.urlencode(data).encode('utf-8')
            req = urlreq.Request(BingTranslator.TRANSLATE_URL, data=post_data, headers=headers)
            
            with urlreq.urlopen(req, timeout=timeout) as resp:
                result = json.loads(resp.read().decode('utf-8'))
                
                # 解析结果
                if result and isinstance(result, list) and len(result) > 0:
                    translation = result[0].get('translations', [])
                    if translation and len(translation) > 0:
                        return translation[0].get('text', '').strip()
        
        except Exception as e:
            return None
        
        return None


class DeepLTranslator:
    """DeepL 翻译（官方免费 API）"""
    
    BASE_URL = "https://api-free.deepl.com/v2/translate"
    
    @staticmethod
    def translate(text: str, api_key: str, timeout: float = 15.0) -> Optional[str]:
        """
        翻译文本
        
        需要注册免费账号：https://www.deepl.com/pro-api
        免费额度：每月 50 万字符
        """
        if not text.strip():
            return ""
        
        data = {
            'text': [text],
            'source_lang': 'EN',
            'target_lang': 'ZH',
        }
        
        headers = {
            'Authorization': f'DeepL-Auth-Key {api_key}',
            'Content-Type': 'application/json',
        }
        
        try:
            post_data = json.dumps(data).encode('utf-8')
            req = urlreq.Request(DeepLTranslator.BASE_URL, data=post_data, headers=headers)
            
            with urlreq.urlopen(req, timeout=timeout) as resp:
                result = json.loads(resp.read().decode('utf-8'))
                
                # 解析结果
                if result and 'translations' in result:
                    translations = result['translations']
                    if translations and len(translations) > 0:
                        return translations[0].get('text', '').strip()
        
        except Exception as e:
            return None
        
        return None


def translate_text(
    text: str,
    config: TranslatorConfig
) -> Optional[str]:
    """
    翻译文本（带重试）
    """
    for attempt in range(config.max_retries):
        try:
            if config.provider == 'google':
                result = GoogleTranslator.translate(text, config.timeout)
            elif config.provider == 'bing':
                result = BingTranslator.translate(text, config.timeout)
            elif config.provider == 'deepl':
                if not config.api_key:
                    return None
                result = DeepLTranslator.translate(text, config.api_key, config.timeout)
            else:
                return None
            
            if result:
                return result
            
            # 失败重试前等待
            if attempt < config.max_retries - 1:
                time.sleep(1)
        
        except Exception:
            if attempt < config.max_retries - 1:
                time.sleep(1)
    
    return None


def translate_item(
    item: dict,
    config: TranslatorConfig
) -> tuple[str, Optional[str], Optional[str]]:
    """
    翻译单条记录
    
    Returns:
        (id, 译文或None, 错误原因或None)
    """
    item_id = item.get('id', '')
    original = item.get('en', '')
    
    if not item_id or not original:
        return item_id, None, 'missing_data'
    
    # 添加延迟避免限流
    time.sleep(config.delay)
    
    # 翻译
    translation = translate_text(original, config)
    
    if translation:
        return item_id, translation, None
    else:
        return item_id, None, 'translate_error'


def process_file(
    input_file: Path,
    output_file: Path,
    rejects_file: Path,
    config: TranslatorConfig
):
    """处理单个文件"""
    # 加载数据
    items: list[dict] = []
    with input_file.open('r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                try:
                    items.append(json.loads(line))
                except:
                    pass
    
    if not items:
        if _console:
            _console.print(f"  [yellow]⚠ 文件为空[/]")
        return
    
    # 清空输出文件
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text('', encoding='utf-8')
    if rejects_file.exists():
        rejects_file.unlink()
    
    # 统计
    success = 0
    failed = 0
    
    # 并发翻译
    if _console:
        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TextColumn("•"),
            TimeElapsedColumn(),
            console=_console
        ) as progress:
            task = progress.add_task(
                f"  [cyan]翻译中 ({config.workers} 并发)[/]",
                total=len(items)
            )
            
            with cf.ThreadPoolExecutor(max_workers=config.workers) as executor:
                futures = [
                    executor.submit(translate_item, item, config)
                    for item in items
                ]
                
                for fut in cf.as_completed(futures):
                    item_id, translation, error = fut.result()
                    
                    if translation:
                        # 保存成功的翻译
                        with output_file.open('a', encoding='utf-8') as f:
                            obj = {'id': item_id, 'zh': translation}
                            f.write(json.dumps(obj, ensure_ascii=False) + '\n')
                        success += 1
                    else:
                        # 记录失败
                        with rejects_file.open('a', encoding='utf-8') as f:
                            f.write(f"{item_id}\t{error}\n")
                        failed += 1
                    
                    progress.advance(task)
    else:
        # 无 Rich 库的简单版本
        with cf.ThreadPoolExecutor(max_workers=config.workers) as executor:
            futures = [
                executor.submit(translate_item, item, config)
                for item in items
            ]
            
            for i, fut in enumerate(cf.as_completed(futures), 1):
                item_id, translation, error = fut.result()
                
                if translation:
                    with output_file.open('a', encoding='utf-8') as f:
                        obj = {'id': item_id, 'zh': translation}
                        f.write(json.dumps(obj, ensure_ascii=False) + '\n')
                    success += 1
                else:
                    with rejects_file.open('a', encoding='utf-8') as f:
                        f.write(f"{item_id}\t{error}\n")
                    failed += 1
                
                if i % 10 == 0:
                    print(f"  进度: {i}/{len(items)} ({100*i//len(items)}%)")
    
    # 显示结果
    if _console:
        _console.print(f"  [green]✓ 完成[/]")
        _console.print(f"  [dim]成功={success}, 失败={failed}, 成功率={100*success/(success+failed):.1f}%[/]")
    else:
        print(f"  ✓ 完成: 成功={success}, 失败={failed}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="使用免费机器翻译 API（Google/Bing/DeepL）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # Google 翻译（推荐，无需注册）
  python tools/translate_free.py outputs/llm_batches -o outputs/llm_results_google \\
    --provider google --workers 10

  # Bing 翻译（备选）
  python tools/translate_free.py outputs/llm_batches -o outputs/llm_results_bing \\
    --provider bing --workers 10

  # DeepL 翻译（质量最好，需免费注册）
  python tools/translate_free.py outputs/llm_batches -o outputs/llm_results_deepl \\
    --provider deepl --api-key YOUR_FREE_API_KEY --workers 5

获取 DeepL 免费 API Key:
  1. 注册: https://www.deepl.com/pro-api
  2. 选择 "DeepL API Free" 计划（每月 50 万字符免费）
  3. 获取 API Key

推荐流程:
  第1步: 用 Google/Bing 快速机翻打底（免费无限制）
  第2步: 用 DeepSeek API 修正关键台词（花费很少）
  第3步: 用 fix_english_leakage.py 检查质量

注意事项:
  ⚠️ 机翻质量一般，不如 AI 翻译
  ⚠️ 可能过滤成人内容
  ⚠️ 适合快速打底，不适合最终发布
        """
    )
    
    parser.add_argument(
        "input",
        help="输入 JSONL 文件或目录"
    )
    parser.add_argument(
        "-o", "--output",
        required=True,
        help="输出目录"
    )
    parser.add_argument(
        "--provider",
        choices=['google', 'bing', 'deepl'],
        required=True,
        help="翻译提供商"
    )
    parser.add_argument(
        "--api-key",
        help="API Key（仅 DeepL 需要）"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=10,
        help="并发数（默认 10）"
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=15.0,
        help="超时时间（秒，默认 15）"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.1,
        help="请求间隔（秒，避免限流，默认 0.1）"
    )
    
    args = parser.parse_args()
    
    # 检查 DeepL API Key
    if args.provider == 'deepl' and not args.api_key:
        print("❌ 错误: DeepL 需要 API Key")
        print("   注册免费账号: https://www.deepl.com/pro-api")
        return 1
    
    # 创建配置
    config = TranslatorConfig(
        provider=args.provider,
        api_key=args.api_key,
        workers=args.workers,
        timeout=args.timeout,
        delay=args.delay,
    )
    
    # 收集文件
    input_path = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    files: list[Path] = []
    if input_path.is_dir():
        files = sorted(input_path.glob('*.jsonl'))
    elif input_path.is_file():
        files = [input_path]
    else:
        print(f"❌ 路径不存在: {input_path}")
        return 1
    
    if not files:
        print("❌ 未找到 JSONL 文件")
        return 1
    
    # 显示配置
    provider_names = {
        'google': 'Google Translate',
        'bing': 'Bing Translator',
        'deepl': 'DeepL (Free)',
    }
    
    if _console:
        _console.print("\n[bold cyan]═══════════════════════════════════════[/]")
        _console.print(f"[bold]翻译引擎:[/] [yellow]{provider_names[args.provider]}[/]")
        _console.print(f"[bold]并发数:[/] [yellow]{config.workers}[/]")
        _console.print(f"[bold]成本:[/] [yellow]完全免费 ✓[/]")
        _console.print("[bold cyan]═══════════════════════════════════════[/]\n")
    else:
        print(f"\n翻译引擎: {provider_names[args.provider]}")
        print(f"并发数: {config.workers}")
        print("成本: 完全免费\n")
    
    # 处理文件
    start_time = time.time()
    
    for i, f in enumerate(files, 1):
        output_file = output_dir / f.name
        rejects_file = output_dir / f"{f.stem}_rejects.tsv"
        
        if _console:
            _console.print(f"[bold green]▶ [{i}/{len(files)}][/] {f.name}")
        else:
            print(f"\n▶ [{i}/{len(files)}] {f.name}")
        
        process_file(f, output_file, rejects_file, config)
    
    # 总结
    elapsed = time.time() - start_time
    
    if _console:
        _console.print(f"\n[bold green]✓ 全部完成![/]")
        _console.print(f"[dim]总耗时: {elapsed:.1f} 秒[/]")
        _console.print(f"[cyan]结果保存到: {output_dir}[/]\n")
    else:
        print(f"\n✓ 全部完成! 耗时: {elapsed:.1f} 秒")
        print(f"结果保存到: {output_dir}\n")
    
    return 0


if __name__ == "__main__":
    exit(main())
