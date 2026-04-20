#!/usr/bin/env python3
"""Tests for custom translation engine plugin system."""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.api_client import (
    APIConfig,
    APIClient,
    _SubprocessPluginClient,
    _load_custom_engine,
)


# ============================================================
# Module loader tests
# ============================================================

def test_load_example_echo():
    """Load the example_echo engine from custom_engines/."""
    mod = _load_custom_engine("example_echo")
    assert hasattr(mod, "translate_batch")
    assert hasattr(mod, "translate")
    print("[OK] test_load_example_echo")


def test_load_with_py_extension():
    """Load with .py extension stripped automatically."""
    mod = _load_custom_engine("example_echo.py")
    assert hasattr(mod, "translate")
    print("[OK] test_load_with_py_extension")


def test_load_nonexistent_raises():
    """Loading a non-existent module raises RuntimeError."""
    try:
        _load_custom_engine("nonexistent_engine_xyz")
        assert False, "should have raised"
    except RuntimeError as e:
        assert "未找到" in str(e)
    print("[OK] test_load_nonexistent_raises")


def test_load_empty_name_raises():
    """Empty module name raises RuntimeError."""
    try:
        _load_custom_engine("")
        assert False, "should have raised"
    except RuntimeError as e:
        assert "需要指定模块名" in str(e)
    print("[OK] test_load_empty_name_raises")


def test_load_path_traversal_rejected():
    """Path separators in module name are rejected (security)."""
    for name in ["../evil", "foo/bar", "foo\\bar", "..\\evil"]:
        try:
            _load_custom_engine(name)
            assert False, f"should have raised for {name}"
        except RuntimeError as e:
            assert "路径分隔符" in str(e)
    print("[OK] test_load_path_traversal_rejected")


def test_load_no_interface_raises():
    """Module without translate or translate_batch raises RuntimeError."""
    with tempfile.TemporaryDirectory() as td:
        # Create a module with no translate functions
        engines_dir = Path(__file__).resolve().parent.parent / "custom_engines"
        bad_module = engines_dir / "_test_no_interface.py"
        try:
            bad_module.write_text("x = 1\n", encoding="utf-8")
            try:
                _load_custom_engine("_test_no_interface")
                assert False, "should have raised"
            except RuntimeError as e:
                assert "必须实现" in str(e)
        finally:
            bad_module.unlink(missing_ok=True)
    print("[OK] test_load_no_interface_raises")


# ============================================================
# APIConfig tests
# ============================================================

def test_config_custom_provider():
    """APIConfig accepts 'custom' provider."""
    c = APIConfig(provider="custom", api_key="", custom_module="example_echo")
    assert c.provider == "custom"
    assert c.model == "custom"
    assert c.custom_module == "example_echo"
    print("[OK] test_config_custom_provider")


def test_config_custom_module_default():
    """custom_module defaults to empty string."""
    c = APIConfig(provider="xai", api_key="test")
    assert c.custom_module == ""
    print("[OK] test_config_custom_module_default")


# ============================================================
# APIClient custom engine call tests
# ============================================================

def test_client_custom_batch():
    """APIClient with custom provider calls translate_batch."""
    config = APIConfig(provider="custom", api_key="", custom_module="example_echo")
    client = APIClient(config)

    items = [{"line": 1, "original": "Hello"}]
    user_prompt = json.dumps(items, ensure_ascii=False)
    result = client.translate("system prompt", user_prompt)

    assert len(result) == 1
    assert result[0]["zh"] == "[ECHO] Hello"
    print("[OK] test_client_custom_batch")


def test_client_custom_single_fallback():
    """Test custom engine with only translate() (no translate_batch)."""
    # Create a temp module with only translate()
    engines_dir = Path(__file__).resolve().parent.parent / "custom_engines"
    single_module = engines_dir / "_test_single_only.py"
    try:
        single_module.write_text(
            'def translate(text, source_lang, target_lang):\n'
            '    return f"[SINGLE] {text}"\n',
            encoding="utf-8",
        )
        config = APIConfig(provider="custom", api_key="", custom_module="_test_single_only")
        client = APIClient(config)

        items = [{"line": 1, "original": "World"}]
        user_prompt = json.dumps(items, ensure_ascii=False)
        result = client.translate("system", user_prompt)

        assert len(result) == 1
        assert result[0]["zh"] == "[SINGLE] World"
    finally:
        single_module.unlink(missing_ok=True)
    print("[OK] test_client_custom_single_fallback")


