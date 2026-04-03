"""Screen text translator — 翻译 Ren'Py screen 定义中的裸英文字符串。

Ren'Py 的 Generate Translations 只提取 Say 对话和 _() 包裹的字符串，
screen 内的裸 text/textbutton/tt.Action 不会被 tl 框架覆盖。
本模块直接修改源 .rpy 文件中的英文字符串为中文。

用法:
    python main.py --game-dir /path/to/game --tl-screen --provider xai --api-key KEY
    python main.py --game-dir /path/to/game --tl-mode --tl-screen  # tl-mode 后自动补充
"""

import argparse
import json
import logging
import os
import re
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ── 数据结构 ──────────────────────────────────────────────────────

@dataclass
class ScreenTextEntry:
    """screen 内可翻译文本条目。"""
    file_path: str       # 源 .rpy 绝对路径
    line_number: int     # 1-based 行号
    pattern_type: str    # "text" | "textbutton" | "tt_action"
    original: str        # 引号内原文（未转义）


# ── 正则 ──────────────────────────────────────────────────────────

_RE_TEXT = re.compile(r'^(\s+text\s+)"((?:[^"\\]|\\.)*)"')
_RE_TEXTBUTTON = re.compile(r'^(\s+textbutton\s+)"((?:[^"\\]|\\.)*)"')
_RE_TT_ACTION = re.compile(r'(tt\.Action\s*\(\s*)"((?:[^"\\]|\\.)*)"(\s*\))')
# Notify("...") 弹出通知，与 tt.Action 角色相同
_RE_NOTIFY = re.compile(r'(Notify\s*\(\s*)"((?:[^"\\]|\\.)*)"(\s*\))')

# 跳过判断用
_RE_PURE_VAR = re.compile(r'^\[[\w.!]+\]$')
_FILE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.webp', '.gif', '.mp3',
                    '.ogg', '.wav', '.ttf', '.otf', '.rpyc', '.rpy')

# ── 扫描 ──────────────────────────────────────────────────────────

def scan_screen_files(game_dir: Path) -> list[Path]:
    """扫描 game_dir 下所有 .rpy 文件（排除 tl/、renpy/）。"""
    result = []
    for rpy in sorted(game_dir.rglob("*.rpy")):
        rel = rpy.relative_to(game_dir)
        parts = rel.parts
        if any(p in ("tl", "renpy", "lib") for p in parts):
            continue
        result.append(rpy)
    return result


# ── 跳过逻辑 ─────────────────────────────────────────────────────

def _should_skip(text: str) -> bool:
    """判断是否应跳过翻译。"""
    stripped = text.strip()
    # 空或纯空白
    if not stripped:
        return True
    # 单字符
    if len(stripped) <= 1:
        return True
    # 已含中文
    if any("\u4e00" <= c <= "\u9fff" for c in stripped):
        return True
    # 纯变量引用 [var] / [var.attr] / [var!t]
    if _RE_PURE_VAR.fullmatch(stripped):
        return True
    # 无英文字母（纯标点/数字/符号）
    if not any(c.isalpha() for c in stripped):
        return True
    # 文件路径
    lower = stripped.lower()
    if any(lower.endswith(ext) for ext in _FILE_EXTENSIONS):
        return True
    # 剥离 Ren'Py 标签后再检测（避免 {/size} 等闭合标签的 / 触发误判）
    tag_stripped = re.sub(r'\{/?[^}]*\}', '', stripped)
    if '/' in tag_stripped and '.' in tag_stripped:
        return True
    return False


def _line_has_underscore_wrap(line: str) -> bool:
    """检查行中引号字符串前是否有 _( 包裹。"""
    # 简单检测: 引号前出现 _(
    before_quote = line.split('"')[0]
    return '_(' in before_quote


# ── 提取 ──────────────────────────────────────────────────────────

