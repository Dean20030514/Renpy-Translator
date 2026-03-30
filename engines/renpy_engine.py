#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ren'Py 薄包装引擎：委托给现有三条管线（direct / tl / retranslate）。

不实现 extract_texts / write_back（Ren'Py 有自己的专有管线），
只覆写 run() 做模式路由。这是整个抽象层中最薄的一个类，
它的意义在于让 Ren'Py 能插入引擎检测和 CLI 路由体系中。
"""

from __future__ import annotations

import logging
from pathlib import Path

from engine_base import EngineBase, EngineProfile, TranslatableUnit, RENPY_PROFILE

logger = logging.getLogger("renpy_translator")


class RenPyEngine(EngineBase):
    """Ren'Py 引擎包装。"""

    def _default_profile(self) -> EngineProfile:
        return RENPY_PROFILE

    def detect(self, game_dir: Path) -> bool:
        """检查目录是否包含 Ren'Py 项目文件。"""
        # game/ 子目录下有 .rpy 或 .rpa
        game_sub = game_dir / "game"
        if game_sub.is_dir():
            if any(game_sub.glob("*.rpy")) or any(game_sub.glob("*.rpa")):
                return True
        # 根目录直接有 .rpy
        if any(game_dir.glob("*.rpy")):
            return True
        return False

    def extract_texts(self, game_dir: Path, **kwargs) -> list[TranslatableUnit]:
        raise NotImplementedError(
            "Ren'Py 使用专有管线（direct_translator / tl_translator），不走通用提取流程"
        )

    def write_back(self, game_dir: Path, units: list[TranslatableUnit],
                   output_dir: Path, **kwargs) -> int:
        raise NotImplementedError(
            "Ren'Py 使用专有管线，不走通用回写流程"
        )

    def run(self, args) -> None:
        """路由到 Ren'Py 的三条管线。"""
        tl_mode = getattr(args, "tl_mode", False)
        retranslate = getattr(args, "retranslate", False)

        if tl_mode:
            try:
                from tl_translator import run_tl_pipeline
            except ImportError as e:
                logger.error(f"[ENGINE] 无法加载 tl-mode 模块: {e}")
                raise
            run_tl_pipeline(args)
        elif retranslate:
            try:
                from retranslator import run_retranslate_pipeline
            except ImportError as e:
                logger.error(f"[ENGINE] 无法加载补翻模块: {e}")
                raise
            run_retranslate_pipeline(args)
        else:
            try:
                from direct_translator import run_pipeline
            except ImportError as e:
                logger.error(f"[ENGINE] 无法加载 direct-mode 模块: {e}")
                raise
            run_pipeline(args)
