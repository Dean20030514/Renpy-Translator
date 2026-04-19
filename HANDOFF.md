# 交接笔记（第 30 轮结束 → 第 31 轮起点）

**目标读者**：下次新对话接手这个项目的 AI / 开发者

**当前时间锚点**：第 30 轮已完成。若您在新对话里看到这份文档，意味着上次工作结束于此处。

---

## 项目当前状态（一句话）

纯 Python 零依赖多引擎游戏汉化工具，**302 个自动化测试 + tl_parser 75 + screen 51 内建自测全绿**。HANDOFF Priority A + B 清空已维持 2 轮；第 30 轮冷启动 Explore 质量审计确认 "no material findings"，仅收敛 4 项防御性加固 + 2 项文档深度刷新。项目进入"多年可维护"的稳态。

---

## 第 20 ~ 30 轮成果索引

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
| 30 | 冷启动质量审计：subprocess stderr 10KB 上限 + 构造器泄漏兜底 + http_pool 异常收窄 + retranslator `quality_report` 死代码清理 + README/engine_guide 深度刷新 | 301 → 302 |

---

## 推荐的第 31+ 轮工作项（按性价比排序）

HANDOFF Priority A + B 清空已维持 2 轮。项目架构健康度达到"多年可维护"水平。

### 🟢 建议方向（优先级无差）

后续工作全部是可选的、无急迫性的投资：

**(1) A-H-3 Medium / Deep**：让 Ren'Py 也走 generic_pipeline 6 阶段（adapter 层或完全迁到 TranslatableUnit）。当前只做了 Minimal（入口统一），未做 Medium/Deep。需真实 API key + 真实游戏做漏翻率 / 成功率回归验证。16-60h。**不推荐 AI 独立推进**。

**(2) S-H-4 Breaking**：强制所有插件走 subprocess，retire importlib 路径。当前 dual-mode 已发布且稳定。切换只应在"我们期望用户都写兼容 sandbox 的插件"决策后做。

**(3) CI 增加 Windows runner**：`.github/workflows/test.yml` 仅 Ubuntu。工作量 ~1h 纯 YAML，但需账号有 Windows runner 权限才能验证。

**(4) 剩余 docs 深度复查**：round 29 / 30 已刷新 `TEST_PLAN` / `dataflow_pipeline` / `README` / `engine_guide`。剩余 `constants` / `error_codes` / `quality_chain` / `roadmap` / `dataflow_translate` 基本仍准确，但每轮重大改动后会慢慢积累小陈旧点。

### 🟡 新功能 / 扩展（Priority C）

- **RPG Maker Plugin Commands / JS 硬编码支持**（CLAUDE.md 已知限制）
- **加密 RPA / RGSS 归档支持**（需要外部依赖，违反零依赖原则；建议作为 opt-in subprocess）
- **CSV/JSONL engine 完善**：generic_pipeline 的 rpgmaker 路径已存在但尚未深入验证

### 🔴 监控项（理论风险，不修）

- Pickle 白名单 `_codecs.encode` / `copyreg._reconstructor` 链式攻击（round 26 已加共享常量 + 差异测试）
- HTTP 响应体 64 KB 精度偏差（非功能性）
- 插件 subprocess 延迟 ~100-150ms 首次启动开销 + 5-15ms per-call（opt-in，默认不启用）
- Glossary 单线程假设：当前架构不会从多线程访问，CLAUDE.md 可在下次大改时加一行文档

---

## 架构健康度总览（第 30 轮末）

| 维度 | 状态 | 最近确认 |
|------|------|---------|
| 分层违规 | ✅ 清零（A-H-1/2/3/5 全收敛；file_processor 独立基层，core 无反向 import，translators 不再依赖 tools/） | round 27 |
| 大文件（>800 行） | ✅ 零（源码最大 direct.py 601；测试最大 test_translators.py 604；总 ~10 个文件超过 500 行） | round 29 |
| 数据完整性 | ✅ TranslationDB 线程安全 + 原子写入 + 接受 line=0 | round 26 |
| 反序列化安全 | ✅ 3 处 pickle 全白名单（RPA + rpyc Tier 1/2），ZIP Slip + 大小预检查 + 白名单差异测试 | round 20/26 |
| 插件沙箱 | ✅ Dual-mode，subprocess 沙箱 opt-in + 10 KB stderr 上限防 OOM | round 28/30 |
| 潜伏 bug | ✅ 清零（main.py os import、patch_font_now 路径错位、retranslator quality_report 死代码 均收敛） | round 28/29/30 |
| 测试覆盖 | ✅ 302 自动化 + tl_parser 75 + screen 51 = 428 断言点；14 套件全绿 | round 30 |
| 文档同步 | ✅ CLAUDE.md / .cursorrules / HANDOFF / CHANGELOG / TEST_PLAN / dataflow_pipeline / README / engine_guide 均现行 | round 30 |

---

## 冷启动质量审计快照（round 30 Explore）

两个独立 Explore 代理分别对：
1. 全项目 core / pipeline / engines / translators / tools + docs 做 bug/security/resource/concurrency/error-handling/dead-code 六维扫描
2. `one_click_pipeline.py` + `translators/retranslator.py`（之前 29 轮从未深度审计的两个文件）做专项扫描

**Verdict**: "no material findings"。两份报告找到的所有问题都是防御性小加固或文档陈旧，没有任何可归类为高危 bug 的发现。第 30 轮收敛了其中 4 项代码小加固 + 2 项文档刷新后，剩余的全部是"可以做也可以不做"的低价值改进（例如 `smoke_test.py` 里 test 代码里的 `except Exception`、RPA/lint 子进程的轻量输入校验）。

这一审计快照本身就是项目已进入 steady-state 的佐证：10 轮系统化改造后，独立、冷启动的代码扫描找不到可归类为"必须修"的新问题。

---

## 无缝衔接建议（给下次 AI 的工作协议）

1. **读这份 HANDOFF.md + CLAUDE.md + CHANGELOG_RECENT.md** 就能重建 100% 上下文
2. **若用户说"处理下一轮建议"** → HANDOFF Priority A + B 都已清空。建议询问用户具体方向（CI / A-H-3 Medium / 新功能等），不建议 AI 独立决策推进
3. **若用户说"深度检查"** → 重复第 30 轮模式：两个独立 Explore + 交叉验证 + 按发现行动。当前状态下大概率仍然 "no material findings"，有风险沦为凭空造工作
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
| 变更日志 | `CHANGELOG_RECENT.md`（含第 28/29/30 轮详细 + 第 1-27 轮摘要） |
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

**本文件由第 30 轮末尾自动生成，作为第 31 轮起点。第 31 轮完成后应更新此文件或删除。**
