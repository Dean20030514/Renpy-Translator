#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
translate.py — 使用本地 Ollama 模型批量翻译 JSONL（支持目录/分包）

用法示例：
  python tools/translate.py outputs/llm_batches -o outputs/llm_results \
    --model qwen2.5:14b --workers auto

输入：
  - JSONL（每行至少包含 id, en，可带上下文字段）或包含多个 *.jsonl 的目录
输出：
  - 目录 out_dir 中按输入同名生成 *.jsonl，每行 {"id": ..., "zh": ...}

优化模式（推荐）：
  --use-optimized    启用连接池 + 质量验证 + 智能重试
  --quality-threshold 0.7  质量阈值（默认 0.7）

特性：
  - 占位符保护（[name], {0}, %s 等）
  - 换行符一致性检查
  - 智能重试机制
  - GPU 信息监控
  - 增量保存（防止丢失进度）
  - 翻译缓存支持（增量翻译）
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import os
import random
import re
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional, Callable
from urllib import request as urlreq
from urllib import error as urlerr

# 添加 src 到路径
_project_root = Path(__file__).parent.parent
if str(_project_root / "src") not in sys.path:
    sys.path.insert(0, str(_project_root / "src"))

# 统一日志
try:
    from renpy_tools.utils.logger import get_logger, TranslationError
    _logger = get_logger("translate")
except ImportError:
    _logger = None
    TranslationError = ValueError

def _log(level: str, msg: str) -> None:
    """统一日志输出"""
    if _logger:
        getattr(_logger, level, _logger.info)(msg)
    elif level in ("warning", "error"):
        print(f"[{level.upper()}] {msg}", file=sys.stderr)
    else:
        print(f"[{level.upper()}] {msg}")

# 全局文件写入锁，防止并发写入竞态条件
_file_write_lock = threading.Lock()

try:
    from rich.console import Console
    from rich.progress import (
        Progress, BarColumn, TimeElapsedColumn, 
        TextColumn, TaskProgressColumn
    )
    _console = Console()
except ImportError:
    _console = None

# 统一导入（从 common.py 获取，避免重复定义）
try:
    from renpy_tools.utils.common import (
        PH_RE, ph_multiset, 
        TranslationCache, AdaptiveRateLimiter, calculate_quality_score
    )
except ImportError:
    # Fallback
    PH_RE = re.compile(
        r"\[[A-Za-z_][A-Za-z0-9_]*\]"
        r"|%(?:\([^)]+\))?[+#0\- ]?\d*(?:\.\d+)?[sdifeEfgGxXo]"
        r"|\{\d+(?:![rsa])?(?::[^{}]+)?\}"
        r"|\{[A-Za-z_][A-Za-z0-9_]*(?:![rsa])?(?::[^{}]+)?\}"
    )
    
    def ph_multiset(s: str) -> dict[str, int]:
        cnt: dict[str, int] = {}
        for m in PH_RE.findall(s or ""):
            cnt[m] = cnt.get(m, 0) + 1
        return cnt
    
    TranslationCache = None
    AdaptiveRateLimiter = None
    calculate_quality_score = None

# 尝试导入优化翻译器
try:
    from renpy_tools.core.translator import OllamaTranslator
    _HAS_OPTIMIZED_TRANSLATOR = True
except ImportError:
    _HAS_OPTIMIZED_TRANSLATOR = False


# ========================================
# 配置类
# ========================================

@dataclass
class TranslationConfig:
    """翻译配置"""
    host: str = "http://127.0.0.1:11434"
    model: str = "qwen2.5:14b"
    workers: int = 4
    timeout: float = 120.0
    temperature: float = 0.2
    retries: int = 1
    min_words: int = 2
    flush_interval: int = 20
    use_optimized: bool = False
    quality_threshold: float = 0.7
    
    def __post_init__(self):
        """验证配置"""
        if self.workers < 1:
            self.workers = 1
        if self.timeout < 10:
            self.timeout = 10.0
        if not (0 <= self.temperature <= 2):
            self.temperature = 0.2
        if not (0 < self.quality_threshold <= 1):
            self.quality_threshold = 0.7