def extract_screen_strings(file_path: Path) -> list[ScreenTextEntry]:
    """从单个 .rpy 文件中提取 screen 定义内的裸英文字符串。"""
    try:
        content = file_path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError):
        try:
            content = file_path.read_text(encoding="latin-1")
        except OSError:
            return []

    lines = content.splitlines()
    entries: list[ScreenTextEntry] = []

    # 上下文检测：是否在 screen 定义内
    in_screen = False
    screen_indent = 0

    for i, line in enumerate(lines):
        stripped = line.lstrip()
        indent = len(line) - len(stripped)

        # 检测 screen 定义开始
        if stripped.startswith("screen ") and stripped.rstrip().endswith(":"):
            in_screen = True
            screen_indent = indent
            continue

        # 检测 screen 定义结束（同级或更低缩进的非空非注释行）
        if in_screen and stripped and not stripped.startswith("#"):
            if indent <= screen_indent:
                in_screen = False

        if not in_screen:
            continue

        # 跳过注释行
        if stripped.startswith("#"):
            continue

        # 跳过 _() 包裹的行
        if _line_has_underscore_wrap(line):
            continue

        line_num = i + 1
        file_str = str(file_path)

        # 匹配 text "..."
        m = _RE_TEXT.match(line)
        if m:
            text = m.group(2)
            if not _should_skip(text):
                entries.append(ScreenTextEntry(file_str, line_num, "text", text))
            continue

        # 匹配 textbutton "..."
        m = _RE_TEXTBUTTON.match(line)
        if m:
            text = m.group(2)
            if not _should_skip(text):
                entries.append(ScreenTextEntry(file_str, line_num, "textbutton", text))
            continue

        # 匹配 tt.Action("...")（可能一行多个）
        for m in _RE_TT_ACTION.finditer(line):
            text = m.group(2)
            if not _should_skip(text):
                entries.append(ScreenTextEntry(file_str, line_num, "tt_action", text))

        # 匹配 Notify("...")（弹出通知，可能一行多个）
        for m in _RE_NOTIFY.finditer(line):
            text = m.group(2)
            if not _should_skip(text):
                entries.append(ScreenTextEntry(file_str, line_num, "notify", text))

    return entries


# ── 去重 ──────────────────────────────────────────────────────────

def _deduplicate_entries(
    entries: list[ScreenTextEntry],
) -> tuple[dict[str, str], dict[str, list[ScreenTextEntry]]]:
    """去重：返回 (unique_text→translation, unique_text→[entries])。"""
    translation_table: dict[str, str] = {}
    entries_by_text: dict[str, list[ScreenTextEntry]] = {}
    for e in entries:
        if e.original not in entries_by_text:
            entries_by_text[e.original] = []
            translation_table[e.original] = ""
        entries_by_text[e.original].append(e)
    return translation_table, entries_by_text


# ── 翻译 ──────────────────────────────────────────────────────────

SCREEN_TRANSLATE_SYSTEM_PROMPT = """\
你是一名专业的游戏 UI 本地化翻译专家。你将收到从 Ren'Py 游戏 screen 定义中提取的 UI 文本。

## 任务
将每条英文 UI 文本翻译为简体中文。

## 文本特点
这些文本来自游戏界面中的按钮、标签、提示等短字符串。

## 规则
- **每一条都必须翻译**，不得跳过
- `[variable]` 方括号变量原样保留
- `{{color=#xxx}}`, `{{/color}}`, `{{b}}`, `{{/b}}`, `{{size=N}}` 等标签原样保留，只翻译标签包围的文字
- 占位符令牌（如 __RENPY_PH_0__）原样保留
- UI 翻译应简洁精炼，符合游戏界面用语

{glossary_block}

## 输出格式
返回 JSON 数组，每个元素包含 id（编号）、original（原文）、zh（译文）：

```json
[
  {{"id": 1, "original": "Save Game", "zh": "保存游戏"}}
]
```

只返回纯 JSON，不要解释。每条都必须翻译。"""


