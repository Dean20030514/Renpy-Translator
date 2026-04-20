#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Custom translation plugin loader — in-process + sandboxed subprocess modes.

Split from ``core/api_client.py`` in round 40 as one of four pre-existing
> 800-line source files flagged by HANDOFF r39→40.  The plugin-loading
surface (``_load_custom_engine`` for legacy ``importlib`` mode +
``_SubprocessPluginClient`` for round 28 S-H-4 sandbox mode) is a
self-contained slice — ~320 lines around a clear concern (how a
third-party plugin is loaded and talked to) — so extracting it keeps
``api_client.py`` under the CLAUDE.md 800-line soft limit without
touching provider dispatch or the APIClient core.

Public API is re-exported from :mod:`core.api_client` so existing
callers / tests (``tests/test_custom_engine.py`` imports both symbols
by the old name) continue to work unchanged.

Two plugin modes:

1. **``importlib`` (legacy, :func:`_load_custom_engine`)**: plugin
   module is loaded directly into the host process.  Fast but shares
   the host's heap and file descriptors.  The plugin module must
   expose ``translate_batch(system_prompt, user_prompt)`` or the
   per-item ``translate(text, source_lang, target_lang)``.

2. **Subprocess sandbox (round 28 S-H-4,
   :class:`_SubprocessPluginClient`)**: plugin runs in a separate
   interpreter invoked with ``python -u <plugin>.py --plugin-serve``.
   Host and plugin exchange JSONL messages over stdin / stdout.
   Reuses a single child across every chunk translation so the
   startup cost is amortised.  10 KB stderr read cap (round 30)
   prevents a pathological plugin from OOMing the host with an
   exception-message flood.
"""

from __future__ import annotations

import atexit
import importlib.util
import json
import logging
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


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
        # ``_proc`` is assigned before ``atexit.register`` so that if the
        # Popen call itself raises (e.g. the interpreter binary vanished),
        # the finalizer has nothing to tear down.  If any post-launch step
        # raises, the try/except below guarantees we kill the child before
        # propagating so a half-initialised instance never leaks a process.
        self._proc = None

        try:
            # Launch the subprocess.  ``-u`` ensures unbuffered stdout so
            # every response line reaches us without waiting for a full
            # buffer.
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
            # Best-effort cleanup when the process interpreter exits without
            # an explicit close() call (e.g. KeyboardInterrupt paths).
            atexit.register(self._shutdown_quietly)
        except BaseException:
            # Round 30 robustness: if we managed to start the child but
            # something else (e.g. ``atexit.register``) raised before we
            # finished initialising, kill the orphaned process so it
            # doesn't linger.
            if self._proc is not None and self._proc.poll() is None:
                try:
                    self._proc.kill()
                    self._proc.wait(timeout=2)
                except (OSError, subprocess.TimeoutExpired):
                    pass
            raise

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
                # Round 30 bound: cap stderr read at 10 KB so a pathological
                # plugin spewing megabytes of text on exit cannot OOM the
                # host.  Only the tail is shown in the error anyway.
                stderr = (self._proc.stderr.read(10_000) or "")[-600:]
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
