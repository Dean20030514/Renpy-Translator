# 交接笔记（第 25 轮结束 → 第 26 轮起点）

**目标读者**：下次新对话接手这个项目的 AI / 开发者

**当前时间锚点**：第 25 轮已完成。若您在新对话里看到这份文档，意味着上次工作结束于此处。

---

## 项目当前状态（一句话）

纯 Python 零依赖多引擎游戏汉化工具，**288 个自动化测试 + tl_parser 内建 75 条自测全绿**，A-H-4 大文件拆分三大目标（direct.py / tl_mode.py / tl_parser.py）已完成，CRITICAL + Top 5 HIGH 审查项全部收敛。

---

## 第 20 ~ 25 轮成果索引

详细记录见 [CHANGELOG_RECENT.md](CHANGELOG_RECENT.md)。摘要：

| 轮 | 主题 | 测试数 |
|----|------|-------|
| 20 | CRITICAL：悬空 import × 3 + pickle RCE × 3 + ZIP Slip + 治理文档 | 266 → 268 |
| 21 | HIGH：HTTP 连接池 + ProgressTracker 双锁 + API Key subprocess env + 11 条 mock 测试 + P1 审查回刷 | 268 → 280 |
| 22 | 响应体 32 MB 硬上限 + T-C-3/T-H-2 集成测试基础 | 280 → 286 |
| 23 | direct.py 拆分 4 模块（1301 → 584） | 286 |
| 24 | tl_mode + tl_parser 拆分 7 模块（2034 → 1099） | 286 |
| 25 | 7 项剩余 HIGH/MEDIUM：A-H-1 收尾 / A-H-6 to_dict / S-H-3 key 路径校验 / PF-H-2 日志句柄 / PF-C-2 正则预编译 / T-H-1 / T-H-3 | 286 → 288 |

---

## 推荐的第 26+ 轮工作项（按性价比排序）

### 🔴 优先级 A — 收尾遗漏（~30 分钟）

**A-H-4 补**：拆分 `translators/screen.py`（877 行，超 800 行红线 77 行）

- 当前职责：screen 语句裸英文字符串识别 + chunk 装配 + 回写
- 拆分建议（3 个模块）：
  - `screen.py`（入口 + `run_screen_translate` 编排）
  - `_screen_extract.py`（文本识别 + 语法边界判断）
  - `_screen_patch.py`（chunk 装配 + 结果回写）
- 需要先确认 screen.py 的测试覆盖 —— 当前 `tests/test_all.py` 里有 12 条 screen 相关测试（J / test_screen_* 系列），足够回归保护
- 参考第 23-24 轮拆分模式（下划线前缀 + re-export）

### 🟠 优先级 B — 大重构（~2-4 小时每项，独立一轮）

**A-H-2**：消除 `core/translation_utils.py` 反向依赖 `file_processor/`
- 位置：`core/translation_utils.py:20` `from file_processor import (check_response_item, restore_placeholders)`
- 方案：把 `_restore_placeholders_in_translations` / `_filter_checked_translations` 下沉到 `file_processor/` 或把被依赖的纯函数提升到 `core/`
- 风险：中（影响 core 接口）

**A-H-3**：统一 `translators/` 与 `engines/` 两套平行概念
- 位置：整个 `translators/` + `engines/renpy_engine.py`
- 方案：让 `main.py` 的 `auto/renpy` 分支也走 `engines.resolve_engine(...).run(args)`，消除 if/else 分叉
- 风险：高（改变默认路径）

**S-H-4**：插件 subprocess 沙箱真正隔离
- 位置：`core/api_client.py::_load_custom_engine`（当前 `importlib.util.spec_from_file_location` 无隔离）
- 方案：用 subprocess + stdin/stdout JSON 协议运行插件
- 风险：高（改变插件接口）

### 🟡 优先级 C — 其他 MEDIUM（小改动，可批量处理成一轮）

从审查报告和代码注释里提取：

