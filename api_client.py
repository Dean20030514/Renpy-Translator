#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""API 客户端 — 支持 xAI/OpenAI/DeepSeek/Claude"""

from __future__ import annotations

import json
import logging
import re
import time
import threading
from dataclasses import dataclass, field
from typing import Optional, Any
from urllib import request as urlreq
from urllib import error as urlerr
from collections import defaultdict

logger = logging.getLogger(__name__)

_USER_AGENT = "RenpyFileTranslator/1.0"

# ====== 定价表 (每百万 token, 美元) ======

# 按模型精确定价 (input, output)
_MODEL_PRICING = {
    # xAI / Grok — https://docs.x.ai/docs/models
    'grok-4-1-fast-reasoning':             (0.20, 0.50),
    'grok-4-1-fast-non-reasoning':         (0.20, 0.50),
    'grok-code-fast-1':                    (0.20, 1.50),
    'grok-4.20-multi-agent-beta-0309':     (2.00, 6.00),
    'grok-4.20-beta-0309-reasoning':       (2.00, 6.00),
    'grok-4.20-beta-0309-non-reasoning':   (2.00, 6.00),
    # OpenAI
    'gpt-4o-mini':       (0.15, 0.60),
    'gpt-4o':            (2.50, 10.00),
    'gpt-4.1-mini':      (0.40, 1.60),
    'gpt-4.1-nano':      (0.10, 0.40),
    'gpt-4.1':           (2.00, 8.00),
    'o3-mini':           (1.10, 4.40),
    'o1-mini':           (1.10, 4.40),
    'o1':                (15.00, 60.00),
    'o3':                (2.00, 8.00),
    'o4-mini':           (1.10, 4.40),
    # DeepSeek
    'deepseek-chat':     (0.14, 0.28),
    'deepseek-reasoner': (0.55, 2.19),
    # Claude
    'claude-sonnet-4-20250514':   (3.00, 15.00),
    'claude-opus-4-20250514':     (15.00, 75.00),
    'claude-3-5-haiku-20241022':  (0.80, 4.00),
    'claude-3-5-sonnet-20241022': (3.00, 15.00),
    # Gemini
    'gemini-2.5-flash':  (0.15, 0.60),
    'gemini-2.5-pro':    (1.25, 10.00),
    'gemini-2.0-flash':  (0.10, 0.40),
}

# 按提供商兜底（用中等价格，防止低估）
_PROVIDER_PRICING = {
    'xai':      (0.20, 0.50),
    'grok':     (0.20, 0.50),
    'openai':   (2.50, 10.00),
    'deepseek': (0.14, 0.28),
    'claude':   (3.00, 15.00),
    'gemini':   (0.15, 0.60),
}


def get_pricing(provider: str, model: str) -> tuple[float, float, bool]:
    """查询定价：先精确匹配模型名，再按模型家族模糊匹配，最后兜底到提供商。

    Returns:
        (input_price, output_price, is_exact)
        is_exact=True 表示从 _MODEL_PRICING 精确匹配到
    """
    model_lower = model.lower()

    # 1. 精确匹配
    if model_lower in _MODEL_PRICING:
        return (*_MODEL_PRICING[model_lower], True)

    # 2. 前缀匹配 — 处理带日期后缀的模型名（如 grok-3-mini-fast-20250301）
    for key in sorted(_MODEL_PRICING, key=len, reverse=True):
        if model_lower.startswith(key):
            return (*_MODEL_PRICING[key], True)

    # 3. 模型家族模糊匹配（去除版本号/日期后缀再试）
    #    例如 grok-4-1-fast-reasoning → 去掉 -reasoning → grok-4-1-fast
    parts = model_lower.split('-')
    for n in range(len(parts) - 1, 0, -1):
        prefix = '-'.join(parts[:n])
        if prefix in _MODEL_PRICING:
            return (*_MODEL_PRICING[prefix], True)

    # 4. 兜底到提供商
    p = _PROVIDER_PRICING.get(provider.lower(), (3.00, 15.00))
    return (*p, False)


def is_reasoning_model(model: str) -> bool:
    """检测是否为推理模型（会产生大量 thinking tokens 的模型）"""
    name = model.lower()
    # 显式包含推理关键词
    if any(kw in name for kw in ('reasoning', 'think', 'reasoner')):
        return True
    # OpenAI o 系列推理模型
    if re.match(r'^o[1-9]', name):
        return True
    return False


