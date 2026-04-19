#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""API 客户端 — 支持 xAI/OpenAI/DeepSeek/Claude/Gemini/自定义引擎"""

from __future__ import annotations

import atexit
import importlib.util
import json
import logging
import re
import subprocess
import sys
import time
import threading
from dataclasses import dataclass, field
from pathlib import Path
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


# ============================================================
# Custom engine plugin loader
# ============================================================

_CUSTOM_ENGINES_DIR = "custom_engines"


def _load_custom_engine(module_name: str) -> Any:
    """Load a custom translation engine module from ``custom_engines/`` directory.

    Security: Only loads from the ``custom_engines/`` subdirectory relative to the
    project root (the directory containing ``main.py``).  Arbitrary paths are
    rejected.  Users should only use modules from trusted sources.

    The module must implement at least one of:
        - ``translate_batch(system_prompt, user_prompt) -> str | list[dict]``
          (preferred — receives the full prompt, returns JSON array)
        - ``translate(text, source_lang, target_lang) -> str``
          (fallback — called per-item, results assembled into JSON array)

    Args:
        module_name: Module filename (e.g. ``"my_engine.py"`` or ``"my_engine"``).

    Returns:
        Loaded module object.

    Raises:
        RuntimeError: If the module cannot be found or loaded.
    """
    if not module_name:
        raise RuntimeError(
            "自定义引擎需要指定模块名: --custom-module <模块名>\n"
            f"模块文件应放在项目目录的 {_CUSTOM_ENGINES_DIR}/ 子目录下"
        )

    # Resolve to custom_engines/ under the project root
    project_root = Path(__file__).resolve().parent.parent
    engines_dir = project_root / _CUSTOM_ENGINES_DIR

    # Strip .py extension if present
    if module_name.endswith(".py"):
        module_name = module_name[:-3]

    # Security: reject path separators — must be a simple filename
    if "/" in module_name or "\\" in module_name or ".." in module_name:
        raise RuntimeError(
            f"自定义引擎模块名不能包含路径分隔符: '{module_name}'\n"
            f"请将模块文件放在 {engines_dir}/ 目录下，然后只传文件名"
        )

    module_path = engines_dir / f"{module_name}.py"
    if not module_path.is_file():
        raise RuntimeError(
            f"自定义引擎模块未找到: {module_path}\n"
            f"请在 {engines_dir}/ 目录下创建 {module_name}.py 文件"
        )

    spec = importlib.util.spec_from_file_location(f"custom_engines.{module_name}", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载自定义引擎模块: {module_path}")

    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    # Validate interface
    if not hasattr(mod, "translate_batch") and not hasattr(mod, "translate"):
        raise RuntimeError(
            f"自定义引擎模块 {module_name} 必须实现 translate_batch() 或 translate() 函数"
        )

    logger.info("[API] 已加载自定义引擎: %s", module_path)
    return mod


class _SubprocessPluginClient:
    """Long-running subprocess wrapper for custom translation plugins.

    Round 28 S-H-4: when ``--sandbox-plugin`` is enabled, custom plugins are
    invoked through an out-of-process JSONL protocol rather than loaded via
    ``importlib``.  That denies the plugin direct access to the host's
    environment variables, file descriptors, and heap, while keeping
    latency acceptable by reusing a single child interpreter across every
    chunk translation.

    Protocol (newline-delimited JSON, one object per line):

    * Request (host → plugin):
      ``{"request_id": <int>, "system_prompt": <str>, "user_prompt": <str>}``
    * Response (plugin → host):
      ``{"request_id": <int>, "response": <str|null>, "error": <str|null>}``
    * Shutdown (host → plugin): ``{"request_id": -1}`` followed by stdin close.

    The plugin module's ``__main__`` block is responsible for reading
    stdin, dispatching to ``translate_batch`` / ``translate``, and writing
    the JSON line to stdout (flushed).  ``custom_engines/example_echo.py``
    demonstrates the canonical shape; new plugins should follow the same
    pattern so they work in either mode.
    """

    _SHUTDOWN_REQUEST_ID = -1

    def __init__(
        self,
        module_name: str,
        *,
        timeout: float = 180.0,
    ) -> None:
        if not module_name:
            raise RuntimeError(
                "自定义引擎需要指定模块名: --custom-module <模块名>\n"
                f"模块文件应放在项目目录的 {_CUSTOM_ENGINES_DIR}/ 子目录下"
            )

        if module_name.endswith(".py"):
            module_name = module_name[:-3]
        if "/" in module_name or "\\" in module_name or ".." in module_name:
            raise RuntimeError(
                f"自定义引擎模块名不能包含路径分隔符: '{module_name}'"
            )

        project_root = Path(__file__).resolve().parent.parent
        engines_dir = project_root / _CUSTOM_ENGINES_DIR
        module_path = engines_dir / f"{module_name}.py"
        if not module_path.is_file():
            raise RuntimeError(
                f"自定义引擎模块未找到: {module_path}\n"
                f"请在 {engines_dir}/ 目录下创建 {module_name}.py 文件"
            )

        self._module_path = module_path
        self._timeout = timeout
        self._request_id = 0
        self._lock = threading.Lock()
        self._closed = False

        # Launch the subprocess.  ``-u`` ensures unbuffered stdout so every
        # response line reaches us without waiting for a full buffer.
        self._proc = subprocess.Popen(
            [sys.executable, "-u", str(module_path), "--plugin-serve"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(project_root),
            text=True,
            encoding="utf-8",
            # Line-buffered on the host side so our writes flush per line.
            bufsize=1,
        )
        logger.info(
            "[API] 沙箱模式启动自定义引擎子进程: %s (pid=%s)",
            module_path, self._proc.pid,
        )
        # Best-effort cleanup when the process interpreter exits without an
        # explicit close() call (e.g. KeyboardInterrupt paths).
        atexit.register(self._shutdown_quietly)

    # -----------------------------------------------------------------
    # Public duck-typed interface mirroring a loaded plugin module.
    # ``APIClient._call_custom`` checks ``hasattr(mod, "translate_batch")``
    # and calls it with the raw prompts — presenting the same method
    # here means the sandbox path reuses the legacy batch-dispatch code.
    # -----------------------------------------------------------------

    def translate_batch(self, system_prompt: str, user_prompt: str) -> str:
        return self._call(system_prompt, user_prompt)

    def _call(self, system_prompt: str, user_prompt: str) -> str:
        if self._closed:
            raise RuntimeError("自定义引擎子进程已关闭，无法继续调用")
        if self._proc.poll() is not None:
            stderr = ""
            try:
                stderr = (self._proc.stderr.read() or "")[-600:]
            except (OSError, ValueError):
                pass
            raise RuntimeError(
                f"自定义引擎子进程意外退出 (exit={self._proc.returncode}): {stderr}"
            )

        with self._lock:
            self._request_id += 1
            req_id = self._request_id
            request = {
                "request_id": req_id,
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
            }
            try:
                line = json.dumps(request, ensure_ascii=False) + "\n"
                self._proc.stdin.write(line)
                self._proc.stdin.flush()
            except (BrokenPipeError, OSError) as e:
                raise RuntimeError(f"自定义引擎子进程写入失败: {e}") from e

            # Single-line read; the protocol guarantees one response per
            # request delimited by ``\n``.  The host-side timeout is the
            # APIConfig timeout; if the plugin hangs we kill the process.
            response_line = self._read_response_line(req_id)
            try:
                response = json.loads(response_line)
            except (json.JSONDecodeError, ValueError) as e:
                raise RuntimeError(
                    f"自定义引擎子进程返回非法 JSON: {response_line[:200]!r}"
                ) from e

            if response.get("request_id") != req_id:
                raise RuntimeError(
                    f"自定义引擎子进程响应乱序: expected request_id={req_id}, "
                    f"got {response.get('request_id')!r}"
                )
            error = response.get("error")
            if error:
                raise RuntimeError(f"自定义引擎子进程报错: {error}")
            payload = response.get("response")
            if payload is None:
                return ""
            if isinstance(payload, str):
                return payload
            # If the plugin returns list[dict] through the JSON field we
            # re-serialise it so the caller's ``json.loads`` round-trip
            # still works.
            return json.dumps(payload, ensure_ascii=False)

    def _read_response_line(self, req_id: int) -> str:
        """Read a single line from the subprocess stdout with timeout."""
        # ``TimeoutExpired`` would only work with ``communicate``; here we
        # emulate a deadline by reading in a helper thread and joining
        # with timeout.  This keeps the implementation pure-stdlib.
        result: list[str] = []
        error: list[BaseException] = []

        def _reader() -> None:
            try:
                line = self._proc.stdout.readline()
                if line == "":
                    error.append(EOFError("plugin stdout closed before response"))
                    return
                result.append(line.rstrip("\n"))
            except BaseException as e:  # noqa: BLE001 - re-raise on main thread
                error.append(e)

        t = threading.Thread(target=_reader, daemon=True)
        t.start()
        t.join(self._timeout)
        if t.is_alive():
            # Plugin stuck — kill the subprocess so we don't leak it.
            # Wait briefly so poll() reflects the terminated state for any
            # diagnostic code the caller runs after catching this error.
            try:
                self._proc.kill()
            except OSError:
                pass
            try:
                self._proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                pass
            raise RuntimeError(
                f"自定义引擎子进程响应超时 (>{self._timeout}s, request_id={req_id})"
            )
        if error:
            raise RuntimeError(f"读取自定义引擎子进程响应失败: {error[0]}") from error[0]
        return result[0] if result else ""

    # -----------------------------------------------------------------
    # Lifecycle
    # -----------------------------------------------------------------

    def close(self) -> None:
        """Send the shutdown sentinel and terminate the subprocess.

        Safe to call multiple times.  Catches every subprocess-related
        error so repeated shutdowns never raise.
        """
        if self._closed:
            return
        self._closed = True
        try:
            if self._proc.poll() is None and self._proc.stdin and not self._proc.stdin.closed:
                self._proc.stdin.write(
                    json.dumps({"request_id": self._SHUTDOWN_REQUEST_ID}) + "\n"
                )
                self._proc.stdin.flush()
                self._proc.stdin.close()
        except (BrokenPipeError, OSError, ValueError):
            pass
        try:
            self._proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            try:
                self._proc.kill()
            except OSError:
                pass
            try:
                self._proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                pass

    def _shutdown_quietly(self) -> None:
        """``atexit`` hook — swallow all errors so interpreter exit is clean."""
        try:
            self.close()
        except BaseException:  # noqa: BLE001
            pass

    def __del__(self) -> None:  # pragma: no cover - finaliser
        try:
            self.close()
        except BaseException:  # noqa: BLE001
            pass


@dataclass
class APIConfig:
    """API 连接配置"""
    provider: str       # xai, openai, deepseek, claude, gemini, custom
    api_key: str
    model: str = ""
    rpm: int = 0        # 每分钟请求数（0=不限）
    rps: int = 0        # 每秒请求数（0=不限）
    timeout: float = 180.0   # 整文件翻译需要更长超时
    temperature: float = 0.1  # 低温保证一致性
    max_retries: int = 5
    max_response_tokens: int = 32768
    custom_module: str = ""  # 自定义翻译引擎模块名（仅 provider="custom" 时使用）
    # Round 28 S-H-4 opt-in subprocess sandbox for custom plugins.
    # Default False keeps the historical ``importlib`` fast-path; passing
    # ``--sandbox-plugin`` on the CLI (plumbed through by every caller
    # that propagates ``custom_module``) launches the plugin in a
    # long-running subprocess that talks JSONL over stdin/stdout,
    # denying the plugin in-process access to env vars, file system,
    # and network.
    sandbox_plugin: bool = False
    # 持久 HTTPS 连接复用（True=thread-local pool, False=每次新建 urllib 连接）。
    # 默认启用：典型游戏 600 次 API 调用可节省 ~90s 的 TCP+TLS 握手时间。
    # 若遇到兼容问题可通过配置文件设置 "use_connection_pool": false 回退。
    use_connection_pool: bool = True

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
            'custom': ('', 'custom'),
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

    def to_dict(self) -> dict:
        """Structured usage snapshot for JSON reports.

        Companion to :meth:`summary`, which returns a human-readable log
        string. Use :meth:`to_dict` when embedding usage in a JSON document
        (e.g. ``pipeline_report.json``) — the string form includes pricing
        disclaimers that would break strict JSON consumption.
        """
        _price_in, _price_out, exact = get_pricing(self.provider, self.model)
        return {
            "provider": self.provider,
            "model": self.model,
            "total_requests": self.total_requests,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "estimated_cost_usd": round(self.estimated_cost, 4),
            "pricing_exact": exact,
        }


class RateLimiter:
    """线程安全速率限制器（不在锁内 sleep）"""

    # Round 26 PF-H-4: cleanup of stale per-second / per-minute buckets
    # runs every N acquisitions instead of every call.  At 5 rps × 64 that
    # caps stale-bucket accumulation at ~13 seconds of history — well under
    # the 5-second and 1-minute relevance windows — while eliminating the
    # per-call ``[k for k in dict]`` scan under the lock.
    _CLEANUP_INTERVAL = 64

    def __init__(self, rpm: int = 0, rps: int = 0):
        self._rpm = rpm
        self._rps = rps
        self._lock = threading.Lock()
        self._minute_counts: dict[str, int] = defaultdict(int)
        self._second_counts: dict[int, int] = defaultdict(int)
        self._cleanup_counter: int = 0

    def acquire(self) -> None:
        while True:
            wait_time = 0.0
            with self._lock:
                if self._rps > 0 and self._second_counts.get(int(time.time()), 0) >= self._rps:
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

                    # Batch cleanup: drop stale buckets every _CLEANUP_INTERVAL
                    # acquisitions.  Staleness thresholds: 5 s for second
                    # counters, current-minute-only for minute counters.
                    self._cleanup_counter += 1
                    if self._cleanup_counter >= self._CLEANUP_INTERVAL:
                        self._cleanup_counter = 0
                        stale_sec = [k for k in self._second_counts if k < sec - 5]
                        for k in stale_sec:
                            del self._second_counts[k]
                        old_min = [k for k in self._minute_counts if k != minute]
                        for k in old_min:
                            del self._minute_counts[k]
                    return  # 获取成功
            # 在锁外等待
            time.sleep(wait_time)


class APIClient:
    """API 客户端，支持多提供商（含自定义引擎插件）"""

    def __init__(self, config: APIConfig):
        self.config = config
        self._limiter = RateLimiter(config.rpm, config.rps) if (config.rpm or config.rps) else None
        self.usage = UsageStats(config.provider, config.model)
        self._custom_module = None
        if config.provider.lower() == "custom":
            if config.sandbox_plugin:
                # Round 28 S-H-4: opt-in subprocess sandbox.  The returned
                # ``_SubprocessPluginClient`` is duck-typed as a plugin
                # module (exposes ``translate_batch``) so the rest of this
                # file continues to work unchanged.
                self._custom_module = _SubprocessPluginClient(
                    config.custom_module, timeout=config.timeout,
                )
            else:
                self._custom_module = _load_custom_engine(config.custom_module)
        # 持久连接池（仅 HTTPS 端点；custom provider 不走 HTTP 所以也不需要）
        self._pool = None
        if config.use_connection_pool and config.provider.lower() != "custom":
            from core.http_pool import HTTPSConnectionPool
            self._pool = HTTPSConnectionPool(timeout=config.timeout)

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

        # 自定义引擎：直接调用用户模块，不走 HTTP 重试逻辑
        if provider == "custom" and self._custom_module is not None:
            return self._call_custom(system_prompt, user_prompt)

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

        if self._pool is not None:
            raw = self._pool.post(self.config.endpoint, data, headers)
            result = json.loads(raw.decode('utf-8'))
        else:
            from core.http_pool import read_bounded
            req = urlreq.Request(self.config.endpoint, data=data, headers=headers)
            with urlreq.urlopen(req, timeout=self.config.timeout) as resp:
                result = json.loads(read_bounded(resp).decode('utf-8'))

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
            # 尝试多种 JSON 数组开头模式（direct-mode: [{"line", tl-mode: [{"id"）
            bracket_start = -1
            for pattern in ('[{"line"', '[{"id"', '[{"original"', '[{'):
                pos = reasoning.rfind(pattern)
                if pos >= 0:
                    bracket_start = pos
                    break
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

        if self._pool is not None:
            raw = self._pool.post(self.config.endpoint, data, headers)
            result = json.loads(raw.decode('utf-8'))
        else:
            from core.http_pool import read_bounded
            req = urlreq.Request(self.config.endpoint, data=data, headers=headers)
            with urlreq.urlopen(req, timeout=self.config.timeout) as resp:
                result = json.loads(read_bounded(resp).decode('utf-8'))

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

    def _call_custom(self, system_prompt: str, user_prompt: str) -> str:
        """调用自定义翻译引擎模块。

        优先使用 ``translate_batch(items, source_lang, target_lang)`` 批量接口。
        如果模块未实现批量接口，降级为 ``translate(text, source_lang, target_lang)``
        逐条翻译，结果包装为 JSON 数组字符串返回。
        """
        mod = self._custom_module
        if mod is None:
            raise RuntimeError("自定义引擎模块未加载")

        if hasattr(mod, "translate_batch"):
            # 批量接口：直接传 user_prompt（JSON 数组），返回 JSON 数组字符串
            result = mod.translate_batch(system_prompt, user_prompt)
            if isinstance(result, str):
                return result
            # 如果返回的是 list[dict]，序列化为 JSON 字符串
            return json.dumps(result, ensure_ascii=False)

        if hasattr(mod, "translate"):
            # 单句降级：解析 user_prompt 中的条目，逐条调用 translate()
            try:
                items = json.loads(user_prompt) if user_prompt.strip().startswith("[") else []
            except (json.JSONDecodeError, ValueError):
                items = []

            if not items:
                # 非 JSON 数组格式，直接传整个 prompt
                return mod.translate(user_prompt, "en", self.config.model or "zh")

            results = []
            for item in items:
                original = item.get("original", item.get("text", ""))
                if not original:
                    continue
                translated = mod.translate(original, "en", self.config.model or "zh")
                entry = dict(item)
                entry["zh"] = translated
                results.append(entry)
            return json.dumps(results, ensure_ascii=False)

        raise RuntimeError(
            f"自定义引擎模块必须实现 translate_batch() 或 translate() 函数"
        )

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

        # 5b. tl-mode: {"id": "xxx", "original": "...", "zh": "..."}
        obj_re_tl = re.compile(
            r'\{\s*"id"\s*:\s*"(?:[^"\\]|\\.)*"\s*,\s*"original"\s*:\s*"(?:[^"\\]|\\.)*"\s*,\s*"zh"\s*:\s*"(?:[^"\\]|\\.)*"\s*\}'
        )
        matches_tl = obj_re_tl.findall(text)
        if matches_tl:
            results = []
            for m in matches_tl:
                try:
                    results.append(json.loads(m))
                except json.JSONDecodeError:
                    continue
            if results:
                return results

        # 6. 尝试容忍字段顺序变化（部分模型可能调换字段顺序）
        obj_re2 = re.compile(
            r'\{[^{}]*"(?:line|id)"\s*:\s*(?:\d+|"[^"]*")[^{}]*"zh"\s*:\s*"(?:[^"\\]|\\.)*"[^{}]*\}'
        )
        matches2 = obj_re2.findall(text)
        if matches2:
            results = []
            for m in matches2:
                try:
                    obj = json.loads(m)
                    if ('line' in obj or 'id' in obj) and 'zh' in obj:
                        results.append(obj)
                except json.JSONDecodeError:
                    continue
            if results:
                return results

        logger.error(f"无法解析 AI 响应为 JSON 数组，响应前200字符: {text[:200]}")
        return []
