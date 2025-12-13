#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
translate_api.py — 使用云端 API 快速翻译（DeepSeek/Grok/OpenAI/Claude）

速度对比:
  本地 Ollama: ~10 条/分钟
  云端 API: ~100-200 条/分钟 (10-20倍速度)

成本对比（每百万Token）:
  DeepSeek: ￥1 (最便宜)
  Claude Haiku: ￥3.5
  OpenAI GPT-3.5: ￥7
  Claude Sonnet: ￥21
  Grok: ￥35
  OpenAI GPT-4: ￥70

用法示例:
  # DeepSeek API (推荐，最快最便宜)
  python tools/translate_api.py outputs/llm_batches -o outputs/llm_results \
    --provider deepseek --api-key YOUR_API_KEY --workers 20

  # Grok API (xAI，质量好但贵)
  python tools/translate_api.py outputs/llm_batches -o outputs/llm_results \
    --provider grok --api-key YOUR_XAI_API_KEY --workers 15

  # OpenAI GPT-4 (质量最好但最贵)
  python tools/translate_api.py outputs/llm_batches -o outputs/llm_results \
    --provider openai-gpt4 --api-key YOUR_API_KEY --workers 10

  # Claude Sonnet (质量和价格平衡)
  python tools/translate_api.py outputs/llm_batches -o outputs/llm_results \
    --provider claude-sonnet --api-key YOUR_API_KEY --workers 10
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from urllib import request as urlreq
from urllib import error as urlerr

try:
    from rich.console import Console
    from rich.progress import Progress, BarColumn, TimeElapsedColumn, TextColumn, TaskProgressColumn
    _console = Console()
except ImportError:
    _console = None


# API 配置
API_CONFIGS = {
    'deepseek': {
        'name': 'DeepSeek',
        'endpoint': 'https://api.deepseek.com/v1/chat/completions',
        'model': 'deepseek-chat',
        'cost_per_1m_tokens': 1.0,  # ￥1/百万Token
    },
    'grok': {
        'name': 'Grok (xAI)',
        'endpoint': 'https://api.x.ai/v1/chat/completions',
        'model': 'grok-beta',
        'cost_per_1m_tokens': 35.0,  # $5/百万Token ≈ ￥35
    },
    'openai': {
        'name': 'OpenAI',
        'endpoint': 'https://api.openai.com/v1/chat/completions',
        'model': 'gpt-3.5-turbo',
        'cost_per_1m_tokens': 7.0,  # $1/百万Token ≈ ￥7
    },
    'openai-gpt4': {
        'name': 'OpenAI GPT-4',
        'endpoint': 'https://api.openai.com/v1/chat/completions',
        'model': 'gpt-4-turbo',
        'cost_per_1m_tokens': 70.0,  # $10/百万Token ≈ ￥70
    },
    'claude': {
        'name': 'Claude',
        'endpoint': 'https://api.anthropic.com/v1/messages',
        'model': 'claude-3-haiku-20240307',
        'cost_per_1m_tokens': 3.5,  # $0.5/百万Token ≈ ￥3.5
    },
    'claude-sonnet': {
        'name': 'Claude Sonnet',
        'endpoint': 'https://api.anthropic.com/v1/messages',
        'model': 'claude-3-5-sonnet-20241022',
        'cost_per_1m_tokens': 21.0,  # $3/百万Token ≈ ￥21
    },
}


@dataclass
class APIConfig:
    """API 配置"""
    provider: str
    api_key: str
    endpoint: str
    model: str
    workers: int = 20
    timeout: float = 30.0
    temperature: float = 0.2
    max_retries: int = 3


def build_system_prompt() -> str:
    """构建系统提示词（与本地版本相同但更严格）"""
    return (
        "你是资深成人游戏本地化译员，将英文台词翻译为简体中文。\n\n"
        
        "【核心要求】\n"
        "⚠️ 严禁输出任何英文单词（变量名除外如[name]）\n"
        "⚠️ 必须将每个英文词汇完整翻译为中文\n"
        "⚠️ 禁止中英文混合输出\n\n"
        
        "【翻译风格】\n"
        "- 成人游戏风格：直白露骨（鸡巴、奶子、小穴、屁股、骚货、操、干、插）\n"
        "- 自然口语化，避免生硬直译\n"
        "- 保持换行符数量一致\n\n"
        
        "【错误示例】禁止以下错误\n"
        "❌ '你 also 也喜欢' → ✅ '你也喜欢'\n"
        "❌ '享受你的 pleasure' → ✅ '享受你的快感'\n"
        "❌ '一个dirty的秘密' → ✅ '一个肮脏的秘密'\n\n"
        
        "【输出】只输出纯中文译文，不要任何解释"
    )


