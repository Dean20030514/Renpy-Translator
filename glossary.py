#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""术语表管理 — 保证跨文件翻译一致性"""

from __future__ import annotations

import csv
import json
import re
import threading
from pathlib import Path
from typing import Optional


class Glossary:
    """术语表：从游戏文件中自动提取 + 手动维护"""

    def __init__(self):
        self._lock = threading.Lock()
        # 角色变量 → 显示名（从 define 提取）
        self.characters: dict[str, str] = {}
        # 通用术语 en → zh
        self.terms: dict[str, str] = {}
        # 翻译记忆：已翻译的 en → zh（相同原文保持翻译一致）
        self.memory: dict[str, str] = {}
        # 术语锁定：这些 key 出现在文本中时，必须使用 terms[key] 作为译名（应少而精）
        self.locked_terms: set[str] = set()
        # 禁翻片段：这些字符串在原文中出现时，译文必须保持同样的英文片段（大小写不敏感）
        self.no_translate: set[str] = set()

    def scan_game_directory(self, game_dir: str) -> None:
        """扫描游戏目录，提取角色定义和关键信息"""
        game_path = Path(game_dir)
        if not game_path.exists():
            print(f"[WARN] 游戏目录不存在: {game_dir}")
            return

        # 匹配 define xxx = Character("Name", ...) 和 DynamicCharacter
        char_re = re.compile(
            r'^\s*define\s+(\w+)\s*=\s*(?:Character|DynamicCharacter)\s*\(\s*["\']([^"\']+)["\']',
            re.MULTILINE
        )
        # 匹配 define config.name = "..."
        config_name_re = re.compile(
            r'^\s*define\s+config\.name\s*=\s*["\']([^"\']+)["\']',
            re.MULTILINE
        )        # 匹配 define config.version = "..."  (不翻译，但可用于报告)
        config_ver_re = re.compile(
            r'^\s*define\s+config\.version\s*=\s*["\']((?:[^"\']|\\.)*)["\'\)]',
            re.MULTILINE
        )
        for rpy in game_path.rglob('*.rpy'):
            # 跳过引擎自带文件
            try:
                rel_parts = rpy.relative_to(game_path).parts
            except ValueError:
                continue
            if rel_parts and rel_parts[0].lower() in ('renpy', 'lib', '__pycache__'):
                continue

            try:
                content = rpy.read_text(encoding='utf-8')
            except (UnicodeDecodeError, OSError):
                try:
                    content = rpy.read_text(encoding='latin-1')
                except Exception:
                    continue

            for m in char_re.finditer(content):
                var_name = m.group(1)
                display_name = m.group(2)
                self.characters[var_name] = display_name

            for m in config_name_re.finditer(content):
                self.terms['__game_name__'] = m.group(1)

            for m in config_ver_re.finditer(content):
                self.terms['__game_version__'] = m.group(1)

        if self.characters:
            print(f"[INFO] 扫描到 {len(self.characters)} 个角色定义")
            # 将角色显示名也加入术语表，避免不同翻译
            for var, name in self.characters.items():
                if name and len(name) > 1 and name not in self.terms:
                    # 不自动翻译角色名 — 只做记录，由 prompt 中提示 AI
                    pass

    def load_dict(self, filepath: str) -> None:
        """加载外部词典（支持 CSV 和 JSONL 格式）

        CSV 格式：每行 "english,chinese" 或 "english\tchinese"
        JSONL 格式：每行 {"en": "...", "zh": "..."}
        """
        path = Path(filepath)
        if not path.exists():
            print(f"[WARN] 词典文件不存在: {filepath}")
            return

        count = 0
        suffix = path.suffix.lower()
        text = path.read_text(encoding='utf-8')

        if suffix == '.jsonl':
            for line in text.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    en = obj.get('en', obj.get('original', obj.get('source', '')))
                    zh = obj.get('zh', obj.get('translation', obj.get('target', '')))
                    if en and zh:
                        self.terms[en] = zh
                        count += 1
                except json.JSONDecodeError:
                    continue
        elif suffix in ('.csv', '.tsv', '.txt'):
            delimiter = '\t' if suffix == '.tsv' else ','
            for row in csv.reader(text.splitlines(), delimiter=delimiter):
                if len(row) >= 2 and row[0].strip() and row[1].strip():
                    # 跳过表头
                    if row[0].lower() in ('en', 'english', 'source', 'original'):
                        continue
                    self.terms[row[0].strip()] = row[1].strip()
                    count += 1
        else:
            print(f"[WARN] 不支持的词典格式: {suffix}")
            return

        print(f"[INFO] 加载词典 {path.name}: {count} 条术语")

    def load_system_terms(self, filepath: str) -> None:
        """加载项目级系统 UI 术语（JSON 格式：{英文: 中文}）

        这些术语通常用于菜单、存读档、设置等固定文案，优先级高于自动记忆。
        """
        path = Path(filepath)
        if not path.exists():
            return

        try:
            data = json.loads(path.read_text(encoding='utf-8'))
        except Exception:
            print(f"[WARN] 系统 UI 术语表解析失败: {filepath}")
            return

        added = 0
        if isinstance(data, dict):
            for en, zh in data.items():
                if isinstance(en, str) and isinstance(zh, str) and en.strip() and zh.strip():
                    self.terms[en] = zh
                    added += 1

        if added:
            print(f"[INFO] 加载系统 UI 术语: {added} 条")

    def load(self, filepath: str) -> None:
        """加载术语表（JSON 格式）"""
        path = Path(filepath)
        if not path.exists():
            return
        data = json.loads(path.read_text(encoding='utf-8'))
        self.characters.update(data.get('characters', {}))
        self.terms.update(data.get('terms', {}))
        self.memory.update(data.get('memory', {}))
        # 新字段向下兼容：旧版本 glossary.json 没有这些字段时，默认空集合
        self.locked_terms = set(data.get('locked_terms', []))
        self.no_translate = set(data.get('no_translate', []))
        print(f"[INFO] 加载术语表: {len(self.characters)} 角色, "
              f"{len(self.terms)} 术语, {len(self.memory)} 翻译记忆, "
              f"{len(self.locked_terms)} 锁定术语, {len(self.no_translate)} 禁翻片段")

    def save(self, filepath: str) -> None:
        """保存术语表"""
        with self._lock:
            data = {
                'characters': self.characters,
                'terms': self.terms,
                'memory': self.memory,
                # locked_terms / no_translate 主要由高级用户少量维护，避免滥用
                'locked_terms': sorted(self.locked_terms),
                'no_translate': sorted(self.no_translate),
            }
            path = Path(filepath)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

    def update_from_translations(self, translations: list[dict]) -> None:
        """从翻译结果中更新翻译记忆（过滤低质量/太短的条目）"""
        with self._lock:
            for item in translations:
                original = item.get('original', '')
                zh = item.get('zh', '')
                if not original or not zh:
                    continue
                if len(original) <= 3:
                    continue
                if original == zh:
                    continue
                if original.strip().isdigit():
                    continue
                # 跳过纯标点符号
                import string
                if all(c in string.punctuation + string.whitespace for c in original):
                    continue
                # 跳过已在固定术语表中的条目（避免重复）
                if original in self.terms:
                    continue
                self.memory[original] = zh

    def to_prompt_text(self) -> str:
        """生成用于 prompt 的术语表文本"""
        with self._lock:
            return self._to_prompt_text_unlocked()

    def _to_prompt_text_unlocked(self) -> str:
        """内部实现（无锁）"""
        parts = []

        if self.characters:
            parts.append("### 角色变量（方括号内的变量名，绝对不能翻译）")
            for var, name in sorted(self.characters.items()):
                parts.append(f"- [{var}] = {name}")

        if self.terms:
            parts.append("\n### 固定术语")
            for en, zh in sorted(self.terms.items()):
                if not en.startswith('__'):
                    parts.append(f"- {en} → {zh}")

        # 锁定术语：这些 key 出现在原文中时，AI 必须使用指定译名（建议数量少而精）
        if self.locked_terms:
            parts.append("\n### 锁定术语（出现时必须严格使用指定译名）")
            for en in sorted(self.locked_terms):
                zh = self.terms.get(en, "")
                if not zh:
                    continue
                parts.append(f"- {en} → {zh}  （必须使用此译名，不得随意改动）")

        # 禁翻片段：这些英文片段在原文中出现时，必须保持英文不翻译
        if self.no_translate:
            parts.append("\n### 禁翻片段（出现时保持原文英文，不要翻译）")
            for s in sorted(self.no_translate):
                parts.append(f"- {s}")

        # 只包含部分翻译记忆（避免 prompt 太长）
        if self.memory:
            # 取较长的、有代表性的条目，限制总字符数
            representative = sorted(
                [(en, zh) for en, zh in self.memory.items() if len(en) > 10],
                key=lambda x: len(x[0]),
                reverse=True
            )
            if representative:
                parts.append("\n### 翻译参考（请保持一致）")
                char_budget = 3000
                used = 0
                for en, zh in representative:
                    entry = f'- "{en}" → "{zh}"'
                    if used + len(entry) > char_budget:
                        break
                    parts.append(entry)
                    used += len(entry)

        return '\n'.join(parts) if parts else ""
