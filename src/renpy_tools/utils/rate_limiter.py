"""
三级速率限制器 — RPM / RPS / TPM

借鉴 RenpyTranslator 的 OpenAI 速率限制方案，实现线程安全的三级限流：
- RPM (Requests Per Minute): 每分钟请求数
- RPS (Requests Per Second): 每秒请求数
- TPM (Tokens Per Minute): 每分钟 Token 数

使用方式:
    limiter = RateLimiter(rpm=60, rps=3, tpm=90000)
    limiter.acquire(estimated_tokens=500)  # 阻塞直到可用
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict
from dataclasses import dataclass


@dataclass
class RateLimiterConfig:
    """速率限制配置"""
    rpm: int = 60       # 每分钟请求数上限
    rps: int = 3        # 每秒请求数上限
    tpm: int = 90000    # 每分钟 Token 数上限


class RateLimiter:
    """线程安全的三级速率限制器"""

    def __init__(self, rpm: int = 60, rps: int = 3, tpm: int = 90000):
        self._rpm = rpm
        self._rps = rps
        self._tpm = tpm
        self._lock = threading.Lock()
        # 按分钟/秒统计
        self._minute_counts: dict[str, int] = defaultdict(int)
        self._second_counts: dict[int, int] = defaultdict(int)
        self._token_count = 0
        self._token_minute = ""

    def acquire(self, estimated_tokens: int = 0) -> None:
        """获取许可，必要时阻塞等待

        Args:
            estimated_tokens: 本次请求预估消耗的 Token 数
        """
        with self._lock:
            self._wait_rpm()
            self._wait_rps()
            self._wait_tpm(estimated_tokens)

            # 记录本次请求
            minute_key = time.strftime("%H:%M")
            second_key = int(time.time())
            self._minute_counts[minute_key] += 1
            self._second_counts[second_key] += 1

            if self._token_minute != minute_key:
                self._token_minute = minute_key
                self._token_count = 0
            self._token_count += estimated_tokens

    def _wait_rpm(self) -> None:
        """RPM 限流检查"""
        if self._rpm <= 0:
            return
        minute_key = time.strftime("%H:%M")
        if self._minute_counts[minute_key] >= self._rpm:
            wait = 61 - time.localtime().tm_sec
            self._lock.release()
            time.sleep(max(wait, 1))
            self._lock.acquire()
            self._minute_counts.clear()

    def _wait_rps(self) -> None:
        """RPS 限流检查"""
        if self._rps <= 0:
            return
        second_key = int(time.time())
        if self._second_counts[second_key] >= self._rps:
            self._lock.release()
            time.sleep(1.05)
            self._lock.acquire()
            # 清理旧的秒级数据
            current = int(time.time())
            stale = [k for k in self._second_counts if k < current - 2]
            for k in stale:
                del self._second_counts[k]

    def _wait_tpm(self, tokens: int) -> None:
        """TPM 限流检查"""
        if self._tpm <= 0:
            return
        minute_key = time.strftime("%H:%M")
        if self._token_minute != minute_key:
            self._token_minute = minute_key
            self._token_count = 0

        if self._token_count + tokens >= self._tpm:
            wait = 61 - time.localtime().tm_sec
            self._lock.release()
            time.sleep(max(wait, 1))
            self._lock.acquire()
            self._minute_counts.clear()
            self._token_count = 0
            self._token_minute = time.strftime("%H:%M")

    def reset(self) -> None:
        """重置所有计数器"""
        with self._lock:
            self._minute_counts.clear()
            self._second_counts.clear()
            self._token_count = 0
            self._token_minute = ""