def call_api(
    text: str,
    config: APIConfig,
    context: dict = None
) -> Optional[str]:
    """
    调用云端 API 翻译
    
    Args:
        text: 要翻译的文本
        config: API 配置
        context: 上下文信息
    
    Returns:
        翻译结果，失败返回 None
    """
    system_prompt = build_system_prompt()
    user_prompt = f"翻译以下英文为简体中文：\n\n{text}"
    
    # DeepSeek/OpenAI/Grok 格式（OpenAI 兼容）
    if config.provider in ['deepseek', 'openai', 'openai-gpt4', 'grok']:
        payload = {
            "model": config.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": config.temperature,
            "max_tokens": 2000,
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.api_key}"
        }
    
    # Claude 格式
    elif config.provider in ['claude', 'claude-sonnet']:
        payload = {
            "model": config.model,
            "max_tokens": 2000,
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": user_prompt}
            ],
            "temperature": config.temperature,
        }
        
        headers = {
            "Content-Type": "application/json",
            "x-api-key": config.api_key,
            "anthropic-version": "2023-06-01"
        }
    
    else:
        return None
    
    # 重试逻辑
    for attempt in range(config.max_retries):
        try:
            data = json.dumps(payload).encode('utf-8')
            req = urlreq.Request(config.endpoint, data=data, headers=headers)
            
            with urlreq.urlopen(req, timeout=config.timeout) as resp:
                result = json.loads(resp.read().decode('utf-8'))
                
                # 提取翻译结果
                if config.provider in ['deepseek', 'openai', 'openai-gpt4', 'grok']:
                    translation = result['choices'][0]['message']['content']
                elif config.provider in ['claude', 'claude-sonnet']:
                    translation = result['content'][0]['text']
                else:
                    return None
                
                return translation.strip()
        
        except urlerr.HTTPError as e:
            if e.code == 429:  # Rate limit
                wait_time = min(2 ** attempt, 10)
                time.sleep(wait_time)
            elif e.code >= 500:  # Server error
                time.sleep(1)
            else:
                return None
        
        except (urlerr.URLError, TimeoutError):
            if attempt < config.max_retries - 1:
                time.sleep(1)
    
    return None


def translate_item(
    item: dict,
    config: APIConfig
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
    
    # 调用 API 翻译
    translation = call_api(original, config, item)
    
    if translation:
        return item_id, translation, None
    else:
        return item_id, None, 'api_error'


def process_file(
    input_file: Path,
    output_file: Path,
    rejects_file: Path,
    config: APIConfig
):
    """处理单个文件"""
    # 加载数据
    items: list[dict] = []
    with input_file.open('r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                try:
                    items.append(json.loads(line))
                except (ValueError, json.JSONDecodeError):
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
        description="使用云端 API 快速翻译（比本地快 10-20 倍）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # DeepSeek API (推荐，最快最便宜 ￥1/百万Token)
  python tools/translate_api.py outputs/llm_batches -o outputs/llm_results \\
    --provider deepseek --api-key YOUR_API_KEY --workers 20

  # OpenAI API
  python tools/translate_api.py outputs/llm_batches -o outputs/llm_results \\
    --provider openai --api-key YOUR_API_KEY --workers 10

  # Claude API
  python tools/translate_api.py outputs/llm_batches -o outputs/llm_results \\
    --provider claude --api-key YOUR_API_KEY --workers 10

获取 API Key:
  DeepSeek: https://platform.deepseek.com/
  OpenAI: https://platform.openai.com/
  Claude: https://console.anthropic.com/

成本估算:
  DeepSeek: ￥1/百万Token → 整个游戏约 ￥5-20
  OpenAI: ￥7/百万Token → 整个游戏约 ￥35-140
  Claude: ￥3.5/百万Token → 整个游戏约 ￥17-70
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
        choices=['deepseek', 'grok', 'openai', 'openai-gpt4', 'claude', 'claude-sonnet'],
        required=True,
        help="API 提供商"
    )
    parser.add_argument(
        "--api-key",
        help="API Key（或设置环境变量 API_KEY）"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=20,
        help="并发数（默认 20，DeepSeek 可以更高）"
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="超时时间（秒，默认 30）"
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.2,
        help="采样温度（默认 0.2）"
    )
    
    args = parser.parse_args()
    
    # 获取 API Key
    api_key = args.api_key or os.environ.get('API_KEY')
    if not api_key:
        print("❌ 错误: 需要提供 API Key")
        print("   使用 --api-key 参数或设置环境变量 API_KEY")
        return 1
    
    # 创建配置
    api_info = API_CONFIGS[args.provider]
    config = APIConfig(
        provider=args.provider,
        api_key=api_key,
        endpoint=api_info['endpoint'],
        model=api_info['model'],
        workers=args.workers,
        timeout=args.timeout,
        temperature=args.temperature,
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
    if _console:
        _console.print("\n[bold cyan]═══════════════════════════════════════[/]")
        _console.print(f"[bold]API 提供商:[/] [yellow]{api_info['name']}[/]")
        _console.print(f"[bold]模型:[/] [yellow]{config.model}[/]")
        _console.print(f"[bold]并发数:[/] [yellow]{config.workers}[/]")
        _console.print(f"[bold]预估成本:[/] [yellow]约 ￥{api_info['cost_per_1m_tokens'] * 10:.1f}-{api_info['cost_per_1m_tokens'] * 40:.1f} (10万条)[/]")
        _console.print("[bold cyan]═══════════════════════════════════════[/]\n")
    else:
        print(f"\nAPI: {api_info['name']}")
        print(f"模型: {config.model}")
        print(f"并发数: {config.workers}\n")
    
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
