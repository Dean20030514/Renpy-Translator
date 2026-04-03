#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ren'Py 整文件翻译工具 — 将完整 .rpy 文件发给 AI，由 AI 自行识别可翻译内容

核心优势：
  - AI 看到完整文件上下文，自行判断什么该翻什么不该翻
  - 不会误翻 screen 关键字、变量名、配置值
  - 跨文件术语一致性（自动维护术语表）
  - 翻译安全校验（变量、标签、缩进、代码结构检查）

用法：
  python main.py --game-dir "E:\\Games\\MyGame" --provider xai --api-key YOUR_KEY
  python main.py --game-dir "E:\\Games\\MyGame" --provider openai --api-key YOUR_KEY --model gpt-4o
  python main.py --resume   # 从上次中断处继续

文件流程：
  扫描 .rpy → 拆分大文件 → 发送 AI 翻译 → JSON 回传 → Patch 回原文件 → 校验
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

logger = logging.getLogger("renpy_translator")


# ============================================================
# Logging 配置
# ============================================================

class _FlushStreamHandler(logging.StreamHandler):
    """每条日志后自动 flush，确保多线程下实时输出。"""
    def emit(self, record):
        super().emit(record)
        self.flush()


def setup_logging(verbose: bool = False, quiet: bool = False, log_file: str = ""):
    """配置全局 logging。verbose=DEBUG, quiet=WARNING, 默认=INFO。"""
    level = logging.DEBUG if verbose else (logging.WARNING if quiet else logging.INFO)
    fmt = "%(message)s"
    handlers: list[logging.Handler] = [_FlushStreamHandler(sys.stdout)]
    if log_file:
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))
    logging.basicConfig(level=level, format=fmt, handlers=handlers, force=True)


# ============================================================
# CLI 参数校验
# ============================================================

def _positive_int(value: str) -> int:
    """argparse type: 正整数。"""
    iv = int(value)
    if iv <= 0:
        raise argparse.ArgumentTypeError(f"必须为正整数: {value}")
    return iv


def _positive_float(value: str) -> float:
    """argparse type: 正浮点数。"""
    fv = float(value)
    if fv <= 0:
        raise argparse.ArgumentTypeError(f"必须为正数: {value}")
    return fv


def _ratio_float(value: str) -> float:
    """argparse type: 0~1 之间的比例值。"""
    fv = float(value)
    if not (0 < fv <= 1.0):
        raise argparse.ArgumentTypeError(f"必须在 (0, 1.0] 范围内: {value}")
    return fv