- **PF-H-1**：`translators/direct.py` 的 `quality_report` dict 在文件级并行时无锁保护。改：把 `quality_report.update(...)` 纳入 `_results_lock`
- **PF-H-3**：`file_processor/patcher.py:_diagnose_writeback_failure` 热路径全文件扫描。改：建反向索引
- **PF-H-4**：`core/api_client.py:RateLimiter.acquire` 持锁期间遍历 dict 清理。改：每 N 次清理一次
- **PF-M-2**：`core/translation_db.py:save()` 每次全量 JSON 序列化。改：dirty flag + 增量写
- **P-H-3 / P-H-4**：`tools/renpy_upgrade_tool.py` 和 `translators/tl_parser.py:1093`、`tools/rpa_unpacker.py:305` 遗留 `os.path` 用法统一改 `pathlib`
- **A-H-5**：`translators/` 内 `from tools.font_patch import ...` 依赖方向问题 — 考虑把 font_patch 移到 `core/`

### 🟢 优先级 D — 测试与文档补齐

- 为 A-H-2 / A-H-3 重构前先补更多集成测试（tl_mode 各功能分支、direct `_translate_file_targeted`、engines/generic_pipeline）
- `docs/` 按需加载文档更新（反映 A-H-4 拆分后的模块关系）
- CI 增加 Windows runner（目前只有 Ubuntu）

---

## 已知未修复的审查发现（非阻塞）

- **screen.py 877 行**：见优先级 A
- **A-H-2 / A-H-3 / S-H-4**：见优先级 B
- **plan 文件** `~/.claude/plans/c-users-16097-desktop-renpy-renpy-sharded-snowglobe.md`：最后一版是第 25 轮计划，可覆盖

---

## 无缝衔接建议（给下次 AI 的工作协议）

1. **读这份 HANDOFF.md + CLAUDE.md + CHANGELOG_RECENT.md** 就能重建 100% 上下文
2. **若用户说"处理下一轮建议"** → 默认从本文档"优先级 A"起推进（screen.py 拆分）
3. **若用户说"深度检查"** → 按第 25 轮后那份深度审查报告的模式做（静态 + 动态 + 逐轮复核）
4. **遵守九大原则**（见 CLAUDE.md）特别是：方案先行、隔离变量、零依赖、最小改动
5. **每轮最后必做**：
   - 全量跑 12 测试套件
   - 更新 CHANGELOG_RECENT.md（按规则压缩最老一轮到摘要）
   - 更新 CLAUDE.md 测试计数
   - `cp CLAUDE.md .cursorrules` 同步
6. **禁止直接推送 remote**（CLAUDE.md 全局规则），给用户推送指令让他自己推

---

## 关键文件路径（快速跳转）

| 类别 | 路径 |
|------|------|
| AI 全局上下文 | `CLAUDE.md` / `.cursorrules`（应字节相同） |
| 本次交接 | `HANDOFF.md`（本文件） |
| 变更日志 | `CHANGELOG_RECENT.md`（含第 23/24/25 轮详细 + 第 1-22 轮摘要） |
| 全量变更历史 | `_archive/CHANGELOG_FULL.md` |
| 入口 | `main.py` / `one_click_pipeline.py` / `gui.py` / `start_launcher.py` |
| 核心 | `core/{api_client,config,glossary,prompts,translation_db,translation_utils,lang_config,http_pool,pickle_safe}.py` |
| Ren'Py 管线 | `translators/{direct,tl_mode,tl_parser,retranslator,screen,renpy_text_utils,_direct_*,_tl_*}.py` |
| 引擎抽象层 | `engines/{engine_base,engine_detector,generic_pipeline,renpy_engine,rpgmaker_engine,csv_engine}.py` |
| 流水线 | `pipeline/{helpers,gate,stages}.py` |
| 测试 | `tests/*.py`（12 套件 + tl_parser 内建自测） |

---

**本文件由第 25 轮末尾自动生成，作为第 26 轮起点。第 26 轮完成后应更新此文件或删除。**
