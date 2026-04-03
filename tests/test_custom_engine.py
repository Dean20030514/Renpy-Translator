#!/usr/bin/env python3
"""Tests for custom translation engine plugin system."""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.api_client import APIConfig, APIClient, _load_custom_engine


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
