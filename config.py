#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""项目级配置文件支持：减少命令行参数记忆成本。

配置文件查找顺序：
1. --config path/to/config.json（CLI 显式指定）
2. <game-dir>/renpy_translate.json
3. <game-dir>/../renpy_translate.json
4. 不存在则使用默认值

优先级：CLI 参数(非None) > 配置文件 > 默认值

安全设计：API Key 不直接写入配置文件，使用 api_key_env 或 api_key_file。
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger("renpy_translator")

# 所有可配置参数的默认值
DEFAULTS: dict[str, Any] = {
    "provider": "xai",
    "model": "",
    "genre": "adult",
    "workers": 1,
    "rpm": 60,
    "rps": 5,
    "timeout": 180.0,
    "temperature": 0.1,
    "max_chunk_tokens": 4000,
    "max_response_tokens": 32768,
    "target_lang": "zh",
    "min_dialogue_density": 0.20,
    "output_dir": "output",
    "tl_lang": "chinese",
}

# 配置文件搜索名
CONFIG_FILENAME = "renpy_translate.json"


class Config:
    """配置管理器：配置文件 + CLI 参数合并。

    用法：
        config = Config(game_dir=Path(args.game_dir), cli_args=args)
        workers = config.get("workers")  # CLI > 配置文件 > 默认值
        api_key = config.resolve_api_key()
    """

    def __init__(self, game_dir: Path, cli_args: Any = None, config_path: str = ""):
        self._cli_args = cli_args
        self._file_config: dict[str, Any] = {}
        self._load_config_file(game_dir, config_path)

    def _load_config_file(self, game_dir: Path, explicit_path: str) -> None:
        """按优先级查找并加载配置文件。"""
        search_paths: list[Path] = []

        # 1. CLI 显式指定
        if explicit_path:
            search_paths.append(Path(explicit_path))

        # 2. 游戏目录下
        if game_dir:
            search_paths.append(game_dir / CONFIG_FILENAME)
            # 3. 游戏目录的父目录
            search_paths.append(game_dir.parent / CONFIG_FILENAME)

        for p in search_paths:
            if p.exists():
                try:
                    data = json.loads(p.read_text(encoding="utf-8"))
                    if isinstance(data, dict):
                        self._file_config = data
                        logger.info(f"[CONFIG] 已加载配置文件: {p}")
                        return
                except (json.JSONDecodeError, OSError) as e:
                    logger.warning(f"[CONFIG] 配置文件解析失败: {p}: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """三层合并：CLI(非None) > 配置文件 > DEFAULTS > default。

        argparse 参数应使用 default=None，这样未传入的参数自然为 None，
        不会覆盖配置文件中的值。
        """
        # 1. CLI 参数（非 None 才使用）
        if self._cli_args is not None:
            cli_val = getattr(self._cli_args, key, None)
            if cli_val is not None:
                return cli_val

        # 2. 配置文件
        if key in self._file_config:
            return self._file_config[key]

        # 3. 默认值
        return DEFAULTS.get(key, default)

    def resolve_api_key(self) -> str:
        """解析 API Key：CLI > 环境变量（配置文件指定）> 密钥文件 > 空。

        配置文件中使用 api_key_env 或 api_key_file，不直接存储明文密钥。
        """
        # 1. CLI 直接传入
        if self._cli_args is not None:
            cli_key = getattr(self._cli_args, "api_key", None)
            if cli_key:
                return cli_key

        # 2. 配置文件中的环境变量名
        env_var = self._file_config.get("api_key_env", "")
        if env_var:
            key = os.environ.get(env_var, "")
            if key:
                return key

        # 3. 配置文件中的密钥文件路径
        key_file = self._file_config.get("api_key_file", "")
        if key_file:
            p = Path(key_file)
            if p.exists():
                try:
                    return p.read_text(encoding="utf-8").strip()
                except OSError:
                    pass

        return ""

    @property
    def file_config(self) -> dict[str, Any]:
        """返回配置文件中的原始数据（只读）。"""
        return dict(self._file_config)

    def has_config_file(self) -> bool:
        """是否加载了配置文件。"""
        return bool(self._file_config)
