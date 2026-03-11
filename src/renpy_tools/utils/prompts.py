"""
翻译提示词模板

统一管理所有翻译引擎使用的 system prompt，避免多处重复维护。
支持从外部文件加载自定义 prompt 和按游戏类型选择模板。
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional


# ── 游戏类型预设模板 ──────────────────────────────────────
_GENRE_STYLES: dict[str, str] = {
    "adult": (
        "【翻译风格】\n"
        "- 成人游戏主基调：直白露骨（鸡巴、奶子、小穴、屁股、骚货、操、干、插）\n"
        "- 自然口语，避免生硬直译\n"
        "- 保持换行符数量一致\n"
        "- UI 文本优先短译\n\n"
        "【语气指南】（从场景标签判断）\n"
        "- Love：俏皮、温馨\n"
        "- Corruption：命令、占有\n"
        "- NTR：不甘、较劲\n"
        "- Sadist：嘲弄、压迫\n"
        "- *dark：加深语气\n"
    ),
    "visual_novel": (
        "【翻译风格】\n"
        "- 视觉小说风格：文学化、注重叙事感\n"
        "- 对话自然流畅，旁白优美\n"
        "- 保留角色语气特征\n"
        "- 保持换行符数量一致\n"
        "- UI 文本优先短译\n"
    ),
    "rpg": (
        "【翻译风格】\n"
        "- RPG 风格：技能名/装备名应简洁有力\n"
        "- 对话保持角色个性\n"
        "- 系统提示简明扼要\n"
        "- 保持换行符数量一致\n"
        "- UI 文本优先短译\n"
    ),
    "general": (
        "【翻译风格】\n"
        "- 通用游戏风格：自然流畅的中文\n"
        "- 保持原文语气和风格\n"
        "- 保持换行符数量一致\n"
        "- UI 文本优先短译\n"
    ),
}


def load_custom_prompt(path: str | Path) -> Optional[str]:
    """从外部文件加载自定义 prompt

    支持 .txt / .md 文件，直接读取文件内容作为 system prompt。
    返回 None 表示文件不存在或读取失败。
    """
    p = Path(path)
    if not p.exists():
        return None
    try:
        return p.read_text(encoding='utf-8').strip()
    except (OSError, UnicodeDecodeError):
        return None


def get_available_genres() -> list[str]:
    """返回可用的游戏类型列表"""
    return list(_GENRE_STYLES.keys())


def build_system_prompt(genre: str = "adult", custom_prompt_path: Optional[str] = None) -> str:
    """构建通用系统提示词（适用于 Ollama / API 翻译）

    Args:
        genre: 游戏类型（adult/visual_novel/rpg/general）
        custom_prompt_path: 自定义 prompt 文件路径，若提供则优先使用

    Returns:
        完整的系统提示词
    """
    # 优先使用自定义 prompt
    if custom_prompt_path:
        custom = load_custom_prompt(custom_prompt_path)
        if custom:
            return custom

    style_block = _GENRE_STYLES.get(genre, _GENRE_STYLES["adult"])
    return (
        "你是资深游戏本地化译员，将英文台词翻译为简体中文。\n\n"

        "【重要提示】\n"
        "- 文本中的 〔数字〕 标记（如〔0〕〔1〕）是占位符，翻译时必须保留\n"
        "- 不要删除或修改这些标记，保持它们在译文中的位置\n\n"

        f"{style_block}\n\n"

        "【翻译质量要求】⚠️ 严格遵守\n"
        "- ⚠️ 严禁输出任何英文单词（专有名词、变量名除外）\n"
        "- ⚠️ 必须将每一个英文词汇完整翻译为中文\n"
        "- ⚠️ 禁止中英文混合输出\n"
        "- ⚠️ 不确定的词宁可意译，也不要保留英文\n\n"

        "【错误示例】禁止模仿以下错误\n"
        "❌ '你 also 也喜欢' → ✅ '你也喜欢'\n"
        "❌ '享受你的 pleasure' → ✅ '享受你的快感'\n"
        "❌ '一个dirty的秘密' → ✅ '一个肮脏的秘密'\n"
        "❌ '那副slutty的look' → ✅ '那副淫荡的眼神'\n\n"

        "【输出规则】\n"
        "- 只输出纯中文译文\n"
        "- 不输出思考过程、代码块、额外说明\n"
        "- 再次强调：绝对不允许输出任何英文单词"
    )


def build_api_system_prompt(genre: str = "adult", custom_prompt_path: Optional[str] = None) -> str:
    """构建 API 翻译专用系统提示词（更简洁，适合付费 API 控制 token 用量）"""
    if custom_prompt_path:
        custom = load_custom_prompt(custom_prompt_path)
        if custom:
            return custom

    style = "成人游戏风格：直白露骨（鸡巴、奶子、小穴、屁股、骚货、操、干、插）" if genre == "adult" else \
            "视觉小说风格：文学化、注重叙事感" if genre == "visual_novel" else \
            "RPG 风格：简洁有力" if genre == "rpg" else \
            "通用游戏风格：自然流畅"
    return (
        "你是资深游戏本地化译员，将英文台词翻译为简体中文。\n\n"

        "【核心要求】\n"
        "⚠️ 严禁输出任何英文单词（变量名除外如[name]）\n"
        "⚠️ 必须将每个英文词汇完整翻译为中文\n"
        "⚠️ 禁止中英文混合输出\n\n"

        "【翻译风格】\n"
        f"- {style}\n"
        "- 自然口语化，避免生硬直译\n"
        "- 保持换行符数量一致\n\n"

        "【错误示例】禁止以下错误\n"
        "❌ '你 also 也喜欢' → ✅ '你也喜欢'\n"
        "❌ '享受你的 pleasure' → ✅ '享受你的快感'\n"
        "❌ '一个dirty的秘密' → ✅ '一个肮脏的秘密'\n\n"

        "【输出】只输出纯中文译文，不要任何解释"
    )


def load_prompt_template(
    template_path: str | Path,
    source_lang: str = "English",
    target_lang: str = "简体中文",
    json_data: str = "",
) -> list[dict[str, str]] | None:
    """加载 JSON 提示词模板文件（借鉴 RenpyTranslator 的 openai_template.json）

    模板中支持以下占位符：
      - #SOURCE_LANGUAGE#: 源语言名称
      - #TARGET_LANGUAGE#: 目标语言名称
      - #JSON_DATA#: 待翻译的 JSON 数据

    Args:
        template_path: JSON 模板文件路径
        source_lang: 源语言
        target_lang: 目标语言
        json_data: 替换到 #JSON_DATA# 的内容

    Returns:
        OpenAI messages 格式的列表，失败返回 None
    """
    import json as _json

    p = Path(template_path)
    if not p.exists():
        return None

    try:
        raw = p.read_text(encoding="utf-8")
        raw = raw.replace("#SOURCE_LANGUAGE#", source_lang)
        raw = raw.replace("#TARGET_LANGUAGE#", target_lang)
        messages = _json.loads(raw)
        if not isinstance(messages, list):
            return None
        # 填充 JSON 数据
        if json_data:
            for msg in messages:
                for key in msg:
                    if isinstance(msg[key], str) and "#JSON_DATA#" in msg[key]:
                        msg[key] = msg[key].replace("#JSON_DATA#", json_data)
        return messages
    except (OSError, UnicodeDecodeError, _json.JSONDecodeError):
        return None
