> 仅在新增引擎支持时加载此文档。

# 新增引擎开发指南

## 核心设计原则

1. **Ren'Py 代码零改动**：现有三条管线不重构，通过薄包装类接入新架构
2. **浅抽象、参数化差异**：只抽象 I/O 层（提取/回写），翻译中间流程通用。引擎差异通过 `EngineProfile` 参数化，非继承多态
3. **零依赖约束不破坏**：核心框架 + RPG Maker MV/MZ + CSV 全部标准库。第三方库引擎作为可选功能
4. **最小新增文件**：整个抽象层新增 ~7 个文件，不改现有结构

## EngineProfile 数据类

引擎差异的参数化描述，让 `protect_placeholders()` 和 `validate_translation()` 根据引擎调整行为。

| 字段 | 类型 | 用途 |
|------|------|------|
| `name` | `str` | 引擎标识符（`"renpy"` / `"rpgmaker_mv"` / `"csv"`） |
| `display_name` | `str` | 用户可见名称 |
| `placeholder_patterns` | `list[str]` | 占位符正则列表，用于 `protect_placeholders` 参数化 |
| `skip_line_patterns` | `list[str]` | 不翻译的行模式正则 |
| `encoding` | `str` | 文件默认编码 |
| `max_line_length` | `int \| None` | 译文行宽限制 |
| `prompt_addon_key` | `str` | 引擎专属 prompt 片段查找 key |
| `supports_context` | `bool` | 提取时是否提供上下文行 |
| `context_lines` | `int` | 上下文行数（默认 3） |

辅助方法：`compile_placeholder_re()` / `compile_skip_re()` 将列表编译为单个正则。

内置 Profile：`RENPY_PROFILE`、`RPGMAKER_MV_PROFILE`、`CSV_PROFILE`，注册在 `ENGINE_PROFILES` 字典中。

## TranslatableUnit 数据类

所有非 Ren'Py 引擎共用的文本单元（Ren'Py 有自己的 DialogueEntry / StringEntry 体系）。

| 字段 | 类型 | 用途 |
|------|------|------|
| `id` | `str` | 全局唯一标识（RPG Maker: JSON path，CSV: 行号/ID 列） |
| `original` | `str` | 原文 |
| `context` | `str` | 上下文行 |
| `file_path` | `str` | 来源文件相对路径 |
| `speaker` | `str` | 说话人/角色名 |
| `metadata` | `dict` | 引擎专属元数据（write_back 的定位关键），通用流水线只透传不碰 |
| `translation` | `str` | 翻译结果 |
| `status` | `str` | `"pending"` / `"translated"` / `"checker_dropped"` / `"ai_not_returned"` / `"skipped"` |

## EngineBase 抽象基类

**必须实现**：`_default_profile()` → EngineProfile、`detect(game_dir)` → bool、`extract_texts(game_dir)` → list[TranslatableUnit]、`write_back(game_dir, units, output_dir)` → int

**可选覆写**：`post_process()`（默认无操作）、`run(args)`（默认走 generic_pipeline）、`dry_run()`（默认统计 extract 结果）

## 新引擎添加流程（7 步）

1. 新建 `engines/xxx_engine.py`：继承 EngineBase，实现四个抽象方法
2. 新建 EngineProfile：在 `engine_base.py` 添加 `XXX_PROFILE`，注册到 `ENGINE_PROFILES`
3. 更新 `engine_detector.py`：`detect_engine_type()` + `create_engine()` + `resolve_engine()` manual_map
4. 更新 `core/prompts.py`：在 `_ENGINE_PROMPT_ADDONS` 添加引擎 prompt
5. 可选：更新 `core/glossary.py` 添加角色/术语扫描
6. 新增测试：在 `tests/test_engines.py` 添加检测、提取、回写测试
7. 更新文档：README "支持引擎"列表 + CLI `--engine` choices

## 零依赖约束处理

| 场景 | 处理 |
|------|------|
| RPG Maker VX/Ace 需 `rubymarshal` | 可选功能，缺依赖时 pip install 提示 |
| Unity AssetBundle 需 `UnityPy` | 不直接支持，通过 XUnity 导出文本间接支持 |
| Kirikiri .scn 需二进制解析 | 优先 .ks 文本格式，.scn 通过 VNTextPatch CSV |
| 老日系编码（Shift_JIS/EUC-JP） | EngineProfile.encoding 指定 |

## 命名与约定

- logging 前缀：`[ENGINE]` / `[DETECT]` / `[RPGM]` / `[CSV]` / `[PIPELINE]`
- CLI 参数：小写短横线分隔（`--engine`、`--placeholder-regex`）
- docstring：中文注释 + 英文 docstring 混合，模块头部有职责说明