@dataclass
class TranslationStats:
    """翻译统计"""
    total: int = 0
    success: int = 0
    failed: int = 0
    retries: int = 0
    skipped: int = 0
    start_time: float = field(default_factory=time.time)
    
    def elapsed_time(self) -> float:
        """经过的时间（秒）"""
        return time.time() - self.start_time
    
    def success_rate(self) -> float:
        """成功率"""
        return self.success / self.total if self.total > 0 else 0.0
    
    def avg_time_per_item(self) -> float:
        """平均每条耗时（秒）"""
        completed = self.success + self.failed
        return self.elapsed_time() / completed if completed > 0 else 0.0


# ========================================
# 工具函数
# ========================================

def get_gpu_info() -> Optional[str]:
    """获取 GPU 使用信息"""
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=utilization.gpu,memory.used,memory.total",
                "--format=csv,noheader,nounits"
            ],
            capture_output=True,
            text=True,
            timeout=2,
            encoding='utf-8',
            errors='ignore',
            check=False
        )
        if result.returncode == 0:
            output = ' '.join(result.stdout.strip().split())
            parts = [p.strip() for p in output.split(',')]
            if len(parts) >= 3:
                return f"GPU: {parts[0]}% | VRAM: {parts[1]}/{parts[2]} MB"
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return None


def get_gpu_total_mem_mb() -> Optional[int]:
    """获取 GPU 总显存（MB）"""
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=memory.total",
                "--format=csv,noheader,nounits"
            ],
            capture_output=True,
            text=True,
            timeout=2,
            check=False
        )
        if result.returncode == 0:
            lines = result.stdout.strip().splitlines()
            if lines:
                return int(lines[0].strip())
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError, ValueError, IndexError):
        pass
    return None