@dataclass
class APIConfig:
    """API 连接配置"""
    provider: str       # xai, openai, deepseek, claude
    api_key: str
    model: str = ""
    rpm: int = 0        # 每分钟请求数（0=不限）
    rps: int = 0        # 每秒请求数（0=不限）
    timeout: float = 180.0   # 整文件翻译需要更长超时
    temperature: float = 0.1  # 低温保证一致性
    max_retries: int = 5
    max_response_tokens: int = 32768

    # 自动填充
    endpoint: str = field(init=False, default="")
    _resolved: bool = field(init=False, default=False)

    def __post_init__(self) -> None:
        providers = {
            'xai': ('https://api.x.ai/v1/chat/completions', 'grok-4-1-fast-reasoning'),
            'grok': ('https://api.x.ai/v1/chat/completions', 'grok-4-1-fast-reasoning'),
            'openai': ('https://api.openai.com/v1/chat/completions', 'gpt-4o-mini'),
            'deepseek': ('https://api.deepseek.com/v1/chat/completions', 'deepseek-chat'),
            'claude': ('https://api.anthropic.com/v1/messages', 'claude-sonnet-4-20250514'),
            'gemini': ('https://generativelanguage.googleapis.com/v1beta/chat/completions', 'gemini-2.5-flash'),
        }
        key = self.provider.lower()
        if key in providers:
            self.endpoint, default_model = providers[key]
            if not self.model:
                self.model = default_model
        # 推理模型自动提高 timeout（推理过程耗时较长）
        if is_reasoning_model(self.model) and self.timeout < 300:
            logger.info(f"[API] 推理模型 {self.model} 检测到，timeout 从 {self.timeout}s 提升到 300s")
            self.timeout = 300.0
        self._resolved = True


class UsageStats:
    """API 用量统计"""

    def __init__(self, provider: str = 'xai', model: str = ''):
        self._lock = threading.Lock()
        self.provider = provider
        self.model = model
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_requests = 0

    def record(self, input_tokens: int, output_tokens: int) -> None:
        with self._lock:
            self.total_input_tokens += input_tokens
            self.total_output_tokens += output_tokens
            self.total_requests += 1

    @property
    def estimated_cost(self) -> float:
        price_in, price_out, _ = get_pricing(self.provider, self.model)
        return (self.total_input_tokens * price_in + self.total_output_tokens * price_out) / 1_000_000

    def summary(self) -> str:
        price_in, price_out, exact = get_pricing(self.provider, self.model)
        cost_str = f"${self.estimated_cost:.4f}"
        if not exact:
            cost_str += " (价格未精确匹配，仅供参考)"
        return (f"请求 {self.total_requests} 次 | "
                f"输入 {self.total_input_tokens:,} tokens | "
                f"输出 {self.total_output_tokens:,} tokens | "
                f"估计费用 {cost_str}")


class RateLimiter:
    """线程安全速率限制器（不在锁内 sleep）"""

    def __init__(self, rpm: int = 0, rps: int = 0):
        self._rpm = rpm
        self._rps = rps
        self._lock = threading.Lock()
        self._minute_counts: dict[str, int] = defaultdict(int)
        self._second_counts: dict[int, int] = defaultdict(int)

    def acquire(self) -> None:
        while True:
            wait_time = 0.0
            with self._lock:
                if self._rps > 0:
                    sec = int(time.time())
                    # 清理旧秒
                    stale = [k for k in self._second_counts if k < sec - 5]
                    for k in stale:
                        del self._second_counts[k]
                    if self._second_counts.get(sec, 0) >= self._rps:
                        wait_time = 1.05
                if wait_time == 0 and self._rpm > 0:
                    minute = time.strftime("%H:%M")
                    if self._minute_counts.get(minute, 0) >= self._rpm:
                        wait_time = max(61 - time.localtime().tm_sec, 1)
                if wait_time == 0:
                    # 可以通过，记录计数
                    sec = int(time.time())
                    self._second_counts[sec] = self._second_counts.get(sec, 0) + 1
                    minute = time.strftime("%H:%M")
                    self._minute_counts[minute] = self._minute_counts.get(minute, 0) + 1
                    # 清理旧分钟
                    old = [k for k in self._minute_counts if k != minute]
                    for k in old:
                        del self._minute_counts[k]
                    return  # 获取成功
            # 在锁外等待
            time.sleep(wait_time)


