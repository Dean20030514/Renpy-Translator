"""
Example custom translation engine — echoes original text with a prefix.

This is a minimal example showing both the batch and single-item interfaces.
Place your custom engine in this directory (custom_engines/) and use it with:

    # Legacy in-process mode (backward compatible):
    python main.py --provider custom --custom-module example_echo ...

    # Opt-in subprocess sandbox (round 28 S-H-4, plugin isolated from the
    # host process's environment variables / file system / network):
    python main.py --provider custom --custom-module example_echo --sandbox-plugin ...

Your module must implement at least one of:
    - translate_batch(system_prompt, user_prompt) -> str | list[dict]
    - translate(text, source_lang, target_lang) -> str

For subprocess-sandbox compatibility, keep the ``if __name__ == "__main__":``
block below — it implements the JSONL protocol the host uses to feed the
plugin over stdin / stdout (one request per line, one response per line).
Plugins that omit the ``__main__`` block still work in legacy mode.
"""

import json


def translate_batch(system_prompt: str, user_prompt: str):
    """Batch interface: receives full prompt, returns JSON array string.

    Args:
        system_prompt: The system prompt (translation instructions).
        user_prompt: The user prompt (JSON array of items to translate).

    Returns:
        JSON string or list of dicts with translations added.
    """
    try:
        items = json.loads(user_prompt)
    except (json.JSONDecodeError, ValueError):
        return "[]"

    results = []
    for item in items:
        original = item.get("original", item.get("text", ""))
        entry = dict(item)
        entry["zh"] = f"[ECHO] {original}"
        results.append(entry)
    return json.dumps(results, ensure_ascii=False)


def translate(text: str, source_lang: str, target_lang: str) -> str:
    """Single-item interface (fallback if translate_batch is not defined).

    Args:
        text: Source text to translate.
        source_lang: Source language code (e.g. "en").
        target_lang: Target language code (e.g. "zh").

    Returns:
        Translated text.
    """
    return f"[ECHO] {text}"


def _plugin_serve() -> None:
    """Subprocess JSONL serve loop — read one request per line from stdin,
    write one response per line to stdout.

    Protocol (matches ``core/api_client._SubprocessPluginClient``):

        Request:  {"request_id": <int>, "system_prompt": <str>,
                   "user_prompt": <str>}
        Response: {"request_id": <int>, "response": <str|null>,
                   "error": <str|null>}
        Shutdown: {"request_id": -1}

    Any uncaught exception in the translation call is wrapped in the
    ``error`` field so the host sees a structured failure instead of an
    unexpected process crash.
    """
    import sys
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except (json.JSONDecodeError, ValueError) as e:
            resp = {"request_id": None, "response": None,
                    "error": f"bad request JSON: {e}"}
            print(json.dumps(resp, ensure_ascii=False), flush=True)
            continue
        req_id = req.get("request_id")
        if req_id == -1:
            break
        try:
            result = translate_batch(
                req.get("system_prompt", ""),
                req.get("user_prompt", ""),
            )
            if isinstance(result, list):
                result = json.dumps(result, ensure_ascii=False)
            resp = {"request_id": req_id, "response": result, "error": None}
        except Exception as exc:  # noqa: BLE001 - propagate to host
            resp = {"request_id": req_id, "response": None, "error": str(exc)}
        print(json.dumps(resp, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--plugin-serve":
        _plugin_serve()
    else:
        print(
            "This is a translation plugin. Invoke via:\n"
            "  python main.py --provider custom --custom-module example_echo ...\n"
            "Or with --sandbox-plugin for subprocess isolation.",
            file=sys.stderr,
        )
        sys.exit(1)
