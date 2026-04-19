#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""file_processor package — re-exports all public names for backward compatibility."""

from file_processor.splitter import (
    estimate_tokens,
    split_file,
    read_file,
    _find_block_boundaries,
    _force_split_lines,
)
from file_processor.checker import (
    SKIP_FILES_FOR_TRANSLATION,
    MODEL_SPEAKING_PATTERNS,
    PLACEHOLDER_ORDER_PATTERNS,
    COMMON_UI_BUTTONS,
    _extract_placeholder_sequence,
    _placeholder_cache,
    clear_placeholder_cache,
    protect_placeholders,
    restore_placeholders,
    protect_locked_terms,
    restore_locked_terms,
    _count_translatable_lines_in_chunk,
    check_response_chunk,
    check_response_item,
    is_common_ui_button,
    fix_chinese_placeholder_drift,
    _filter_checked_translations,
    _restore_placeholders_in_translations,
    _restore_locked_terms_in_translations,
    _fix_chinese_placeholder_drift_in_translations,
    # Round 32 Commit 2: runtime-configurable UI-button whitelist extensions
    add_ui_button_whitelist,
    load_ui_button_whitelist,
    clear_ui_button_whitelist,
    get_ui_button_whitelist_extensions,
)
from file_processor.patcher import (
    apply_translations,
    _replace_string_in_line,
    _escape_for_renpy_string,
    _check_translation_safety,
    _count_unescaped_quote,
    _extract_first_quoted_text,
    _strip_double_quoted_segments,
    _auto_fix_translation,
)
from file_processor.validator import validate_translation, _looks_untranslated_dialogue

__all__ = [
    # splitter
    "estimate_tokens",
    "split_file",
    "read_file",
    "_find_block_boundaries",
    "_force_split_lines",
    # checker
    "SKIP_FILES_FOR_TRANSLATION",
    "MODEL_SPEAKING_PATTERNS",
    "PLACEHOLDER_ORDER_PATTERNS",
    "_extract_placeholder_sequence",
    "_placeholder_cache",
    "clear_placeholder_cache",
    "protect_placeholders",
    "restore_placeholders",
    "protect_locked_terms",
    "restore_locked_terms",
    "_count_translatable_lines_in_chunk",
    "check_response_chunk",
    "check_response_item",
    "is_common_ui_button",
    "COMMON_UI_BUTTONS",
    "fix_chinese_placeholder_drift",
    "_filter_checked_translations",
    "_restore_placeholders_in_translations",
    "_restore_locked_terms_in_translations",
    "_fix_chinese_placeholder_drift_in_translations",
    # Round 32 Commit 2: runtime-configurable UI-button whitelist extensions
    "add_ui_button_whitelist",
    "load_ui_button_whitelist",
    "clear_ui_button_whitelist",
    "get_ui_button_whitelist_extensions",
    # patcher
    "apply_translations",
    "_replace_string_in_line",
    "_escape_for_renpy_string",
    "_check_translation_safety",
    "_count_unescaped_quote",
    "_extract_first_quoted_text",
    "_strip_double_quoted_segments",
    "_auto_fix_translation",
    # validator
    "validate_translation",
    "_looks_untranslated_dialogue",
]
