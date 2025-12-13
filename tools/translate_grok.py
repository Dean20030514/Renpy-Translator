#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
translate_grok.py — 使用 Grok API 专业翻译（基于你的自定义指令）

特点:
  - 使用你的专业 Grok 指令（针对 Ren'Py JSONL）
  - 支持 grok-4-fast-reasoning（2M 上下文，超低成本）
  - 逐行 JSON 处理，保护占位符和标签
  - 分支语气控制（inc/NTR/Love 等）

成本估算（100万字游戏）:
  grok-4-fast-reasoning: 
    输入 $0.20/M tokens (~150万 tokens) = $0.30
    输出 $0.50/M tokens (~180万 tokens) = $0.90
    总计: $1.20 ≈ ¥8.5

用法:
  python tools/translate_grok.py outputs/llm_batches -o outputs/llm_results \
    --api-key YOUR_XAI_API_KEY --model grok-4-fast-reasoning --workers 10
"""

import argparse
import json
import time
import gzip
from pathlib import Path
from typing import Optional
from urllib import request as urlreq
from urllib import error as urlerr
import concurrent.futures as cf

try:
    from rich.console import Console
    from rich.progress import (
        Progress, 
        BarColumn, 
        TimeElapsedColumn, 
        TextColumn,
        TaskProgressColumn
    )
    console = Console()
except ImportError:
    console = None
    TaskProgressColumn = None


# Grok API 配置
GROK_MODELS = {
    'grok-4-fast-reasoning': {
        'name': 'Grok 4 Fast Reasoning',
        'context': 2_000_000,  # 2M tokens
        'cost_input': 0.20,    # $/M tokens
        'cost_output': 0.50,   # $/M tokens
        'rpm_limit': 480,      # 480 RPM
        'tpm_limit': 4_000_000, # 4M TPM
    },
    'grok-4': {
        'name': 'Grok 4',
        'context': 2_000_000,
        'cost_input': 3.00,
        'cost_output': 6.00,
        'rpm_limit': 480,
        'tpm_limit': 4_000_000,
    },
    'grok-3': {
        'name': 'Grok 3',
        'context': 131_072,
        'cost_input': 2.00,
        'cost_output': 10.00,
        'rpm_limit': 480,
        'tpm_limit': 4_000_000,
    },
}


def estimate_tokens(text: str) -> int:
    """估算文本的 token 数量（中文约 1.5 字符/token，英文约 4 字符/token）"""
    # 简化估算：中英文混合按 2 字符/token
    return len(text) // 2


def calculate_cost(input_tokens: int, output_tokens: int, model: str) -> dict:
    """
    计算翻译成本
    
    Returns:
        {
            'input_cost': float,  # 输入成本 ($)
            'output_cost': float, # 输出成本 ($)
            'total_cost': float,  # 总成本 ($)
            'total_cost_cny': float  # 总成本 (¥)
        }
    """
    model_info = GROK_MODELS[model]
    input_cost = (input_tokens / 1_000_000) * model_info['cost_input']
    output_cost = (output_tokens / 1_000_000) * model_info['cost_output']
    total_cost = input_cost + output_cost
    
    # 美元转人民币（汇率 7.1）
    total_cost_cny = total_cost * 7.1
    
    return {
        'input_cost': input_cost,
        'output_cost': output_cost,
        'total_cost': total_cost,
        'total_cost_cny': total_cost_cny
    }


def build_grok_system_prompt() -> str:
    """构建基于你的专业指令的系统提示词"""
    return """# 【系统指令】Ren'Py JSONL 本地化（只增 `zh`｜零破坏）

## 目标

你将收到**逐行 JSON 对象**组成的 **JSONL**。
**任务**：把对象中的 `en` 文本翻成**简体中文**，并在**同一行对象**中**新增**一个中文字段 `zh`。
**禁止**修改、删除或重排任何已有字段或其值。

> ✅ 默认输出格式（首选）：**仅回 `id` 与 `zh` 两个键**
> 形如：`{"id":"<原样>","zh":"<中文>"}`
>
> 允许的替代（次选）：把**整行对象原样复制**，只**新增** `zh` 键，其余字段**逐字不变**。

