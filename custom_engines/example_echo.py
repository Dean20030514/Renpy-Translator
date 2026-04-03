"""
Example custom translation engine — echoes original text with a prefix.

This is a minimal example showing both the batch and single-item interfaces.
Place your custom engine in this directory (custom_engines/) and use it with:

    python main.py --provider custom --custom-module your_engine ...

Your module must implement at least one of:
    - translate_batch(system_prompt, user_prompt) -> str | list[dict]
    - translate(text, source_lang, target_lang) -> str
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
