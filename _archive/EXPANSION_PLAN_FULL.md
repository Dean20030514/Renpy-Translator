# 多引擎翻译工具扩展方案（历史快照，r12-r19 时期）

> **本文件已精简**。原始未删节版（60 KB / 1043 行，含完整代码示例）可通过 git 恢复：
> `git log --oneline _archive/EXPANSION_PLAN_FULL.md` 找重写本文件之前的 commit hash → `git show <hash>:_archive/EXPANSION_PLAN_FULL.md`。
>
> **当前架构与路线图**：见 [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md) + [docs/REFERENCE.md](../docs/REFERENCE.md)。

---

## 1. 当前进度（r12-r19 状态快照）

| 章节 | 内容 | 状态 |
|------|------|------|
| §1 Ren'Py 优化 | chunk 拆分重试 + pipeline 拆分 + rpyc 清理 + dry-run 增强 | ✅ Done |
| §2 引擎抽象层 | EngineProfile / TranslatableUnit / EngineBase / EngineDetector | ✅ Done |
| §3 RPG Maker | MV/MZ 事件指令 + 数据库 + System.json | ✅ Done |
| §4 CSV/JSONL | 通用格式支持（列名别名 + UTF-8 BOM + 多行） | ✅ Done |
| §5 通用管线 | 6 阶段统一翻译流程 | ✅ Done |
| §6 模块适配 | checker/prompts/glossary 引擎参数化 | ✅ Done |
| §7 测试策略 | 多引擎回归测试 | ✅ Done |
| §8 后续路线图 | RPG Maker VX/Ace、Godot、Unity 等 | 📋 已迁移至 [docs/REFERENCE.md §13](../docs/REFERENCE.md) |

---

## 2. 各章节核心决策（设计动机摘要）

### §1 Ren'Py 优化（已落地）

四项低风险高价值改进：
1. `_should_retry` 检测截断（返回条数 < 50%）→ `_translate_chunk_with_retry` 拆分（label 边界 > 空行 > 二等分）→ 分别翻译 → 合并；仅一层拆分，不递归
2. `one_click_pipeline.main()` 拆为 `_run_pilot_phase` / `_run_gate_phase` / `_run_full_translation_phase` / `_run_retranslate_phase` / `_run_final_report` 五阶段函数
3. `run_tl_pipeline` 完成后自动清理 `.rpyc/.rpymc/.rpyb`，`--no-clean-rpyc` 可禁用
4. `--dry-run --verbose` 输出每文件密度 + 翻译策略 + 密度分布直方图 + 术语预览

### §2 引擎抽象层（已落地）

**核心设计原则**：
- **浅抽象、参数化差异** — 引擎差异通过 `EngineProfile` 数据类参数化（occluded behind 数据类，而非继承多态）
- **Ren'Py 代码零改动** — 现有管线不重构，通过 `RenPyEngine` 薄包装接入
- **零依赖约束不破坏** — 核心框架全部 stdlib

**新增文件**：
- `engines/engine_base.py` — `EngineProfile` / `TranslatableUnit` / `EngineBase` ABC
- `engines/engine_detector.py` — 自动检测 + `--engine` CLI 路由
- `engines/renpy_engine.py` — Ren'Py 薄包装（委托现有三条管线）
- `engines/rpgmaker_engine.py` — RPG Maker MV/MZ 实现
- `engines/csv_engine.py` — CSV/JSONL/JSON 通用
- `engines/generic_pipeline.py` — 6 阶段通用流水线（非 Ren'Py 引擎共用）

**EngineProfile 数据类**：详见 [docs/ARCHITECTURE.md §5.1](../docs/ARCHITECTURE.md)
**TranslatableUnit 数据类**：详见 [docs/ARCHITECTURE.md §5.2](../docs/ARCHITECTURE.md)
**EngineBase ABC**：详见 [docs/ARCHITECTURE.md §5.3](../docs/ARCHITECTURE.md)

### §3 RPG Maker MV/MZ 支持（已落地）

**目录结构识别**：MV `www/data/System.json`；MZ `data/System.json`（无 `www/`）

**可翻译文本分类**：
1. **事件指令**（`Map001.json` 等地图，code 401/405 合并多行对话；code 102 选项）
2. **8 种数据库 JSON**（Actors / Classes / Skills / Items / Weapons / Armors / Enemies / States — 各取 `name` / `description` / `note` 字段）
3. **System.json**（系统术语，约 100 项）

**ID 设计**：`<file>:events[E].pages[P].list[L]` 或 `<db>:[I].name` — 全局唯一，write_back 用作精确定位 key