---

## 输入字段（可能出现）

* 定位：`id`, `id_hash`, `file`, `line`, `col`, `idx`, `label`
* 文本：`en`
* 提示：`placeholders`（仅为集合提示）、`anchor_prev`, `anchor_next`
* 形态：`quote`（`"` 或 `'`），`is_triple`（布尔，是否三引号多行）

**硬规定**：以上**已有字段与其值**一律**不可改动**；你**只新增**一个 `zh` 字段。

---

## 只翻什么

* 仅翻 `en` 中的**可见文本**（对白、叙述、UI 文案、菜单项等，抽取器已剔除 `python:` 等代码块）。
* **已有中文**保持原样（不要再"润色"）。
* `<...>` **动作/拟声**是可读文本：翻译并**保留尖括号**（例：`<giggle>`→`<咯咯笑>`）。

---

## 绝对保留（数量与顺序**必须一致**）

以下三类"保护件"在 `zh` 中**原位保留**、**不增不减不换序**：

1. **方括号占位**：`[pov]`、`[ls]`、`[bs]`、`[mother]`、`[name]` ……
2. **Ren'Py 文本标签**：`{i}` / `{/i}` / `{b}` / `{color=#...}` / `{w}` / `{nw}` / `{a=...}` ……
3. **旧式格式化**：`%(name)s`、`%(n)d`、`%(f).2f` 等
   同时**原样保留**：`\\n`、`\\t`、以及三引号文本的**换行数与相对位置**。

> `placeholders` 字段仅为**集合提示**，其顺序不保证；以 `en` 正文为准在 `zh` 中逐一对齐。

---

## 引号与多行

* 你**不处理代码层引号**（由回填脚本根据 `quote`/`is_triple` 注入）。
* **禁止**引入新的英文引号 `"`/`'`。若确需引述语气，**尽量不用新增引号**；万不得已才用中文引号""，但一般请避免。
* 若 `is_triple: true`：`zh` 中的**换行数、段落分割**应与 `en` 对齐；不要把多行并成一行或反向拆分。

---

## 多分支一致性（称呼与语气）

**优先级**：①称呼（`inc`）▶ ②路径语气（`NTR`/子型）▶ ③暗色叠加（`*dark`）▶ ④其它。

* `inc==True` 且文本中出现**可见称呼**时：

  * 玩家→`[ls]`：译作 **"妹妹"**；`[ls]`→玩家：**"哥哥"**
  * 玩家→`[bs]`：译作 **"姐姐"**；`[bs]`→玩家：**"弟弟"**
  * 玩家→`[mother]`：译作 **"妈妈"**；`[mother]`→玩家：**"儿子"**
* **仅出现占位**时：**保留占位**（不要把 `[ls]` 等硬替中文称呼）。
* 语气矩阵：
  * 主语气：低俗、色情，比如（鸡巴、奶子、奶头、屁眼、小穴、屁股、龟头、荡妇、妓女、婊子、骚逼、撸管、做爱、肛交、口交、射精、阴蒂、高潮、自慰、肛门、干、操、骚货、屌、插、精液、骚、等等等等）；
  * Love/常规：俏皮、自然；
  * Corruption/支配：命令、占有；
  * Voyeur：旁观、玩味；
  * NTR：不甘、较劲；
  * Revenge：安抚、夺回；
  * Sadist：嘲弄、压迫；
  * `*dark`：在同一路径上**加深**。
* 借助 `label` 与 `anchor_prev/next` 判断近域语境，避免"串味"。

---

## 风格与长度

* **自然口语 > 生硬直译**，但**不改变语义**。
* **长度克制**：避免明显膨胀/缩水；UI 用语**短译优先**，防止按钮溢出。
* **标点**：保留原节奏；不要把 `...` 强改为 `……`（除非 `en` 原本如此）。`!?` 可在中文中用 `！？`，非强制。

---

## 逻辑/引擎相关：保守不译