def _build_screen_user_prompt(chunk_texts: list[str]) -> str:
    """构建用户提示。"""
    lines = []
    for i, text in enumerate(chunk_texts, 1):
        lines.append(f'[{i}] "{text}"')
    return (
        f"请翻译以下 {len(chunk_texts)} 条游戏界面 UI 文本：\n\n"
        + "\n".join(lines)
    )


def _build_screen_chunks(
    texts: list[str], max_per_chunk: int = 40,
) -> list[list[str]]:
    """将唯一文本分成翻译批次。"""
    chunks = []
    for i in range(0, len(texts), max_per_chunk):
        chunks.append(texts[i:i + max_per_chunk])
    return chunks


def _translate_screen_chunk(
    chunk_texts: list[str],
    client: Any,
    glossary: Any,
    genre: str = "adult",
) -> tuple[dict[str, str], int, list[str]]:
    """翻译一批 screen 文本。

    Returns:
        (text→translation 映射, 丢弃数, 警告列表)
    """
    from file_processor.checker import (
        protect_placeholders, restore_placeholders, check_response_item,
    )

    result: dict[str, str] = {}
    warnings: list[str] = []
    dropped = 0

    # 占位符保护
    protected_texts = []
    mappings = []
    for text in chunk_texts:
        protected, mapping = protect_placeholders(text)
        protected_texts.append(protected)
        mappings.append(mapping)

    # 构建 prompt
    glossary_block = ""
    if glossary:
        gt = glossary.to_prompt_text()
        if gt:
            glossary_block = f"## 术语表\n{gt}"

    system_prompt = SCREEN_TRANSLATE_SYSTEM_PROMPT.format(
        glossary_block=glossary_block,
    )
    user_prompt = _build_screen_user_prompt(protected_texts)

    # API 调用
    try:
        response = client.translate(system_prompt, user_prompt)
    except Exception as e:
        logger.warning(f"[SCREEN] API 调用失败: {e}")
        return result, len(chunk_texts), warnings

    if not response:
        logger.warning("[SCREEN] API 返回空结果")
        return result, len(chunk_texts), warnings

    # 解析结果：按 id（编号）或 original 匹配
    for item in response:
        item_id = item.get("id", "")
        original = item.get("original", "")
        zh = item.get("zh", item.get("translation", ""))

        if not zh:
            dropped += 1
            continue

        # 按编号匹配
        matched_idx = None
        if isinstance(item_id, int) and 1 <= item_id <= len(chunk_texts):
            matched_idx = item_id - 1
        elif isinstance(item_id, str) and item_id.isdigit():
            idx = int(item_id) - 1
            if 0 <= idx < len(chunk_texts):
                matched_idx = idx

        # 按 original 文本匹配（fallback）
        if matched_idx is None and original:
            for j, pt in enumerate(protected_texts):
                if pt == original or chunk_texts[j] == original:
                    matched_idx = j
                    break

        if matched_idx is None:
            dropped += 1
            continue

        orig_text = chunk_texts[matched_idx]
        mapping = mappings[matched_idx]

        # 还原占位符
        if mapping:
            zh = restore_placeholders(zh, mapping)

        # 校验
        check_item = {"original": orig_text, "zh": zh}
        item_warnings = check_response_item(check_item)
        if item_warnings:
            # 有占位符丢失等严重问题则丢弃
            has_error = any("E210" in w or "E220" in w or "E230" in w for w in item_warnings)
            if has_error:
                dropped += 1
                warnings.extend(item_warnings)
                continue

        result[orig_text] = zh

    return result, dropped, warnings


# ── 替换 ──────────────────────────────────────────────────────────

def _escape_for_screen(text: str) -> str:
    """转义翻译文本以安全嵌入 Ren'Py 引号字符串。"""
    # 复用 patcher 的转义逻辑
    try:
        from file_processor.patcher import _escape_for_renpy_string
        return _escape_for_renpy_string(text, '"')
    except ImportError:
        # fallback: 基本转义
        text = text.replace('\\', '\\\\')
        text = text.replace('"', '\\"')
        return text


