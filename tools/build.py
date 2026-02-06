#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
Build CN Package — 生成中文构建目录，避免双载冲突

两种策略：
1) mirror 模式：将 .zh.rpy 镜像内容替换英文 .rpy，最终目录不包含 .zh.rpy，避免中英并存双载。
2) tl 模式：拷贝并仅开启 game/tl/<lang>/ 翻译（官方 i18n），不触碰英文基线文件。

用法示例（PowerShell）：
    # 使用 mirror 模式（来自回填输出 out_patch）
    python build.py "E:\\TheTyrant" -o "E:\\TheTyrant_CN" --mode mirror --zh-mirror "E:\\out_patch"

    # 使用 tl 模式（来自 tl 输出 out_tl）
    python build.py "E:\\TheTyrant" -o "E:\\TheTyrant_CN" --mode tl --tl-root "E:\\out_tl" --lang zh_CN

注意：本脚本不修改原项目目录，仅生成新的构建目录。
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path
from typing import Set, Optional

# 添加 src 到路径
_project_root = Path(__file__).parent.parent
if str(_project_root / "src") not in sys.path:
    sys.path.insert(0, str(_project_root / "src"))

DEFAULT_EXCLUDES: Set[str] = {"saves", "cache", "tmp", ".git", "__pycache__"}

# 尝试导入统一日志
try:
    from renpy_tools.utils.logger import get_logger, FileOperationError
    logger = get_logger("build")
except ImportError:
    logger = None
    class FileOperationError(Exception):
        pass

# 可选：彩色日志
try:
    from rich.console import Console  # type: ignore
    _console = Console()
except ImportError:  # 可选
    _console = None


def _log(msg: str, level: str = "info") -> None:
    """统一日志输出"""
    if logger:
        getattr(logger, level)(msg)
    elif _console:
        style = {"info": "dim", "warning": "yellow", "error": "red"}.get(level, "")
        _console.print(f"[{style}]{msg}[/]")
    else:
        print(msg)


# 统一 IO 写入函数（延迟导入，避免静态分析导入错误；不可用时使用回退实现）
def _write_text_file_compat(path: Path, text: str, encoding: str = "utf-8") -> None:
    """兼容的文件写入函数"""
    try:
        from renpy_tools.utils.io import write_text_file as _wtf  # type: ignore
        _wtf(path, text, encoding=encoding)
    except ImportError:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding=encoding)


def copy_project(src: Path, dst: Path, exclude_dirs: Set[str]) -> None:
    """复制项目目录结构
    
    Args:
        src: 源目录
        dst: 目标目录
        exclude_dirs: 要排除的目录名集合
    """
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True, exist_ok=True)
    iter_paths = list(src.rglob("*"))
    _log(f"Copying project tree ({len(iter_paths)} entries) ...")
    
    for p in iter_paths:
        rel = p.relative_to(src)
        if any(part in exclude_dirs for part in rel.parts):
            continue
        outp = dst / rel
        if p.is_dir():
            outp.mkdir(parents=True, exist_ok=True)
        else:
            outp.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, outp)


def apply_mirror_overwrite(dst_root: Path, zh_mirror_root: Path) -> None:
    """将 zh_mirror_root 中生成的 .zh.rpy 内容覆盖到 dst_root 的同名 .rpy 中，并移除任何 .zh.rpy 文件。"""
    # 1) 用 .zh.rpy 内容替换对应的 .rpy
    replaced = 0
    for p in zh_mirror_root.rglob("*.zh.rpy"):
        rel = p.relative_to(zh_mirror_root)
        # 对应目标文件路径：改回 .rpy 后缀
        tgt_rel = rel.with_suffix(".rpy")
        tgt_path = dst_root / tgt_rel
        if tgt_path.exists():
            text = p.read_text(encoding="utf-8", errors="ignore")
            _write_text_file_compat(tgt_path, text, encoding="utf-8")
            replaced += 1
    # 2) 移除目标中的所有 .zh.rpy（避免双载）
    removed = 0
    for p in dst_root.rglob("*.zh.rpy"):
        try:
            p.unlink()
            removed += 1
        except OSError:
            pass
    return replaced, removed


def overlay_tl(dst_root: Path, tl_root: Path, lang: str):
    """将 tl_root/game/tl/<lang>/ 覆盖到 dst_root/game/tl/<lang>/ 下。"""
    src_dir = tl_root / "game" / "tl" / lang
    if not src_dir.exists():
        raise FileNotFoundError(f"TL 目录不存在: {src_dir}")
    dst_dir = dst_root / "game" / "tl" / lang
    dst_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for p in src_dir.rglob("*.rpy"):
        rel = p.relative_to(src_dir)
        outp = dst_dir / rel
        outp.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, outp)
        count += 1
    # 清理任何遗留的 .zh.rpy
    removed = 0
    for p in dst_root.rglob("*.zh.rpy"):
        try:
            p.unlink(); removed += 1
        except OSError:
            pass
    return count, removed


