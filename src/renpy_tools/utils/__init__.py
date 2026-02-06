from .common import (
    load_jsonl, save_jsonl, get_id, get_zh, has_zh, get_en,
    normalize_text, is_asset_path, should_skip_translation,
    TRANS_KEYS, EN_KEYS, ASSET_EXTS, SKIP_KEYWORDS,
    PH_RE, RENPY_SINGLE_TAGS, RENPY_PAIRED_TAGS,
    ph_set, ph_multiset, strip_renpy_tags,
    AdaptiveRateLimiter, QualityScore, calculate_quality_score,
    TranslationConfig, TranslationCache
)
from .dict_utils import load_dictionary
from .io import read_jsonl_lines, write_jsonl_lines
from .ui import BilingualMessage, confirm_operation, check_prerequisites, show_system_info
from .config import ConfigManager, get_config
from .placeholder import compute_semantic_signature, normalize_for_signature
from .logger import (
    TranslationLogger, get_logger, setup_logger, log_exceptions,
    # 异常类
    RenpyToolsError, FileOperationError, ValidationError,
    TranslationError, ConfigurationError, APIError
)
from .cache import (
    kv_get, kv_set, kv_set_batch, kv_get_batch,
    kv_delete, kv_clear, kv_count,
    text_hash, cached, close_all_connections
)
from .tm import (
    TranslationMemory, TMEntry, TMMatch,
    get_global_tm, load_tm_from_file, query_tm
)

__all__ = [
    # common utilities
    "load_jsonl",
    "save_jsonl",
    "get_id",
    "get_zh",
    "has_zh",
    "get_en",
    "normalize_text",
    "is_asset_path",
    "should_skip_translation",
    # constants
    "TRANS_KEYS",
    "EN_KEYS",
    "ASSET_EXTS",
    "SKIP_KEYWORDS",
    # placeholder (from common - unified)
    "PH_RE",
    "RENPY_SINGLE_TAGS",
    "RENPY_PAIRED_TAGS",
    "ph_set",
    "ph_multiset",
    "strip_renpy_tags",
    # quality scoring
    "QualityScore",
    "calculate_quality_score",
    # rate limiting
    "AdaptiveRateLimiter",
    # config & cache
    "TranslationConfig",
    "TranslationCache",
    "ConfigManager",
    "get_config",
    # cache (sqlite)
    "kv_get",
    "kv_set",
    "kv_set_batch",
    "kv_get_batch",
    "kv_delete",
    "kv_clear",
    "kv_count",
    "text_hash",
    "cached",
    "close_all_connections",
    # translation memory
    "TranslationMemory",
    "TMEntry",
    "TMMatch",
    "get_global_tm",
    "load_tm_from_file",
    "query_tm",
    # dictionary
    "load_dictionary",
    # io
    "read_jsonl_lines",
    "write_jsonl_lines",
    # ui
    "BilingualMessage",
    "confirm_operation",
    "check_prerequisites",
    "show_system_info",
    # placeholder (advanced)
    "compute_semantic_signature",
    "normalize_for_signature",
    # logger
    "TranslationLogger",
    "get_logger",
    "setup_logger",
    "log_exceptions",
    # exceptions
    "RenpyToolsError",
    "FileOperationError",
    "ValidationError",
    "TranslationError",
    "ConfigurationError",
    "APIError",
]