若从 `anchor_prev/next` 能判断该串与**逻辑比较/引擎调用**相关（如 `if difficulty == "Hard":`、`FileAction("...")`、`Preference("...")` 等），**不要翻译**，令 `zh = en`。
拿不准是否可译时，**一律保守不译**（`zh = en`）。

---

## 输出要求（极其重要）

* **逐行输入，逐行输出**；**每个输入对象对应恰好一个输出对象**。
* **仅输出 JSON 对象**，不要输出解释、编号、额外文本、代码块标记。
* **首选**：只含两键 `{"id":"...","zh":"..."}`；
  **次选**：整行原样 + `"zh":"..."`。
* `zh` 必须是**字符串**；不要返回 `null`、数组或对象。

---

## 自检清单（逐条满足再给出 `zh`）

1. `zh` 中所有 `[]`/`{}`/`%()`/`\\n` 是否与 `en` **数量与顺序完全一致**？
2. 是否**未**引入新的英文引号或多余空格？
3. 若 `is_triple:true`：换行数是否对齐？
4. 语气是否符合 `label`/锚点对应的分支？称呼是否符合 `inc` 语境？
5. 不确定是否可译时是否保持 `zh = en`？

---

## 示例（按首选输出：仅 `id` 与 `zh`）

**输入：**
```
{"id":"game/basement.rpy:8:0","en":"You wake up.","placeholders":[]}
{"id":"game/basement.rpy:9:0","en":"{i}Huh? Did I hear something?{/i}","placeholders":["{i}","{/i}"]}
```

**输出：**
```
{"id":"game/basement.rpy:8:0","zh":"你醒了。"}
{"id":"game/basement.rpy:9:0","zh":"{i}嗯？我是不是听到什么声音？{/i}"}
```

---