**RPG Maker 占位符语法**：`\V[n]` / `\N[n]` / `\P[n]` / `\C[n]` / `\I[n]` / `\G` / `\{` / `\}` / `\!` / `\.` / `\|` / `\>` / `\<` — 全部进入 `RPGMAKER_MV_PROFILE.placeholder_patterns`

**特殊难点**（未实现，rounds backlog）：
- Plugin Commands (code 356) — 第三方插件命令的参数翻译（路线图 P3）
- JS 硬编码字符串 — `js/plugins/*.js` 中的字符串（路线图 P3）

### §4 CSV/JSONL 通用格式（已落地）

**设计目标**：当某引擎无原生支持时，用任何外部工具（Translator++ / VNTextPatch / GARbro 等）导出为 CSV/JSONL，让本工具做 AI 翻译，再用原工具回灌。**一天覆盖所有引擎**。

**支持输入**：
- CSV（含 TSV，支持 UTF-8 BOM）
- JSONL（每行一个 JSON 对象）
- JSON 数组（顶层为数组的单文件）

**列名/字段名自动匹配**（按优先级）：
- 原文字段：`original` / `source` / `text` / `en` / `english` / `ja`
- 译文字段：`translation` / `target` / `trans` / `zh` / `chinese` / `cn`

**输出**：`translations_zh.csv` 或 `translations_zh.jsonl`，保留所有原列 + 加翻译列

### §5 通用翻译流水线（generic_pipeline）（已落地）

**6 阶段**：extract（提取）→ build_chunks（构建 chunk）→ concurrent translate（并发翻译）→ ResponseChecker → write_back（回写）→ post_process（可选后处理）

`EngineBase.run()` 默认走此流水线；`RenPyEngine` 覆写 `run()` 委托给现有三条管线（兼容历史）。

### §6 模块适配（已落地）

**checker 参数化**（r42 完成）：`check_response_item(item, lang_config=None)` 加 `lang_config` kwarg；调用点 `engines/generic_pipeline` + `translators/tl_mode._translate_one_tl_chunk` 透传；deferred `core.lang_config` import 保 r27 A-H-2 layering（`file_processor` 不在 module load 时 import `core`）

**prompts 参数化**：`_ENGINE_PROMPT_ADDONS` 字典按 `prompt_addon_key` 查找引擎专属提示片段（`renpy` / `rpgmaker` / `generic`）

**glossary 参数化**：`scan_rpgmaker_database` 与 `scan_game_directory`（Ren'Py character defines）独立；前者读 Actors.json 等数据库，后者扫 `.rpy` 中 `define Character(...)`

### §7 测试策略（已落地）

详见 [docs/ARCHITECTURE.md §8](../docs/ARCHITECTURE.md)（测试体系）+ [_archive/TEST_PLAN_r50.md](TEST_PLAN_r50.md)（r50 末快照）。

### §8 后续引擎路线图

已迁移至 [docs/REFERENCE.md §13](../docs/REFERENCE.md)。

---

## 3. 实施顺序与里程碑（历史回顾）

| 里程碑 | 完成轮次 |
|--------|---------|
| M1：Ren'Py 优化四项 | r12（阶段零） |
| M2：引擎抽象层骨架 + RenPyEngine | r12（阶段一） |
| M3：CSV/JSONL + 通用流水线 | r12（阶段二） |
| M4：RPG Maker MV/MZ 完整支持 | r12（阶段三） |
| M5：文档 + 发布 + GUI + PyInstaller | r12（阶段四 + GUI） |

---

## 4. 风险与避坑（设计阶段记录）

1. **EngineProfile 数据类 vs 继承多态** — 选数据类是因为引擎差异主要在数据（占位符模式 / 跳过模式 / 编码），不在行为。避免"为加引擎写大量子类"的过度抽象
2. **TranslatableUnit 的 metadata 字段** — 引擎自己塞 write_back 定位信息，通用流水线只透传不碰，让流水线对引擎差异完全无感
3. **RenPyEngine 不实现 extract_texts / write_back** — Ren'Py 有自己的专有管线（DialogueEntry / StringEntry），覆写 `run()` 委托即可。这是整个抽象层中最薄的一个类，意义在于让 Ren'Py 能插入引擎检测和 CLI 路由体系
4. **RPG Maker 没有标准 placeholder 文档** — 规范散在不同 plugin 文档；EngineProfile 只覆盖核心 13 种，自定义插件命令需用户提供 `--placeholder-regex`
5. **CSV 引擎不自动检测** — 因为 CSV 本身是通用格式，目录里有 `.csv` 不代表是游戏数据。仅通过 `--engine csv` 显式指定
