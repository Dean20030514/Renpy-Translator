from .common import load_jsonl, save_jsonl, get_id, get_zh, has_zh, get_en, TRANS_KEYS
from .dict_utils import load_dictionary
from .io import read_jsonl_lines, write_jsonl_lines
from .ui import BilingualMessage, confirm_operation, check_prerequisites, show_system_info
from .config import TranslationConfig, ConfigManager, get_config
from .placeholder import ph_set, ph_multiset, PH_RE, compute_semantic_signature, normalize_for_signature
from .logger import TranslationLogger, get_logger, setup_logger

__all__ = [
    # common utilities
    "load_jsonl",
    "save_jsonl",
    "get_id",
    "get_zh",
    "has_zh",
    "get_en",
    "TRANS_KEYS",
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
    # config
    "TranslationConfig",
    "ConfigManager",
    "get_config",
    # placeholder
    "ph_set",
    "ph_multiset",
    "PH_RE",
    "compute_semantic_signature",
    "normalize_for_signature",
    # logger
    "TranslationLogger",
    "get_logger",
    "setup_logger",
]