def suggest_workers(model: str) -> int:
    """根据模型和显存推荐并发数"""
    model_lower = (model or "").lower()
    total_mem = get_gpu_total_mem_mb() or 0
    
    # 量化模型可以更高并发
    if any(q in model_lower for q in ["q4", "q5", "int4", "int8"]):
        return 4 if total_mem >= 6000 else 3
    
    # 7B 模型
    if "7b" in model_lower or "8b" in model_lower:
        return 4 if total_mem >= 8000 else 2
    
    # 大模型（13B+）
    if any(size in model_lower for size in ["13b", "14b", "32b", "70b"]):
        return 2 if total_mem >= 12000 else 1
    
    # CPU 或未知模型
    cpu_count = os.cpu_count() or 2
    return max(1, min(4, cpu_count // 2))


def is_non_dialog_text(text: str, min_words: int = 2) -> bool:
    """
    判断是否为非对话文本（应跳过翻译）
    
    【已废弃】此功能容易误判，建议在提取阶段过滤
    现在只过滤明显的非文本内容
    
    跳过规则：
    - 空文本
    - 纯布尔值（True/False/None）
    - 明显的资源路径（包含 / 或 .png/.jpg 等）
    """
    if not text or not text.strip():
        return True
    
    # 移除标签后判断
    clean = re.sub(r'\{[/a-z_]+\}', '', text)
    clean = re.sub(r'\[[a-z_]+\]', '', clean, flags=re.IGNORECASE)
    clean = clean.strip()
    
    if not clean:
        return True
    
    lower = clean.lower()
    
    # 只过滤明显的非文本
    if lower in {"true", "false", "none", "null"}:
        return True
    
    # 明显的资源路径
    if "/" in text or "\\" in text:
        return True
    
    # 图片/音频文件
    if re.search(r'\.(png|jpg|jpeg|gif|webp|mp3|ogg|wav)$', lower):
        return True
    
    return False


def http_post_json(url: str, payload: dict, timeout: float = 120.0) -> dict:
    """发送 JSON POST 请求"""
    data = json.dumps(payload).encode("utf-8")
    req = urlreq.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urlreq.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8", errors="ignore"))


def strip_thinking_blocks(text: str) -> str:
    """移除思考块和代码围栏"""
    if not text:
        return ""
    # 移除 <think>...</think>
    text = re.sub(r"<think>[\s\S]*?</think>", "", text, flags=re.IGNORECASE)
    # 移除 ```...```
    text = re.sub(r"```(?:json)?\s*([\s\S]*?)\s*```", r"\1", text, flags=re.IGNORECASE)
    return text.strip()


# ========================================
# Prompt 构建
# ========================================

def build_system_prompt() -> str:
    """构建系统提示词"""
    return (
        "你是资深成人游戏本地化译员，将英文台词翻译为简体中文。\n\n"
        
        "【重要提示】\n"
        "- 文本中的 〔数字〕 标记（如〔0〕〔1〕）是占位符，翻译时必须保留\n"
        "- 不要删除或修改这些标记，保持它们在译文中的位置\n\n"
        
        "【翻译风格】\n"
        "- 成人游戏主基调：直白露骨（鸡巴、奶子、小穴、屁股、骚货、操、干、插）\n"
        "- 自然口语，避免生硬直译\n"
        "- 保持换行符数量一致\n"
        "- UI 文本优先短译\n\n"
        
        "【语气指南】（从场景标签判断）\n"
        "- Love：俏皮、温馨\n"
        "- Corruption：命令、占有\n"
        "- NTR：不甘、较劲\n"
        "- Sadist：嘲弄、压迫\n"
        "- *dark：加深语气\n\n"
        
        "【翻译质量要求】⚠️ 严格遵守\n"
        "- ⚠️ 严禁输出任何英文单词（专有名词、变量名除外）\n"
        "- ⚠️ 必须将每一个英文词汇完整翻译为中文\n"
        "- ⚠️ 禁止中英文混合输出\n"
        "- ⚠️ 不确定的词宁可意译，也不要保留英文\n\n"
        
        "【错误示例】禁止模仿以下错误\n"
        "❌ '你 also 也喜欢' → ✅ '你也喜欢'\n"
        "❌ '享受你的 pleasure' → ✅ '享受你的快感'\n"
        "❌ '一个dirty的秘密' → ✅ '一个肮脏的秘密'\n"
        "❌ '那副slutty的look' → ✅ '那副淫荡的眼神'\n\n"
        
        "【输出规则】\n"
        "- 只输出纯中文译文\n"
        "- 不输出思考过程、代码块、额外说明\n"
        "- 再次强调：绝对不允许输出任何英文单词"
    )


def build_user_prompt(text: str, context: dict[str, Any]) -> str:
    """构建用户提示词"""
    parts = [
        "[翻译任务] 将下列英文翻译为简体中文。",
        f"[英文]\n{text}",
    ]
    
    if context.get("label"):
        parts.append(f"[场景/标签] {context['label']}")
    if context.get("anchor_prev"):
        parts.append(f"[前文] {context['anchor_prev']}")
    if context.get("anchor_next"):
        parts.append(f"[后文] {context['anchor_next']}")
    if context.get("ctx_prev"):
        parts.append(f"[同段前句] {' | '.join(context['ctx_prev'])}")
    if context.get("ctx_next"):
        parts.append(f"[同段后句] {' | '.join(context['ctx_next'])}")
    
    return "\n\n".join(parts)


# ========================================
# 占位符处理
# ========================================

def extract_placeholders(text: str) -> tuple[str, list[tuple[str, int]]]:
    """
    提取占位符，返回(纯文本, [(占位符, 位置)])
    
    提取的占位符类型：
    1. Ren'Py 标签：{i} {/i} {b} {color=#...}
    2. 方括号变量：[name] [pov] [ls]
    3. 格式化占位符：%(name)s %s {0} {name}
    
    占位符用 〔0〕, 〔1〕 等替换（全角括号，模型不会删除）
    """
    pattern = re.compile(
        r'\{[/a-z_][^}]*\}'  # {i}, {/i}, {color=#fff}
        r'|\[[a-z_][^\]]*\]'  # [name], [pov]
        r'|%\([^)]+\)[sdifeEfgGxXo]'  # %(name)s
        r'|%[sdifeEfgGxXo]'  # %s, %d
        r'|\{\d+(?:![rsa])?(?::[^{}]+)?\}'  # {0}, {0:.2f}
        r'|\{[A-Za-z_][A-Za-z0-9_]*(?:![rsa])?(?::[^{}]+)?\}',  # {name}
        flags=re.IGNORECASE
    )
    
    matches = list(pattern.finditer(text))
    placeholders: list[tuple[str, int]] = []
    result = text
    
    # 从后往前替换，避免位置偏移
    for i in range(len(matches) - 1, -1, -1):
        match = matches[i]
        ph = match.group(0)
        pos = match.start()
        tag = f'〔{i}〕'  # 全角括号
        placeholders.insert(0, (ph, i))
        result = result[:pos] + tag + result[pos + len(ph):]
    
    return result, placeholders


def restore_placeholders(text: str, placeholders: list[tuple[str, int]]) -> str:
    """将 〔0〕, 〔1〕 等替换回原始占位符"""
    result = text
    for ph, idx in placeholders:
        tag = f'〔{idx}〕'
        result = result.replace(tag, ph)
    return result


def ensure_valid_translation(source: str, translation: str) -> tuple[bool, str]:
    """
    验证翻译质量
    
    Returns:
        (是否通过, 错误原因)
    """
    if not translation:
        return False, "empty_translation"
    
    # 换行符数量必须一致
    if source.count("\n") != translation.count("\n"):
        return False, "newline_count_mismatch"
    
    # 占位符必须一致
    if ph_multiset(source) != ph_multiset(translation):
        return False, "placeholder_mismatch"
    
    return True, ""


# ========================================
# Ollama 交互
# ========================================

def chat_ollama(
    host: str,
    model: str,
    system: str,
    user: str,
    timeout: float = 120.0,
    temperature: float = 0.2
) -> str:
    """调用 Ollama API 进行翻译"""
    url = host.rstrip("/") + "/api/chat"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "stream": False,
        "options": {"temperature": temperature},
    }
    
    resp = http_post_json(url, payload, timeout=timeout)
    msg = (resp.get("message") or {}).get("content") or ""
    return strip_thinking_blocks(msg)


def translate_one_item(
    item: dict,
    config: TranslationConfig,
    system_prompt: str
) -> tuple[str, Optional[str], Optional[str]]:
    """
    翻译单条记录
    
    Returns:
        (id, 译文或None, 错误原因或None)
    """
    item_id = item.get("id", "")
    original = item.get("en", "")
    
    if not item_id:
        return "", None, "missing_id"
    if not original:
        return item_id, "", None
    
    # 提取占位符
    clean_text, placeholders = extract_placeholders(original)
    if not clean_text.strip() or len(clean_text.strip()) < 2:
        return item_id, original, None
    
    # 构建提示词
    context = {k: v for k, v in item.items() if k not in ("id", "en")}
    user_prompt = build_user_prompt(clean_text, context)
    
    # 重试翻译
    last_error: Optional[str] = None
    for attempt in range(config.retries + 1):
        # 根据上次错误调整提示
        if attempt == 0:
            sys_prompt = system_prompt
        elif last_error == "newline_count_mismatch":
            sys_prompt = system_prompt + "\n\n⚠️ 严格要求：译文换行数必须与原文完全一致！"
        else:
            sys_prompt = system_prompt + "\n\n严格模式：保持换行数一致，不允许增删。"
        
        try:
            # 调用翻译
            translated = chat_ollama(
                config.host, config.model,
                sys_prompt, user_prompt,
                config.timeout, config.temperature
            ).strip()
            
            # 恢复占位符
            final = restore_placeholders(translated, placeholders)
            
            # 验证
            valid, error = ensure_valid_translation(original, final)
            if valid:
                return item_id, final, None
            
            # 尝试自动修复换行问题
            if error == "newline_count_mismatch" and final.endswith('\n'):
                fixed = final.rstrip('\n')
                valid, _ = ensure_valid_translation(original, fixed)
                if valid:
                    return item_id, fixed, None
            
            last_error = error
            # 指数退避 + 抖动，避免雷击效应
            base_delay = 0.5 * (2 ** attempt)
            jitter = random.uniform(0, 0.5 * base_delay)
            time.sleep(base_delay + jitter)

        except (urlerr.URLError, urlerr.HTTPError, TimeoutError) as e:
            last_error = f"network_error:{type(e).__name__}"
            # 网络错误使用更长的退避时间
            base_delay = min(2.0 * (2 ** attempt), 16.0)
            jitter = random.uniform(0, 0.5 * base_delay)
            time.sleep(base_delay + jitter)
    
    return item_id, None, last_error or "unknown_error"


# ========================================
# 文件处理
# ========================================

class TranslationProcessor:
    """翻译处理器"""
    
    def __init__(self, config: TranslationConfig):
        self.config = config
        self.stats = TranslationStats()
        self.system_prompt = build_system_prompt()
    
    def load_items(self, file_path: Path) -> list[dict]:
        """加载 JSONL 文件"""
        items: list[dict] = []
        with file_path.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    obj = json.loads(line)
                    if obj.get("id"):
                        items.append(obj)
                except (ValueError, json.JSONDecodeError):
                    continue
        return items
    
    def filter_items(self, items: list[dict]) -> list[dict]:
        """过滤明显的非文本内容（已简化，不再激进过滤）"""
        before = len(items)
        filtered = [
            item for item in items
            if not is_non_dialog_text(item.get("en", ""), self.config.min_words)
        ]
        after = len(filtered)
        
        if before > after:
            self._print(f"  [dim]过滤非文本内容: {before-after}/{before} 已跳过[/]")
        
        return filtered
    
    def _print(self, msg: str):
        """打印消息"""
        if _console:
            _console.print(msg)
        else:
            # 移除 Rich 标记
            clean_msg = re.sub(r'\[/?[a-z]+[^\]]*\]', '', msg)
            print(clean_msg)
    
    def flush_results(
        self,
        output_file: Path,
        rejects_file: Path,
        out_lines: list[dict],
        rej_lines: list[tuple[str, str]]
    ):
        """刷新结果到文件（线程安全）"""
        with _file_write_lock:
            if out_lines:
                with output_file.open("a", encoding="utf-8") as f:
                    for obj in out_lines:
                        f.write(json.dumps(obj, ensure_ascii=False) + "\n")
                out_lines.clear()

            if rej_lines:
                with rejects_file.open("a", encoding="utf-8") as f:
                    for rid, err in rej_lines:
                        f.write(f"{rid}\t{err}\n")
                rej_lines.clear()
    
    def process_standard(
        self,
        input_file: Path,
        output_file: Path,
        rejects_file: Path
    ):
        """标准模式处理"""
        # 加载和过滤
        items = self.load_items(input_file)
        items = self.filter_items(items)
        
        if not items:
            self._print("  [yellow]⚠ 无有效数据[/]")
            return
        
        self.stats.total = len(items)
        
        # 清空输出文件
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text("", encoding="utf-8")
        if rejects_file.exists():
            rejects_file.unlink()
        
        out_lines: list[dict] = []
        rej_lines: list[tuple[str, str]] = []
        
        # 显示GPU信息
        gpu_info = get_gpu_info()
        if gpu_info:
            self._print(f"  [cyan]🎮 {gpu_info}[/]")
        
        self._print(f"  [bold]翻译 {len(items)} 条文本...[/]")
        
        # 并发翻译
        if self.config.workers > 1:
            self._process_concurrent(items, out_lines, rej_lines, output_file, rejects_file)
        else:
            self._process_sequential(items, out_lines, rej_lines, output_file, rejects_file)
        
        # 最后刷新
        self.flush_results(output_file, rejects_file, out_lines, rej_lines)
        
        self._print_stats()
    
    def _process_concurrent(
        self,
        items: list[dict],
        out_lines: list[dict],
        rej_lines: list[tuple[str, str]],
        output_file: Path,
        rejects_file: Path
    ):
        """并发处理"""
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
                    f"  [cyan]翻译中 ({self.config.workers} 线程)[/]",
                    total=len(items)
                )
                
                with cf.ThreadPoolExecutor(max_workers=self.config.workers) as executor:
                    futures = [
                        executor.submit(translate_one_item, item, self.config, self.system_prompt)
                        for item in items
                    ]
                    
                    for fut in cf.as_completed(futures):
                        item_id, translation, error = fut.result()
                        
                        if translation is not None:
                            out_lines.append({"id": item_id, "zh": translation})
                            self.stats.success += 1
                        else:
                            rej_lines.append((item_id, error or ""))
                            self.stats.failed += 1
                        
                        progress.advance(task)
                        
                        # 周期性刷新
                        completed = len(out_lines) + len(rej_lines)
                        if self.config.flush_interval > 0 and completed % self.config.flush_interval == 0:
                            self.flush_results(output_file, rejects_file, out_lines, rej_lines)
                        
                        # 更新GPU信息
                        if completed % 5 == 0:
                            gpu_info = get_gpu_info()
                            if gpu_info:
                                progress.update(task, description=f"  [cyan]翻译中 ({self.config.workers} 线程) | {gpu_info}[/]")
        else:
            with cf.ThreadPoolExecutor(max_workers=self.config.workers) as executor:
                futures = [
                    executor.submit(translate_one_item, item, self.config, self.system_prompt)
                    for item in items
                ]
                
                for i, fut in enumerate(cf.as_completed(futures), 1):
                    item_id, translation, error = fut.result()
                    
                    if translation is not None:
                        out_lines.append({"id": item_id, "zh": translation})
                        self.stats.success += 1
                    else:
                        rej_lines.append((item_id, error or ""))
                        self.stats.failed += 1
                    
                    if self.config.flush_interval > 0 and i % self.config.flush_interval == 0:
                        self.flush_results(output_file, rejects_file, out_lines, rej_lines)
                    
                    if i % 10 == 0:
                        print(f"  进度: {i}/{len(items)} ({100*i//len(items)}%)")
    
    def _process_sequential(
        self,
        items: list[dict],
        out_lines: list[dict],
        rej_lines: list[tuple[str, str]],
        output_file: Path,
        rejects_file: Path
    ):
        """顺序处理"""
        if _console:
            with Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TextColumn("•"),
                TimeElapsedColumn(),
                console=_console
            ) as progress:
                task = progress.add_task("  [cyan]翻译中[/]", total=len(items))
                
                for i, item in enumerate(items, 1):
                    item_id, translation, error = translate_one_item(
                        item, self.config, self.system_prompt
                    )
                    
                    if translation is not None:
                        out_lines.append({"id": item_id, "zh": translation})
                        self.stats.success += 1
                    else:
                        rej_lines.append((item_id, error or ""))
                        self.stats.failed += 1
                    
                    progress.advance(task)
                    
                    if self.config.flush_interval > 0 and i % self.config.flush_interval == 0:
                        self.flush_results(output_file, rejects_file, out_lines, rej_lines)
        else:
            for i, item in enumerate(items, 1):
                item_id, translation, error = translate_one_item(
                    item, self.config, self.system_prompt
                )
                
                if translation is not None:
                    out_lines.append({"id": item_id, "zh": translation})
                    self.stats.success += 1
                else:
                    rej_lines.append((item_id, error or ""))
                    self.stats.failed += 1
                
                if self.config.flush_interval > 0 and i % self.config.flush_interval == 0:
                    self.flush_results(output_file, rejects_file, out_lines, rej_lines)
                
                if i % 10 == 0:
                    print(f"  进度: {i}/{len(items)} ({100*i//len(items)}%)")
    
    def _print_stats(self):
        """打印统计信息"""
        self._print("  [green]✓ 完成翻译[/]")
        self._print(
            f"  [dim]统计: 成功={self.stats.success}, 失败={self.stats.failed}, "
            f"成功率={self.stats.success_rate():.1%}, "
            f"平均耗时={self.stats.avg_time_per_item():.2f}s/条[/]"
        )