class APIClient:
    """API 客户端，支持多提供商"""

    def __init__(self, config: APIConfig):
        self.config = config
        self._limiter = RateLimiter(config.rpm, config.rps) if (config.rpm or config.rps) else None
        self.usage = UsageStats(config.provider, config.model)

    def translate(self, system_prompt: str, user_prompt: str) -> list[dict]:
        """发送翻译请求，返回解析后的 JSON 数组

        Returns:
            [{"line": N, "original": "...", "zh": "..."}, ...]
        """
        if self._limiter:
            self._limiter.acquire()

        raw = self._call_api(system_prompt, user_prompt)
        result = self._parse_json_response(raw)

        # 如果原始响应非空但解析失败，重试一次（附加格式强调）
        if not result and len(raw.strip()) > 20:
            logger.warning("JSON 解析失败，重试中...")
            if self._limiter:
                self._limiter.acquire()
            retry_suffix = "\n\n⚠️ 你必须只返回纯 JSON 数组，不要包含任何其他文字、解释或 markdown 标记。"
            raw = self._call_api(system_prompt, user_prompt + retry_suffix)
            result = self._parse_json_response(raw)
            if not result:
                logger.warning("重试后仍无法解析，跳过该块")

        return result

    def _call_api(self, system_prompt: str, user_prompt: str) -> str:
        """调用 API，返回原始响应文本"""
        provider = self.config.provider.lower()

        import random

        for attempt in range(1, self.config.max_retries + 1):
            try:
                if provider == 'claude':
                    return self._call_claude(system_prompt, user_prompt)
                else:
                    return self._call_openai_format(system_prompt, user_prompt)
            except urlerr.HTTPError as e:
                status = e.code
                body = ""
                retry_after = 0
                try:
                    # 优先使用服务端返回的 Retry-After header
                    ra = e.headers.get("Retry-After", "") if e.headers else ""
                    if ra and ra.isdigit():
                        retry_after = int(ra)
                except (AttributeError, KeyError, ValueError):
                    pass
                try:
                    body = e.read().decode('utf-8', errors='replace')[:500]
                except (AttributeError, OSError, ValueError):
                    pass

                if status == 404:
                    raise RuntimeError(
                        f"API 404: 模型 '{self.config.model}' 不存在或已下线，"
                        f"请检查 --model 参数是否正确 (body: {body[:200]})"
                    )
                elif status == 401:
                    raise RuntimeError(
                        f"API 401: 认证失败，请检查 --api-key 是否正确 (provider: {self.config.provider})"
                    )
                elif status == 429:
                    base = retry_after if retry_after > 0 else min(2 ** attempt * 5, 60)
                    jitter = random.uniform(0, min(base * 0.3, 5))
                    wait = base + jitter
                    logger.warning(f"429 限速，等待 {wait:.1f}s 后重试 ({attempt}/{self.config.max_retries})")
                    time.sleep(wait)
                    continue
                elif status >= 500:
                    base = min(2 ** attempt * 3, 60)
                    jitter = random.uniform(0, min(base * 0.3, 5))
                    wait = base + jitter
                    logger.warning(f"{status} 服务端错误，等待 {wait:.1f}s 后重试 ({attempt}/{self.config.max_retries})")
                    time.sleep(wait)
                    continue
                else:
                    raise RuntimeError(f"API {status} 错误: {body}")
            except (urlerr.URLError, OSError, TimeoutError) as e:
                if attempt < self.config.max_retries:
                    base = min(2 ** attempt * 3, 60)
                    jitter = random.uniform(0, min(base * 0.3, 5))
                    wait = base + jitter
                    logger.warning(f"网络错误: {e}, 等待 {wait:.1f}s 后重试 ({attempt}/{self.config.max_retries})")
                    time.sleep(wait)
                    continue
                raise

        raise RuntimeError(f"API 调用失败，已重试 {self.config.max_retries} 次")

    def _call_openai_format(self, system_prompt: str, user_prompt: str) -> str:
        """OpenAI 兼容格式 (xAI / OpenAI / DeepSeek)"""
        payload = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_response_tokens,
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.api_key}",
            "User-Agent": _USER_AGENT,
        }
        data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        req = urlreq.Request(self.config.endpoint, data=data, headers=headers)

        with urlreq.urlopen(req, timeout=self.config.timeout) as resp:
            result = json.loads(resp.read().decode('utf-8'))

        # 记录 token 用量
        usage = result.get("usage", {})
        self.usage.record(
            usage.get("prompt_tokens", 0),
            usage.get("completion_tokens", 0),
        )

        choices = result.get("choices") or []
        if not choices:
            logger.warning("[API] 响应中无 choices 字段，返回空内容")
            return ""
        msg = choices[0].get("message", {})
        content = msg.get("content", "")
        # grok reasoning 模型可能有 reasoning_content
        if not content and msg.get("reasoning_content"):
            reasoning = msg["reasoning_content"]
            bracket_start = reasoning.rfind('[{"line"')
            if bracket_start >= 0:
                bracket_end = reasoning.rfind(']')
                if bracket_end > bracket_start:
                    content = reasoning[bracket_start:bracket_end + 1]
            if not content:
                content = reasoning
        return content or ""

    def _call_claude(self, system_prompt: str, user_prompt: str) -> str:
        """Anthropic Claude 格式"""
        payload = {
            "model": self.config.model,
            "max_tokens": self.config.max_response_tokens,
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": user_prompt},
            ],
            "temperature": self.config.temperature,
        }
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.config.api_key,
            "anthropic-version": "2023-06-01",
            "User-Agent": _USER_AGENT,
        }
        data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        req = urlreq.Request(self.config.endpoint, data=data, headers=headers)

        with urlreq.urlopen(req, timeout=self.config.timeout) as resp:
            result = json.loads(resp.read().decode('utf-8'))

        # 记录 token 用量
        usage = result.get("usage", {})
        self.usage.record(
            usage.get("input_tokens", 0),
            usage.get("output_tokens", 0),
        )

        blocks = result.get("content", [])
        if not blocks:
            return ""
        return blocks[0].get("text", "")

    @staticmethod
    def _parse_json_response(text: str) -> list[dict]:
        """从 AI 响应中提取 JSON 数组

        处理常见格式问题：markdown 代码块、多余文字等
        """
        text = text.strip()

        # 1. 尝试直接解析
        try:
            result = json.loads(text)
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass

        # 2. 从 markdown 代码块提取
        md_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?\s*```', text, re.DOTALL)
        if md_match:
            try:
                result = json.loads(md_match.group(1))
                if isinstance(result, list):
                    return result
            except json.JSONDecodeError:
                pass

        # 3. 找到第一个 [ 和最后一个 ]
        start = text.find('[')
        end = text.rfind(']')
        if start != -1 and end > start:
            try:
                result = json.loads(text[start:end + 1])
                if isinstance(result, list):
                    return result
            except json.JSONDecodeError:
                pass

        # 4. 尝试修复常见 JSON 问题（末尾逗号）
        if start != -1 and end > start:
            fixed = re.sub(r',\s*([}\]])', r'\1', text[start:end + 1])
            try:
                result = json.loads(fixed)
                if isinstance(result, list):
                    return result
            except json.JSONDecodeError:
                pass

        # 5. 逐个提取翻译对象（容错：即使整体 JSON 损坏也能挽救部分结果）
        # 5a. direct-mode: {"line": N, "original": "...", "zh": "..."}
        obj_re = re.compile(
            r'\{\s*"line"\s*:\s*\d+\s*,\s*"original"\s*:\s*"(?:[^"\\]|\\.)*"\s*,\s*"zh"\s*:\s*"(?:[^"\\]|\\.)*"\s*\}'
        )
        matches = obj_re.findall(text)
        if matches:
            results = []
            for m in matches:
                try:
                    results.append(json.loads(m))
                except json.JSONDecodeError:
                    continue
            if results:
                return results

        # 6. 尝试容忍字段顺序变化（部分模型可能调换字段顺序）
        obj_re2 = re.compile(
            r'\{[^{}]*"line"\s*:\s*\d+[^{}]*"zh"\s*:\s*"(?:[^"\\]|\\.)*"[^{}]*\}'
        )
        matches2 = obj_re2.findall(text)
        if matches2:
            results = []
            for m in matches2:
                try:
                    obj = json.loads(m)
                    if 'line' in obj and 'zh' in obj:
                        results.append(obj)
                except json.JSONDecodeError:
                    continue
            if results:
                return results

        logger.error(f"无法解析 AI 响应为 JSON 数组，响应前200字符: {text[:200]}")
        return []