现在开始翻译！"""


def call_grok_api(
    batch_lines: list[str],
    api_key: str,
    model: str = 'grok-4-fast-reasoning',
    timeout: int = 180
) -> Optional[tuple[list[dict], int, int]]:
    """
    调用 Grok API 翻译一批 JSONL 行
    
    Args:
        batch_lines: JSONL 行列表
        api_key: xAI API Key
        model: 模型名称
        timeout: 超时时间（秒）
    
    Returns:
        (翻译结果列表, 输入tokens, 输出tokens) 或 None
    """
    try:
        # 构建用户消息（提供简化的 JSONL，只保留必要字段）
        simplified_lines = []
        for line in batch_lines:
            try:
                obj = json.loads(line)
                # 只传递必要字段给 Grok
                simplified = {
                    'id': obj['id'],
                    'en': obj['en'],
                    'placeholders': obj.get('placeholders', []),
                    'label': obj.get('label', ''),
                    'speaker': obj.get('speaker', ''),
                    'is_triple': obj.get('is_triple', False),
                    'anchor_prev': obj.get('anchor_prev', ''),
                    'anchor_next': obj.get('anchor_next', '')
                }
                simplified_lines.append(json.dumps(simplified, ensure_ascii=False))
            except:
                simplified_lines.append(line)
        
        user_content = "翻译以下游戏文本为简体中文：\n\n" + "\n".join(simplified_lines)
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": build_grok_system_prompt()},
                {"role": "user", "content": user_content}
            ],
            "temperature": 0.3,
            "max_tokens": len(simplified_lines) * 200,  # 根据行数动态调整
            "stream": False
        }
        
        req = urlreq.Request(
            "https://api.x.ai/v1/chat/completions",
            data=json.dumps(payload).encode('utf-8'),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive"
            }
        )
        
        with urlreq.urlopen(req, timeout=timeout) as response:
            # 检查是否 gzip 压缩
            raw_data = response.read()
            if response.info().get('Content-Encoding') == 'gzip' or raw_data[:2] == b'\x1f\x8b':
                raw_data = gzip.decompress(raw_data)
            result = json.loads(raw_data.decode('utf-8'))
        
        content = result['choices'][0]['message']['content'].strip()
        
        # 获取 token 使用信息
        usage = result.get('usage', {})
        input_tokens = usage.get('prompt_tokens', 0)
        output_tokens = usage.get('completion_tokens', 0)
        
        # 解析返回的 JSONL
        translations = []
        for line in content.split('\n'):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if 'id' in obj and 'zh' in obj:
                    translations.append(obj)
            except json.JSONDecodeError:
                continue
        
        return translations, input_tokens, output_tokens
        
    except urlerr.HTTPError as e:
        try:
            error_body = e.read().decode('utf-8')
            error_json = json.loads(error_body)
            error_msg = error_json.get('error', {}).get('message', error_body)
        except:
            error_msg = f"HTTP {e.code}"
        
        if console:
            console.print(f"[red]API 错误 {e.code}: {error_msg}[/red]")
        else:
            print(f"API 错误 {e.code}: {error_msg}")
        return None
    except Exception as e:
        if console:
            console.print(f"[red]请求失败: {e}[/red]")
        return None


def translate_batch_file(
    batch_file: Path,
    output_dir: Path,
    api_key: str,
    model: str,
    batch_size: int = 50,
    single_file_mode: bool = False
) -> tuple[int, int, int, int]:
    """
    翻译一个批次文件
    
    Args:
        single_file_mode: 如果为 True，输出到 translated.jsonl，否则用原文件名
    
    Returns:
        (成功数, 失败数, 输入tokens, 输出tokens)
    """
    with open(batch_file, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]
    
    # 输出文件名
    if single_file_mode:
        output_file = output_dir / 'translated.jsonl'
        reject_file = output_dir / 'rejected.tsv'
    else:
        output_file = output_dir / batch_file.name
        reject_file = output_dir / batch_file.name.replace('.jsonl', '_rejects.tsv')
    
    # 读取已有结果（断点续传）
    translated_ids = set()
    if output_file.exists():
        with open(output_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    obj = json.loads(line.strip())
                    if 'zh' in obj and obj['zh']:
                        translated_ids.add(obj['id'])
                except:
                    pass
    
    # 过滤已翻译的行
    remaining_lines = []
    for line in lines:
        try:
            obj = json.loads(line)
            if obj['id'] not in translated_ids:
                remaining_lines.append(line)
        except:
            remaining_lines.append(line)
    
    if not remaining_lines:
        return len(lines), 0, 0, 0
    
    success_count = len(translated_ids)
    fail_count = 0
    total_input_tokens = 0
    total_output_tokens = 0
    
    # 分批翻译
    for i in range(0, len(remaining_lines), batch_size):
        batch = remaining_lines[i:i+batch_size]
        
        # 调用 Grok API
        result = call_grok_api(batch, api_key, model)
        
        if result:
            translations, input_tokens, output_tokens = result
            total_input_tokens += input_tokens
            total_output_tokens += output_tokens
            
            # 写入结果
            with open(output_file, 'a', encoding='utf-8') as f:
                for trans in translations:
                    # 找到原始行并合并
                    for line in batch:
                        try:
                            orig_obj = json.loads(line)
                            if orig_obj['id'] == trans['id']:
                                orig_obj['zh'] = trans['zh']
                                f.write(json.dumps(orig_obj, ensure_ascii=False) + '\n')
                                success_count += 1
                                break
                        except:
                            continue
        else:
            fail_count += len(batch)
            # 记录失败
            with open(reject_file, 'a', encoding='utf-8') as f:
                for line in batch:
                    try:
                        obj = json.loads(line)
                        f.write(f"{obj['id']}\t{obj['en']}\tAPI_FAILED\n")
                    except:
                        pass
        
        # 避免触发速率限制（480 RPM）
        time.sleep(0.15)  # 约 400 RPM
    
    return success_count, fail_count, total_input_tokens, total_output_tokens


def main():
    parser = argparse.ArgumentParser(
        description='使用 Grok API 翻译（基于专业指令）'
    )
    parser.add_argument('source', help='输入 JSONL 文件或批次目录')
    parser.add_argument('-o', '--output', required=True, help='输出目录')
    parser.add_argument('--api-key', required=True, help='xAI API Key')
    parser.add_argument('--model', default='grok-4-fast-reasoning',
                       choices=list(GROK_MODELS.keys()), help='模型名称')
    parser.add_argument('--workers', type=int, default=5, help='并发数')
    parser.add_argument('--batch-size', type=int, default=50, 
                       help='每次 API 请求的行数')
    
    args = parser.parse_args()
    
    source_path = Path(args.source)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 判断是文件还是目录
    if source_path.is_file():
        # 单个 JSONL 文件模式（Grok 直接翻译）
        batch_files = [source_path]
        # 输出到 translated.jsonl
        single_file_mode = True
    elif source_path.is_dir():
        # 批次目录模式（分批翻译）
        batch_files = sorted(source_path.glob('batch_*.jsonl'))
        single_file_mode = False
    else:
        print(f"❌ 输入路径不存在: {source_path}")
        return 1
    
    if not batch_files:
        print("❌ 未找到批次文件")
        return 1
    
    model_info = GROK_MODELS[args.model]
    
    if console:
        console.print(f"\n[cyan]═══════════════════════════════════════[/cyan]")
        console.print(f"[green]模型:[/green] {model_info['name']}")
        console.print(f"[green]上下文:[/green] {model_info['context']:,} tokens")
        console.print(f"[green]成本:[/green] 输入 ${model_info['cost_input']}/M, 输出 ${model_info['cost_output']}/M")
        console.print(f"[green]输入:[/green] {source_path}")
        console.print(f"[green]模式:[/green] {'单文件' if single_file_mode else '批次目录'}")
        console.print(f"[green]文件数:[/green] {len(batch_files)}")
        console.print(f"[green]并发数:[/green] {args.workers}")
        console.print(f"[cyan]═══════════════════════════════════════[/cyan]\n")
    
    total_success = 0
    total_fail = 0
    total_input_tokens = 0
    total_output_tokens = 0
    
    if console:
        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            task = progress.add_task("翻译进度", total=len(batch_files))
            
            with cf.ThreadPoolExecutor(max_workers=args.workers) as executor:
                futures = {
                    executor.submit(
                        translate_batch_file,
                        bf, output_dir, args.api_key, args.model, args.batch_size, single_file_mode
                    ): bf for bf in batch_files
                }
                
                for future in cf.as_completed(futures):
                    success, fail, input_tok, output_tok = future.result()
                    total_success += success
                    total_fail += fail
                    total_input_tokens += input_tok
                    total_output_tokens += output_tok
                    progress.advance(task)
    else:
        # 无 rich 的简单版本
        for i, bf in enumerate(batch_files, 1):
            print(f"[{i}/{len(batch_files)}] {bf.name}...")
            success, fail, input_tok, output_tok = translate_batch_file(
                bf, output_dir, args.api_key, args.model, args.batch_size, single_file_mode
            )
            total_success += success
            total_fail += fail
            total_input_tokens += input_tok
            total_output_tokens += output_tok
    
    # 计算成本
    cost_info = calculate_cost(total_input_tokens, total_output_tokens, args.model)
    
    # 统计
    if console:
        console.print("\n[cyan]═══════════════════════════════════════[/cyan]")
        console.print(f"[green]✓ 翻译成功:[/green] {total_success}")
        console.print(f"[red]✗ 翻译失败:[/red] {total_fail}")
        console.print(f"[yellow]完成率:[/yellow] {total_success/(total_success+total_fail)*100:.1f}%")
        console.print(f"[cyan]输入 Tokens:[/cyan] {total_input_tokens:,}")
        console.print(f"[cyan]输出 Tokens:[/cyan] {total_output_tokens:,}")
        console.print(f"[yellow]总成本:[/yellow] ${cost_info['total_cost']:.4f} (¥{cost_info['total_cost_cny']:.2f})")
        console.print("[cyan]═══════════════════════════════════════[/cyan]")
    
    return 0 if total_fail == 0 else 1


if __name__ == '__main__':
    exit(main())