def test_client_custom_batch_returns_list():
    """translate_batch returning list[dict] (not string) is serialized correctly."""
    engines_dir = Path(__file__).resolve().parent.parent / "custom_engines"
    list_module = engines_dir / "_test_list_return.py"
    try:
        list_module.write_text(
            'def translate_batch(system_prompt, user_prompt):\n'
            '    import json\n'
            '    items = json.loads(user_prompt)\n'
            '    return [{"line": it.get("line",0), "original": it["original"], "zh": "OK"} for it in items]\n',
            encoding="utf-8",
        )
        config = APIConfig(provider="custom", api_key="", custom_module="_test_list_return")
        client = APIClient(config)

        items = [{"line": 1, "original": "Test"}]
        user_prompt = json.dumps(items, ensure_ascii=False)
        result = client.translate("sys", user_prompt)

        assert len(result) == 1
        assert result[0]["zh"] == "OK"
    finally:
        list_module.unlink(missing_ok=True)
    print("[OK] test_client_custom_batch_returns_list")


# ============================================================
# Subprocess sandbox tests (round 28 S-H-4)
# ============================================================

_CUSTOM_ENGINES_DIR = Path(__file__).resolve().parent.parent / "custom_engines"


def _write_plugin(name: str, body: str) -> Path:
    """Write a throwaway plugin under custom_engines/ and return its path.

    The body must include an ``if __name__ == "__main__":`` block that
    calls a ``_plugin_serve`` helper implementing the JSONL protocol.
    """
    p = _CUSTOM_ENGINES_DIR / f"{name}.py"
    p.write_text(body, encoding="utf-8")
    return p


def test_config_sandbox_plugin_default():
    """``sandbox_plugin`` defaults to False to preserve legacy behaviour."""
    c = APIConfig(provider="xai", api_key="test")
    assert c.sandbox_plugin is False
    print("[OK] test_config_sandbox_plugin_default")


def test_sandbox_roundtrip_batch():
    """Full happy path: launch example_echo under --sandbox-plugin, send a
    batch request, verify the response reaches the host unchanged."""
    config = APIConfig(
        provider="custom", api_key="",
        custom_module="example_echo", sandbox_plugin=True,
    )
    client = APIClient(config)
    try:
        items = [{"line": 1, "original": "Hello"}]
        user_prompt = json.dumps(items, ensure_ascii=False)
        result = client.translate("system prompt", user_prompt)
        assert len(result) == 1
        assert result[0]["zh"] == "[ECHO] Hello", result
    finally:
        # The client's subprocess client exposes close() for deterministic
        # teardown inside tests; production callers rely on atexit.
        client._custom_module.close()
    print("[OK] test_sandbox_roundtrip_batch")


def test_sandbox_request_id_tracking():
    """Multiple chunks share one subprocess; every response's request_id
    must match the dispatched request (no off-by-one / no lost messages)."""
    config = APIConfig(
        provider="custom", api_key="",
        custom_module="example_echo", sandbox_plugin=True,
    )
    client = APIClient(config)
    try:
        for i in range(3):
            items = [{"line": i + 1, "original": f"Text_{i}"}]
            result = client.translate("sys", json.dumps(items, ensure_ascii=False))
            assert len(result) == 1
            assert result[0]["zh"] == f"[ECHO] Text_{i}"
        # Request counter should reflect 3 dispatches.
        assert client._custom_module._request_id == 3
    finally:
        client._custom_module.close()
    print("[OK] test_sandbox_request_id_tracking")


def test_sandbox_plugin_exception_wrapped():
    """A plugin raising inside translate_batch must surface as a
    RuntimeError in the host (wrapping the ``error`` JSON field)."""
    body = (
        "import json, sys\n"
        "\n"
        "def translate_batch(system_prompt, user_prompt):\n"
        "    raise ValueError('plugin crashed on purpose')\n"
        "\n"
        "def _plugin_serve():\n"
        "    for line in sys.stdin:\n"
        "        line = line.strip()\n"
        "        if not line: continue\n"
        "        req = json.loads(line)\n"
        "        if req.get('request_id') == -1: break\n"
        "        try:\n"
        "            result = translate_batch(req.get('system_prompt',''),\n"
        "                                     req.get('user_prompt',''))\n"
        "            resp = {'request_id': req['request_id'],\n"
        "                    'response': result, 'error': None}\n"
        "        except Exception as e:\n"
        "            resp = {'request_id': req['request_id'],\n"
        "                    'response': None, 'error': str(e)}\n"
        "        print(json.dumps(resp), flush=True)\n"
        "\n"
        "if __name__ == '__main__':\n"
        "    if len(sys.argv) > 1 and sys.argv[1] == '--plugin-serve':\n"
        "        _plugin_serve()\n"
    )
    path = _write_plugin("_test_sandbox_raises", body)
    try:
        config = APIConfig(
            provider="custom", api_key="",
            custom_module="_test_sandbox_raises", sandbox_plugin=True,
        )
        client = APIClient(config)
        try:
            raised = False
            try:
                client.translate("sys", json.dumps([{"line": 1, "original": "x"}]))
            except RuntimeError as e:
                raised = "plugin crashed on purpose" in str(e)
            assert raised, "host should have raised RuntimeError wrapping plugin error"
        finally:
            client._custom_module.close()
    finally:
        path.unlink(missing_ok=True)
    print("[OK] test_sandbox_plugin_exception_wrapped")