# ========================================
# 优化模式处理
# ========================================

def process_optimized(
    input_file: Path,
    output_file: Path,
    rejects_file: Path,
    config: TranslationConfig
):
    """使用优化翻译器处理（连接池 + 质量验证 + 智能重试）"""
    if not _HAS_OPTIMIZED_TRANSLATOR:
        print("  ⚠ 优化翻译器模块未找到，回退到标准模式")
        processor = TranslationProcessor(config)
        processor.process_standard(input_file, output_file, rejects_file)
        return
    
    # 加载和过滤
    processor = TranslationProcessor(config)
    items = processor.load_items(input_file)
    items = processor.filter_items(items)
    
    if not items:
        processor._print("  [yellow]⚠ 无有效数据[/]")
        return
    
    out_lines: list[dict] = []
    rej_lines: list[tuple[str, str]] = []
    
    # 清空输出文件
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text("", encoding="utf-8")
    if rejects_file.exists():
        rejects_file.unlink()
    
    # 显示GPU信息
    gpu_info = get_gpu_info()
    if gpu_info:
        processor._print(f"  [cyan]🎮 {gpu_info}[/]")
    
    # 创建优化翻译器
    with OllamaTranslator(
        host=config.host,
        model=config.model,
        max_workers=config.workers,
        timeout=config.timeout,
        temperature=config.temperature,
        quality_threshold=config.quality_threshold,
        max_retries=3
    ) as translator:
        processor._print(
            f"  [bold]使用优化翻译器（连接池 + 质量验证）翻译 {len(items)} 条文本...[/]"
        )
        
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
                    f"  [cyan]翻译中 ({config.workers} 线程)[/]",
                    total=len(items)
                )
                
                for i, item in enumerate(items, 1):
                    en = item.get("en", "")
                    if not en:
                        out_lines.append({"id": item.get("id"), "zh": ""})
                        progress.advance(task)
                        continue
                    
                    # 提取占位符
                    clean, placeholders = extract_placeholders(en)
                    if not clean.strip() or len(clean.strip()) < 2:
                        out_lines.append({"id": item.get("id"), "zh": en})
                        progress.advance(task)
                        continue
                    
                    # 构建上下文
                    ctx = {k: v for k, v in item.items() if k not in ("id", "en")}
                    
                    # 调用优化翻译器
                    result = translator.translate_with_validation(clean, context=ctx)
                    
                    if result["success"]:
                        # 恢复占位符
                        final = restore_placeholders(result["translation"], placeholders)
                        out_lines.append({"id": item.get("id"), "zh": final})
                    else:
                        # 记录失败
                        errors = "; ".join(result.get("issues", []))
                        rej_lines.append((item.get("id", ""), f"quality_failed: {errors}"))
                    
                    progress.advance(task)
                    
                    # 周期性刷新
                    if config.flush_interval > 0 and i % config.flush_interval == 0:
                        processor.flush_results(output_file, rejects_file, out_lines, rej_lines)
                    
                    # 更新GPU信息
                    if i % 5 == 0:
                        gpu_info = get_gpu_info()
                        if gpu_info:
                            progress.update(
                                task,
                                description=f"  [cyan]翻译中 ({config.workers} 线程) | {gpu_info}[/]"
                            )
        else:
            for i, item in enumerate(items, 1):
                en = item.get("en", "")
                if not en:
                    out_lines.append({"id": item.get("id"), "zh": ""})
                    continue
                
                clean, placeholders = extract_placeholders(en)
                if not clean.strip() or len(clean.strip()) < 2:
                    out_lines.append({"id": item.get("id"), "zh": en})
                    continue
                
                ctx = {k: v for k, v in item.items() if k not in ("id", "en")}
                result = translator.translate_with_validation(clean, context=ctx)
                
                if result["success"]:
                    final = restore_placeholders(result["translation"], placeholders)
                    out_lines.append({"id": item.get("id"), "zh": final})
                else:
                    errors = "; ".join(result.get("issues", []))
                    rej_lines.append((item.get("id", ""), f"quality_failed: {errors}"))
                
                if config.flush_interval > 0 and i % config.flush_interval == 0:
                    processor.flush_results(output_file, rejects_file, out_lines, rej_lines)
                
                if i % 10 == 0:
                    print(f"  进度: {i}/{len(items)} ({100*i//len(items)}%)")
        
        # 最后刷新
        processor.flush_results(output_file, rejects_file, out_lines, rej_lines)
        
        # 显示统计
        stats = translator.get_stats()
        processor._print("  [green]✓ 完成翻译[/]")
        processor._print(
            f"  [dim]统计: 总数={stats['total']}, 成功={stats['success']}, "
            f"失败={stats['failed']}, 重试={stats['retries']}, "
            f"平均质量={stats['avg_quality']:.2f}[/]"
        )