def post_build_selfcheck(dst_root: Path, mode: str, lang: str) -> None:
    """
    二次自检：确保无双载风险
    - 任意模式下：不应存在任何 *.zh.rpy 残留
    - mirror 模式下：不应包含 game/tl/<lang>/ 下的任何 .rpy（mirror 与 tl 互斥）
    - tl 模式下：允许 game/tl/<lang>/ 存在，但不应有任何 *.zh.rpy
    发现风险直接退出（非零）。
    """
    issues = []
    zh_left = list(dst_root.rglob("*.zh.rpy"))
    if zh_left:
        issues.append(f"发现遗留 .zh.rpy {len(zh_left)} 个，例如: {zh_left[0]}")

    tl_dir = dst_root / "game" / "tl" / lang
    if mode == "mirror" and tl_dir.exists():
        # 任意 tl 脚本均视为双载风险
        tl_rpys = list(tl_dir.rglob("*.rpy"))
        if tl_rpys:
            issues.append(f"mirror 模式下检测到 TL 目录文件 {len(tl_rpys)} 个（互斥冲突），例如: {tl_rpys[0]}")

    if issues:
        msg = "\n- ".join(["构建自检失败："] + issues)
        if _console:
            _console.print(f"[bold red]{msg}[/]")
        else:
            print(msg)
        sys.exit(10)


def main():
    ap = argparse.ArgumentParser(description="Build CN package from project with mirror or tl strategy (no double-load)")
    ap.add_argument("project_root", help="Ren'Py 项目根目录（包含 game/ 等）")
    ap.add_argument("-o", "--out", required=True, help="中文构建输出目录")
    ap.add_argument("--mode", choices=["auto","mirror","tl"], default="auto", help="构建模式：mirror/tl，默认 auto（优先 mirror）")
    ap.add_argument("--zh-mirror", help=".zh.rpy 镜像根目录（patch 回填输出目录）")
    ap.add_argument("--tl-root", help="tl 输出根目录（包含 game/tl/<lang>/）")
    ap.add_argument("--lang", default="zh_CN", help="TL 语言目录名，默认 zh_CN")
    ap.add_argument("--exclude-dirs", default=",".join(sorted(DEFAULT_EXCLUDES)), help="拷贝时排除目录，逗号分隔")
    args = ap.parse_args()

    project_root = Path(args.project_root).resolve()
    out_root = Path(args.out).resolve()
    exclude_dirs = {x.strip() for x in args.exclude_dirs.split(',') if x.strip()}

    if not project_root.exists():
        print(f"Project not found: {project_root}")
        sys.exit(1)

    mode = args.mode
    if mode == "auto":
        if args.zh_mirror:
            mode = "mirror"
        elif args.tl_root:
            mode = "tl"
        else:
            print("auto 模式需要 --zh-mirror 或 --tl-root 至少提供一个")
            sys.exit(2)

    if _console:
        _console.print(f"复制项目到: [magenta]{out_root}[/]")
    else:
        print(f"复制项目到: {out_root}")
    copy_project(project_root, out_root, exclude_dirs)

    if mode == "mirror":
        if not args.zh_mirror:
            print("mirror 模式需要 --zh-mirror")
            sys.exit(3)
        zh_root = Path(args.zh_mirror).resolve()
        if not zh_root.exists():
            print(f"zh_mirror 不存在: {zh_root}")
            sys.exit(4)
        replaced, removed = apply_mirror_overwrite(out_root, zh_root)
        if _console:
            _console.print(f"mirror 模式完成：覆盖 [bold]{replaced}[/] 个 .rpy；移除 [bold]{removed}[/] 个 .zh.rpy")
        else:
            print(f"mirror 模式完成：覆盖 {replaced} 个 .rpy；移除 {removed} 个 .zh.rpy")
    elif mode == "tl":
        if not args.tl_root:
            print("tl 模式需要 --tl-root")
            sys.exit(5)
        tl_root = Path(args.tl_root).resolve()
        if not tl_root.exists():
            print(f"tl_root 不存在: {tl_root}")
            sys.exit(6)
        copied, removed = overlay_tl(out_root, tl_root, args.lang)
        if _console:
            _console.print(f"tl 模式完成：拷贝 [bold]{copied}[/] 个 TL 脚本；移除遗留 .zh.rpy [bold]{removed}[/] 个")
        else:
            print(f"tl 模式完成：拷贝 {copied} 个 TL 脚本；移除遗留 .zh.rpy {removed} 个")

    # 二次自检（双载风险检测）
    post_build_selfcheck(out_root, mode, args.lang)

    if _console:
        _console.print(f"[bold green]中文构建完成[/]：{out_root}")
    else:
        print(f"中文构建完成：{out_root}")


if __name__ == "__main__":
    main()