def test_sandbox_rejects_path_traversal():
    """Subprocess mode reuses the same name-sanitisation as importlib mode."""
    for name in ["../evil", "foo/bar", "..\\evil"]:
        raised = False
        try:
            _SubprocessPluginClient(name)
        except RuntimeError as e:
            raised = "路径分隔符" in str(e)
        assert raised, f"should have rejected {name!r}"
    print("[OK] test_sandbox_rejects_path_traversal")


def test_sandbox_rejects_missing_module():
    """Missing plugin file raises RuntimeError before spawning any process."""
    raised = False
    try:
        _SubprocessPluginClient("nonexistent_sandbox_plugin_xyz")
    except RuntimeError as e:
        raised = "未找到" in str(e)
    assert raised
    print("[OK] test_sandbox_rejects_missing_module")


def test_sandbox_timeout_kills_hung_plugin():
    """A plugin that never responds must be killed by the host timeout."""
    body = (
        "import sys, time\n"
        "\n"
        "def translate_batch(system_prompt, user_prompt):\n"
        "    time.sleep(30)\n"
        "    return '[]'\n"
        "\n"
        "def _plugin_serve():\n"
        "    for line in sys.stdin:\n"
        "        if not line.strip(): continue\n"
        "        time.sleep(30)  # never responds\n"
        "\n"
        "if __name__ == '__main__':\n"
        "    if len(sys.argv) > 1 and sys.argv[1] == '--plugin-serve':\n"
        "        _plugin_serve()\n"
    )
    path = _write_plugin("_test_sandbox_hang", body)
    try:
        # Use a very small timeout so the test finishes quickly.
        config = APIConfig(
            provider="custom", api_key="",
            custom_module="_test_sandbox_hang", sandbox_plugin=True,
            timeout=1.0,
        )
        client = APIClient(config)
        try:
            raised = False
            try:
                client.translate("sys", json.dumps([{"line": 1, "original": "x"}]))
            except RuntimeError as e:
                raised = "超时" in str(e)
            assert raised, "host should have raised on subprocess timeout"
            # After timeout the subprocess must be reaped / no longer alive.
            assert client._custom_module._proc.poll() is not None, (
                "subprocess should have been killed after timeout"
            )
        finally:
            client._custom_module.close()
    finally:
        path.unlink(missing_ok=True)
    print("[OK] test_sandbox_timeout_kills_hung_plugin")


def test_sandbox_stderr_read_bounded():
    """When a plugin exits prematurely, the host's diagnostic reads at most
    10 KB of stderr and includes only a ~600-char tail in the RuntimeError
    (round 30 robustness fix guarding against OOM on pathological plugin
    output).

    The plugin writes 3 KB to stderr (safe under every OS's pipe buffer so
    the child can exit without blocking) and returns exit code 7.  The
    parent's ``stderr.read(10_000)`` returns the full 3 KB, then ``[-600:]``
    truncates — the final error string is proven bounded by the
    ``len(err) < 2_000`` assertion, which would fail under the old
    unbounded ``read()`` followed by the same tail slice only incidentally:
    the important invariant is that changing ``3_000`` here to ``3_000_000``
    must not change the assertion's outcome because of the 10 KB cap.
    """
    body = (
        "import sys\n"
        "\n"
        "def translate_batch(system_prompt, user_prompt):\n"
        "    return '[]'\n"
        "\n"
        "if __name__ == '__main__':\n"
        "    if len(sys.argv) > 1 and sys.argv[1] == '--plugin-serve':\n"
        "        sys.stderr.write('X' * 3_000)\n"
        "        sys.stderr.flush()\n"
        "        sys.exit(7)\n"
    )
    path = _write_plugin("_test_sandbox_big_stderr", body)
    try:
        config = APIConfig(
            provider="custom", api_key="",
            custom_module="_test_sandbox_big_stderr", sandbox_plugin=True,
        )
        client = APIClient(config)
        try:
            # Give the child a moment to exit before we call it.
            client._custom_module._proc.wait(timeout=5)
            raised = False
            err = ""
            try:
                client.translate("sys", json.dumps([{"line": 1, "original": "x"}]))
            except RuntimeError as e:
                raised = True
                err = str(e)
            assert raised, "host should have detected the prematurely-exited child"
            assert "exit=7" in err, f"expected exit code surfaced, got: {err!r}"
            # Total error message including Chinese prefix must be bounded;
            # the stderr payload was 3 KB but the error embeds only the last
            # 600 chars of a 10 KB-bounded read — so the message stays short
            # regardless of how much the plugin wrote.
            assert len(err) < 2_000, (
                f"stderr tail leaked too much into error ({len(err)} chars)"
            )
        finally:
            client._custom_module.close()
    finally:
        path.unlink(missing_ok=True)
    print("[OK] test_sandbox_stderr_read_bounded")


