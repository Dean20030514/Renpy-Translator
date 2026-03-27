#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ren'Py tl 文件解析器 — 解析 translate 块并提取/回填翻译条目。

独立模块，只依赖标准库 (os, re, dataclasses, pathlib, collections)。
"""

import os
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union


# ============================================================
# 数据结构
# ============================================================

@dataclass
class DialogueEntry:
    """对话翻译条目"""
    identifier: str          # "start_636ae3f5"
    original: str            # 原文 (从注释提取)
    translation: str         # 译文 (空字符串 = 未翻译)
    character: str           # "e" 或 "" (旁白)
    source_file: str         # "game/script.rpy"
    source_line: int         # 95
    tl_file: str             # tl 文件路径
    tl_line: int             # say 行在 tl 文件中的行号 (1-based)
    block_start_line: int    # translate 块的起始行号


@dataclass
class StringEntry:
    """字符串翻译条目"""
    old: str                 # 原文
    new: str                 # 译文 (空字符串 = 未翻译)
    source_file: str         # "game/screens.rpy"
    source_line: int         # 281
    tl_file: str
    tl_line: int             # new 行的行号 (1-based)
    block_start_line: int    # translate strings 块的起始行号


@dataclass
class TlParseResult:
    """单个 tl 文件的解析结果"""
    dialogues: list[DialogueEntry]
    strings: list[StringEntry]
    file_path: str


# ============================================================
# 常量 & 正则
# ============================================================

_NON_SAY_KEYWORDS = frozenset({
    'show', 'hide', 'with', 'scene',
    'play', 'stop', 'queue', 'pause',
    'voice', 'window',
    'python', 'return', 'jump', 'call', 'pass',
    'define', 'default', 'init', 'label',
    'screen', 'transform', 'style', 'image',
})

_COMPLEX_KEYWORDS = frozenset({'if', 'elif', 'else'})

_RE_STRINGS_HEADER = re.compile(r'^translate\s+\w+\s+strings\s*:\s*$')
_RE_PYTHON_HEADER = re.compile(r'^translate\s+\w+\s+python\s*:\s*$')
_RE_STYLE_HEADER = re.compile(r'^translate\s+\w+\s+style\s+')
_RE_DIALOGUE_HEADER = re.compile(r'^translate\s+\w+\s+(\w+)\s*:\s*$')
_RE_SOURCE_COMMENT = re.compile(r'^(\S+\.rpy[mc]?)\s*:\s*(\d+)\s*$')

# AI 返回译文时可能包裹的外层引号对，fill_translation 回填前自动剥离
_QUOTE_STRIP_PAIRS = [('"', '"'), ('\u201c', '\u201d'), ('\uff02', '\uff02')]

# AI 有时会把 prompt 中的元数据标记回显到译文中
_RE_META_ID = re.compile(r'\[ID:\s*\S*\]\s*')
_RE_META_CHAR = re.compile(r'\[Char:\s*\w*\]\s*')
_RE_META_STRING = re.compile(r'\[STRING\]\s*')


def _sanitize_translation(text: str) -> str:
    """清理 AI 返回的译文，防止破坏 Ren'Py 语法。

    处理三类问题：
    1. 元数据泄漏 ([ID: ...], [Char: ...], [STRING])
    2. 外层引号包裹 ("text", \u201ctext\u201d, \uff02text\uff02)
    3. 内嵌未转义 ASCII 引号 ("word" → \\"word\\")
    """
    # 1. 去除元数据标记
    text = _RE_META_ID.sub('', text)
    text = _RE_META_CHAR.sub('', text)
    text = _RE_META_STRING.sub('', text)

    # 去除换行（AI 有时在元数据后换行再写译文）
    text = text.replace('\n', ' ').replace('\r', '').strip()

    # 2. 循环剥离外层引号（AI 可能返回 ""text""，单层剥离会残留一层导致 new ""text""）
    while len(text) >= 2:
        stripped = False
        for lq, rq in _QUOTE_STRIP_PAIRS:
            if text[0] == lq and text[-1] == rq:
                text = text[1:-1].strip()
                stripped = True
                break
        if not stripped:
            break

    # 2b. 单侧残存 "（如 "译文"" 剥一层后变成 译文"）
    if text.count('"') == 1:
        if text.startswith('"'):
            text = text[1:]
        elif text.endswith('"'):
            text = text[:-1]

    # 3. 转义内嵌 ASCII 引号（保留已转义的 \"）
    temp = text.replace('\\"', '\x00_ESCAPED_\x00')
    if '"' in temp:
        temp = temp.replace('"', '\\"')
    text = temp.replace('\x00_ESCAPED_\x00', '\\"')

    return text


# ============================================================
# 辅助函数
# ============================================================

def extract_quoted_text(line: str) -> Optional[str]:
    """提取行中第一对未转义双引号之间的文本。

    处理转义：\\" 不算结束引号，\\\\ 是转义反斜杠。
    没有合法引号对时返回 None。
    """
    start = line.find('"')
    if start == -1:
        return None

    i = start + 1
    chars: list[str] = []
    while i < len(line):
        ch = line[i]
        if ch == '\\' and i + 1 < len(line):
            chars.append(line[i:i + 2])
            i += 2
        elif ch == '"':
            return ''.join(chars)
        else:
            chars.append(ch)
            i += 1

    return None


# ============================================================
# 核心解析
# ============================================================

def parse_tl_file(filepath: str) -> TlParseResult:
    """解析单个 tl 文件，提取所有对话和字符串条目。

    解析规则:
    1. ``translate <lang> <identifier>:``  → 对话块
    2. ``translate <lang> strings:``       → 字符串块
    3. ``translate <lang> python:``        → 跳过
    4. ``translate <lang> style ...``      → 跳过
    5. 空行不改变状态；非缩进非空行结束当前块。
    """
    content = Path(filepath).read_text(encoding='utf-8-sig')
    lines = content.splitlines()

    dialogues: list[DialogueEntry] = []
    strings: list[StringEntry] = []

    state = 'IDLE'  # IDLE | DIALOGUE | STRINGS | SKIP

    # 缓存顶层 source 注释，给下一个 dialogue 块用
    pending_src_file = ''
    pending_src_line = 0

    # --- Dialogue 块状态 ---
    dlg_id = ''
    dlg_original = ''
    dlg_src_file = ''
    dlg_src_line = 0
    dlg_block_start = 0
    dlg_found_say = False

    # --- Strings 块状态 ---
    str_block_start = 0
    str_old_text = ''
    str_src_file = ''
    str_src_line = 0
    str_has_old = False

    for line_idx, raw_line in enumerate(lines):
        line_no = line_idx + 1
        stripped = raw_line.strip()

        if not stripped:
            continue

        is_indented = raw_line[0] in (' ', '\t')

        # ── 顶层（非缩进）行 ──────────────────────────────
        if not is_indented:
            # 1) translate ... strings:
            if _RE_STRINGS_HEADER.match(stripped):
                state = 'STRINGS'
                str_block_start = line_no
                str_old_text = ''
                str_src_file = ''
                str_src_line = 0
                str_has_old = False
                pending_src_file = ''
                pending_src_line = 0
                continue

            # 2) translate ... python: / style ...
            if _RE_PYTHON_HEADER.match(stripped) or _RE_STYLE_HEADER.match(stripped):
                state = 'SKIP'
                pending_src_file = ''
                pending_src_line = 0
                continue

            # 3) translate ... <identifier>:  (对话块)
            m_dlg = _RE_DIALOGUE_HEADER.match(stripped)
            if m_dlg:
                state = 'DIALOGUE'
                dlg_id = m_dlg.group(1)
                dlg_block_start = line_no
                dlg_src_file = pending_src_file
                dlg_src_line = pending_src_line
                dlg_original = ''
                dlg_found_say = False
                pending_src_file = ''
                pending_src_line = 0
                continue

            # 4) 顶层注释
            if stripped.startswith('#'):
                comment_body = stripped[1:].strip()
                m_src = _RE_SOURCE_COMMENT.match(comment_body)
                if m_src:
                    pending_src_file = m_src.group(1)
                    pending_src_line = int(m_src.group(2))
                # 非 source 注释不清空 pending（允许注释与 header 之间有其他注释行）
                state = 'IDLE'
                continue

            # 5) 其他非缩进行 → 回到 IDLE
            state = 'IDLE'
            pending_src_file = ''
            pending_src_line = 0
            continue

        # ── 缩进行（块内部） ──────────────────────────────
        if state == 'DIALOGUE':
            if dlg_found_say:
                continue

            # 注释行
            if stripped.startswith('#'):
                comment_body = stripped[1:].strip()

                # 块内 source 注释（不常见但存在）
                m_src = _RE_SOURCE_COMMENT.match(comment_body)
                if m_src:
                    if not dlg_src_file:
                        dlg_src_file = m_src.group(1)
                        dlg_src_line = int(m_src.group(2))
                    continue

                # 原文注释: # e "..." 或 # "..."
                if '"' in comment_body:
                    text = extract_quoted_text(comment_body)
                    if text is not None:
                        dlg_original = text
                continue

            # 非注释缩进行
            words = stripped.split()
            if not words:
                continue

            first_word = words[0].rstrip(':')

            # if / elif / else → 复杂条件翻译块，视为已填充
            if first_word in _COMPLEX_KEYWORDS:
                dlg_found_say = True
                continue

            # show / hide / voice 等非 say 语句
            if first_word in _NON_SAY_KEYWORDS or stripped.startswith('$'):
                continue

            # 尝试匹配 say 行: <character> "..." 或 "..."
            if '"' in stripped:
                text = extract_quoted_text(stripped)
                if text is not None:
                    quote_pos = stripped.index('"')
                    character = stripped[:quote_pos].strip()
                    dlg_found_say = True
                    dialogues.append(DialogueEntry(
                        identifier=dlg_id,
                        original=dlg_original,
                        translation=text,
                        character=character,
                        source_file=dlg_src_file,
                        source_line=dlg_src_line,
                        tl_file=filepath,
                        tl_line=line_no,
                        block_start_line=dlg_block_start,
                    ))

        elif state == 'STRINGS':
            # 注释行 → 可能是 source 注释
            if stripped.startswith('#'):
                comment_body = stripped[1:].strip()
                m_src = _RE_SOURCE_COMMENT.match(comment_body)
                if m_src:
                    str_src_file = m_src.group(1)
                    str_src_line = int(m_src.group(2))
                continue

            # old "..."
            if stripped.startswith('old ') and '"' in stripped:
                text = extract_quoted_text(stripped)
                if text is not None:
                    str_old_text = text
                    str_has_old = True
                continue

            # new "..."
            if stripped.startswith('new ') and '"' in stripped and str_has_old:
                text = extract_quoted_text(stripped)
                if text is not None:
                    strings.append(StringEntry(
                        old=str_old_text,
                        new=text,
                        source_file=str_src_file,
                        source_line=str_src_line,
                        tl_file=filepath,
                        tl_line=line_no,
                        block_start_line=str_block_start,
                    ))
                    str_has_old = False
                    str_src_file = ''
                    str_src_line = 0
                continue

        # state == 'SKIP' 或 'IDLE': 忽略缩进行

    return TlParseResult(
        dialogues=dialogues,
        strings=strings,
        file_path=filepath,
    )


def scan_tl_directory(tl_dir: str, language: str = "chinese") -> list[TlParseResult]:
    """扫描 tl/<language>/ 目录下所有 .rpy 文件，逐个解析。

    排除 common.rpy（Ren'Py 引擎内置字符串，通常不需要翻译）。
    """
    lang_dir = Path(tl_dir) / language
    if not lang_dir.is_dir():
        print(f"[tl_parser] 目录不存在: {lang_dir}")
        return []

    results: list[TlParseResult] = []
    for rpy_file in sorted(lang_dir.rglob('*.rpy')):
        if rpy_file.name == 'common.rpy':
            continue
        try:
            results.append(parse_tl_file(str(rpy_file)))
        except Exception as e:
            print(f"[tl_parser] 解析失败 {rpy_file}: {e}")

    return results


def get_untranslated_entries(
    results: list[TlParseResult],
) -> tuple[list[DialogueEntry], list[StringEntry]]:
    """从解析结果中筛选未翻译的条目。

    - DialogueEntry.translation 为空字符串
    - StringEntry.new 为空字符串
    """
    dialogues: list[DialogueEntry] = []
    strings_list: list[StringEntry] = []
    for r in results:
        dialogues.extend(d for d in r.dialogues if d.translation == '')
        strings_list.extend(s for s in r.strings if s.new == '')
    return dialogues, strings_list


def fill_translation(
    tl_file_path: str,
    entries: list[Union[DialogueEntry, StringEntry]],
) -> str:
    """将翻译结果回填到 tl 文件，返回修改后的文件内容（不直接写文件）。

    回填前校验 tl_line 对应的行确实包含空字符串 ``""``,
    否则跳过并打印 warning。
    """
    content = Path(tl_file_path).read_text(encoding='utf-8-sig')
    file_lines = content.splitlines()
    has_trailing_nl = content.endswith('\n')

    for entry in entries:
        new_text = entry.translation if isinstance(entry, DialogueEntry) else entry.new
        if not new_text:
            continue

        new_text = _sanitize_translation(new_text)
        if not new_text:
            continue

        line_idx = entry.tl_line - 1
        if line_idx < 0 or line_idx >= len(file_lines):
            print(f"[WARNING] tl_line {entry.tl_line} 超出范围 "
                  f"(文件共 {len(file_lines)} 行): {tl_file_path}")
            continue

        line = file_lines[line_idx]
        if '""' not in line:
            print(f"[WARNING] 第 {entry.tl_line} 行不含空字符串 \"\","
                  f" 可能已被修改，跳过: {tl_file_path}")
            continue

        file_lines[line_idx] = line.replace('""', f'"{new_text}"', 1)

    result = '\n'.join(file_lines)
    if has_trailing_nl:
        result += '\n'
    return result


_RE_TRANSLATE_BLOCK = re.compile(r'^translate\s+\w+\s+\w+\s*:\s*$')


def postprocess_tl_file(file_path: str) -> dict:
    """Post-process a tl file after fill_translation to fix Ren'Py compatibility issues.

    Fixes:
    1. Remove ``nvl clear`` from inside translate blocks (Ren'Py 7.x compat).
    2. Add ``pass`` to translate blocks left empty after removal.

    Returns dict with fix counts: {"nvl_removed": int, "pass_added": int}.
    """
    content = Path(file_path).read_text(encoding='utf-8-sig')
    lines = content.splitlines()
    has_trailing_nl = content.endswith('\n')

    new_lines: list[str] = []
    stats = {"nvl_removed": 0, "pass_added": 0}
    i = 0

    while i < len(lines):
        header = lines[i].strip()
        if _RE_TRANSLATE_BLOCK.match(header) and 'strings' not in header:
            new_lines.append(lines[i])
            i += 1

            block_lines: list[str] = []
            has_code = False
            while i < len(lines):
                s = lines[i].strip()
                if s == '' or s.startswith('#'):
                    block_lines.append(lines[i])
                    i += 1
                    continue
                if _RE_TRANSLATE_BLOCK.match(s) or s.startswith('translate '):
                    break
                if s == 'nvl clear':
                    stats["nvl_removed"] += 1
                    i += 1
                    continue
                has_code = True
                block_lines.append(lines[i])
                i += 1
            if not has_code:
                new_lines.append('    pass')
                stats["pass_added"] += 1
            new_lines.extend(block_lines)
        else:
            new_lines.append(lines[i])
            i += 1

    result = '\n'.join(new_lines)
    if has_trailing_nl:
        result += '\n'

    if stats["nvl_removed"] or stats["pass_added"]:
        Path(file_path).write_text(result, encoding='utf-8')

    return stats


def postprocess_tl_directory(tl_dir: str, lang: str) -> dict:
    """Post-process all tl files in a directory after translation.

    Returns aggregate stats.
    """
    tl_path = Path(tl_dir) / lang
    if not tl_path.exists():
        return {"files": 0, "nvl_removed": 0, "pass_added": 0}

    totals = {"files": 0, "nvl_removed": 0, "pass_added": 0}
    for rpy in sorted(tl_path.rglob("*.rpy")):
        stats = postprocess_tl_file(str(rpy))
        if stats["nvl_removed"] or stats["pass_added"]:
            totals["files"] += 1
            totals["nvl_removed"] += stats["nvl_removed"]
            totals["pass_added"] += stats["pass_added"]

    if totals["files"]:
        print(f"[TL-POSTPROCESS] 修复 {totals['files']} 个文件: "
              f"移除 {totals['nvl_removed']} 处 nvl clear, "
              f"补 {totals['pass_added']} 处 pass")
    return totals


def print_tl_stats(results: list[TlParseResult]) -> None:
    """打印统计摘要。"""
    total_d = trans_d = 0
    total_s = trans_s = 0
    untrans_by_src: dict[str, int] = defaultdict(int)

    for r in results:
        for d in r.dialogues:
            total_d += 1
            if d.translation:
                trans_d += 1
            else:
                untrans_by_src[d.source_file or r.file_path] += 1
        for s in r.strings:
            total_s += 1
            if s.new:
                trans_s += 1
            else:
                untrans_by_src[s.source_file or r.file_path] += 1

    print("\n=== TL 解析统计 ===")
    print(f"文件数: {len(results)}")
    print(f"对话条目: 总计 {total_d} / 已翻译 {trans_d} / 待翻译 {total_d - trans_d}")
    print(f"字符串条目: 总计 {total_s} / 已翻译 {trans_s} / 待翻译 {total_s - trans_s}")

    if untrans_by_src:
        print("\n待翻译数量 Top 10 (按源文件):")
        for src, cnt in sorted(untrans_by_src.items(), key=lambda x: -x[1])[:10]:
            print(f"  {src}: {cnt}")


# ============================================================
# 内置自测
# ============================================================

def _run_self_tests() -> None:
    import tempfile

    passed = 0
    failed = 0

    def _assert(condition: bool, msg: str):
        nonlocal passed, failed
        if condition:
            passed += 1
        else:
            failed += 1
            print(f"  FAIL: {msg}")

    def _write_tmp(text: str) -> str:
        f = tempfile.NamedTemporaryFile(
            mode='w', suffix='.rpy', delete=False, encoding='utf-8')
        f.write(text)
        f.close()
        return f.name

    print("运行自测...\n")

    # ── 1. extract_quoted_text ──
    print("[1] extract_quoted_text")
    _assert(extract_quoted_text('e ""') == '', 'empty string')
    _assert(extract_quoted_text('e "Hello"') == 'Hello', 'simple text')
    _assert(extract_quoted_text('# e "Thank you"') == 'Thank you', 'comment text')
    _assert(extract_quoted_text(r'e "Hello \"World\""') == r'Hello \"World\"',
            'escaped quotes')
    _assert(extract_quoted_text(r'e "path\\to\\file"') == r'path\\to\\file',
            'escaped backslashes')
    _assert(extract_quoted_text('no quotes here') is None, 'no quotes')
    _assert(extract_quoted_text('"Just narration"') == 'Just narration', 'narration')
    _assert(extract_quoted_text('"unclosed') is None, 'unclosed quote')
    _assert(extract_quoted_text('old "First\\nSecond"') == 'First\\nSecond',
            'newline escape')
    print()

    # ── 2. 正常对话块（未翻译 + 已翻译） ──
    print("[2] 对话块解析")
    dlg_text = (
        '# game/script.rpy:95\n'
        'translate chinese start_636ae3f5:\n'
        '\n'
        '    # e "Thank you for taking a look."\n'
        '    e ""\n'
        '\n'
        '# game/script.rpy:98\n'
        'translate chinese start_abcd1234:\n'
        '\n'
        '    # e "This is already translated."\n'
        '    e "这已经翻译过了。"\n'
    )
    p = _write_tmp(dlg_text)
    try:
        r = parse_tl_file(p)
        _assert(len(r.dialogues) == 2, f'expected 2 dialogues, got {len(r.dialogues)}')
        d0 = r.dialogues[0]
        _assert(d0.identifier == 'start_636ae3f5', f'id={d0.identifier}')
        _assert(d0.original == 'Thank you for taking a look.', f'orig={d0.original}')
        _assert(d0.translation == '', f'trans should be empty, got "{d0.translation}"')
        _assert(d0.character == 'e', f'char={d0.character}')
        _assert(d0.source_file == 'game/script.rpy', f'src={d0.source_file}')
        _assert(d0.source_line == 95, f'src_line={d0.source_line}')
        _assert(d0.tl_line == 5, f'tl_line={d0.tl_line}')
        _assert(d0.block_start_line == 2, f'block_start={d0.block_start_line}')

        d1 = r.dialogues[1]
        _assert(d1.translation == '这已经翻译过了。', f'trans={d1.translation}')
        _assert(d1.source_line == 98, f'src_line={d1.source_line}')

        ud, us = get_untranslated_entries([r])
        _assert(len(ud) == 1, f'untranslated dialogues: {len(ud)}')
    finally:
        os.unlink(p)
    print()

    # ── 3. 旁白（无 character） ──
    print("[3] 旁白（无 character）")
    nar_text = (
        '# game/script.rpy:10\n'
        'translate chinese narrator_0001:\n'
        '\n'
        '    # "You enter the dark room."\n'
        '    ""\n'
    )
    p = _write_tmp(nar_text)
    try:
        r = parse_tl_file(p)
        _assert(len(r.dialogues) == 1, f'count={len(r.dialogues)}')
        d = r.dialogues[0]
        _assert(d.character == '', f'char should be empty, got "{d.character}"')
        _assert(d.original == 'You enter the dark room.', f'orig={d.original}')
        _assert(d.translation == '', 'should be untranslated')
    finally:
        os.unlink(p)
    print()

    # ── 4. 字符串块 ──
    print("[4] 字符串块解析")
    str_text = (
        'translate chinese strings:\n'
        '\n'
        '    # game/screens.rpy:281\n'
        '    old "History"\n'
        '    new ""\n'
        '\n'
        '    # game/screens.rpy:283\n'
        '    old "Skip"\n'
        '    new "快进"\n'
        '\n'
        '    old "Save"\n'
        '    new ""\n'
    )
    p = _write_tmp(str_text)
    try:
        r = parse_tl_file(p)
        _assert(len(r.strings) == 3, f'expected 3 strings, got {len(r.strings)}')

        s0 = r.strings[0]
        _assert(s0.old == 'History', f'old={s0.old}')
        _assert(s0.new == '', f'new should be empty')
        _assert(s0.source_file == 'game/screens.rpy', f'src={s0.source_file}')
        _assert(s0.source_line == 281, f'src_line={s0.source_line}')
        _assert(s0.tl_line == 5, f'tl_line={s0.tl_line}')

        s1 = r.strings[1]
        _assert(s1.old == 'Skip', f'old={s1.old}')
        _assert(s1.new == '快进', f'new={s1.new}')
        _assert(s1.source_line == 283, f'src_line={s1.source_line}')

        s2 = r.strings[2]
        _assert(s2.source_file == '', 'no source comment')
        _assert(s2.source_line == 0, 'no source line')

        ud, us = get_untranslated_entries([r])
        _assert(len(us) == 2, f'untranslated strings: {len(us)}')
    finally:
        os.unlink(p)
    print()

    # ── 5. show/hide 跳过 + 复杂块 + python 块 ──
    print("[5] 非 say 跳过 + 复杂块 + python/style 块")
    mixed_text = (
        '# game/script.rpy:10\n'
        'translate chinese show_block:\n'
        '\n'
        '    show eileen happy\n'
        '    with dissolve\n'
        '    # e "Hello there!"\n'
        '    e ""\n'
        '\n'
        '# game/script.rpy:20\n'
        'translate chinese complex_block:\n'
        '\n'
        '    # e "Greetings"\n'
        '    if some_flag:\n'
        '        e "你好"\n'
        '    else:\n'
        '        e "您好"\n'
        '\n'
        'translate chinese python:\n'
        '    pass\n'
        '\n'
        'translate chinese style default:\n'
        '    font "DejaVuSans.ttf"\n'
    )
    p = _write_tmp(mixed_text)
    try:
        r = parse_tl_file(p)
        _assert(len(r.dialogues) == 1, f'expected 1 dialogue, got {len(r.dialogues)}')
        d = r.dialogues[0]
        _assert(d.identifier == 'show_block', f'id={d.identifier}')
        _assert(d.original == 'Hello there!', f'orig={d.original}')
        _assert(d.translation == '', 'should be untranslated')
        _assert(d.character == 'e', f'char={d.character}')
        _assert(d.tl_line == 7, f'tl_line={d.tl_line}')
    finally:
        os.unlink(p)
    print()

    # ── 6. fill_translation ──
    print("[6] fill_translation")
    fill_text = (
        '# game/script.rpy:95\n'
        'translate chinese start_636ae3f5:\n'
        '\n'
        '    # e "Hello"\n'
        '    e ""\n'
        '\n'
        'translate chinese strings:\n'
        '\n'
        '    old "Save"\n'
        '    new ""\n'
    )
    p = _write_tmp(fill_text)
    try:
        r = parse_tl_file(p)
        d = r.dialogues[0]
        s = r.strings[0]

        d.translation = '你好'
        s.new = '保存'
        modified = fill_translation(p, [d, s])

        _assert('e "你好"' in modified, 'dialogue filled')
        _assert('new "保存"' in modified, 'string filled')
        _assert('""' not in modified, 'no empty strings left')
    finally:
        os.unlink(p)
    print()

    # ── 7. fill_translation 校验：已修改的行跳过 ──
    print("[7] fill_translation 跳过已修改行")
    skip_text = (
        'translate chinese strings:\n'
        '\n'
        '    old "Hello"\n'
        '    new "你好"\n'
    )
    p = _write_tmp(skip_text)
    try:
        r = parse_tl_file(p)
        s = r.strings[0]
        _assert(s.new == '你好', 'already translated')
        s.new = '哈喽'
        modified = fill_translation(p, [s])
        _assert('new "你好"' in modified, 'should NOT be overwritten (no "" on that line)')
    finally:
        os.unlink(p)
    print()

    # ── 8. 转义引号处理 ──
    print("[8] 转义引号")
    esc_text = (
        '# game/script.rpy:1\n'
        'translate chinese esc_block:\n'
        '\n'
        '    # e "She said \\"hello\\""\n'
        '    e ""\n'
    )
    p = _write_tmp(esc_text)
    try:
        r = parse_tl_file(p)
        _assert(len(r.dialogues) == 1, f'count={len(r.dialogues)}')
        d = r.dialogues[0]
        _assert(d.original == 'She said \\"hello\\"', f'orig={d.original!r}')
        _assert(d.translation == '', 'untranslated')
    finally:
        os.unlink(p)
    print()

    # ── 9. extend / nvl 角色 ──
    print("[9] extend / nvl 角色")
    ext_text = (
        '# game/script.rpy:50\n'
        'translate chinese ext_block:\n'
        '\n'
        '    # extend "and goodbye."\n'
        '    extend ""\n'
    )
    p = _write_tmp(ext_text)
    try:
        r = parse_tl_file(p)
        _assert(len(r.dialogues) == 1, f'count={len(r.dialogues)}')
        d = r.dialogues[0]
        _assert(d.character == 'extend', f'char={d.character}')
        _assert(d.original == 'and goodbye.', f'orig={d.original}')
    finally:
        os.unlink(p)
    print()

    # ── 10. 无 source 注释的对话块 ──
    print("[10] 无 source 注释")
    nosrc_text = (
        'translate chinese no_source_block:\n'
        '\n'
        '    # e "No source line."\n'
        '    e ""\n'
    )
    p = _write_tmp(nosrc_text)
    try:
        r = parse_tl_file(p)
        d = r.dialogues[0]
        _assert(d.source_file == '', f'src should be empty, got "{d.source_file}"')
        _assert(d.source_line == 0, f'src_line should be 0, got {d.source_line}')
    finally:
        os.unlink(p)
    print()

    # ── 汇总 ──
    total = passed + failed
    print(f"\n{'='*40}")
    print(f"自测完成: {passed}/{total} 通过", end='')
    if failed:
        print(f", {failed} 失败")
    else:
        print(" OK")


# ============================================================
# CLI
# ============================================================

if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        _run_self_tests()
    elif len(sys.argv) > 1:
        target = sys.argv[1]
        if os.path.isfile(target):
            r = parse_tl_file(target)
            print_tl_stats([r])
        elif os.path.isdir(target):
            lang = sys.argv[2] if len(sys.argv) > 2 else 'chinese'
            results = scan_tl_directory(target, lang)
            print_tl_stats(results)
        else:
            print(f"路径不存在: {target}")
    else:
        print("用法:")
        print("  python tl_parser.py --test              运行自测")
        print("  python tl_parser.py <file.rpy>          解析单个文件")
        print("  python tl_parser.py <tl_dir> [language]  扫描目录")
