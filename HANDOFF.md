# 交接笔记（第 26 轮结束 → 第 27 轮起点）

**目标读者**：下次新对话接手这个项目的 AI / 开发者

**当前时间锚点**：第 26 轮已完成。若您在新对话里看到这份文档，意味着上次工作结束于此处。

---

## 项目当前状态（一句话）

纯 Python 零依赖多引擎游戏汉化工具，**293 个自动化测试 + tl_parser 内建 75 条自测全绿**，`core/translation_db.py` 已线程安全 + 原子写入 + 接受 `line=0`，RPA 大小预检查到位，RPYC Tier1/Tier2 白名单抽取共享常量，screen.py 877 → 478 拆出 `_screen_extract` / `_screen_patch` 两个子模块后全部 < 800 行。

---

## 第 20 ~ 26 轮成果索引

详细记录见 [CHANGELOG_RECENT.md](CHANGELOG_RECENT.md)。摘要：

| 轮 | 主题 | 测试数 |
|----|------|-------|
| 20 | CRITICAL：悬空 import × 3 + pickle RCE × 3 + ZIP Slip + 治理文档 | 266 → 268 |
| 21 | HIGH：HTTP 连接池 + ProgressTracker 双锁 + API Key subprocess env + 11 条 mock 测试 + P1 审查回刷 | 268 → 280 |
| 22 | 响应体 32 MB 硬上限 + T-C-3/T-H-2 集成测试基础 | 280 → 286 |
| 23 | direct.py 拆分 4 模块（1301 → 584） | 286 |
| 24 | tl_mode + tl_parser 拆分 7 模块（2034 → 1099） | 286 |
| 25 | 7 项剩余 HIGH/MEDIUM：A-H-1 收尾 / A-H-6 to_dict / S-H-3 key 路径校验 / PF-H-2 日志句柄 / PF-C-2 正则预编译 / T-H-1 / T-H-3 | 286 → 288 |
| 26 | 综合收敛包（A+B+C）：TranslationDB 三件套（RLock + 原子写 + line=0 + dirty flag） / RPA 大小预检查 / RPYC 白名单共享常量 / stages + gate 静默降级显式化 / screen.py 拆分 / quality_report 加锁 / patcher 反向索引 / RateLimiter 批量清理 / os.path → pathlib | 288 → 293 |

---

## 推荐的第 27+ 轮工作项（按性价比排序）

### 🟠 优先级 A — 大重构（每项 ~2-4 小时，独立一轮）

**A-H-2**：消除 `core/translation_utils.py` 反向依赖 `file_processor/`
- 位置：`core/translation_utils.py:20` `from file_processor import (check_response_item, restore_placeholders)`
- 方案：把 `_restore_placeholders_in_translations` / `_filter_checked_translations` 下沉到 `file_processor/` 或把被依赖的纯函数提升到 `core/`
- 风险：中（影响 core 接口）

**A-H-3**：统一 `translators/` 与 `engines/` 两套平行概念
- 位置：整个 `translators/` + `engines/renpy_engine.py`
- 方案：让 `main.py` 的 `auto/renpy` 分支也走 `engines.resolve_engine(...).run(args)`，消除 if/else 分叉
- 风险：高（改变默认路径）

**A-H-5**：`tools/font_patch` 迁移到 `core/`
- 当前：`translators/` 反向依赖 `tools/font_patch` 违反分层
- 与 A-H-2 耦合度高，建议同一轮联合做

**S-H-4**：插件 subprocess 沙箱真正隔离
- 位置：`core/api_client.py::_load_custom_engine`（当前 `importlib.util.spec_from_file_location` 无隔离）
- 方案：用 subprocess + stdin/stdout JSON 协议运行插件
- 风险：高（改变插件接口）

### 🟡 优先级 B — 监控项（Pickle 白名单链式攻击）

- 第 20 轮的 `SafeUnpickler` 已经非常严格（拒绝 `os` / `subprocess` / `builtins.eval`），但白名单里保留的 `_codecs.encode` / `copyreg._reconstructor` 在理论上允许链式构造。实际 Ren'Py 类反序列化普遍依赖这些，**不建议彻底移除**
- 如需进一步加固：引入可选的"严格模式"CLI 开关，只用于已信任归档，默认仍保持兼容

### 🟢 优先级 C — 测试与文档补齐

- 为 A-H-2 / A-H-3 重构前先补更多集成测试（tl_mode 各功能分支、direct `_translate_file_targeted`、engines/generic_pipeline）
- `docs/` 按需加载文档更新（反映 screen.py 拆分后的模块关系）
- CI 增加 Windows runner（目前只有 Ubuntu）

---

## 已知未修复的审查发现（非阻塞）

- **A-H-2 / A-H-3 / S-H-4 / A-H-5**：见优先级 A
- **Pickle `_codecs.encode` 链式攻击理论风险**：见优先级 B
- **HTTP 响应体限制 64 KB 偏差**：精度问题非功能性，不修
- **RPA 并发写冲突**：`unpack_rpa` 当前单线程，未并行化前不构成实际风险

---

## 无缝衔接建议（给下次 AI 的工作协议）

1. **读这份 HANDOFF.md + CLAUDE.md + CHANGELOG_RECENT.md** 就能重建 100% 上下文
2. **若用户说"处理下一轮建议"** → 默认从本文档"优先级 A"起推进（A-H-2 或 A-H-5 规模适中，可以作为入口）
3. **若用户说"深度检查"** → 按第 25 / 26 轮那份审查报告的模式做（静态 + 动态 + 逐轮复核 + Explore 代理交叉对比 CHANGELOG 避免重复）
4. **遵守九大原则**（见 CLAUDE.md）特别是：方案先行、隔离变量、零依赖、最小改动
5. **每轮最后必做**：
   - 全量跑 12 测试套件 + `python -m translators.tl_parser --test`
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
| 变更日志 | `CHANGELOG_RECENT.md`（含第 24/25/26 轮详细 + 第 1-23 轮摘要） |
| 全量变更历史 | `_archive/CHANGELOG_FULL.md` |
| 入口 | `main.py` / `one_click_pipeline.py` / `gui.py` / `start_launcher.py` |
| 核心 | `core/{api_client,config,glossary,prompts,translation_db,translation_utils,lang_config,http_pool,pickle_safe}.py` |
| Ren'Py 管线 | `translators/{direct,tl_mode,tl_parser,retranslator,screen,renpy_text_utils,_direct_*,_tl_*,_screen_*}.py` |
| 引擎抽象层 | `engines/{engine_base,engine_detector,generic_pipeline,renpy_engine,rpgmaker_engine,csv_engine}.py` |
| 流水线 | `pipeline/{helpers,gate,stages}.py` |
| 测试 | `tests/*.py`（12 套件 + tl_parser 内建自测） |

---

**本文件由第 26 轮末尾自动生成，作为第 27 轮起点。第 27 轮完成后应更新此文件或删除。**
