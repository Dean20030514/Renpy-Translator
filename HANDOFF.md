# 交接笔记（第 28 轮结束 → 第 29 轮起点）

**目标读者**：下次新对话接手这个项目的 AI / 开发者

**当前时间锚点**：第 28 轮已完成。若您在新对话里看到这份文档，意味着上次工作结束于此处。

---

## 项目当前状态（一句话）

纯 Python 零依赖多引擎游戏汉化工具，**301 个自动化测试 + tl_parser 内建 75 条自测全绿**。`main.py` 所有引擎统一走 `engines.resolve_engine(...).run(args)` 单入口；自定义插件默认 `importlib` 快路径，`--sandbox-plugin` 可切 subprocess JSONL 沙箱。HANDOFF 优先级 A 的 4 项全部收敛完毕。

---

## 第 20 ~ 28 轮成果索引

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

---

## 推荐的第 29+ 轮工作项（按性价比排序）

**HANDOFF Priority A 四项（A-H-2 / A-H-3 / A-H-5 / S-H-4）已全部收敛。** 后续建议进入"持续优化"阶段：

### 🟠 优先级 A — 延续未做的深度重构（可选）

**A-H-3 Medium / Deep**：本轮 A-H-3 只做 Minimal（entry-point 统一），如需要把 Ren'Py 也走 generic_pipeline 六阶段（统一 TranslatableUnit 模型），还需要 16-60h 工作量：
- 位置：`engines/renpy_engine.py::extract_texts` / `write_back`（当前 raise NotImplementedError）
- 风险：direct-mode 4.01% / tl-mode 99.97% 的成功率依赖 DialogueEntry/StringEntry 的精细 block ID 追踪；迁移需真实 API key + 真实游戏 end-to-end 回归
- 建议：除非明确受益场景（比如要给 Ren'Py 加 CSV 风格的 batch-file 处理），否则保持 Minimal 即可

**S-H-4 Breaking**：当前 dual-mode 已发布，社区适应期后可考虑强制所有插件走 subprocess：
- 删除 `_load_custom_engine` importlib 路径
- 要求所有 `custom_engines/*.py` 实现 `_plugin_serve` + `__main__`
- 影响：`custom_engines/example_echo.py`（已兼容）+ 11 条 legacy 测试

### 🟢 优先级 B — 持续优化

- **test_all.py 1800+ 行**：已超 CLAUDE.md 800 行软上限，可考虑按职责拆分为 `test_api.py` / `test_glossary.py` / `test_screen.py` / `test_translation_db.py` 等
- **docs/ 内容更新**：反映第 26-28 轮的模块变化（_screen_* / core.font_patch / `--sandbox-plugin`）
- **CI 增加 Windows runner**：当前仅 Ubuntu，Windows 特定 bug（如 LF/CRLF、subprocess 行为差异）可能溜掉
- **`tools/patch_font_now.py:27` 资源路径错位**：`Path(__file__).parent / "resources" / "fonts"` 解析为 `tools/resources/fonts/`，但实际资源在项目根 `resources/fonts/`

### 🟡 优先级 C — 新功能 / 扩展

- **RPG Maker Plugin Commands / JS 硬编码支持**（CLAUDE.md 已知限制）
- **加密 RPA / RGSS 归档支持**（需要外部依赖，违反零依赖原则；建议作为 opt-in subprocess）
- **CSV/JSONL engine 完善**：generic_pipeline 的 rpgmaker 路径已存在但尚未深入验证；CSV 路径基础可用

### 🔴 监控项（理论风险，暂不修）

- Pickle 白名单 `_codecs.encode` / `copyreg._reconstructor` 链式攻击（第 26 轮已加共享常量 + 差异测试）
- HTTP 响应体 64KB 精度偏差（非功能性）
- 插件 subprocess 延迟 100-150ms 首次启动开销 + 5-15ms per-call（用户可选，不影响默认路径）

---

## 架构健康度总览（第 28 轮末）

| 维度 | 状态 |
|------|------|
| 分层违规 | ✅ 清零（A-H-1/2/3/5 全收敛；file_processor 独立基层，core 无反向 import，translators 不再依赖 tools/） |
| 大文件（>800 行）| ✅ 零（最大 direct.py 601 行） |
| 数据完整性 | ✅ TranslationDB 线程安全 + 原子写入 + 接受 line=0 |
| 反序列化安全 | ✅ 3 处 pickle 全白名单（RPA + rpyc Tier 1/2），ZIP Slip + 大小预检查 + 白名单差异测试 |
| 插件沙箱 | ✅ Dual-mode，subprocess 沙箱 opt-in 可用 |
| 测试覆盖 | ✅ 301 自动化 + tl_parser 75 自测，12 套件全绿 |
| 文档同步 | ✅ CLAUDE.md / .cursorrules / HANDOFF.md / CHANGELOG 同步，`diff CLAUDE.md .cursorrules` 无输出 |

---

## 无缝衔接建议（给下次 AI 的工作协议）

1. **读这份 HANDOFF.md + CLAUDE.md + CHANGELOG_RECENT.md** 就能重建 100% 上下文
2. **若用户说"处理下一轮建议"** → HANDOFF 优先级 A 已清空；默认从本文档"优先级 B 持续优化"起推进，或询问用户方向
3. **若用户说"深度检查"** → 按第 25-28 轮审查报告的模式做（Explore 代理交叉对比 CHANGELOG 避免重复）
4. **遵守九大原则**（见 CLAUDE.md）特别是：方案先行、隔离变量、零依赖、最小改动
5. **每轮最后必做**：
   - 全量跑 12 测试套件 + `python -m translators.tl_parser --test`
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
| 变更日志 | `CHANGELOG_RECENT.md`（含第 26/27/28 轮详细 + 第 1-25 轮摘要） |
| 全量变更历史 | `_archive/CHANGELOG_FULL.md` |
| 入口 | `main.py`（已简化到仅 engine.run() 分派）/ `one_click_pipeline.py` / `gui.py` / `start_launcher.py` |
| 核心 | `core/{api_client,config,glossary,prompts,translation_db,translation_utils,lang_config,http_pool,pickle_safe,font_patch}.py` |
| 插件沙箱 | `core/api_client._SubprocessPluginClient`（S-H-4）+ `custom_engines/example_echo.py::_plugin_serve` |
| Ren'Py 管线 | `translators/{direct,tl_mode,tl_parser,retranslator,screen,renpy_text_utils,_direct_*,_tl_*,_screen_*}.py` |
| 引擎抽象层 | `engines/{engine_base,engine_detector,generic_pipeline,renpy_engine,rpgmaker_engine,csv_engine}.py` |
| 流水线 | `pipeline/{helpers,gate,stages}.py` |
| file_processor | `file_processor/{splitter,checker,patcher,validator}.py` |
| 测试 | `tests/*.py`（12 套件 + tl_parser 内建 75 自测） |

---

**本文件由第 28 轮末尾自动生成，作为第 29 轮起点。第 29 轮完成后应更新此文件或删除。**
