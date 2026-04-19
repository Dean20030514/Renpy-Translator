# 交接笔记（第 29 轮结束 → 第 30 轮起点）

**目标读者**：下次新对话接手这个项目的 AI / 开发者

**当前时间锚点**：第 29 轮已完成。若您在新对话里看到这份文档，意味着上次工作结束于此处。

---

## 项目当前状态（一句话）

纯 Python 零依赖多引擎游戏汉化工具，**301 个自动化测试 + tl_parser 75 + screen 51 内建自测全绿**。所有源代码文件 < 800 行软上限（`test_all.py` round 29 拆为 meta-runner + 5 聚焦文件后，历史最大的测试文件也已合规）。HANDOFF Priority A 清零第二轮完成，Priority B 的 3 项持续优化（测试拆分 / 路径 bug / 文档刷新）同步收敛。

---

## 第 20 ~ 29 轮成果索引

详细记录见 [CHANGELOG_RECENT.md](CHANGELOG_RECENT.md)。摘要：

| 轮 | 主题 | 测试数 |
|----|------|-------|
| 20 | CRITICAL：悬空 import × 3 + pickle RCE × 3 + ZIP Slip + 治理文档 | 266 → 268 |
| 21 | HIGH：HTTP 连接池 + ProgressTracker 双锁 + API Key subprocess env + 11 条 mock 测试 + P1 审查回刷 | 268 → 280 |
| 22 | 响应体 32 MB 硬上限 + T-C-3/T-H-2 集成测试基础 | 280 → 286 |
| 23 | direct.py 拆分 4 模块（1301 → 584） | 286 |
| 24 | tl_mode + tl_parser 拆分 7 模块（2034 → 1099） | 286 |
| 25 | 7 项 HIGH/MEDIUM：A-H-1 尾巴 / A-H-6 to_dict / S-H-3 key 路径校验 / PF-H-2 / PF-C-2 / T-H-1 / T-H-3 | 286 → 288 |
| 26 | 综合包（A+B+C）：TranslationDB 三件套 / RPA 大小预检查 / RPYC 白名单同步 / stages+gate 可见化 / screen.py 拆分 / quality_report 加锁 / patcher 反向索引 / RateLimiter 批量清理 / os.path → pathlib | 288 → 293 |
| 27 | 分层收尾：A-H-2（3 wrapper 下沉 file_processor）+ A-H-5（font_patch tools/ → core/）| 293 |
| 28 | A-H-3 Minimal 路由统一 + S-H-4 Dual-mode 插件沙箱（`--sandbox-plugin` opt-in）+ `main.py` 潜伏 `os` bug 修复 | 293 → 301 |
| 29 | Priority B 持续优化：`test_all.py` 2,539 行 → 5 拆分文件 + 49 行 meta-runner；`tools/patch_font_now.py:27` 路径修复；TEST_PLAN + dataflow_pipeline 文档刷新 | 301 |

---

## 推荐的第 30+ 轮工作项（按性价比排序）

HANDOFF Priority A + Priority B 全部清空。项目已达到"稳定 + 可维护 + 文档完整"状态。

### 🟢 优先级 A — 继续持续优化（可选）

**CI 增加 Windows runner**：当前 `.github/workflows/test.yml` 仅 Ubuntu；Windows 特定 bug（LF/CRLF、subprocess 行为差异、路径分隔符）可能溜掉。工作量 ~1h（纯 YAML 配置），但需账号有 Windows runner 权限。

**docs/ 深度审计**：第 29 轮只更新了 `dataflow_pipeline.md`，其他五个专题文档（`constants` / `engine_guide` / `error_codes` / `quality_chain` / `roadmap`）未逐一核对。建议在下次重大功能变更时同步复查。

### 🟠 优先级 B — 大重构（延续第 28 轮未做）

**A-H-3 Medium / Deep**：让 Ren'Py 也走 generic_pipeline 6 阶段（adapter 层或完全迁到 TranslatableUnit）。需真实 API key + 真实游戏做漏翻率 / 成功率回归验证。第 28 轮已做 A-H-3 Minimal（入口统一），Medium/Deep 不是必须。

**S-H-4 Breaking**：强制所有插件走 subprocess，retire importlib 路径。当前 dual-mode 已足够，等社区反馈再决定是否切换。

### 🟡 优先级 C — 新功能 / 扩展

- **RPG Maker Plugin Commands / JS 硬编码支持**（CLAUDE.md 已知限制）
- **加密 RPA / RGSS 归档支持**（需要外部依赖，违反零依赖原则；建议作为 opt-in subprocess）
- **CSV/JSONL engine 完善**：generic_pipeline 的 rpgmaker 路径已存在但尚未深入验证

