#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
replace_fonts.py - 自动替换 Ren'Py 游戏字体为中文字体

功能：
1. 删除游戏中的所有字体文件（.ttf, .otf）
2. 复制 NotoSansSC 字体到游戏目录
3. 修改所有 .rpy 文件中的字体引用

用法：
  python tools/replace_fonts.py <游戏根目录> [--font-dir 字体源目录]
"""

from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path
from typing import Optional

# 默认字体文件名
DEFAULT_FONTS = {
    'regular': 'NotoSansSC.ttf',
    'bold': 'NotoSansSCBold.ttf',
}

# 字体文件扩展名
FONT_EXTENSIONS = ('.ttf', '.otf', '.TTF', '.OTF')


def find_font_files(game_dir: Path) -> list[Path]:
    """查找游戏目录中的所有字体文件"""
    fonts = []
    for ext in FONT_EXTENSIONS:
        fonts.extend(game_dir.rglob(f'*{ext}'))
    return fonts


def delete_old_fonts(game_dir: Path, backup_dir: Optional[Path] = None) -> list[Path]:
    """删除旧字体文件（可选备份）"""
    fonts = find_font_files(game_dir)
    deleted = []
    
    for font in fonts:
        try:
            if backup_dir:
                backup_dir.mkdir(parents=True, exist_ok=True)
                backup_path = backup_dir / font.name
                shutil.copy2(font, backup_path)
                print(f"  备份: {font.name} -> {backup_path}")
            
            font.unlink()
            deleted.append(font)
            print(f"  删除: {font.relative_to(game_dir)}")
        except (OSError, PermissionError) as e:
            print(f"  ⚠ 无法删除 {font}: {e}")
    
    return deleted


def copy_chinese_fonts(game_dir: Path, font_source_dir: Path) -> dict[str, Path]:
    """复制中文字体到游戏目录"""
    target_font_dir = game_dir / 'game' / 'fonts'
    target_font_dir.mkdir(parents=True, exist_ok=True)
    
    copied = {}
    for key, filename in DEFAULT_FONTS.items():
        source = font_source_dir / filename
        if not source.exists():
            print(f"  ⚠ 源字体不存在: {source}")
            continue
        
        target = target_font_dir / filename
        shutil.copy2(source, target)
        copied[key] = target
        print(f"  复制: {filename} -> {target.relative_to(game_dir)}")
    
    return copied


def update_font_references(game_dir: Path) -> int:
    """更新 .rpy 文件中的字体引用"""
    game_subdir = game_dir / 'game'
    if not game_subdir.exists():
        print(f"  ⚠ game 目录不存在: {game_subdir}")
        return 0
    
    rpy_files = list(game_subdir.rglob('*.rpy'))
    updated_count = 0
    
    # 字体定义的正则模式
    # 匹配: define gui.text_font = "xxx.ttf"
    # 或: style.xxx.font = "xxx.ttf"
    font_pattern = re.compile(
        r'((?:define\s+gui\.\w+_font|style\.\w+\.font)\s*=\s*["\'])([^"\']+\.(?:ttf|otf))(["\'])',
        re.IGNORECASE
    )
    
    for rpy_file in rpy_files:
        try:
            content = rpy_file.read_text(encoding='utf-8')
            original = content
            
            # 替换所有字体引用
            def replace_font(match):
                prefix = match.group(1)
                old_font = match.group(2)
                suffix = match.group(3)
                
                # 根据是否包含 "bold" 选择字体
                if 'bold' in old_font.lower():
                    new_font = 'fonts/NotoSansSCBold.ttf'
                else:
                    new_font = 'fonts/NotoSansSC.ttf'
                
                return f"{prefix}{new_font}{suffix}"
            
            content = font_pattern.sub(replace_font, content)
            
            if content != original:
                rpy_file.write_text(content, encoding='utf-8')
                updated_count += 1
                print(f"  更新: {rpy_file.relative_to(game_dir)}")
        
        except (OSError, UnicodeDecodeError) as e:
            print(f"  ⚠ 无法处理 {rpy_file}: {e}")
    
    return updated_count


def main():
    ap = argparse.ArgumentParser(description='自动替换 Ren\'Py 游戏字体为中文字体')
    ap.add_argument('game_root', help='Ren\'Py 游戏根目录（包含 game 文件夹）')
    ap.add_argument('--font-dir', help='中文字体源目录（默认为当前工作区的 data/fonts）')
    ap.add_argument('--backup', action='store_true', help='备份旧字体到 outputs/font_backup')
    ap.add_argument('--dry-run', action='store_true', help='仅显示将要执行的操作，不实际修改')
    args = ap.parse_args()
    
    game_dir = Path(args.game_root).resolve()
    if not game_dir.exists():
        print(f"❌ 游戏目录不存在: {game_dir}")
        return 1
    
    game_subdir = game_dir / 'game'
    if not game_subdir.exists():
        print(f"❌ 不是有效的 Ren'Py 游戏目录（缺少 game 子目录）: {game_dir}")
        return 1
    
    # 确定字体源目录
    if args.font_dir:
        font_source_dir = Path(args.font_dir).resolve()
    else:
        # 默认使用工作区的 data/fonts
        font_source_dir = Path(__file__).parent.parent / 'data' / 'fonts'
    
    if not font_source_dir.exists():
        print(f"❌ 字体源目录不存在: {font_source_dir}")
        print("提示: 请将 NotoSansSC.ttf 和 NotoSansSCBold.ttf 放到该目录")
        return 1
    
    print("=" * 60)
    print("Ren'Py 游戏字体替换工具")
    print("=" * 60)
    print(f"游戏目录: {game_dir}")
    print(f"字体源: {font_source_dir}")
    print()
    
    if args.dry_run:
        print("⚠ 试运行模式（不会实际修改文件）")
        print()
    
    # 步骤 1: 查找并删除旧字体
    print("▶ 步骤 1: 删除旧字体文件")
    fonts = find_font_files(game_subdir)
    if fonts:
        print(f"  发现 {len(fonts)} 个字体文件:")
        for font in fonts:
            print(f"    - {font.relative_to(game_dir)}")
        
        if not args.dry_run:
            backup_dir = game_dir.parent / 'outputs' / 'font_backup' if args.backup else None
            deleted = delete_old_fonts(game_subdir, backup_dir)
            print(f"  ✓ 已删除 {len(deleted)} 个字体文件")
    else:
        print("  未发现字体文件")
    print()
    
    # 步骤 2: 复制中文字体
    print("▶ 步骤 2: 复制中文字体")
    if not args.dry_run:
        copied = copy_chinese_fonts(game_dir, font_source_dir)
        if copied:
            print(f"  ✓ 已复制 {len(copied)} 个字体文件")
        else:
            print("  ⚠ 未复制任何字体")
    else:
        print("  (试运行: 将复制 NotoSansSC.ttf 和 NotoSansSCBold.ttf)")
    print()
    
    # 步骤 3: 更新字体引用
    print("▶ 步骤 3: 更新 .rpy 文件中的字体引用")
    if not args.dry_run:
        updated = update_font_references(game_dir)
        if updated > 0:
            print(f"  ✓ 已更新 {updated} 个文件")
        else:
            print("  未发现需要更新的字体引用")
    else:
        print("  (试运行: 将扫描并更新所有 .rpy 文件)")
    print()
    
    print("=" * 60)
    if args.dry_run:
        print("✓ 试运行完成（未实际修改文件）")
    else:
        print("✓ 字体替换完成！")
    print("=" * 60)
    
    return 0


if __name__ == '__main__':
    exit(main())