def _replace_screen_strings_in_file(
    file_path: Path,
    entries: list[ScreenTextEntry],
    translation_table: dict[str, str],
) -> tuple[str, int]:
    """在文件中逐行替换 screen 文本。

    Returns:
        (修改后的文件内容, 替换成功数)
    """
    try:
        content = file_path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError):
        content = file_path.read_text(encoding="latin-1")

    lines = content.splitlines(keepends=True)
    replaced_count = 0

    # 按行号分组
    entries_by_line: dict[int, list[ScreenTextEntry]] = {}
    for e in entries:
        if e.original in translation_table and translation_table[e.original]:
            entries_by_line.setdefault(e.line_number, []).append(e)

    for line_num, line_entries in entries_by_line.items():
        idx = line_num - 1
        if idx < 0 or idx >= len(lines):
            continue

        line = lines[idx]

        for entry in line_entries:
            zh = translation_table.get(entry.original, "")
            if not zh:
                continue

            escaped_zh = _escape_for_screen(zh)

            if entry.pattern_type == "text":
                new_line, n = _RE_TEXT.subn(
                    lambda m, ez=escaped_zh: m.group(1) + '"' + ez + '"',
                    line, count=1,
                )
                if n > 0:
                    line = new_line
                    replaced_count += 1

            elif entry.pattern_type == "textbutton":
                new_line, n = _RE_TEXTBUTTON.subn(
                    lambda m, ez=escaped_zh: m.group(1) + '"' + ez + '"',
                    line, count=1,
                )
                if n > 0:
                    line = new_line
                    replaced_count += 1

            elif entry.pattern_type in ("tt_action", "notify"):
                # tt.Action / Notify 可能一行多个，逐个替换
                orig_escaped = re.escape(entry.original)
                func_name = r'tt\.Action' if entry.pattern_type == "tt_action" else r'Notify'
                pattern = re.compile(
                    r'(' + func_name + r'\s*\(\s*)"' + orig_escaped + r'"(\s*\))'
                )
                new_line, n = pattern.subn(
                    lambda m, ez=escaped_zh: m.group(1) + '"' + ez + '"' + m.group(2),
                    line, count=1,
                )
                if n > 0:
                    line = new_line
                    replaced_count += 1

        lines[idx] = line

    return "".join(lines), replaced_count


# ── 进度 ──────────────────────────────────────────────────────────