# ============================================================
# CLI 入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Ren'Py 整文件翻译工具 — AI 自主识别翻译内容",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--game-dir", required=True, help="游戏目录（自动检测 game/ 子目录，自动排除 renpy/ 引擎文件）")
    parser.add_argument("--output-dir", default=None, help="输出目录 (默认: output)")
    parser.add_argument("--provider", default=None, choices=['xai', 'grok', 'openai', 'deepseek', 'claude', 'gemini'],
                        help="API 提供商")
    parser.add_argument("--api-key", default="", help="API 密钥（dry-run 模式可不填）")
    parser.add_argument("--model", default=None, help="模型名称 (留空使用默认)")
    parser.add_argument("--genre", default=None, choices=['adult', 'visual_novel', 'rpg', 'general'],
                        help="翻译风格 (默认: adult)")
    parser.add_argument("--rpm", type=_positive_int, default=None, help="每分钟请求数限制 (默认: 60)")
    parser.add_argument("--rps", type=_positive_int, default=None, help="每秒请求数限制 (默认: 5)")
    parser.add_argument("--timeout", type=_positive_float, default=None, help="API 超时秒数 (默认: 180)")
    parser.add_argument("--temperature", type=float, default=None, help="生成温度 (默认: 0.1, 低=一致性高)")
    parser.add_argument("--max-chunk-tokens", type=_positive_int, default=None,
                        help="每个分块最大 token 数 (默认: 4000)")
    parser.add_argument("--resume", action="store_true", help="从上次中断处继续")
    parser.add_argument("--dict", nargs="*", default=None, metavar="PATH",
                        help="外部词典文件（CSV/JSONL，可多个）")
    parser.add_argument("--copy-assets", action="store_true",
                        help="复制非 .rpy 资源文件到输出目录")
    parser.add_argument("--workers", type=int, default=None,
                        help="并发翻译线程数 (默认: 1)")
    parser.add_argument("--exclude", nargs="*", default=None, metavar="PATTERN",
                        help="排除匹配的文件 (glob 模式)")
    parser.add_argument("--dry-run", action="store_true",
                        help="仅扫描统计，不实际翻译（预估费用）")
    parser.add_argument("--max-response-tokens", type=_positive_int, default=None,
                        help="API 最大响应 token 数 (默认: 32768)")
    parser.add_argument("--log-file", default="", metavar="PATH",
                        help="保存详细日志到文件")
    parser.add_argument("--target-lang", default=None,
                        help="目标语言 (默认: zh 简体中文)")
    parser.add_argument("--input-price", type=float, default=None, metavar="USD",
                        help="手动指定输入价格 (每百万 tokens, 美元)")
    parser.add_argument("--output-price", type=float, default=None, metavar="USD",
                        help="手动指定输出价格 (每百万 tokens, 美元)")
    parser.add_argument("--tl-priority", action="store_true",
                        help="启用 tl 优先模式：若检测到 tl/ 目录，则仅翻译 tl 下的脚本")
    parser.add_argument("--stage", default="single",
                        help="内部使用：由一键流水线指定当前运行阶段")
    parser.add_argument("--patch-font", action="store_true", default=False,
                        help="启用自动字体补丁")
    parser.add_argument("--font-file", default="", metavar="PATH",
                        help="指定字体文件路径")
    parser.add_argument("--font-config", default="", metavar="PATH",
                        help="字体配置文件路径（font_config.json，可设置字号/布局参数）")
    parser.add_argument("--retranslate", action="store_true",
                        help="补翻模式：扫描残留英文对话行，精准补翻")
    parser.add_argument("--min-dialogue-density", type=_ratio_float, default=None, metavar="RATIO",
                        help="对话密度阈值 (默认: 0.20)")
    parser.add_argument("--tl-mode", action="store_true",
                        help="tl 模式：翻译 tl/<lang>/ 空槽位")
    parser.add_argument("--tl-lang", default=None, metavar="LANG",
                        help="tl 语言子目录名 (默认: chinese)")
    parser.add_argument("--cot", action="store_true",
                        help="启用 CoT 思维链翻译（直译→校正→意译，质量更高但费用+30-50%%）")
    parser.add_argument("--verbose", action="store_true",
                        help="输出详细调试信息（DEBUG 级别）")
    parser.add_argument("--quiet", action="store_true",
                        help="仅输出警告和错误（WARNING 级别）")
    parser.add_argument("--no-clean-rpyc", action="store_true",
                        help="跳过 tl-mode 翻译后的 .rpyc 缓存清理")
    parser.add_argument("--tl-screen", action="store_true",
                        help="翻译 screen 中的裸英文字符串（text/textbutton/Tooltip）")
    parser.add_argument("--engine", default="auto",
                        choices=["auto", "renpy", "rpgmaker", "csv", "jsonl"],
                        help="游戏引擎类型 (默认: auto 自动检测)")
    parser.add_argument("--config", default="", metavar="PATH",
                        help="配置文件路径（默认自动查找 renpy_translate.json）")

    args = parser.parse_args()

    setup_logging(
        verbose=args.verbose,
        quiet=args.quiet,
        log_file=args.log_file,
    )

    # 智能检测游戏目录
    game_dir = Path(args.game_dir)
    if (game_dir / "game").exists():
        root_rpys = [f for f in game_dir.glob('*.rpy')]
        if root_rpys:
            logger.info(f"[INFO] 根目录和 game/ 都包含 .rpy 文件，扫描整个目录")
        else:
            game_dir = game_dir / "game"

    if not game_dir.exists():
        logger.error(f"[ERROR] 游戏目录不存在: {game_dir}")
        sys.exit(1)

    # 加载配置文件，与 CLI 参数合并（CLI 优先）
    from core.config import Config
    cfg = Config(game_dir=game_dir, cli_args=args, config_path=args.config)

    # 用 Config 三层合并填充 args 中为 None 的参数
    args.game_dir = str(game_dir)
    args.output_dir = cfg.get("output_dir", "output")
    args.provider = cfg.get("provider", "xai")
    args.model = cfg.get("model", "")
    args.genre = cfg.get("genre", "adult")
    args.workers = cfg.get("workers", 1)
    args.rpm = cfg.get("rpm", 60)
    args.rps = cfg.get("rps", 5)
    args.timeout = cfg.get("timeout", 180.0)
    args.temperature = cfg.get("temperature", 0.1)
    args.max_chunk_tokens = cfg.get("max_chunk_tokens", 4000)
    args.max_response_tokens = cfg.get("max_response_tokens", 32768)
    args.target_lang = cfg.get("target_lang", "zh")
    args.min_dialogue_density = cfg.get("min_dialogue_density", 0.20)
    args.tl_lang = cfg.get("tl_lang", "chinese")
    if args.dict is None:
        args.dict = cfg.get("dict", []) or []
    if args.exclude is None:
        args.exclude = cfg.get("exclude", []) or []

    # 解析目标语言配置
    from core.lang_config import get_language_config
    args.lang_config = get_language_config(args.target_lang)
    logger.debug(f"[LANG] 目标语言: {args.lang_config.native_name} ({args.lang_config.code})")

    # API Key 解析：CLI > 配置文件(env/file) > 空
    if not args.api_key:
        args.api_key = cfg.resolve_api_key()

    # dry-run 模式不需要 API key
    if not args.dry_run and not args.api_key:
        logger.error("[ERROR] 非 dry-run 模式必须提供 --api-key（或在配置文件中设置 api_key_env）")
        sys.exit(1)

    tl_mode = getattr(args, "tl_mode", False)
    if args.retranslate and tl_mode:
        logger.error("[ERROR] --retranslate 和 --tl-mode 互斥，不能同时使用")
        sys.exit(1)

    engine_arg = getattr(args, "engine", "auto")
    if engine_arg in ("auto", "renpy"):
        # Ren'Py 路径
        if tl_mode:
            from translators.tl_mode import run_tl_pipeline
            run_tl_pipeline(args)
            if getattr(args, "tl_screen", False):
                from translators.screen import run_screen_translate
                run_screen_translate(args)
        elif getattr(args, "tl_screen", False):
            from translators.screen import run_screen_translate
            logger.info("[SCREEN] 建议先运行 --tl-mode 完成主体翻译，再用 --tl-screen 补充 screen 文本")
            run_screen_translate(args)
        elif args.retranslate:
            from translators.retranslator import run_retranslate_pipeline
            run_retranslate_pipeline(args)
        else:
            from translators.direct import run_pipeline
            run_pipeline(args)
    else:
        # 非 Ren'Py 引擎路由
        from engines.engine_detector import resolve_engine as _resolve_engine
        engine = _resolve_engine(engine_arg, Path(args.game_dir))
        if engine is None:
            logger.error(f"[ERROR] 无法创建引擎: {engine_arg}")
            sys.exit(1)
        engine.run(args)


if __name__ == "__main__":
    main()
