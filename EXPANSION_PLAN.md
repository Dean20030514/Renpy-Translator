# 多引擎翻译工具扩展方案

> 基于「多引擎游戏汉化工具」当前状态（第十六轮全部完成、~14700 行核心代码、87+62+13=162 单元测试、三引擎支持：Ren'Py + RPG Maker MV/MZ + CSV/JSONL）的完整扩展规划。
>
> **阶段零~四全部落地**，里程碑 M1~M4 达成。额外完成：项目结构整理 + Tkinter GUI + PyInstaller 打包 + 第十四轮 Ren'Py 专项五阶段优化 + 第十六轮 screen 裸英文翻译（`--tl-screen`）。后续路线见 §8。

---

## 目录

1. [当前 Ren'Py 工具优化](#1-当前-renpy-工具优化)
2. [引擎抽象层设计](#2-引擎抽象层设计)
3. [RPG Maker MV/MZ 支持](#3-rpg-maker-mvmz-支持)
4. [CSV/JSONL 通用格式支持](#4-csvjsonl-通用格式支持)
5. [通用翻译流水线](#5-通用翻译流水线)
6. [现有模块的适配改动](#6-现有模块的适配改动)
7. [测试策略](#7-测试策略)
8. [后续引擎路线图](#8-后续引擎路线图)
9. [实施顺序与里程碑](#9-实施顺序与里程碑)
10. [风险与避坑](#10-风险与避坑)

---

## 1. 当前 Ren'Py 工具优化 ✅ 已完成

> **状态**：四项优化全部落地（第十二轮），测试 66→70，zero regression。

在做多引擎扩展之前，先把现有 Ren'Py 工具的几个低风险高价值改进落地。这些改进与多引擎扩展互不依赖，可以独立推进。

### 1.1 chunk 失败自动拆分重试

**现状**：`_translate_chunk_with_retry` 在 API 错误或高丢弃率时整 chunk 原样重试，最多 2 次。

**问题**：当 chunk 过大导致 AI 输出被截断时，原样重试不会有效果。截断是因为响应 token 不够，重试只会得到同样的截断结果。

**方案**：

- 在 `_should_retry` 函数中新增一个判断条件：如果返回的翻译条数 < 期望条数的 50%（强烈暗示截断），标记为 `needs_split`
- `_translate_chunk_with_retry` 检测到 `needs_split` 后，不做原样重试，而是：
  - 将 chunk 从中间空行处（或直接二分）拆成两个子 chunk
  - 分别翻译子 chunk
  - 合并两个子 chunk 的结果
- 拆分只做一层（不递归），避免复杂度爆炸
- 拆分点的选择：优先在 label/screen 边界处拆，其次在空行处，最后直接二等分

**涉及文件**：`translators/direct.py`（`_translate_chunk_with_retry` 和 `_should_retry`）

**风险**：低。拆分逻辑只在重试路径触发，正常翻译路径不受影响。`split_file` 里已有 `_force_split_block` 的拆分经验可以复用。

**验证方式**：构造一个超大 chunk（比如 200 行对话），设置很低的 `max_response_tokens`（如 1000），验证拆分重试后翻译完整度优于原样重试。

### 1.2 one_click_pipeline.py 进一步拆分

**现状**：`one_click_pipeline.py` 有 ~1410 行，已拆出 `_run_retranslate_phase` 和 `_run_final_report`，但 `main()` 函数仍然偏大。

**方案**：

- 将 pilot 阶段拆为 `_run_pilot_phase()`：文件风险评分（`_compute_file_risk_score`）+ 选择 pilot 文件 + 执行 pilot 翻译 + AI 术语提取
- 将闸门评估拆为 `_run_gate_phase()`：`evaluate_gate` 调用 + 结果判定 + 日志输出
- 将全量翻译拆为 `_run_full_translation_phase()`
- `main()` 变成纯编排函数：调用四个 `_run_*_phase()` + 异常处理 + 报告汇总
- 预计 `main()` 从 ~300 行缩减到 ~80 行

**涉及文件**：仅 `one_click_pipeline.py`

**风险**：极低。纯重构，不改任何逻辑，只是把函数体搬到命名函数中。

### 1.3 tl-mode 自动清理 .rpyc 缓存

**现状**：`translators/tl_mode.py` 的 `_clean_rpyc` 函数已存在，但需要用户在 `_apply_tl_game_patches` 中手动触发。

**方案**：

- 在 `run_tl_pipeline` 的最后阶段（所有文件回填完成后），自动扫描翻译过的 `.rpy` 文件对应的 `.rpyc` 文件并删除
- 只删除与本次翻译修改过的 `.rpy` 同名的 `.rpyc`，不全目录清理
- 输出日志 `[RPYC] 已清理 N 个缓存文件`
- 用 `--no-clean-rpyc` 参数允许禁用（默认启用）

**涉及文件**：`translators/tl_mode.py`（`run_tl_pipeline` 尾部 + CLI 参数传递）

**风险**：极低。`.rpyc` 是自动生成的缓存，删除后 Ren'Py 会自动重建。

### 1.4 dry-run 模式增强

**现状**：`--dry-run` 只输出文件数、token 估算、费用估算。

**方案**：

- 新增按文件的明细输出：每个 `.rpy` 文件的对话行数、token 数、预估费用
- 输出对话密度分布直方图（文字版），帮助用户预判哪些文件会走定向翻译
- 输出术语扫描结果预览（自动提取的角色名 + 已有词典条目数）
- 所有新增输出仅在 `--verbose` 时显示，默认保持简洁

**涉及文件**：`translators/direct.py`（`run_pipeline` 的 dry-run 分支）

**风险**：零。dry-run 不调用 API，不修改文件。

> **第十四轮补充**：第十四轮在此基础上做了进一步的 Ren'Py 专项五阶段优化：基础重构（pipeline/ 包 + renpy_text_utils.py）→ 代码健壮性（except 收窄 + 配置校验 + GUI 优雅终止）→ 性能优化（TranslationCache + token 估算改进 + 背压机制）→ 翻译质量（E250/W460/W470 新规则 + 术语一致性主动执行）→ 用户体验（GUI 进度条 + 自适应轮询 + 日志裁剪 + SIGTERM 处理）。详见 CHANGELOG.md 第十四轮。
>
> **第十五轮补充**：新增 `fix_nvl_translation_ids` / `fix_nvl_ids_directory`，自动修正 Ren'Py 8.6+ 生成的 say-only 翻译块 ID 为 7.x nvl+say 哈希，解决含 `nvl clear` 的翻译静默失败。已集成到 `run_tl_pipeline` 后处理链。测试 71→75。详见 CHANGELOG.md 第十五轮。
>
> **第十六轮补充**：新增 `translators/screen.py`（原 `screen_translator.py`，~420 行），翻译 screen 定义中 Ren'Py tl 框架无法提取的裸英文字符串（`text "..."`/`textbutton "..."`/`tt.Action("...")`）。通过 `--tl-screen` 参数启用，可与 `--tl-mode` 联用。同时修复 `_clean_rpyc`/`delete_rpyc_files`/资源复制中 `.rpymc` 缓存清理遗漏。测试 75→86。详见 CHANGELOG.md 第十六轮。

---

## 2. 引擎抽象层设计 ✅ 已完成

> **状态**：阶段一落地。`engine_base.py`（202 行）+ `engine_detector.py`（160 行）+ `engines/renpy_engine.py`（74 行）+ `engines/__init__.py`（3 行）。`main.py` 新增 `--engine` 参数（auto/renpy/rpgmaker/csv/jsonl），auto/renpy 走原路径零改动，其他引擎走 `resolve_engine()` → `engine.run(args)`。25 个引擎测试全绿，70 现有测试零回归。

### 2.1 核心设计原则

1. **Ren'Py 代码零改动**：现有 `translators/direct` / `translators/tl_mode` / `translators/retranslator` 不重构，通过薄包装类接入新架构
2. **浅抽象、参数化差异**：只抽象 I/O 层（提取/回写），翻译中间流程通用。引擎间的差异（占位符语法、校验规则）通过 `EngineProfile` 数据类参数化，而非继承多态
3. **零依赖约束不破坏**：核心框架 + RPG Maker MV/MZ + CSV 全部用标准库。需要第三方库的引擎（VX/Ace 的 rubymarshal、Unity 的 UnityPy）作为可选功能，缺依赖时给友好提示
4. **最小新增文件**：整个抽象层新增 ~7 个文件，不改现有文件结构

### 2.2 新增文件清单

| 文件 | 预计行数 | 实际行数 | 职责 |
|------|----------|----------|------|
| `engines/engine_base.py` | ~300 | **202** | `EngineProfile` 数据类 + `TranslatableUnit` 数据类 + `EngineBase` ABC + 内置 Profile 常量 |
| `engines/engine_detector.py` | ~200 | **160** | `detect_engine_type()` 目录特征扫描 + `resolve_engine()` CLI 路由 + `EngineType` 枚举 |
| `engines/generic_pipeline.py` | ~450 | **414** | 通用翻译流水线（非 Ren'Py 引擎共用）：提取 → 分块 → 翻译 → 校验 → 回写 → 报告 |
| `engines/__init__.py` | ~10 | **39** | 包公共 API re-export |
| `engines/renpy_engine.py` | ~100 | **74** | Ren'Py 薄包装：`run()` 委托给现有三条管线，`extract_texts()` 和 `write_back()` 抛 NotImplementedError |
| `engines/rpgmaker_engine.py` | ~600 | **636** | RPG Maker MV/MZ JSON 解析与回写（详见第 3 节） |
| `engines/csv_engine.py` | ~350 | **317** | CSV/JSONL 通用格式读写（详见第 4 节） |

### 2.3 EngineProfile 数据类

`EngineProfile` 是引擎差异的"参数化描述"，让 `protect_placeholders()` 和 `validate_translation()` 能根据引擎调整行为，而不需要写 if-else 分支。

**字段设计**：

| 字段 | 类型 | 用途 |
|------|------|------|
| `name` | `str` | 引擎标识符，如 `"renpy"` / `"rpgmaker_mv"` / `"csv"` |
| `display_name` | `str` | 用户可见名称，如 `"RPG Maker MV/MZ"` |
| `placeholder_patterns` | `list[str]` | 占位符正则列表，用于 `protect_placeholders` 参数化。Ren'Py: `[r"\[\w+\]", r"\{[^}]+\}"]`；RPG Maker: `[r"\\V\[\d+\]", r"\\N\[\d+\]", r"\\C\[\d+\]"]` 等 |
| `skip_line_patterns` | `list[str]` | 不应翻译的行模式正则（整行匹配） |
| `encoding` | `str` | 文件默认编码。RPG Maker MV/MZ 是 `"utf-8"`，老日系 VN 可能是 `"shift_jis"` |
| `max_line_length` | `int \| None` | 译文行宽限制。RPG Maker 自动换行所以为 None，某些老引擎有固定行宽 |
| `prompt_addon_key` | `str` | `core/prompts.py` 中引擎专属 prompt 片段的查找 key |
| `supports_context` | `bool` | 提取时是否提供上下文行 |
| `context_lines` | `int` | 上下文行数（默认 3，与 Ren'Py 的 `prev_context` 5 行对应） |

**辅助方法**：

- `compile_placeholder_re() -> re.Pattern | None`：将 `placeholder_patterns` 列表编译为单个正则（用 `|` 合并），返回 None 表示无占位符
- `compile_skip_re() -> re.Pattern | None`：同上，编译 skip 模式

**内置 Profile 常量**：

- `RENPY_PROFILE`：Ren'Py 专属占位符模式（`[var]`、`{tag}`、`%(name)s`），跳过 label/screen/init 行
- `RPGMAKER_MV_PROFILE`：RPG Maker 占位符（`\V[n]`、`\N[n]`、`\C[n]`、`\{`、`\}`、`\!`、`\\.`、`\|`、`\>`、`\<`、`\n`），无行跳过模式
- `CSV_PROFILE`：空占位符列表（用户可通过 CLI 自定义 `--placeholder-regex`），无上下文支持

用一个 `ENGINE_PROFILES` 字典注册所有内置 Profile，key 为 name 字符串。`rpgmaker_mv` 和 `rpgmaker_mz` 指向同一个 Profile 实例（MZ 和 MV 格式完全一致）。

### 2.4 TranslatableUnit 数据类

这是所有非 Ren'Py 引擎共用的"文本单元"数据类。Ren'Py 不使用它（Ren'Py 有自己的 DialogueEntry / StringEntry / chunk 体系）。

**字段设计**：

| 字段 | 类型 | 用途 |
|------|------|------|
| `id` | `str` | 全局唯一标识。格式由引擎决定：RPG Maker 用 JSON path（如 `"Map001.json:events[3].pages[0].list[5]"`），CSV 用行号或用户提供的 ID 列 |
| `original` | `str` | 原文 |
| `context` | `str` | 上下文（前后几行文本），用于 prompt 中给 AI 参考 |
| `file_path` | `str` | 来源文件相对路径，用于报告和进度追踪 |
| `speaker` | `str` | 说话人/角色名（如果引擎能提取到） |
| `metadata` | `dict[str, Any]` | 引擎专属元数据，round-trip 保留。RPG Maker 存 event code、page index、command index；CSV 存源格式和源文件路径 |
| `translation` | `str` | 翻译结果，由翻译流水线填入 |
| `status` | `str` | 状态枚举字符串：`"pending"` / `"translated"` / `"checker_dropped"` / `"ai_not_returned"` / `"skipped"` |

**设计要点**：

- `id` 的唯一性由引擎负责保证。RPG Maker 用 `文件名:JSON路径` 组合，天然唯一
- `metadata` 是 write_back 的关键——引擎在 extract 阶段存入定位信息，write_back 阶段根据这些信息精确回写。通用流水线不碰 metadata，只透传
- `status` 复用现有的状态命名约定（与 `core/translation_db.py` 的 status 字段一致），便于统一报告

### 2.5 EngineBase 抽象基类

**抽象方法（子类必须实现）**：

| 方法 | 签名 | 职责 |
|------|------|------|
| `_default_profile()` | `-> EngineProfile` | 返回该引擎的默认 Profile |
| `detect(game_dir)` | `Path -> bool` | 检查目录是否属于该引擎 |
| `extract_texts(game_dir, **kwargs)` | `Path -> list[TranslatableUnit]` | 从游戏文件中提取所有可翻译文本 |
| `write_back(game_dir, units, output_dir, **kwargs)` | `-> int` | 将翻译结果写回游戏文件，返回成功写入数 |

**可选覆写方法（有默认实现）**：

| 方法 | 默认行为 | 覆写场景 |
|------|----------|----------|
| `post_process(game_dir, output_dir)` | 什么都不做 | RPG Maker 可能需要清理临时文件 |
| `run(args)` | 调用 `generic_pipeline.run_generic_pipeline(self, args)` | **Ren'Py 覆写此方法**，委托给现有三条管线 |
| `dry_run(game_dir)` | 调用 `extract_texts()` 统计文件数/文本数/估算 token | 需要更精确统计时覆写 |

**构造函数**：`__init__` 调用 `_default_profile()` 存储到 `self.profile`。

### 2.6 EngineDetector 引擎检测器

**检测逻辑**（优先级从高到低，first match wins）：

| 优先级 | 引擎 | 检测特征 |
|--------|------|----------|
| 1 | Ren'Py | `game_dir/game/` 下有 `.rpy` 或 `.rpa` 文件；或 `game_dir/` 直接有 `.rpy` 文件 |
| 2 | RPG Maker MV | `game_dir/www/data/System.json` 存在 |
| 3 | RPG Maker MZ | `game_dir/data/System.json` 存在（注意：MZ 没有 `www/` 层级） |
| 4 | RPG Maker VX/Ace | `game_dir/` 下有 `.rgss2a` 或 `.rgss3a` 文件；或 `game_dir/Data/` 下有 `.rvdata` / `.rvdata2` 文件 |
| 5 | CSV/JSONL | 不自动检测，仅通过 `--engine csv` 手动指定 |

**注意 MV vs MZ 的区别**：两者 JSON 格式完全一致，唯一区别是目录结构（MV 多一层 `www/`）。代码中用同一个 Engine 类处理，只在 `_find_data_dir()` 内部区分路径。

**未识别时的行为**：
- 输出该目录下 top 10 文件扩展名及数量（诊断信息），帮助用户判断引擎类型
- 提示用户使用 `--engine` 手动指定

**公开函数**：

| 函数 | 签名 | 职责 |
|------|------|------|
| `detect_engine_type(game_dir)` | `Path -> EngineType` | 返回枚举值（纯检测，不实例化） |
| `detect_engine(game_dir)` | `Path -> EngineBase \| None` | 检测并返回 Engine 实例 |
| `create_engine(engine_type)` | `EngineType -> EngineBase \| None` | 从枚举创建 Engine 实例（延迟导入） |
| `resolve_engine(engine_arg, game_dir)` | `str, Path -> EngineBase \| None` | CLI `--engine` 参数路由。`"auto"` 调 `detect_engine()`；`"renpy"` / `"rpgmaker"` / `"csv"` 直接映射 |

**EngineType 枚举**：`RENPY` / `RPGMAKER_MV` / `RPGMAKER_VXACE` / `CSV` / `JSONL` / `UNKNOWN`

**延迟导入**：`create_engine()` 内部用 deferred import（`if engine_type == ...: from engines.xxx import XxxEngine`），避免加载不需要的模块，也避免不存在的模块导致 import 失败。

### 2.7 RenPyEngine 薄包装

**核心设计**：不实现 `extract_texts` / `write_back`（抛 NotImplementedError），只覆写 `run(args)`：

- 检查 `args.tl_mode` → 调用 `translators.tl_mode.run_tl_pipeline(args)`
- 检查 `args.retranslate` → 调用 `translators.retranslator.run_retranslate_pipeline(args)`
- 默认 → 调用 `translators.direct.run_pipeline(args)`

**import 策略**：`run()` 内部 deferred import `translators.direct` / `translators.tl_mode` / `translators.retranslator`，并 try-except 捕获 ImportError 给友好提示。

**detect 方法**：与 `engine_detector.py` 中 Ren'Py 检测逻辑一致（检查 `game//*.rpy` 或 `*.rpy`）。

**代码量**：预计 ~100 行。这是整个抽象层中最薄的一个类，它的意义不在于封装逻辑，而在于让 Ren'Py 能插入引擎检测和 CLI 路由体系中。

### 2.8 数据流总览

```
用户输入
  │
  ▼
main.py（--engine auto/renpy/rpgmaker/csv）
  │
  ├── resolve_engine() ──────────────────────────────────────────┐
  │                                                               │
  │   ┌──────────────────────────────────────────────────────┐   │
  │   │ engine_detector.py                                    │   │
  │   │  auto → detect_engine_type() → create_engine()       │   │
  │   │  manual → 直接映射 EngineType → create_engine()      │   │
  │   └──────────────────────────────────────────────────────┘   │
  │                                                               │
  ▼                                                               │
engine.run(args) ◄────────────────────────────────────────────────┘
  │
  ├── [Ren'Py] → 委托给现有三条管线（零改动）
  │     ├── translators.direct.run_pipeline()
  │     ├── translators.tl_mode.run_tl_pipeline()
  │     └── translators.retranslator.run_retranslate_pipeline()
  │
  └── [非 Ren'Py] → generic_pipeline.run_generic_pipeline()
        │
        ├── 1. engine.extract_texts(game_dir) → list[TranslatableUnit]
        ├── 2. build_chunks(units) → list[GenericChunk]
        ├── 3. 并发翻译（复用 APIClient / Glossary / Checker）
        │     ├── protect_placeholders（使用 EngineProfile.placeholder_patterns）
        │     ├── client.translate()
        │     ├── restore_placeholders
        │     └── check_response_item（使用 EngineProfile 参数化校验）
        ├── 4. engine.write_back(game_dir, units, output_dir) → int
        ├── 5. engine.post_process()
        └── 6. 报告生成（pipeline_report.json）
```

---

## 3. RPG Maker MV/MZ 支持 ✅ 已完成

> **状态**：阶段三落地。`engines/rpgmaker_engine.py`（636 行）实现完整的 RPGMakerMVEngine：目录定位（MV www/data/ vs MZ data/）、事件指令提取（401/405 连续合并 + 102 选项 + 402 When + 320/324 改名）、8 种数据库 JSON 提取（_DB_FIELDS 配置表）、System.json 全字段提取、JSON path 导航回写（_navigate_to_node + _patch_by_json_path）、对话块拆分回写（行数不匹配处理：少补空串、多截断）、紧凑 JSON 输出。`core/glossary.py` 新增 `scan_rpgmaker_database()` 方法（从 Actors.json 提取角色名 + System.json 提取系统术语）。15 个 RPG Maker 测试全绿。
>
> **第一版限制**：不处理 Code 356 插件指令、不自动安装中文字体、不处理 JS 硬编码文本（详见 §3.6）。

### 3.1 目录结构识别

RPG Maker MV 的典型目录结构：

```
GameRoot/
├── Game.exe / nw.exe
├── package.json              ← MV 特有
├── www/
│   ├── data/
│   │   ├── System.json       ← 检测入口
│   │   ├── Actors.json
│   │   ├── CommonEvents.json
│   │   ├── Map001.json ~ MapNNN.json
│   │   ├── Items.json / Skills.json / ...
│   │   └── Troops.json
│   ├── img/ / audio/ / js/
│   └── fonts/
```

RPG Maker MZ 的区别：没有 `www/` 层级，`data/` 直接在根目录下。JSON 格式完全一致。

### 3.2 可翻译文本的分类

RPG Maker 的可翻译文本分为两大类：**事件指令文本**和**数据库字段**。

#### 3.2.1 事件指令文本（Map / CommonEvents / Troops）

RPG Maker 的事件由一个 `list` 数组存储，每个元素是一个 `{code, indent, parameters}` 对象。翻译需要关注的 code：

| Code | 含义 | parameters 结构 | 翻译处理 |
|------|------|----------------|----------|
| 101 | Show Text 设置行 | `[faceName, faceIndex, background, positionType]` | **不翻译**。这是对话的"元数据行"（立绘、位置），紧跟在它后面的 401 才是文本 |
| 401 | Show Text 内容行 | `[text_string]` | **翻译** `parameters[0]`。多个连续 401 构成一条完整对话，需要**合并为一个 TranslatableUnit** |
| 102 | Show Choices | `[choices_array, cancelType]` | **翻译** `parameters[0]` 数组中的每个字符串 |
| 402 | When [Choice] | `[choiceIndex, choiceText]` | **翻译** `parameters[1]`（选项显示文本） |
| 105 | Show Scrolling Text 设置 | `[speed, noFast]` | **不翻译** |
| 405 | Show Scrolling Text 内容 | `[text_string]` | **翻译** `parameters[0]`。与 401 类似，连续 405 合并 |
| 320 | Change Name | `[actorId, name]` | **翻译** `parameters[1]` |
| 324 | Change Nickname | `[actorId, nickname]` | **翻译** `parameters[1]` |
| 108 | Comment | `[text]` | **不翻译**（开发者注释） |
| 408 | Comment 续行 | `[text]` | **不翻译** |
| 355 | Script Call | `[script]` | **不翻译**（JS 代码） |
| 356 | Plugin Command | `[command]` | **默认不翻译**。但某些插件（如 YEP_MessageCore、SRD_NameInputUpgrade）会在此嵌入文本，需要特殊处理——这是 RPG Maker 翻译最大的坑之一，详见 3.6 节 |
| 0 | 空指令 / 结束 | `[]` | 跳过 |

**关键设计：连续 401 合并**

RPG Maker 的对话文本是拆成多个 401 指令存储的。比如：

```json
{"code": 101, "parameters": ["Actor1", 0, 0, 2]},
{"code": 401, "parameters": ["Hello, traveler!"]},
{"code": 401, "parameters": ["Welcome to our town."]},
{"code": 401, "parameters": ["Please enjoy your stay."]},
{"code": 0,   "parameters": []}
```

这三行 401 在游戏中是一个对话框中的三行文字。翻译时必须作为一个整体发给 AI（否则 AI 无法理解上下文），回写时再按行拆回去。

**合并策略**：
- 遇到 401 开始缓冲，遇到非 401 时 flush 缓冲区
- 合并后的 `original` 用 `\n` 连接各行
- `metadata` 中记录起始 command index 和行数（`start_idx`, `line_count`）
- 回写时将翻译按 `\n` 拆分，逐行写回对应的 401 指令的 `parameters[0]`
- 如果翻译行数少于原文行数（AI 合并了行），后面的 401 填空字符串
- 如果翻译行数多于原文行数（AI 拆分了行），截断到原行数

同样的逻辑适用于连续 405（滚动文本）。

#### 3.2.2 数据库字段（Actors / Items / Skills / ...）

这些 JSON 文件是简单的对象数组（第一个元素始终为 null）。每个对象有固定的可翻译字段：

| 文件 | 可翻译字段 |
|------|-----------|
| `Actors.json` | `name`, `nickname`, `profile` |
| `Armors.json` | `name`, `description` |
| `Weapons.json` | `name`, `description` |
| `Items.json` | `name`, `description` |
| `Skills.json` | `name`, `description` |
| `States.json` | `name`, `message1`, `message2`, `message3`, `message4` |
| `Enemies.json` | `name` |
| `Classes.json` | `name` |

**提取策略**：遍历数组，跳过 null 元素，对每个对象提取指定字段中非空的字符串。

**ID 格式**：`文件名:[索引].字段名`，如 `"Actors.json:[1].name"` → `"Harold"`。

#### 3.2.3 System.json

System.json 包含系统级文本：

| 字段路径 | 含义 |
|----------|------|
| `gameTitle` | 游戏标题 |
| `currencyUnit` | 货币单位名 |
| `armorTypes[n]` | 护甲类型名（数组） |
| `elements[n]` | 属性名（数组） |
| `equipTypes[n]` | 装备部位名（数组） |
| `skillTypes[n]` | 技能类型名（数组） |
| `weaponTypes[n]` | 武器类型名（数组） |
| `terms.messages.*` | 系统消息字典（如 `alwaysDash`, `commandRemember` 等） |
| `terms.commands[n]` | 菜单命令名（数组） |
| `terms.params[n]` | 角色属性名（数组） |
| `terms.basic[n]` | 基础术语（等级、HP、MP 等名称）（数组） |

**提取策略**：分两类处理——简单字符串字段直接提取，数组/字典字段遍历提取。ID 使用 JSON path 格式，如 `"System.json:terms.messages.alwaysDash"`。

#### 3.2.4 MapInfos.json

`MapInfos.json` 包含地图名称列表。每个元素有 `name` 字段（如 "地下城 B1F"）。可翻译，但优先级低——只在需要翻译地图列表 UI 时才处理。建议第一版跳过，后续作为可选项。

### 3.3 TranslatableUnit 的 ID 设计

RPG Maker 的 ID 需要在 extract 和 write_back 之间精确对应。推荐格式：

```
文件名:JSON路径
```

示例：
- 地图对话：`Map001.json:events[3].pages[0].list[5]`（指向 401 块的起始 command）
- 选项：`Map001.json:events[3].pages[0].list[10].choices[2]`
- 角色名：`Actors.json:[1].name`
- 系统消息：`System.json:terms.messages.alwaysDash`

**为什么不用纯数字 hash？** 因为 JSON path 格式的 ID 在报告中直接可读（用户看到 `Map001.json:events[3].pages[0].list[5]` 就知道是哪个地图哪个事件），而 hash 需要额外的映射表。调试时也更方便。

### 3.4 write_back 回写策略

**整体流程**：

1. 将所有翻译后的 TranslatableUnit 按 `file_path` 分组
2. 对每个文件：加载原始 JSON → 遍历该文件的 units → 按 `metadata` 中的定位信息找到 JSON 节点 → 替换值 → 写出
3. 输出位置：如果指定了 `output_dir`，写到 `output_dir/data/xxx.json`（保持目录结构）；否则原地修改（先创建 `.bak` 备份，不覆盖已有备份）

**JSON path 导航**：需要实现一个通用的 `_patch_by_json_path(data, path, value)` 函数，支持 `[n]` 数组索引和 `.key` 字典索引混合。

**对话块回写**（type == "dialogue"）特殊处理：
- 根据 `metadata.start_idx` 和 `metadata.line_count` 定位到 command list 中的连续 401 指令
- 将翻译文本按 `\n` 拆分
- 逐行写回每个 401 的 `parameters[0]`
- 行数不匹配时：多的截断，少的填空字符串

**JSON 输出格式**：使用 `json.dump(data, f, ensure_ascii=False)`。注意 RPG Maker 的 JSON 默认是无缩进、紧凑格式（`separators=(",", ":")`）。保持紧凑格式可以减小文件体积，也与游戏原始格式一致。但这一点可以做成可配置的（`--pretty-json` 用于调试时查看差异）。

### 3.5 RPG Maker 占位符语法

RPG Maker 的文本控制码（message codes）需要在翻译中保留：

| 控制码 | 含义 | 保护优先级 |
|--------|------|-----------|
| `\V[n]` | 显示游戏变量 n 的值 | 高——必须保留 |
| `\N[n]` | 显示角色 n 的名字 | 高——必须保留 |
| `\P[n]` | 显示队伍成员 n 的名字 | 高——必须保留 |
| `\G` | 显示货币单位 | 高 |
| `\C[n]` | 改变文字颜色 | 中——保留但位置可变 |
| `\I[n]` | 显示图标 | 中 |
| `\{` / `\}` | 放大/缩小文字 | 中 |
| `\!` | 等待玩家按键 | 低——位置相关 |
| `\.` / `\|` | 等待 1/4 秒 / 1 秒 | 低 |
| `\>` / `\<` | 瞬间显示开/关 | 低 |
| `\n` | 文本内换行 | 中——结构相关 |
| `\\` | 显示反斜杠 | 低 |

**与 Ren'Py 占位符的对比**：

Ren'Py 的占位符（`[var]`、`{tag}`）是用方括号和花括号，与英文文本不太容易混淆。RPG Maker 的控制码用反斜杠开头，这有两个特殊问题：

1. JSON 中反斜杠需要转义。`\V[1]` 在 JSON 中存储为 `"\\V[1]"`，读入内存后是 `\V[1]`。但有些游戏的 JSON 转义不规范（比如直接存 `\V[1]` 而不是 `\\V[1]`），需要兼容处理。

2. AI 可能会把 `\n` 当作换行符而不是 RPG Maker 的换行控制码。需要在 prompt 中明确说明 `\n` 在 RPG Maker 中是显示换行命令，不是转义字符。

**保护策略**：复用现有的 `protect_placeholders()` 框架，但传入 `RPGMAKER_MV_PROFILE.placeholder_patterns` 作为匹配模式。因为占位符模式存在 `EngineProfile` 中，所以 `protect_placeholders()` 只需要新增一个可选参数 `patterns: list[str] | None`，为 None 时使用默认的 Ren'Py 模式（向后兼容）。

### 3.6 RPG Maker 的特殊难点

#### 3.6.1 插件指令文本（Code 356）

很多 RPG Maker 色情游戏使用第三方插件来实现扩展功能，这些插件可能在 Code 356（Plugin Command）中嵌入可翻译文本。常见的有：

- **YEP_MessageCore**：扩展消息语法（`<WordWrap>`、`\af[n]` 等）
- **SRD_NameInputUpgrade**：名字输入界面文本
- **Galv_MessageStyles**：气泡对话样式
- **YEP_QuestJournal**：任务描述

**处理策略**：第一版不处理 356 指令。原因：插件指令格式不标准（每个插件自定义），误翻可能导致游戏崩溃。后续可以做成可配置的白名单机制——用户指定哪些插件的 356 需要翻译。

#### 3.6.2 同一原文多次出现

RPG Maker 中同一句话可能在多个地图/事件中出现（比如 NPC 的通用对话 "Welcome!"）。因为 ID 是 JSON path 格式（包含文件名 + 事件索引），每次出现都是独立的 TranslatableUnit，不会互相干扰。这比 Ren'Py 的 direct-mode（按文本匹配回写，同一原文多次出现会冲突）天然更安全。

#### 3.6.3 中文字体

RPG Maker MV/MZ 使用 Web 字体。游戏默认字体通常不包含中文字符。翻译后需要：

1. 在 `www/fonts/` 或 `fonts/` 下放入中文字体文件（如 NotoSansSC）
2. 修改 `www/js/plugins.js` 或 `data/System.json` 中的字体配置
3. 某些游戏需要修改 `css/game.css` 中的 `@font-face`

**处理策略**：第一版不自动处理字体。在翻译完成后的报告中提示用户需要手动安装中文字体，并给出常见的字体安装方法。后续可以做成可选的 `--patch-font` 功能（类似现有 Ren'Py 的 `tools/font_patch.py`）。

#### 3.6.4 www/js/plugins.js 中的硬编码文本

有些游戏在 `plugins.js` 中硬编码了 UI 文本（如菜单标签、提示信息）。这些不在 `data/` 的 JSON 中，需要单独提取。

**处理策略**：第一版不处理 JS 文件。这类文本数量通常很少，用户可以手动翻译。后续可以考虑支持正则扫描 JS 文件中的引号字符串。

#### 3.6.5 加密的 .rpgmvo / .rpgmvp / .ogg_ 文件

有些游戏对图片和音频做了加密（非文本加密）。这不影响文本翻译——`data/` 下的 JSON 文件不加密。但如果游戏使用了 rpg_core.js 的自定义加密，可能会影响 System.json 的读取。

**处理策略**：正常读取 JSON。如果 JSON 解析失败，输出警告并跳过该文件。大多数情况下 data/*.json 是不加密的。

### 3.7 RPGMakerMVEngine 类的方法设计

**公开方法**（实现 EngineBase 接口）：

| 方法 | 核心逻辑 |
|------|----------|
| `detect(game_dir)` | 检查 `www/data/System.json` 或 `data/System.json` 是否存在 |
| `extract_texts(game_dir)` | 遍历 data/ 下所有 JSON，按文件类型分发给不同的提取函数，汇总返回 |
| `write_back(game_dir, units, output_dir)` | 按文件分组 → 加载 JSON → 按 metadata 定位 → 替换 → 写出 |
| `post_process(game_dir, output_dir)` | 可选：输出字体安装提示 |

**内部方法**：

| 方法 | 职责 |
|------|------|
| `_find_data_dir(game_dir)` | 定位 `www/data/` 或 `data/`，返回 Path 或 None |
| `_extract_map(json_path)` | 解析 MapXXX.json：提取 displayName + 遍历 events → pages → list |
| `_extract_common_events(json_path)` | 解析 CommonEvents.json：遍历 events → list |
| `_extract_troops(json_path)` | 解析 Troops.json：提取 troop name + 遍历 pages → list |
| `_extract_event_commands(cmd_list, json_path, prefix)` | **核心函数**：遍历 command list，按 code 分发，处理 401 合并、102 选项、320/324 改名 |
| `_extract_database(json_path, filename)` | 通用数据库提取：按文件名查配置表获取字段列表 → 遍历数组提取 |
| `_extract_system(json_path)` | System.json 专属提取：简单字段 + 数组字段 + 嵌套字典 |
| `_patch_by_id(data, unit)` | 单条回写分发：根据 `metadata.type` 调用不同的 patch 方法 |
| `_patch_dialogue(data, unit)` | 对话块回写：导航到 command list → 按行拆分翻译 → 写回连续 401 |
| `_patch_by_json_path(data, path, value)` | 通用 JSON path 导航 + 赋值：支持 `[n]` 索引和 `.key` 混合 |
| `_navigate_to_list(data, prefix_path)` | 导航到某个 event page 的 `list` 数组 |
| `_rel_path(json_path)` | 计算相对于 data/ 的路径（保留 `www/data/` 或 `data/` 前缀） |

### 3.8 RPG Maker 翻译的 prompt 设计

RPG Maker 的 prompt 与 Ren'Py 有几个关键差异需要在 `core/prompts.py` 中体现：

1. **变量语法说明**：需要在 prompt 中明确列出 `\V[n]`、`\N[n]`、`\C[n]` 等控制码及其含义，告诉 AI 必须保留
2. **多行对话**：RPG Maker 的对话是一个文本框多行显示，翻译需要保持 `\n` 换行结构
3. **选项文本**：选项通常很短（2-6 个字），需要提示 AI 保持简洁
4. **角色引用**：`\N[1]` 会被游戏替换为角色名，prompt 中应说明这是"角色名引用"而非乱码
5. **H 场景特殊性**：色情 RPG Maker 游戏的 H 描述通常比 VN 更碎片化（穿插在战斗/事件中），上下文不如 VN 连贯，需要更依赖术语表保持一致性

**建议实现**：在 `core/prompts.py` 中新增一个 `_ENGINE_PROMPT_ADDONS` 字典，key 为 `EngineProfile.prompt_addon_key`，value 为追加到基础 prompt 末尾的引擎专属说明。Ren'Py 现有 prompt 零改动。

### 3.9 与现有 Glossary 的集成

Glossary 的 `scan_game_directory` 目前只扫描 `.rpy` 文件中的 `define` 语句来提取角色名。对 RPG Maker 需要：

- 读取 `Actors.json` 提取角色名（`name` 和 `nickname`）
- 读取 `System.json` 的 `terms` 提取系统术语

**改动方式**：在 `Glossary` 类中新增 `scan_rpgmaker_database(data_dir)` 方法，在 `generic_pipeline` 初始化阶段调用。现有 `scan_game_directory` 不改。

---

## 4. CSV/JSONL 通用格式支持 ✅ 已完成

> **状态**：阶段二落地。`engines/csv_engine.py`（317 行）实现 CSVEngine：单文件或目录扫描（.csv/.tsv/.jsonl/.json）、6 组列名别名集自动匹配（original/source/text/en 等）、UTF-8 BOM 支持、多行 CSV 安全读取（`with open(..., newline="")` + DictReader）、JSON 数组 fallback、按源格式分流回写（CSV → translations_zh.csv / JSONL → translations_zh.jsonl）。10 个 CSV 测试全绿。

### 4.1 设计目标

让用户能用**任何外部工具**（GARbro、Translator++、VNTextPatch、AssetStudio、XUnity AutoTranslator 导出）提取文本，导出为 CSV 或 JSONL，然后用我们的工具做 AI 翻译 + 质量校验，再用原工具回灌。

这条路径的价值在于：**一天之内覆盖所有引擎**，而且零依赖（CSV 和 JSON 都是标准库）。

### 4.2 支持的输入格式

#### CSV（含 TSV）

```csv
id,original,speaker,context
line_001,"Hello, traveler!",Guard,"Near town gate"
line_002,"Welcome to our town.",Guard,"After greeting"
```

**规则**：

- 第一行必须是表头
- 必须包含至少一个"原文列"：`original` / `source` / `text` / `en` / `english`（大小写不敏感）
- 可选列：`id` / `key`（没有则自动用行号）、`speaker` / `character`、`context` / `note`、`file` / `filename`
- 列名匹配使用**别名集合**（不要求精确匹配某个特定名字）
- 支持 UTF-8 BOM（`utf-8-sig`）
- TSV 用 `\t` 分隔，文件扩展名 `.tsv`

**为什么要支持这么多列名别名？** 因为不同工具导出的 CSV 用的列名不一样。Translator++ 用 `original`，VNTextPatch 用 `source`，有些自制工具用 `text` 或 `en`。支持别名可以让用户拿到的 CSV 直接用，不需要手动改表头。

#### JSONL

```jsonl
{"id": "line_001", "original": "Hello, traveler!", "speaker": "Guard"}
{"id": "line_002", "original": "Welcome to our town.", "speaker": "Guard"}
```

**规则**：

- 每行一个 JSON 对象
- 字段名别名同 CSV
- 也支持标准 JSON 数组格式（`[{...}, {...}]`）作为 fallback

### 4.3 输出格式

翻译完成后，输出一个新文件（不修改输入文件），添加目标语言列/字段：

**CSV 输出**：`translations_zh.csv`

```csv
id,original,speaker,context,zh
line_001,"Hello, traveler!",Guard,"Near town gate","你好，旅行者！"
line_002,"Welcome to our town.",Guard,"After greeting","欢迎来到我们的小镇。"
```

**JSONL 输出**：`translations_zh.jsonl`

```jsonl
{"id": "line_001", "original": "Hello, traveler!", "zh": "你好，旅行者！", "speaker": "Guard"}
```

### 4.4 CSVEngine 类的方法设计

| 方法 | 职责 |
|------|------|
| `detect(game_dir)` | **始终返回 False**。CSV 不自动检测，必须通过 `--engine csv` 手动指定 |
| `extract_texts(game_dir)` | 扫描 game_dir 下所有 `.csv` / `.tsv` / `.jsonl` / `.json` 文件，分发给对应的解析方法 |
| `write_back(game_dir, units, output_dir)` | 按输出格式（CSV 或 JSONL）写出翻译结果文件 |
| `_extract_csv(file_path, delimiter)` | 读 CSV：DictReader → 列名别名解析 → 构建 TranslatableUnit |
| `_extract_jsonl(file_path)` | 读 JSONL：逐行 json.loads → 字段别名解析 → 构建 TranslatableUnit |
| `_extract_json_or_jsonl(file_path)` | `.json` 文件先尝试 JSONL，失败后尝试 JSON 数组 |
| `_obj_to_unit(obj, file_path, idx)` | 将一个 JSON 对象转为 TranslatableUnit（含别名解析） |
| `_write_csv(units, out_dir, target_lang)` | DictWriter 输出 + UTF-8 BOM |
| `_write_jsonl(units, out_dir, target_lang)` | 逐行 json.dumps 输出 |
| `_find_column(headers, aliases)` | 在 CSV 表头中按别名集合找到实际列名 |

### 4.5 CLI 交互设计

```bash
# CSV 翻译（指定输入文件）
python main.py --engine csv --game-dir texts.csv --provider xai --api-key KEY

# CSV 翻译（指定输入目录，翻译目录下所有 CSV）
python main.py --engine csv --game-dir /path/to/csvs/ --provider xai --api-key KEY

# JSONL 翻译
python main.py --engine jsonl --game-dir texts.jsonl --provider xai --api-key KEY

# 指定输出目录
python main.py --engine csv --game-dir texts.csv --output-dir translated/ --provider xai --api-key KEY

# 自定义占位符模式（某些自制格式可能有特殊变量语法）
python main.py --engine csv --game-dir texts.csv --placeholder-regex '\{\w+\}' --provider xai --api-key KEY
```

---

## 5. 通用翻译流水线 ✅ 已完成

> **状态**：阶段二落地。`generic_pipeline.py`（414 行）实现 6 阶段通用翻译流水线：Stage 0 提取 + Stage 1 初始化（APIClient/Glossary/TranslationDB/断点恢复/RPG Maker 术语钩子）+ Stage 2 分块（`build_generic_chunks` 按 file_path 分组 + max_size=30/max_chars=6000）+ Stage 3 并发翻译（ThreadPoolExecutor + id/original 双重匹配 + 多字段名查找 + 占位符保护/还原）+ Stage 4 回写 + Stage 5 后处理 + Stage 6 报告。原子进度写入 `generic_progress.json`，translation_db 断点恢复避免重复翻译。5 个 pipeline 测试全绿。

### 5.1 generic_pipeline.py 的职责

这个模块是所有非 Ren'Py 引擎共用的翻译编排器。它的流程类似于 `translators/direct.py` 的 `run_pipeline`，但基于 `TranslatableUnit` 而非 `.rpy` 文件。

**它不是 Ren'Py 管线的替代品**——Ren'Py 仍然走自己的三条专用管线。它是新引擎的默认 `run()` 实现。

### 5.2 流程详解

#### Stage 0: 提取

- 调用 `engine.extract_texts(game_dir)` 获取全部 TranslatableUnit
- 输出统计：文件数、文本条数、总字符数
- 如果返回空列表，直接退出

#### Stage 1: 初始化

- 创建 `APIClient`（从 args 读取 provider / model / api_key / rpm / rps 等）
- 创建 `Glossary`（加载用户词典 `--dict`）
- 对 RPG Maker 引擎：调用 `glossary.scan_rpgmaker_database()` 自动提取角色名/系统术语
- 创建 `TranslationDB`（`output_dir/translation_db.json`）
- 加载断点续传进度（`output_dir/generic_progress.json`），过滤掉已完成的 unit

#### Stage 2: 分块

`build_chunks(units, max_size, max_chars) -> list[GenericChunk]`

- 先按 `file_path` 分组（同一文件的文本在一起，提供上下文连贯性）
- 在文件内部按 `max_size`（默认 30 条）和 `max_chars`（默认 6000 字符）拆块
- `GenericChunk` 数据类包含：`units: list[TranslatableUnit]`、`chunk_id: int`、`file_path: str`

**与 Ren'Py 分块的区别**：Ren'Py 按代码块边界（label / screen / init）拆分，这里按条数/字符数拆分。因为 TranslatableUnit 已经是独立的文本单元，不需要关心代码结构。

#### Stage 3: 翻译

每个 chunk 的翻译流程：

1. 构建 user prompt：将 chunk 中每个 unit 的 `{id, original, speaker?, context?}` 打成 JSON 数组
2. 调用 `client.translate(system_prompt, user_prompt)`
3. 解析返回的 JSON 数组（复用 `core.api_client.parse_json_response` 的 6 级容错）
4. 匹配结果到 unit：先按 `id` 匹配，fallback 按 `original` 文本匹配
5. 提取 translation：按 `[target_lang, "translation", "trans", "zh"]` 顺序查找字段
6. 基本校验：翻译非空、与原文不完全相同（相同时仅 debug 日志，不丢弃——可能是术语/专有名词）
7. 设置 `unit.status = "translated"` 并记录到 `completed_ids`

**并发控制**：使用 `ThreadPoolExecutor(max_workers=args.workers)`，与 Ren'Py 的 tl-mode 并发策略一致。`RateLimiter` 和 `UsageStats` 天然线程安全（已有 `threading.Lock`）。

**进度保存**：每完成一个 chunk 后保存 `completed_ids` 到 `generic_progress.json`（atomic write：tmp + os.replace，与 ProgressTracker 相同策略）。

**重试策略**：复用 `core/api_client.py` 的指数退避 + Retry-After + jitter 机制。chunk 级重试暂不实现（留给后续迭代，可复用 Ren'Py 的 `_translate_chunk_with_retry` 逻辑）。

#### Stage 4: 回写

- 调用 `engine.write_back(game_dir, units, output_dir)`
- 引擎内部负责定位和替换
- 返回成功写入数

#### Stage 5: 后处理

- 调用 `engine.post_process(game_dir, output_dir)`
- 默认空操作，引擎可覆写

#### Stage 6: 报告

- 生成 `pipeline_report.json`：引擎名、总条数、已翻译数、未翻译数、翻译率、成功写入数
- 与 `one_click_pipeline` 的 `pipeline_report.json` 格式保持兼容（共用字段名）
- 后续可以扩展：接入 `review_generator.py` 生成 HTML 校对报告

### 5.3 与现有基础设施的复用关系

| 现有模块 | 通用流水线中的用法 | 是否需要改动 |
|----------|-------------------|-------------|
| `core/api_client.py` | 直接复用。`APIClient`、`RateLimiter`、`UsageStats`、`parse_json_response` | **不改** |
| `core/glossary.py` | 直接复用。`Glossary`、`load_dict`、`to_prompt_text`、`update_from_translations` | **小改**：新增 `scan_rpgmaker_database()` 方法 |
| `core/translation_db.py` | 直接复用。`TranslationDB` 存储 per-unit 翻译元数据 | **不改** |
| `core/prompts.py` | 新增引擎 addon 机制。`build_system_prompt` 新增 `engine_profile` 参数（可选，默认 None 走 Ren'Py 路径） | **小改**：新增 addon 字典 + 通用模板 |
| `file_processor/patcher.py` | `protect_placeholders()` / `restore_placeholders()` 新增可选 `patterns` 参数 | **小改**：参数化占位符模式 |
| `file_processor/checker.py` | `check_response_item()` 中的占位符集合校验需要感知引擎占位符语法 | **小改**：新增可选 `placeholder_re` 参数 |
| `file_processor/validator.py` | 通用流水线中暂不调用（不做 .rpy 行级校验）。后续可扩展引擎专属 validator | **不改** |
| `translation_utils.py` | `ProgressTracker` 不直接复用（通用流水线用自己的 progress.json 格式），但 `ChunkResult` 数据类可参考 | **不改** |
| `config.py` | 直接复用。Config 类的三层合并机制 | **不改** |
| `lang_config.py` | 直接复用。`LanguageConfig` 用于 prompt 和 W442 校验的语言参数化 | **不改** |
| `review_generator.py` | 后续可接入通用流水线，生成 HTML 校对报告 | **不改**（后续扩展） |

---

## 6. 现有模块的适配改动 ✅ 已完成

> **状态**：全部适配已落地。实际改动：`main.py`（+15 行：`--engine` 参数 + 路由分支）、`file_processor/checker.py`（+20 行：`protect_placeholders(patterns=)` + `check_response_item(placeholder_re=)` + `_extract_placeholder_sequence(regex=)` 三处参数化）、`core/prompts.py`（+40 行：`_ENGINE_PROMPT_ADDONS` 字典 + `build_system_prompt(engine_profile=)` 参数）、`core/glossary.py`（+60 行：`scan_rpgmaker_database()` 方法）。所有改动通过可选参数实现，70 现有测试零回归，`test_prompt_zh_unchanged` 基线保证中文 prompt 不变。

本节列出为了支持多引擎，现有代码需要做的最小改动。遵循"默认行为不变"原则——所有改动都通过新增可选参数实现，不改现有调用方的代码。

### 6.1 main.py

**改动内容**：

1. argparse 新增 `--engine` 参数：`choices=["auto", "renpy", "rpgmaker", "csv", "jsonl"]`，默认 `"auto"`
2. 在参数解析完成后、路由逻辑之前，调用 `resolve_engine(args.engine, game_dir)`
3. 如果 `resolve_engine` 返回 `RenPyEngine` 或参数中有 `--tl-mode` / `--retranslate`，走现有路径（完全不变）
4. 如果返回其他引擎，调用 `engine.run(args)`

**预计改动量**：~20 行新增，0 行修改现有代码。

**向后兼容**：`--engine` 默认为 `"auto"`，auto 检测到 Ren'Py 后走原有路径。用户不加 `--engine` 参数时行为完全不变。

### 6.2 file_processor/patcher.py

**改动内容**：

`protect_placeholders(text, existing_mapping=None)` → `protect_placeholders(text, existing_mapping=None, patterns=None)`

- `patterns` 为 `list[str] | None`
- 为 None 时使用现有的 Ren'Py 硬编码模式（`_PLACEHOLDER_RE` 等）——**默认行为不变**
- 非 None 时使用传入的正则模式列表（从 `EngineProfile.placeholder_patterns` 传入）

`restore_placeholders(text, mapping)` 不需要改动——它只根据 mapping 字典还原，与引擎无关。

**预计改动量**：~15 行。在 `protect_placeholders` 函数开头加一个分支：如果 `patterns` 不为 None，编译传入的模式并用它匹配，替代默认正则。

### 6.3 file_processor/checker.py

**改动内容**：

`check_response_item(item, line_offset, ...)` 中的占位符集合一致性校验目前硬编码了 Ren'Py 的占位符正则。需要参数化：

- 新增可选参数 `placeholder_re: re.Pattern | None`
- 为 None 时使用现有的 Ren'Py 正则——**默认行为不变**
- 非 None 时使用传入的编译后正则

**预计改动量**：~10 行。

### 6.4 core/prompts.py

**改动内容**：

1. 新增一个模块级字典 `_ENGINE_PROMPT_ADDONS`，存储引擎专属 prompt 片段：

   ```
   _ENGINE_PROMPT_ADDONS = {
       "rpgmaker": "RPG Maker 变量语法说明...",
       "generic": "通用翻译说明...",
   }
   ```

2. `build_system_prompt(genre, glossary, ..., engine_profile=None)` 新增可选参数：
   - 为 None 时走现有的中文/通用分支——**默认行为不变**
   - 非 None 时：先构建基础 prompt（复用 `_build_generic_system_prompt` 的逻辑），然后追加 `_ENGINE_PROMPT_ADDONS[engine_profile.prompt_addon_key]`

**预计改动量**：~40 行新增（prompt addon 文本 + 参数传递）。

**中文 prompt 零变更验证**：新增的代码路径只在 `engine_profile` 非 None 时触发。现有 `test_prompt_zh_unchanged` 测试保证 Ren'Py prompt 不受影响。

### 6.5 core/glossary.py

**改动内容**：

新增方法 `scan_rpgmaker_database(data_dir: Path) -> None`：

- 读取 `Actors.json` 提取角色名（`name`、`nickname`）加入 `characters` 字典
- 读取 `System.json` 的 `terms.basic` / `terms.commands` 加入 `terms` 字典
- 不修改现有的 `scan_game_directory` 方法

**预计改动量**：~40 行。

### 6.6 one_click_pipeline.py

**第一版不改动**。one_click_pipeline 只服务于 Ren'Py 的四阶段流水线（pilot → gate → full → retranslate），其逻辑与 Ren'Py 深度耦合（风险评分、density 检测、retranslate 补翻等）。

后续可以做一个 `generic_one_click_pipeline.py`，提供类似的 pilot → 全量 → 补翻 流程，但这不在第一版范围内。

### 6.7 改动汇总

| 文件 | 改动类型 | 预计 | 实际 | 现有行为 |
|------|----------|------|------|----------|
| `main.py` | 新增 `--engine` 参数 + 路由分支 | ~20 行 | **+15 行** | 不变 |
| `file_processor/checker.py` | `protect_placeholders(patterns=)` + `check_response_item(placeholder_re=)` + `_extract_placeholder_sequence(regex=)` | ~25 行 | **+20 行** | 不变 |
| `core/prompts.py` | `_ENGINE_PROMPT_ADDONS` 字典 + `build_system_prompt(engine_profile=)` | ~40 行 | **+40 行** | 不变（baseline 测试保证） |
| `core/glossary.py` | `scan_rpgmaker_database()` 方法 | ~40 行 | **+60 行** | 不变 |
| **合计** | | **~125 行** | **~135 行新增** | **0 行修改** |

> **注**：原计划中 `file_processor/patcher.py` 的改动实际合并到 `checker.py`（`protect_placeholders` 和 `check_response_item` 都在 `checker.py` 中）。

---

## 7. 测试策略 ✅ 已完成

### 7.1 新增测试文件

| 文件 | 预计用例数 | 实际用例数 | 覆盖范围 |
|------|-----------|-----------|----------|
| `tests/test_engines.py` | ~55-65 | **62** | EngineProfile 编译 6 + TranslatableUnit 3 + 引擎检测 10 + RenPyEngine 5 + EngineBase 1 + CSV 提取/回写 10 + generic_pipeline 分块/匹配 5 + patcher/checker 参数化 4 + prompts addon 2 + RPG Maker 提取/回写 15 + glossary RPG Maker 1 |

### 7.2 测试数据

所有测试使用 `tempfile.TemporaryDirectory()` 动态构造，不需要预置测试文件：

- **引擎检测**：创建临时目录，放入特征文件（如 `game/script.rpy` 或 `data/System.json`），验证检测结果
- **RPG Maker 提取**：构造最小合法的 Map JSON（含 101 + 401 + 102 + 0 指令序列），验证提取出的 TranslatableUnit 数量和字段正确性
- **RPG Maker 回写**：提取 → 手动填入翻译 → 回写 → 重新读取 JSON 验证值已替换
- **CSV/JSONL**：写入临时 CSV/JSONL 文件 → 提取 → 验证字段映射

### 7.3 测试分类

| 类型 | 需要 API | 测试内容 |
|------|---------|----------|
| 单元测试 | 否 | EngineProfile / TranslatableUnit / build_chunks / 列名别名解析 |
| 集成测试 | 否 | 引擎检测 + 提取 + 回写的完整流程 |
| 端到端测试 | **是** | 对真实 RPG Maker 游戏目录运行 `--engine rpgmaker --dry-run` 验证提取完整性 |

### 7.4 对现有测试的影响

**零影响**（已验证）。所有现有 70 个测试 + 13 个冒烟测试 + 75 个 tl_parser 断言全部通过。因为：

- 现有模块的改动全部通过新增可选参数实现，默认值保持原有行为
- `test_prompt_zh_unchanged` 基线测试保证 Ren'Py prompt 不受影响
- 新测试在独立文件 `tests/test_engines.py` 中

### 7.5 CI 扩展

在 `.github/workflows/test.yml` 中新增：

1. 新文件的 `py_compile` 语法检查：`engine_base.py` / `engine_detector.py` / `generic_pipeline.py` / `engines/*.py`
2. 运行 `python test_engines.py`
3. 可选：RPG Maker dry-run 集成测试（需要在 `tests/` 下放一个最小的 RPG Maker data/ 目录）

---

## 8. 后续引擎路线图

### 8.1 优先级排序（按色情游戏实际占比 + 实现难度）

| 优先级 | 引擎 | 占比估计 | 实现难度 | 依赖 | 状态 |
|--------|------|----------|----------|------|------|
| ✅ P0 | Ren'Py | ~35% | — | — | **已完成**（第一轮~第十二轮） |
| ✅ P0 | RPG Maker MV/MZ | ~25% | 低 | 纯标准库 | **已完成**（第十二轮阶段三，636 行） |
| ✅ P0 | CSV/JSONL 通用 | 覆盖全部 | 最低 | 纯标准库 | **已完成**（第十二轮阶段二，317 行） |
| 🟡 P1 | RPG Maker VX/Ace | ~5% | 中 | `rubymarshal`（可选） | 待实现 |
| 🟡 P1 | Wolf RPG Editor | ~5% | 中 | 需要自定义二进制解析 | 待实现 |
| 🟡 P1 | Godot | ~3% | 低 | 纯标准库（.tscn/.gd 是文本格式） | 待实现 |
| 🟢 P2 | Unity（XUnity 格式） | ~10% | 低 | 只支持 XUnity AutoTranslator 导出的文本文件，不做 AssetBundle 解析 | 待实现 |
| 🟢 P2 | Kirikiri 2/Z | ~5% | 中 | 参考 VNTextPatch 的 .ks/.scn 解析 | 待实现 |
| 🟢 P2 | TyranoBuilder | ~3% | 低 | .ks 脚本格式类似 Kirikiri | 待实现 |
| 🔵 P3 | Unreal Engine | ~5% | 高 | 需要 uasset 工具或 Runtime Hook | 暂不计划 |
| 🔵 P3 | HTML5 / 浏览器游戏 | ~3% | 最低 | 解析 JS/JSON 字符串 | 按需 |
| 🔵 P3 | HTML5 / 浏览器游戏 | ~3% | 最低 | 解析 JS/JSON 字符串 | 按需 |

### 8.2 各引擎的实现要点

#### RPG Maker VX/Ace（P1）

- **文件格式**：Ruby Marshal（`.rxdata` / `.rvdata` / `.rvdata2`），二进制格式
- **依赖**：需要 `rubymarshal` 库（`pip install rubymarshal`）
- **零依赖处理**：`RPGMakerVXEngine.detect()` 中 try-import，缺依赖时返回 None + 友好提示
- **数据结构**：与 MV/MZ 类似的数组/对象结构，但用 Ruby 的 Marshal.dump 序列化
- **可翻译内容**：同 MV/MZ，但事件指令的 code 编号不同（VX 和 XP 用的 code 体系与 MV 略有差异）
- **回写**：需要 `rubymarshal.writer` 写回 Ruby Marshal 格式
- **建议**：先只读取支持（提取 → CSV 输出 → 用户手动导入），后续再做直接回写

#### Wolf RPG Editor（P1）

- **文件格式**：自定义二进制格式（`.wolf` / `.dat`）
- **已有工具**：WolfTrans、DXExtract 可以提取文本
- **建议路径**：不自己解析二进制，而是支持 WolfTrans 的导出格式（通常是 CSV 或自定义文本文件），通过 CSVEngine 间接支持

#### Godot（P1）

- **文件格式**：`.tscn`（场景文件，文本格式）、`.gd`（GDScript，文本格式）、`.tres`（资源文件）
- **可翻译内容**：
  - `.tscn` 中的 `text` 属性（Label、Button 等节点）
  - `.gd` 中的 `tr("...")` 翻译函数调用
  - `.csv` 翻译表（Godot 的 I18N 系统用 CSV）
  - `.po` / `.pot` Gettext 格式（Godot 也支持）
- **建议路径**：
  - Godot 的 CSV 翻译表可以直接用 CSVEngine
  - `.gd` 中的 `tr("...")` 需要正则提取
  - `.tscn` 是 INI-like 格式，需要简单的文本解析
- **依赖**：纯标准库

#### Unity / XUnity 格式（P2）

- **不做 AssetBundle 解析**（需要 `UnityPy`，破坏零依赖，且加密问题多）
- **支持 XUnity AutoTranslator 的导出格式**：XUnity 会在游戏目录下生成 `AutoTranslator/` 文件夹，里面有 `_AutoGeneratedTranslations.txt` 和其他文本文件
- **格式**：每行 `original=translation`（键值对格式），或 JSON 格式
- **实现**：新增 `engines/xunity_engine.py`，解析 XUnity 的文本文件 → TranslatableUnit → 翻译 → 写回
- **用户工作流**：
  1. 安装 BepInEx + XUnity.AutoTranslator
  2. 运行游戏一次，XUnity 自动导出未翻译文本
  3. 用我们的工具翻译导出的文本
  4. 将翻译结果放回 XUnity 目录
  5. 再次运行游戏，XUnity 加载翻译

#### Kirikiri 2/Z（P2）

- **文件格式**：`.ks`（KAG 脚本，文本格式）、`.scn`（编译后的场景，二进制）
- **已有工具**：VNTextPatch（C#）已支持 Kirikiri 的 extract/patch
- **建议路径**：
  - `.ks` 是文本格式，可以直接正则提取对话行
  - `.scn` 需要二进制解析，优先通过 VNTextPatch 导出 CSV → CSVEngine
- **Kirikiri 对话格式**：`[name]角色名\n对话文本[p]`，正则可匹配

### 8.3 新引擎的添加流程（模板）

当需要支持新引擎时，按以下步骤操作：

1. **新建 `engines/xxx_engine.py`**：继承 `EngineBase`，实现 `_default_profile()` / `detect()` / `extract_texts()` / `write_back()`
2. **新建 EngineProfile**：在 `engine_base.py` 中添加该引擎的 `XXX_PROFILE` 常量，注册到 `ENGINE_PROFILES` 字典
3. **更新 `engine_detector.py`**：在 `detect_engine_type()` 中添加检测逻辑，在 `create_engine()` 中添加实例化分支，在 `resolve_engine()` 的 manual_map 中添加 CLI 名称映射
4. **更新 `core/prompts.py`**：在 `_ENGINE_PROMPT_ADDONS` 中添加引擎专属 prompt 片段
5. **可选：更新 `core/glossary.py`**：如果引擎有结构化的角色/术语数据（如 RPG Maker 的 Actors.json），添加扫描方法
6. **新增测试**：在 `tests/test_engines.py` 中添加该引擎的检测、提取、回写测试
7. **更新文档**：README 的"支持引擎"列表、CLI 帮助的 `--engine` choices

每个新引擎预计 200-600 行代码（取决于文件格式复杂度），不需要改动任何现有引擎的代码。

---

## 9. 实施顺序与里程碑

### 阶段零：当前 Ren'Py 优化 ✅ 已完成

| 任务 | 预计工时 | 状态 |
|------|----------|------|
| chunk 失败自动拆分重试 | 0.5-1 天 | ✅ 已完成 |
| one_click_pipeline 阶段函数拆分 | 0.5 天 | ✅ 已完成 |
| tl-mode 自动清理 .rpyc | 0.5 天 | ✅ 已完成 |
| dry-run 增强 | 0.5 天 | ✅ 已完成 |

### 阶段一：引擎抽象层骨架 ✅ 已完成

| 任务 | 预计工时 | 状态 |
|------|----------|------|
| 实现 `engine_base.py` | 0.5 天 | ✅ 已完成 |
| 实现 `engine_detector.py` | 0.5 天 | ✅ 已完成 |
| 实现 `engines/renpy_engine.py` | 0.5 天 | ✅ 已完成 |
| 修改 `main.py` 添加 `--engine` | 0.5 天 | ✅ 已完成 |
| 验证 Ren'Py 回归 | 0.5 天 | ✅ 已完成（70 + 25 测试全绿） |

**里程碑 M1** ✅：`python main.py --engine auto --game-dir xxx` 自动检测 Ren'Py 并走原有路径，行为与不加 `--engine` 完全一致。

### 阶段二：CSV/JSONL 通用格式 ✅ 已完成

| 任务 | 预计工时 | 状态 |
|------|----------|------|
| 实现 `engines/csv_engine.py` | 1 天 | ✅ 已完成 |
| 实现 `generic_pipeline.py` 基本流程 | 1-1.5 天 | ✅ 已完成 |
| 适配 `file_processor/checker.py` | 0.5 天 | ✅ 已完成（protect_placeholders + check_response_item 参数化） |
| 适配 `core/prompts.py` | 0.5 天 | ✅ 已完成（引擎 addon 机制） |
| 测试 + CI | 0.5 天 | ✅ 已完成（47 引擎测试） |

**里程碑 M2** ✅：`python main.py --engine csv --game-dir texts.csv` 可翻译任意 CSV/JSONL 文件。支持断点续传、术语表、并发。

### 阶段三：RPG Maker MV/MZ ✅ 已完成

| 任务 | 预计工时 | 状态 |
|------|----------|------|
| 实现 `engines/rpgmaker_engine.py` 提取 | 1.5 天 | ✅ 已完成 |
| 实现 `engines/rpgmaker_engine.py` 回写 | 1 天 | ✅ 已完成 |
| RPG Maker prompt addon | 0.5 天 | ✅ 已完成（阶段二已实现） |
| `core/glossary.py` 新增 `scan_rpgmaker_database` | 0.5 天 | ✅ 已完成 |
| 测试 | 1 天 | ✅ 已完成（62 引擎测试） |

**里程碑 M3** ✅：`python main.py --engine auto --game-dir E:\Games\RPGMakerGame` 自动检测 RPG Maker MV/MZ 并完成翻译。

### 阶段四：文档 + 发布 ✅ 已完成

| 任务 | 状态 |
|------|------|
| README 更新：多引擎标题 + RPG Maker/CSV 用法示例 | ✅ 已完成（各阶段增量更新） |
| CHANGELOG 更新 | ✅ 已完成（各阶段增量更新） |
| .cursor_prompt 更新 | ✅ 已完成（各阶段增量更新） |
| TEST_PLAN 更新 | ✅ 已完成（各阶段增量更新） |
| start_launcher.py 新增 RPG Maker / CSV 模式 | ✅ 已完成（模式 8/9） |

**里程碑 M4** ✅：文档齐全，用户可以按文档操作完成 Ren'Py / RPG Maker / CSV 三种路径的翻译。

### 总预计工时 — 全部完成 ✅

| 阶段 | 预计 | 状态 |
|------|------|------|
| 阶段零（Ren'Py 优化） | 1.5-2 天 | ✅ 已完成 |
| 阶段一（抽象层骨架） | 2-2.5 天 | ✅ 已完成 |
| 阶段二（CSV/JSONL） | 3.5-4 天 | ✅ 已完成 |
| 阶段三（RPG Maker） | 4-5 天 | ✅ 已完成 |
| 阶段四（文档发布） | 2 天 | ✅ 已完成 |
| **总计** | **13-15.5 天** | **✅ 全部完成** |

---

## 10. 风险与避坑

### 10.1 架构风险

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| 抽象层过度设计，新引擎发现接口不适配 | 中 | 需要修改 EngineBase 接口 | TranslatableUnit 的 `metadata` 字段是万能逃生舱——引擎间的差异都可以塞进 metadata。EngineBase 的方法签名用 `**kwargs` 保留扩展空间 |
| Ren'Py 代码被改动导致回归 | 低 | 核心功能受损 | 薄包装模式 + 向后兼容可选参数 + 所有现有测试不动 + prompt baseline 测试 |
| generic_pipeline 与 Ren'Py 管线的功能差距太大 | 高 | 用户觉得 RPG Maker 翻译质量远不如 Ren'Py | 这是预期的。第一版 generic_pipeline 没有 pilot → gate → retranslate 流程，没有密度自适应，没有 Review HTML。这些可以后续逐步加入，但第一版的核心价值是"能用"而不是"完美" |

### 10.2 RPG Maker 特有风险

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| 插件指令（Code 356）中有翻译需求但被跳过 | 高 | 部分游戏文本未被提取 | 第一版文档明确说明 356 不支持，建议用户用 Translator++ 补充提取。后续可做插件白名单 |
| 连续 401 合并后翻译行数不匹配 | 中 | 回写时行数对不上 | 多的截断、少的填空。在报告中标记这些 unit 让用户校对 |
| 某些游戏的 JSON 格式非标准（如缺少 System.json） | 低 | 引擎检测失败 | 输出诊断信息 + 支持 `--engine rpgmaker` 手动指定 |
| JSON 文件编码不是 UTF-8 | 极低 | 读取失败 | MV/MZ 强制 UTF-8。VX/Ace 可能有 Shift_JIS，但那是第二版的问题 |
| 回写后 JSON 格式与原始不一致导致游戏加载异常 | 低 | 游戏崩溃 | 使用 `ensure_ascii=False` 保持非 ASCII 字符原样输出。使用紧凑格式 `separators=(",", ":")`。始终创建 `.bak` 备份 |

### 10.3 CSV 特有风险

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| 用户 CSV 的列名不在别名集合中 | 中 | 提取失败 | 错误信息中明确列出"我找到了这些列名，但没有匹配到原文列。支持的别名有 xxx" |
| CSV 中有特殊字符导致解析错误 | 低 | 部分行丢失 | 使用 `csv.DictReader` 的标准实现（处理引号转义、换行等），支持 UTF-8 BOM |
| 用户期望 CSV 输出能直接导入回原工具 | 高 | 列顺序/格式不兼容 | 第一版只输出自己格式的 CSV（id + original + translation）。后续可以做"保持原始列 + 追加翻译列"的模式 |

### 10.4 零依赖约束的挑战

| 场景 | 挑战 | 处理 |
|------|------|------|
| RPG Maker VX/Ace | 需要 `rubymarshal` | 作为可选功能，缺依赖时给 pip install 提示 |
| Unity AssetBundle | 需要 `UnityPy` | 不直接支持，通过 XUnity 导出文本间接支持 |
| Kirikiri .scn | 需要二进制解析 | 优先支持 .ks（文本格式），.scn 通过 VNTextPatch 导出 CSV 间接支持 |
| 老日系编码 | Shift_JIS / EUC-JP | 在 EngineProfile.encoding 中指定，读取时按指定编码打开 |

### 10.5 命名与约定

- 所有新增文件的 logging 使用 `[ENGINE]` / `[DETECT]` / `[RPGM]` / `[CSV]` / `[PIPELINE]` 前缀标签，与现有的 `[CHUNK]` / `[DENSITY]` / `[SKIP-CFG]` 风格一致
- 新增 CLI 参数遵循现有命名习惯：`--engine`（小写，短横线分隔），`--placeholder-regex`（如果后续需要）
- 新增函数和类的 docstring 遵循现有风格（中文注释 + 英文 docstring 混合）
- 所有新模块在文件头部有模块级 docstring，说明职责和设计决策