### 🔴 监控项（理论风险，暂不修）

- Pickle 白名单 `_codecs.encode` / `copyreg._reconstructor` 链式攻击（第 26 轮已加共享常量 + 差异测试）
- HTTP 响应体 64 KB 精度偏差（非功能性）
- 插件 subprocess 延迟 100-150ms 首次启动开销 + 5-15ms per-call（用户可选，不影响默认路径）

---

## 架构健康度总览（第 29 轮末）

| 维度 | 状态 |
|------|------|
| 分层违规 | ✅ 清零（A-H-1/2/3/5 全收敛；file_processor 独立基层，core 无反向 import，translators 不再依赖 tools/） |
| 大文件（>800 行）| ✅ 零（源代码最大 direct.py 601；测试最大 test_translators.py 604；总 ~10 个文件超过 500 行） |
| 数据完整性 | ✅ TranslationDB 线程安全 + 原子写入 + 接受 line=0 |
| 反序列化安全 | ✅ 3 处 pickle 全白名单（RPA + rpyc Tier 1/2），ZIP Slip + 大小预检查 + 白名单差异测试 |
| 插件沙箱 | ✅ Dual-mode，subprocess 沙箱 opt-in 可用 |
| 测试覆盖 | ✅ 301 自动化 + tl_parser 75 + screen 51 = 427 断言点；12 套件全绿 |
| 文档同步 | ✅ CLAUDE.md / .cursorrules / HANDOFF / CHANGELOG / TEST_PLAN / dataflow_pipeline 同步 |
| `tools/patch_font_now.py` 路径 bug | ✅ 第 29 轮修复 |

---

## 无缝衔接建议（给下次 AI 的工作协议）

1. **读这份 HANDOFF.md + CLAUDE.md + CHANGELOG_RECENT.md** 就能重建 100% 上下文
2. **若用户说"处理下一轮建议"** → HANDOFF 优先级 A 已清空；Priority B 的结构性 backlog 也已清空。建议询问用户具体方向（CI Windows runner / docs 深度审计 / A-H-3 Medium / 新功能等）
3. **若用户说"深度检查"** → 按第 25-29 轮审查报告的模式做（Explore 代理交叉对比 CHANGELOG 避免重复）
4. **遵守九大原则**（见 CLAUDE.md）特别是：方案先行、隔离变量、零依赖、最小改动
5. **每轮最后必做**：
   - 全量跑 12 测试套件 + `python -m translators.tl_parser --test` + `python -m translators.screen`
   - 更新 CHANGELOG_RECENT.md（按规则压缩最老一轮到摘要）
   - 更新 CLAUDE.md 测试计数 + 模块图
   - `cp CLAUDE.md .cursorrules` 同步
6. **禁止直接推送 remote**（CLAUDE.md 全局规则）

---

## 关键文件路径（快速跳转）

| 类别 | 路径 |
|------|------|
| AI 全局上下文 | `CLAUDE.md` / `.cursorrules`（字节相同） |
| 本次交接 | `HANDOFF.md`（本文件） |
| 变更日志 | `CHANGELOG_RECENT.md`（含第 27/28/29 轮详细 + 第 1-26 轮摘要） |
| 全量变更历史 | `_archive/CHANGELOG_FULL.md` |
| 入口 | `main.py`（统一 `engine.run()` 分派）/ `one_click_pipeline.py` / `gui.py` / `start_launcher.py` |
| 核心 | `core/{api_client,config,glossary,prompts,translation_db,translation_utils,lang_config,http_pool,pickle_safe,font_patch}.py` |
| 插件沙箱 | `core/api_client._SubprocessPluginClient`（S-H-4）+ `custom_engines/example_echo.py::_plugin_serve` |
| Ren'Py 管线 | `translators/{direct,tl_mode,tl_parser,retranslator,screen,renpy_text_utils,_direct_*,_tl_*,_screen_*}.py` |
| 引擎抽象层 | `engines/{engine_base,engine_detector,generic_pipeline,renpy_engine,rpgmaker_engine,csv_engine}.py` |
| 流水线 | `pipeline/{helpers,gate,stages}.py` |
| file_processor | `file_processor/{splitter,checker,patcher,validator}.py` |
| 测试 | `tests/test_all.py`（meta-runner）+ `tests/test_{api_client,file_processor,translators,glossary_prompts_config,translation_state}.py` + 其他 8 个独立套件 |

---

**本文件由第 29 轮末尾自动生成，作为第 30 轮起点。第 30 轮完成后应更新此文件或删除。**