def test_sandbox_rejects_oversize_response_line():
    """Round 43 audit-tail: ``_SubprocessPluginClient._read_response_line``
    enforces a 50 MB cap per response line to prevent an adversarial or
    malfunctioning plugin from OOMing the host with an unbounded single
    line of stdout.  Pairs with the r30 stderr 10 KB cap to bound every
    channel the host reads from.

    Uses a stubbed ``_proc`` with a fake ``stdout.readline`` so the test
    does not need to spin up a real subprocess nor actually allocate 50
    MB — ``_MAX_PLUGIN_RESPONSE_BYTES`` is temporarily patched to a tiny
    value (1 KB) and ``readline(1024)`` returns exactly 1024 bytes
    without a newline to trip the oversize detection.
    """
    from unittest import mock

    from core import api_plugin
    from core.api_plugin import _SubprocessPluginClient

    # Build a bare instance; __init__ would try to Popen a subprocess.
    client = _SubprocessPluginClient.__new__(_SubprocessPluginClient)
    client._timeout = 5.0

    class _FakeStdout:
        def __init__(self, payload: str):
            self._payload = payload

        def readline(self, size: int = -1) -> str:
            # Simulate a plugin that emits exactly ``size`` bytes with
            # no newline — the cap's worst case.
            if size > 0:
                return self._payload[:size]
            return self._payload

    class _FakeProc:
        def __init__(self, payload: str):
            self.stdout = _FakeStdout(payload)

        def poll(self):
            return None

        def kill(self):
            pass

        def wait(self, timeout=None):
            pass

    # Patch the cap to 1 KB so the test only needs 1 KB of payload.
    # Round 44: canonical name is ``_MAX_PLUGIN_RESPONSE_CHARS``;
    # the old ``_MAX_PLUGIN_RESPONSE_BYTES`` alias still exists but
    # only ``_CHARS`` is read by ``_read_response_line``.
    with mock.patch.object(api_plugin, "_MAX_PLUGIN_RESPONSE_CHARS", 1024):
        client._proc = _FakeProc("X" * 2048)  # more than the cap, no newline
        raised = False
        try:
            client._read_response_line(req_id=42)
        except RuntimeError as e:
            msg = str(e)
            raised = (
                "oversized" in msg.lower()
                or "exceeded" in msg.lower()
                or "bytes" in msg.lower()
            )
        assert raised, (
            "plugin response > cap bytes without newline must raise "
            "a RuntimeError; no RuntimeError observed"
        )
    print("[OK] test_sandbox_rejects_oversize_response_line")