# ========================================
# 主函数
# ========================================

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="使用 Ollama 批量翻译 JSONL 文件",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 标准模式
  python tools/translate.py outputs/llm_batches -o outputs/llm_results

  # 优化模式（推荐）
  python tools/translate.py outputs/llm_batches -o outputs/llm_results --use-optimized

  # 自定义配置
  python tools/translate.py outputs/llm_batches -o outputs/llm_results \\
    --model qwen2.5:14b --workers 4 --use-optimized --quality-threshold 0.8
        """
    )
    
    # 必需参数
    parser.add_argument("in_path", help="输入 JSONL 或目录（目录下所有 *.jsonl 将被处理）")
    parser.add_argument("-o", "--out", required=True, help="输出目录（将按输入名称写出 *.jsonl）")
    
    # Ollama 配置
    parser.add_argument(
        "--model",
        default=os.environ.get("OLLAMA_MODEL", "qwen2.5:14b"),
        help="Ollama 模型名（默认：qwen2.5:14b）"
    )
    
    ollama_host_env = os.environ.get("OLLAMA_HOST", "")
    if ollama_host_env and not ollama_host_env.startswith("http"):
        ollama_host_default = f"http://{ollama_host_env}"
    else:
        ollama_host_default = ollama_host_env or "http://127.0.0.1:11434"
    
    parser.add_argument(
        "--host",
        default=ollama_host_default,
        help="Ollama HTTP 地址（默认：http://127.0.0.1:11434）"
    )
    
    # 并发配置
    parser.add_argument(
        "--workers",
        default="auto",
        help="并发线程数（整数或 'auto'，默认 auto）"
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=120.0,
        help="HTTP 超时时间（秒，默认 120）"
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.2,
        help="采样温度（默认 0.2）"
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=1,
        help="标准模式下的重试次数（默认 1）"
    )
    
    # 内容过滤（已简化，不再激进过滤）
    parser.add_argument(
        "--min-words",
        type=int,
        default=2,
        help="最少英文词数过滤（默认 2，设为 0 禁用）"
    )
    
    # 保存配置
    parser.add_argument(
        "--flush-interval",
        type=int,
        default=20,
        help="每翻译多少条后自动保存（默认 20，设为 0 则仅最后保存）"
    )
    
    # 优化模式
    parser.add_argument(
        "--use-optimized",
        action="store_true",
        default=False,
        help="使用优化翻译器（连接池 + 质量验证 + 智能重试，推荐）"
    )
    parser.add_argument(
        "--quality-threshold",
        type=float,
        default=0.7,
        help="优化模式下的最低质量阈值（默认 0.7）"
    )
    
    args = parser.parse_args()
    
    # 解析输入文件
    src = Path(args.in_path)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    files: list[Path] = []
    if src.is_dir():
        files = sorted([x for x in src.glob("*.jsonl")])
    else:
        files = [src]
    
    if not files:
        print(f"未找到 JSONL 文件: {src}")
        return
    
    # 解析 workers
    workers_val: int
    if args.workers.isdigit():
        workers_val = max(1, int(args.workers))
    else:
        workers_val = suggest_workers(args.model)
    
    # 创建配置
    config = TranslationConfig(
        host=args.host,
        model=args.model,
        workers=workers_val,
        timeout=args.timeout,
        temperature=args.temperature,
        retries=args.retries,
        min_words=args.min_words,
        flush_interval=args.flush_interval,
        use_optimized=args.use_optimized and _HAS_OPTIMIZED_TRANSLATOR,
        quality_threshold=args.quality_threshold
    )
    
    # 显示配置
    if _console:
        _console.print("\n[bold cyan]═══════════════════════════════════════[/]")
        _console.print(f"[bold]模型:[/] [yellow]{config.model}[/]")
        _console.print(f"[bold]并发线程:[/] [yellow]{config.workers}[/]")
        _console.print(
            f"[bold]翻译模式:[/] [yellow]"
            f"{'🚀 优化模式（连接池+质量验证）' if config.use_optimized else '标准模式'}[/]"
        )
        if config.use_optimized:
            _console.print(f"[bold]质量阈值:[/] [yellow]{config.quality_threshold:.1f}[/]")
        
        gpu_info = get_gpu_info()
        if gpu_info:
            _console.print(f"[bold]GPU 状态:[/] [green]{gpu_info}[/]")
        else:
            _console.print("[bold]GPU 状态:[/] [yellow]未检测到 NVIDIA GPU[/]")
        _console.print("[bold cyan]═══════════════════════════════════════[/]\n")
    else:
        print(f"\n模型: {config.model}")
        print(f"并发线程: {config.workers}")
        print(
            f"翻译模式: "
            f"{'🚀 优化模式（连接池+质量验证）' if config.use_optimized else '标准模式'}"
        )
        if config.use_optimized:
            print(f"质量阈值: {config.quality_threshold:.1f}")
        
        gpu_info = get_gpu_info()
        if gpu_info:
            print(f"GPU 状态: {gpu_info}")
        print()
    
    # 处理文件
    for i, f in enumerate(files, 1):
        of = out_dir / f.name
        rj = out_dir / (f.stem + "_rejects.tsv")
        
        if _console:
            _console.print(f"[bold green]▶ [{i}/{len(files)}][/] {f.name}")
        else:
            print(f"\n▶ [{i}/{len(files)}] 翻译: {f.name} -> {of.name}")
        
        # 根据模式选择处理函数
        if config.use_optimized:
            process_optimized(f, of, rj, config)
        else:
            processor = TranslationProcessor(config)
            processor.process_standard(f, of, rj)
        
        if _console:
            _console.print(f"  [green]✓[/] 完成: {of.name}\n")
    
    if _console:
        _console.print(f"[bold green]✓ 全部完成![/] 结果保存到: [cyan]{out_dir}[/]\n")
    else:
        print(f"\n✓ 全部完成! 结果保存到: {out_dir}")


if __name__ == "__main__":
    main()