def _load_progress(progress_path: Path) -> dict:
    """加载进度文件。"""
    if progress_path.is_file():
        try:
            data = json.loads(progress_path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                data.setdefault("completed_texts", {})
                data.setdefault("completed_chunks", [])
                data.setdefault("stats", {})
                return data
        except (json.JSONDecodeError, OSError):
            logger.warning("[SCREEN] 进度文件损坏，已重置")
    return {"completed_texts": {}, "completed_chunks": [], "stats": {}}


def _save_progress(progress_path: Path, progress: dict) -> None:
    """原子写入进度文件。"""
    tmp_path = progress_path.with_suffix(".tmp")
    try:
        tmp_path.write_text(
            json.dumps(progress, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        shutil.move(str(tmp_path), str(progress_path))
    except OSError as e:
        logger.warning(f"[SCREEN] 保存进度失败: {e}")


# ── 备份 ──────────────────────────────────────────────────────────

def _create_backup(file_path: Path) -> None:
    """创建 .bak 备份（不覆盖已有）。"""
    bak = file_path.with_suffix(file_path.suffix + ".bak")
    if not bak.exists():
        shutil.copy2(str(file_path), str(bak))
        logger.debug(f"[SCREEN] 备份: {bak.name}")


# ── 主流程 ────────────────────────────────────────────────────────

def run_screen_translate(args: argparse.Namespace) -> None:
    """Screen 文本翻译主入口。"""
    from core.api_client import APIClient, APIConfig
    from core.glossary import Glossary
    from core.config import Config

    start_time = time.time()
    game_dir = Path(args.game_dir)

    # 智能检测 game 子目录
    if (game_dir / "game").exists():
        scan_dir = game_dir / "game"
    else:
        scan_dir = game_dir

    logger.info("\n" + "=" * 60)
    logger.info("Screen 文本翻译")
    logger.info("=" * 60)

    # ── 1. 扫描 ──
    rpy_files = scan_screen_files(scan_dir)
    logger.info(f"[SCREEN] 扫描到 {len(rpy_files)} 个 .rpy 文件")

    # ── 2. 提取 ──
    all_entries: list[ScreenTextEntry] = []
    for rpy in rpy_files:
        entries = extract_screen_strings(rpy)
        all_entries.extend(entries)

    if not all_entries:
        logger.info("[SCREEN] 未发现需要翻译的 screen 文本")
        return

    # ── 3. 去重 ──
    translation_table, entries_by_text = _deduplicate_entries(all_entries)

    # 统计
    n_total = len(all_entries)
    n_unique = len(translation_table)
    n_files = len({e.file_path for e in all_entries})
    logger.info(f"[SCREEN] 提取 {n_total} 条文本（{n_unique} 种不重复），"
                f"涉及 {n_files} 个文件")

    # dry-run 模式
    if getattr(args, "dry_run", False):
        logger.info(f"\n[SCREEN] Dry-run 模式：发现 {n_unique} 种不重复 screen 文本")
        logger.info(f"[SCREEN] 预估 API 请求：{(n_unique + 39) // 40} 次")
        # 按类型统计
        type_counts: dict[str, int] = {}
        for e in all_entries:
            type_counts[e.pattern_type] = type_counts.get(e.pattern_type, 0) + 1
        for ptype, count in sorted(type_counts.items()):
            logger.info(f"  {ptype}: {count} 条")
        return

    # ── 4. 加载进度 ──
    output_dir = Path(getattr(args, "output_dir", "output"))
    output_dir.mkdir(parents=True, exist_ok=True)
    progress_path = output_dir / "screen_translate_progress.json"
    progress = _load_progress(progress_path)

    # 恢复已翻译的文本
    completed = progress["completed_texts"]
    for text, zh in completed.items():
        if text in translation_table:
            translation_table[text] = zh

    remaining = [t for t, zh in translation_table.items() if not zh]
    if not remaining:
        logger.info(f"[SCREEN] 所有 {n_unique} 条文本已翻译，直接执行替换")
    else:
        logger.info(f"[SCREEN] 待翻译: {len(remaining)} / {n_unique}")

        # API key 检查
        if not getattr(args, "api_key", ""):
            logger.error("[SCREEN] 非 dry-run 模式必须提供 --api-key")
            return

        # ── 5. 翻译 ──
        api_config = APIConfig(
            provider=args.provider,
            model=getattr(args, "model", "") or "",
            api_key=args.api_key,
            rpm=getattr(args, "rpm", 60),
            rps=getattr(args, "rps", 5),
            timeout=getattr(args, "timeout", 180.0),
            temperature=getattr(args, "temperature", 0.1),
            max_response_tokens=getattr(args, "max_response_tokens", 32768),
            custom_module=getattr(args, "custom_module", ""),
        )
        client = APIClient(api_config)

        # 加载术语表
        glossary = Glossary()
        dict_files = getattr(args, "dict", []) or []
        if isinstance(dict_files, str):
            dict_files = [dict_files]
        for d in dict_files:
            if Path(d).is_file():
                glossary.load_dict(d)

        chunks = _build_screen_chunks(remaining)
        total_dropped = 0
        all_warnings: list[str] = []

        for ci, chunk in enumerate(chunks):
            if ci in progress.get("completed_chunks", []):
                continue

            logger.info(f"[SCREEN] 翻译 chunk {ci + 1}/{len(chunks)}"
                        f"（{len(chunk)} 条）")

            translations, dropped, warnings = _translate_screen_chunk(
                chunk, client, glossary,
                genre=getattr(args, "genre", "adult"),
            )
            total_dropped += dropped
            all_warnings.extend(warnings)

            # 更新翻译表和进度
            for text, zh in translations.items():
                translation_table[text] = zh
                completed[text] = zh

            progress["completed_chunks"].append(ci)
            progress["completed_texts"] = completed
            progress["stats"] = {
                "total_unique": n_unique,
                "translated": sum(1 for v in translation_table.values() if v),
            }
            _save_progress(progress_path, progress)

        logger.info(f"[SCREEN] 翻译完成: "
                    f"{sum(1 for v in translation_table.values() if v)}/{n_unique} "
                    f"已翻译, {total_dropped} 丢弃")
        if all_warnings:
            logger.info(f"[SCREEN] {len(all_warnings)} 条警告")

        # 输出费用
        logger.info(f"[SCREEN] {client.usage.summary()}")

    # ── 6. 替换 ──
    translated = {t: zh for t, zh in translation_table.items() if zh}
    if not translated:
        logger.warning("[SCREEN] 无可用翻译，跳过替换")
        return

    # 按文件分组
    files_to_patch: dict[str, list[ScreenTextEntry]] = {}
    for text, entry_list in entries_by_text.items():
        if text in translated:
            for e in entry_list:
                files_to_patch.setdefault(e.file_path, []).append(e)

    total_replaced = 0
    files_modified = 0
    for file_path_str, file_entries in sorted(files_to_patch.items()):
        fpath = Path(file_path_str)

        # 备份
        _create_backup(fpath)

        # 替换
        new_content, replaced = _replace_screen_strings_in_file(
            fpath, file_entries, translated,
        )
        if replaced > 0:
            fpath.write_text(new_content, encoding="utf-8")
            total_replaced += replaced
            files_modified += 1
            logger.debug(f"[SCREEN] {fpath.name}: {replaced} 处替换")

    # ── 7. 报告 ──
    elapsed = time.time() - start_time
    logger.info(f"\n[SCREEN] 完成: {total_replaced} 处替换, "
                f"{files_modified} 个文件修改, 耗时 {elapsed:.1f}s")
    logger.info(f"[SCREEN] 注意: screen 翻译直接修改了源文件（已创建 .bak 备份）。"
                f"游戏更新后需重新执行 --tl-screen。")


# ── 自测 ──────────────────────────────────────────────────────────

def _run_self_tests() -> None:
    """内建自测。"""
    import tempfile

    passed = 0

    # T1: _should_skip
    assert _should_skip("") is True
    assert _should_skip("[var]") is True
    assert _should_skip("[mother]") is True
    assert _should_skip("123") is True
    assert _should_skip("...") is True
    assert _should_skip("已保存") is True
    assert _should_skip("images/bg.png") is True
    assert _should_skip("a") is True  # 单字符
    assert _should_skip("Save Game") is False
    assert _should_skip("NTR: undecided") is False
    assert _should_skip("{color=#f00}Warning{/color}") is False
    assert _should_skip("[name] is here") is False  # 含英文，不是纯变量
    assert _should_skip("{size=-10}- You can find work at the tanning salon.{/size}") is False
    assert _should_skip("{size=-10}when you're a gangmember.{/size}") is False
    assert _should_skip("icons/bg.png") is True  # 真正的文件路径仍被跳过
    passed += 15
    print(f"[OK] _should_skip: {passed} assertions")

    # T2: _line_has_underscore_wrap
    assert _line_has_underscore_wrap('        textbutton _("Back") action Rollback()') is True
    assert _line_has_underscore_wrap('        text "Hello"') is False
    assert _line_has_underscore_wrap('        textbutton "Start" action Start()') is False
    passed += 3
    print(f"[OK] _line_has_underscore_wrap: {passed} assertions")

    # T3: extract_screen_strings
    with tempfile.NamedTemporaryFile(mode='w', suffix='.rpy', delete=False,
                                      encoding='utf-8') as f:
        f.write("""
screen contacts():
    vbox:
        text "Mom"
        text "[var]"
        textbutton "Start Game" action Start()
        textbutton _("Back") action Rollback()
        imagebutton auto "icon.png" hovered tt.Action("Go closer") focus_mask True
        imagebutton auto "icon2.png" action Jump("x") hovered Notify("Help needed") focus_mask True
        text "{color=#f00}Warning{/color}"

label start:
    text "Not in screen"
    "Hello"
""")
        f.flush()
        tmp_path = Path(f.name)

    try:
        entries = extract_screen_strings(tmp_path)
        # 应该提取: "Mom", "Start Game", "Go closer", "{color=#f00}Warning{/color}"
        # 跳过: "[var]" (纯变量), _("Back") (已包裹), "Not in screen" (不在 screen 内)
        originals = [e.original for e in entries]
        assert "Mom" in originals, f"Missing 'Mom', got {originals}"
        assert "Start Game" in originals, f"Missing 'Start Game', got {originals}"
        assert "Go closer" in originals, f"Missing 'Go closer', got {originals}"
        assert "Help needed" in originals, f"Missing 'Help needed', got {originals}"
        assert "{color=#f00}Warning{/color}" in originals
        assert "[var]" not in originals, "[var] should be skipped"
        assert "Back" not in originals, "_('Back') should be skipped"
        assert "Not in screen" not in originals, "text outside screen should be skipped"

        # 检查类型
        type_map = {e.original: e.pattern_type for e in entries}
        assert type_map["Mom"] == "text"
        assert type_map["Start Game"] == "textbutton"
        assert type_map["Go closer"] == "tt_action"
        assert type_map["Help needed"] == "notify"
        passed += 12
        print(f"[OK] extract_screen_strings: {passed} assertions")
    finally:
        os.unlink(tmp_path)

    # T4: _deduplicate_entries
    e1 = ScreenTextEntry("a.rpy", 1, "text", "Hello")
    e2 = ScreenTextEntry("b.rpy", 5, "text", "Hello")
    e3 = ScreenTextEntry("a.rpy", 3, "text", "World")
    table, by_text = _deduplicate_entries([e1, e2, e3])
    assert len(table) == 2  # "Hello" 和 "World"
    assert len(by_text["Hello"]) == 2
    assert len(by_text["World"]) == 1
    passed += 3
    print(f"[OK] _deduplicate_entries: {passed} assertions")

    # T5: _replace_screen_strings_in_file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.rpy', delete=False,
                                      encoding='utf-8') as f:
        f.write('    text "Save Game"\n')
        f.write('    textbutton "Start" action Start() style "btn"\n')
        f.write('    imagebutton hovered tt.Action("Go closer") focus_mask True\n')
        f.write('    text "{color=#f00}Warning{/color}"\n')
        f.flush()
        tmp_path = Path(f.name)

    try:
        test_entries = [
            ScreenTextEntry(str(tmp_path), 1, "text", "Save Game"),
            ScreenTextEntry(str(tmp_path), 2, "textbutton", "Start"),
            ScreenTextEntry(str(tmp_path), 3, "tt_action", "Go closer"),
            ScreenTextEntry(str(tmp_path), 4, "text", "{color=#f00}Warning{/color}"),
        ]
        test_table = {
            "Save Game": "保存游戏",
            "Start": "开始",
            "Go closer": "靠近",
            "{color=#f00}Warning{/color}": "{color=#f00}警告{/color}",
        }
        new_content, count = _replace_screen_strings_in_file(
            tmp_path, test_entries, test_table,
        )
        assert count == 4, f"Expected 4 replacements, got {count}"
        assert '"保存游戏"' in new_content
        assert '"开始"' in new_content
        # textbutton: action 参数的 "btn" 应该不被替换
        assert 'style "btn"' in new_content
        assert '"靠近"' in new_content
        assert '{color=#f00}警告{/color}' in new_content
        passed += 5
        print(f"[OK] _replace_screen_strings_in_file: {passed} assertions")
    finally:
        os.unlink(tmp_path)

    # T6: 备份逻辑
    with tempfile.NamedTemporaryFile(mode='w', suffix='.rpy', delete=False,
                                      encoding='utf-8') as f:
        f.write("test content\n")
        f.flush()
        tmp_path = Path(f.name)
    try:
        bak_path = tmp_path.with_suffix(tmp_path.suffix + ".bak")
        assert not bak_path.exists()
        _create_backup(tmp_path)
        assert bak_path.exists()
        # 再次调用不应覆盖
        bak_path.write_text("old backup", encoding="utf-8")
        _create_backup(tmp_path)
        assert bak_path.read_text(encoding="utf-8") == "old backup"
        passed += 3
        print(f"[OK] _create_backup: {passed} assertions")
    finally:
        os.unlink(tmp_path)
        if bak_path.exists():
            os.unlink(bak_path)

    # T7: _build_screen_chunks
    texts = [f"text_{i}" for i in range(100)]
    chunks = _build_screen_chunks(texts, max_per_chunk=40)
    assert len(chunks) == 3
    assert len(chunks[0]) == 40
    assert len(chunks[2]) == 20
    passed += 3
    print(f"[OK] _build_screen_chunks: {passed} assertions")

    # T8: Notify 替换
    with tempfile.NamedTemporaryFile(mode='w', suffix='.rpy', delete=False,
                                      encoding='utf-8') as f:
        f.write('    imagebutton action Jump("x") hovered Notify("Help needed") focus_mask True\n')
        f.flush()
        tmp_path = Path(f.name)
    try:
        test_entries_notify = [
            ScreenTextEntry(str(tmp_path), 1, "notify", "Help needed"),
        ]
        test_table_notify = {"Help needed": "需要帮助"}
        new_content, count = _replace_screen_strings_in_file(
            tmp_path, test_entries_notify, test_table_notify,
        )
        assert count == 1
        assert '"需要帮助"' in new_content
        assert 'Notify' in new_content  # 函数名保留
        assert 'Jump("x")' in new_content  # action 不动
        passed += 4
        print(f"[OK] Notify replacement: {passed} assertions")
    finally:
        os.unlink(tmp_path)

    # T9: 多个 tt.Action 同一行
    with tempfile.NamedTemporaryFile(mode='w', suffix='.rpy', delete=False,
                                      encoding='utf-8') as f:
        f.write('    imagebutton hovered tt.Action("Open") xpos 100 hovered tt.Action("Close") focus_mask True\n')
        f.flush()
        tmp_path = Path(f.name)
    try:
        test_entries_multi = [
            ScreenTextEntry(str(tmp_path), 1, "tt_action", "Open"),
            ScreenTextEntry(str(tmp_path), 1, "tt_action", "Close"),
        ]
        test_table_multi = {"Open": "打开", "Close": "关闭"}
        new_content, count = _replace_screen_strings_in_file(
            tmp_path, test_entries_multi, test_table_multi,
        )
        assert '"打开"' in new_content
        assert '"关闭"' in new_content
        assert count == 2
        passed += 3
        print(f"[OK] multi tt.Action replacement: {passed} assertions")
    finally:
        os.unlink(tmp_path)

    print(f"\n{'=' * 40}")
    print(f"ALL {passed} SCREEN TRANSLATOR TESTS PASSED")
    print(f"{'=' * 40}")


if __name__ == "__main__":
    _run_self_tests()