def test_sandbox_oversize_response_line_char_semantics_multibyte():
    """Round 44 audit-tail: ``_MAX_PLUGIN_RESPONSE_CHARS`` counts chars,
    not bytes (Popen text=True + readline(N) → N chars).  This test
    feeds a multibyte-dominant payload to prove the cap triggers at the
    same char count regardless of per-char byte width — a CJK response
    and an ASCII response both cap at the same number of characters.

    Documents the r43 audit-tail correction: r43 commit introduced the
    cap as ``_MAX_PLUGIN_RESPONSE_BYTES`` (misleading), r44 renamed to
    ``_MAX_PLUGIN_RESPONSE_CHARS`` and kept the old name as a deprecated
    alias.  The original r43 test exercises the cap with ASCII payload;
    this test covers the multibyte case to close the audit gap.
    """
    from unittest import mock

    from core import api_plugin
    from core.api_plugin import _SubprocessPluginClient

    client = _SubprocessPluginClient.__new__(_SubprocessPluginClient)
    client._timeout = 5.0

    class _FakeStdout:
        def __init__(self, payload: str):
            self._payload = payload

        def readline(self, size: int = -1) -> str:
            # Text-mode readline counts CHARS, not bytes.  Return exactly
            # ``size`` chars of the payload so the caller sees the cap.
            if size > 0:
                return self._payload[:size]
            return self._payload

    class _FakeProc:
        def __init__(self, payload: str):
            self.stdout = _FakeStdout(payload)

        def poll(self):
            return None

        def kill(self):
            pass

        def wait(self, timeout=None):
            pass

    # Patch the cap to 1024 chars so the test only needs 1024-2048 chars
    # of payload, not 50 MB.  Use CJK chars to prove char-semantics:
    # each "你" is 3 bytes in UTF-8, so 2048 chars = 6144 bytes — but
    # the cap still triggers at 1024 **chars**, not bytes.
    with mock.patch.object(api_plugin, "_MAX_PLUGIN_RESPONSE_CHARS", 1024):
        client._proc = _FakeProc("你" * 2048)  # 2048 chars, 6144 bytes
        raised = False
        msg = ""
        try:
            client._read_response_line(req_id=99)
        except RuntimeError as e:
            msg = str(e)
            raised = "chars" in msg.lower() or "exceeded" in msg.lower()
        assert raised, (
            f"multibyte (CJK) payload > cap chars without newline must "
            f"raise RuntimeError mentioning 'chars' or 'exceeded'; "
            f"got msg={msg!r}"
        )

    # Symmetric: same char count, same trigger regardless of byte width.
    # Patch cap to 1024 chars again; test with ASCII.  Same cap fires at
    # same char count.  (r43's original test covered this already, but
    # re-exercising here documents the byte-agnostic contract.)
    with mock.patch.object(api_plugin, "_MAX_PLUGIN_RESPONSE_CHARS", 1024):
        client._proc = _FakeProc("X" * 2048)  # 2048 chars, 2048 bytes
        raised_ascii = False
        try:
            client._read_response_line(req_id=100)
        except RuntimeError:
            raised_ascii = True
        assert raised_ascii, (
            "ASCII payload > cap chars without newline must also raise"
        )
    print("[OK] test_sandbox_oversize_response_line_char_semantics_multibyte")


def test_sandbox_close_idempotent():
    """Calling close() twice on a subprocess client is a no-op the second time."""
    config = APIConfig(
        provider="custom", api_key="",
        custom_module="example_echo", sandbox_plugin=True,
    )
    client = APIClient(config)
    sandbox = client._custom_module
    sandbox.close()
    # Second close should not raise.
    sandbox.close()
    # Calling translate_batch after close raises.
    raised = False
    try:
        sandbox.translate_batch("s", "[]")
    except RuntimeError:
        raised = True
    assert raised, "calls after close() must raise"
    print("[OK] test_sandbox_close_idempotent")


# ============================================================
# Runner
# ============================================================

ALL_TESTS = [
    test_load_example_echo,
    test_load_with_py_extension,
    test_load_nonexistent_raises,
    test_load_empty_name_raises,
    test_load_path_traversal_rejected,
    test_load_no_interface_raises,
    test_config_custom_provider,
    test_config_custom_module_default,
    test_client_custom_batch,
    test_client_custom_single_fallback,
    test_client_custom_batch_returns_list,
    # Round 28 S-H-4 subprocess sandbox coverage.
    test_config_sandbox_plugin_default,
    test_sandbox_roundtrip_batch,
    test_sandbox_request_id_tracking,
    test_sandbox_plugin_exception_wrapped,
    test_sandbox_rejects_path_traversal,
    test_sandbox_rejects_missing_module,
    test_sandbox_timeout_kills_hung_plugin,
    test_sandbox_stderr_read_bounded,
    test_sandbox_close_idempotent,
    # Round 43 audit-tail: per-response-line size cap (matches r30 stderr cap)
    test_sandbox_rejects_oversize_response_line,
    # Round 44 audit-tail: cap is CHARS not BYTES — multibyte payload
    test_sandbox_oversize_response_line_char_semantics_multibyte,
]


if __name__ == "__main__":
    passed = 0
    failed = 0
    for t in ALL_TESTS:
        try:
            t()
            passed += 1
        except Exception as e:
            print(f"[FAIL] {t.__name__}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    total = passed + failed
    if failed:
        print(f"\n{passed}/{total} PASSED, {failed} FAILED")
        sys.exit(1)
    else:
        print(f"\nALL {total} CUSTOM ENGINE TESTS PASSED")
