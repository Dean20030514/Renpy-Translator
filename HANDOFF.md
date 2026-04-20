# 交接笔记（第 45 轮结束 + audit-tail → 第 46 轮起点）

**目标读者**：下次新对话接手这个项目的 AI / 开发者

**当前时间锚点**：第 45 轮及末尾 **r41-r45 五轮累计深度审计 + 2 audit-tail commits** 已完成。若您在新对话里看到这份文档，意味着上次工作结束于此处。

---

## 项目当前状态（一句话）

纯 Python 零依赖多引擎游戏汉化工具，**413 个自动化测试 + tl_parser 75 + screen 51 内建自测全绿**（共 539 断言点）。第 45 轮 Auto mode 下做 11 项维护清算（10 commits）+ 末尾 user 要求深度审计 r41-r45，agent 3 维度并行审计 + 独立 grep 核查后发现 **1 CRITICAL（CI 漏 test_ui_whitelist）+ 3 MEDIUM defense-in-depth**，**全部 r45 audit-tail 2 commits 同轮 fix**。r45 总计 12 commits（`13405dc`→`bd9d6e1`）；连续 6 轮 3 维度审计 0 CRITICAL correctness；本地 main 领先 origin/main 12 commits 未推送。

---

## 第 20 ~ 45 轮成果索引

详细记录见 [CHANGELOG_RECENT.md](CHANGELOG_RECENT.md)。摘要：

| 轮 | 主题 | 测试数 |
|----|------|-------|
| 20-24 | CRITICAL 修复 / HIGH 收敛 / 大文件拆 | 266 → 286 |
| 25-30 | HIGH/MEDIUM × 7 / 综合包 A+B+C / 分层 / A-H-3 Minimal / test_all 拆 / 冷启动加固 | 286 → 302 |
| 31-35 | 运行时注入 / UI whitelist / 字体打包 / v2 schema / DB language / 多语言外循环 / side-by-side | 302 → 376 |
| 36 | 深度审计 H1 + H2 bug 修复 | 376 → 378 |
| 37 | M 级防御加固包 M1-M5 | 378 → 385 |
| 38 | "收尾包"：拆 test_editor + M2 扩 4 处 + config bool + mobile @media | 385 → 391 |
| 39 | "收尾包 Part 2"：拆 test_state + tl-mode per-lang prompt + M2 phase-2 | 391 → 396 |
| 40 | pre-existing 大文件拆 3/4 | 396 保持 |
| 41 | gui.py 拆 4/4 mixin 收官 + 3 项审计小尾巴 | 396 → 398 |
| 42 | 内部 JSON cap 收尾（声称 18/18）+ checker per-language | 398 → 405 |
| 43 | r36-r42 累计三维度审计 + 3 test 补 + plugin stdout cap | 405 → 409 |
| 44 | r43 审计 + 3 漏网 JSON cap（声称 21/21）+ plugin cap rename + 4 docs + CI Windows + PyInstaller smoke | 409 → 413 |
| 45 | r44 三维度审计 + test_file_processor 拆分 + 22/22 JSON cap（rpyc_decompiler）+ 4 docs 刷新 + `.gitattributes` + build --clean + pre-commit + CI verify | 413 保持 |
| **45 audit-tail** | r41-r45 累计深度审计（连续 6 轮 0 CRITICAL）+ **CI 漏 test_ui_whitelist 同轮 fix** + 3 MEDIUM defense-in-depth | **413 保持** |

---

## 🔴 r45 末尾深度审计发现（已全部 fix）

用户在 r45 末尾要求"深度检查 r41-r45 确保没有任何问题"。启动 3 并行 agent + 独立 grep 核查。

### CRITICAL：CI workflow 漏 `test_ui_whitelist`（fix: `3ce823f`）

**问题**：r45 Commit 1 拆 `tests/test_file_processor.py` 830→560，新建 `tests/test_ui_whitelist.py` 315 行含 7 tests。但 r45 Commit 8（`scripts/verify_workflow.py` 本地 CI verify）**没同步更新** `.github/workflows/test.yml` 加 test_ui_whitelist 步骤。结果：
- `tests/test_all.py` meta-runner 只聚合 6 focused suites（设计如此，不含独立 suites）
- CI workflow 18 个独立 suite 步骤 — **缺 `test_ui_whitelist`**
- `test_ui_whitelist.py` 还缺 `run_all()` 函数（其他 22 suites 都有）

**结果**：7 UI whitelist tests 在 CI 是 **ghost tests** — 虽然本地 `python tests/test_ui_whitelist.py` 能跑通，但 CI / pre-commit 都不跑。

**Fix**：
1. `.github/workflows/test.yml` 加 `- name: Run UI whitelist tests\n  run: python tests/test_ui_whitelist.py`（CI steps 27→28；22 独立 suite **全部 CI 覆盖**）
2. `tests/test_ui_whitelist.py` 加 `run_all() -> int` 函数（对齐其他 22 suites pattern，内部 `__main__` block 调 run_all）

### MEDIUM：3 defense-in-depth（fix: `bd9d6e1`）

1. **`build.py --clean-only` symlink defense**：Python 3.8+ `shutil.rmtree` 默认不跨 symlink，但显式 `d.is_symlink()` check 让 audit-trail intent 可见 + 零成本防御用户 `ln -s dist/ ~/Documents/` 意外场景
2. **`scripts/verify_workflow.py` PyYAML 零依赖例外披露**：docstring 加 "Note" 澄清 PyYAML 仅是 **dev-only tool 依赖**，不 ship with 任何 runtime module（core/ / translators/ / engines/ / tools/ / pipeline/ / file_processor/ / gui*.py 严格 stdlib-only，CLAUDE.md 零依赖原则仅约束 runtime 代码）
3. **`docs/quality_chain.md` `--sandbox-plugin` secure-by-default 推荐**：文档化 r42 checker 的 deferred import `from core.lang_config import resolve_translation_field` 在 legacy `importlib` plugin 模式下潜在 supply-chain 面（attacker 通过 `--custom-module` 控制的 plugin 提前 `import core.lang_config` + monkey-patch `resolve_translation_field`）。`--sandbox-plugin`（r28 S-H-4）用 subprocess 隔离 `sys.modules`，阻断 attack。明确推荐 sandbox 为默认；legacy importlib 仅用于完全受信的 first-party plugin。

### ✅ PASS（审计证实）

- **JSON loader 22/22 全覆盖** 独立 grep 核查确认（25 A-sites + 0 B-sites after r45 rpyc fix）
- **r41 mixin MRO** 正确（init 顺序 / bound method / 跨 mixin 调用）
- **r42 checker deferred import** 无 warm-up case（test 未在 fixture 提前调）
- **r43-r44 plugin cap 边界语义** 正确（恰好 cap chars + newline 合法接受）
- **所有 test fixture cleanup** 正确（`with mock.patch.object` / try/finally）
- **Shell scripts 安全**（.git-hooks + scripts 无 metacharacter / race 风险）
- **CI workflow 安全 posture**（actions 版本 current / no secrets / fail-fast:false / 新加 test_ui_whitelist 步骤）
- **文档一致性**：constants.md / quality_chain.md / roadmap.md / engine_guide.md / dataflow_translate.md 全现行

---

## 推荐的第 46+ 轮工作项

r45 总 12 commits（含 audit-tail 2 fix）清零了一波 maintenance 欠账 + 修了 r41-r45 累计 audit 的 1 CRITICAL + 3 MEDIUM。r46 剩下的都是需要外部资源或新 feature 工作。

### 🟢 最高优先（r41-r45 五轮积压的 UX 验证）

**真实桌面 user-click GUI smoke test**（需 human 或 computer-use agent）

`python gui.py` 3s subprocess smoke + PyInstaller build 33.9 MB exe 已在 r44 validate（import + init + mixin MRO + 静态分析 ≈ 95%）。剩 5% user-interactive runtime UX 需真实点击：
- 切换引擎 / 提供商 / 翻译模式 下拉
- 填 game_dir + API key → 点 "开始翻译" 验证 warning
- 点 "停止" / "清空日志"
- 工具菜单 Dry-run / 升级扫描 / 配置保存/加载

若 callback UX 异常（MRO dispatch 错位但 Python 不抱怨），回退 mixin 继承顺序或合并回单文件。预估 15 分钟 human time 或 30 分钟 computer-use agent。

### 🟡 备选短平快（~2-3h 无外部资源）

1. **Round 46 起始审计**（~3h）— 回溯验证 r45 audit-tail 2 commits（CI 修复生效 + symlink check 边界 + docs 准确性）
2. **r45 audit 的 4 optional MEDIUM gap 补齐**（~2h）：`.tsv` cap / UI whitelist 混合目录 / multibyte plugin cap 加 ja hiragana + ko hangul + emoji 测试 / alias priority over generic
3. **`tests/test_runtime_hook.py` 794 预防性拆分**（~1h，接近 800 soft limit，比 test_translation_state 765 更紧迫）
4. **`scripts/install_hooks.sh` 开发者启用**（本地一次性命令）

### 🟠 需真实 API / 游戏资源（独立一轮）

5. **非中文目标语言端到端验证**（生产 ja / ko / zh-tw） — r39+r41+r42+r43+r44 五层 + r45 docs 记录已锁死 code-level contract
6. **A-H-3 Medium**：adapter 让 Ren'Py 走 generic_pipeline 6 阶段
7. **A-H-3 Deep**：完全退役 DialogueEntry
8. **S-H-4 Breaking**：强制所有 plugins 走 subprocess，retire importlib
9. **RPG Maker Plugin Commands (code 356)**
10. **加密 RPA / RGSS 归档**

### ⚫ 架构基础设施

11. **CI workflow 实跑验证**（需 GitHub repo push access）— push r45 commits 看 `tests.yml` 现在 6 jobs × 28 steps 真实跑
12. **pre-commit hook 实际启用**：`scripts/install_hooks.sh` 已提供，开发者需主动运行

### 🔴 监控项（暂不修）

- Pickle 白名单 `_codecs.encode` / `copyreg._reconstructor` 理论链式攻击
- HTTP 响应体 64 KB 精度偏差

---

## 架构健康度总览（第 45 轮 + audit-tail 末）

| 维度 | 状态 | 最近确认 |
|------|------|---------|
| 分层违规 | ✅ 清零 | round 27 |
| 大文件（>800 行）| ✅ 源码 4/4 + 测试全 < 800（`test_runtime_hook` 794 最接近，r46 预防性拆分候选） | round 45 |
| 数据完整性 | ✅ TranslationDB 线程安全 + 原子写入 + line=0 + r37 M1 partial v2 backfill | round 37 |
| 反序列化安全 | ✅ 3 处 pickle 全白名单 + r40 `_rpyc_shared` leaf 模块 | round 40 |
| **插件沙箱** | ✅ Dual-mode + r43/r44 stdout + r30 stderr 两通道 bound + stdin lifecycle；**r45 audit-tail 文档化 `--sandbox-plugin` 为 secure-by-default 防 r42 checker deferred import 的潜在 supply-chain 面** | round 45 audit-tail |
| 运行时注入 | ✅ 全套 r31-39 能力 | round 39 |
| 多语言完整栈 | ✅ r39 prompt + r41 alias-read + r42 checker + r43-r44 zh-tw 隔离 + generic fallback 5 层契约 pinned | round 44 |
| OOM 防护 / JSON loader 覆盖 | ✅ 真实 22/22（r37-r44 21 + r45 rpyc_decompiler 补齐）；independent grep 验证 25 A-sites + 0 B-sites；plugin stdout/stderr 双通道 bound | round 45 |
| 路径信任边界 | ✅ r37 M4 CWD 白名单 + r41 OSError log；**r45 audit-tail build.py --clean-only symlink check 防御 ln -s 误用** | round 45 audit-tail |
| 潜伏 bug | ✅ 清零 | round 37 |
| 模块分层 | ✅ r40 rpyc/plugin tier + r41 GUI mixin + r42 checker deferred import 保 r27 A-H-2 | round 42 |
| 测试覆盖 | ✅ **413 自动化** + tl_parser 75 + screen 51 = 539 断言点；**23 测试文件**（22 独立 suite + `test_all.py` meta）；r45 新 `test_ui_whitelist` 有 `run_all()` 对齐 pattern | round 45 audit-tail |
| **CI / 自动化** | ✅ r44 双 OS matrix × 3 Python = 6 jobs；**r45 audit-tail 扩 CI 28 steps 含所有 22 独立 suite**（修复 CI 漏 test_ui_whitelist regression）+ `scripts/verify_workflow.py` 本地 verify | round 45 audit-tail |
| 开发者体验 | ✅ r45 `.gitattributes` LF policy + `build.py --clean-only` + `.git-hooks/pre-commit` + `scripts/install_hooks.sh` + `scripts/verify_workflow.py` + 扩 `.gitignore` 现代工具链 | round 45 |
| 生产打包验证 | ✅ r44 PyInstaller build 33.9 MB exe + python gui.py 3s smoke（95% validate）；5% user-click UX 为 r46 human follow-up | round 44 |
| 文档完整性 | ✅ **r44 + r45 + audit-tail 7 大 docs 全刷新**：constants / quality_chain（+sandbox rec）/ roadmap / engine_guide / dataflow_translate / CHANGELOG_FULL archive / verify_workflow PyYAML note | round 45 audit-tail |
| **零依赖原则合规** | ✅ runtime modules 严格 stdlib-only；**PyYAML 仅限 `scripts/verify_workflow.py` dev-only tool，已在 docstring 显式披露**（audit-tail） | round 45 audit-tail |
| **累计审计** | ✅ **连续 6 轮 0 CRITICAL**（r35 末 / r40 末 / r43 / r44 / r45 / r41-r45 累计）；r45 + r41-r45 累计共报 1 CRITICAL + 2 HIGH + 6 MEDIUM **全部同轮 fix** | round 45 audit-tail |

---

## 关键文件路径

| 类别 | 路径 |
|------|------|
| AI 全局上下文 | `CLAUDE.md` / `.cursorrules`（字节相同，r45 audit-tail note 已追加） |
| 本次交接 | `HANDOFF.md`（本文件） |
| 变更日志 | `CHANGELOG_RECENT.md`（43/44/45 详细 + audit-tail section + 1-42 摘要） |
| 全量变更历史 | `_archive/CHANGELOG_FULL.md`（r20-r45 overview table） |
| 入口 | `main.py` / `gui.py` |
| 核心 | `core/{api_client,api_plugin,config,glossary,prompts,translation_db,translation_utils,lang_config,http_pool,pickle_safe,font_patch,runtime_hook_emitter}.py`（`api_plugin._MAX_PLUGIN_RESPONSE_CHARS = 50M chars`；`translation_utils._MAX_PROGRESS_JSON_SIZE = 50 MB`） |
| 引擎抽象层 | `engines/{engine_base,engine_detector,generic_pipeline,renpy_engine,rpgmaker_engine,csv_engine}.py`（csv_engine 2 caps + rpgmaker 2 caps + generic_pipeline 1 cap） |
| 流水线 | `pipeline/{helpers,gate,stages}.py`（gate 1 cap + stages 2 caps） |
| file_processor | `file_processor/{splitter,checker,patcher,validator}.py`（checker `lang_config` kwarg + UI whitelist cap） |
| rpyc 反编译 | `tools/rpyc_decompiler.py`（r45 `_MAX_RPYC_RESULT_SIZE = 50 MB`）+ `_rpyc_tier2.py` + `_rpyc_shared.py` |
| GUI（r41 mixin） | `gui.py` 489 + `gui_handlers.py` 73 + `gui_pipeline.py` 230 + `gui_dialogs.py` 140 |
| **测试（r45 + audit-tail）** | `tests/test_all.py` meta + **独立套件 22** 个；**`test_ui_whitelist.py` 315（r45 新，audit-tail 加 `run_all()`）** |
| docs（r44 + r45 + audit-tail 全刷） | `docs/constants.md`（50 MB caps + pricing + rate limit + retry + lang_config 5 大表）+ `docs/quality_chain.md`（r44 per-language + r45 audit-tail sandbox recommendation）+ `docs/roadmap.md` + `docs/engine_guide.md` + `docs/dataflow_translate.md` |
| CI | `.github/workflows/test.yml`（r44 双 OS matrix + **r45 audit-tail 28 steps 含全 22 独立 suite**）+ `scripts/verify_workflow.py`（r45，PyYAML dev-only 依赖已披露） |
| 开发者工具 | `.gitattributes` + `.gitignore` + `build.py --clean-only`（**audit-tail +is_symlink check**）+ `.git-hooks/pre-commit` + `.git-hooks/README.md` + `scripts/install_hooks.sh` + `scripts/verify_workflow.py` |
| 生产打包 | `build.py` + `dist/多引擎游戏汉化工具.exe`（r44 build 33.9 MB，当前 dist/ 已被 `--clean-only` 清） |
| **r45 audit-tail 关键增量** | `3ce823f`：`.github/workflows/test.yml` +UI whitelist step + `tests/test_ui_whitelist.py` +`run_all()` / `bd9d6e1`：`build.py` +`is_symlink()` check + `scripts/verify_workflow.py` +PyYAML note + `docs/quality_chain.md` +sandbox recommendation |

---

## 🔍 Round 31-45 审计 / 加固 / 拆分状态

### ✅ 已修（commit 记录）

| 轮 | Fix | Commit 范围 |
|----|-----|--------|
| r36 | H1 + H2 | `39bb791` / `8ec89d2` |
| r37 | M1-M5 | `5d8e53a`..`0932a04` |
| r38 | test split + M2 × 4 + config bool + mobile @media | `daa7c1b`..`e492148` |
| r39 | test_state split + tl/retranslate per-lang prompt + M2 phase-2 × 3 | `7fc6c1b`..`58fd6ab` |
| r40 | test_engines / rpyc_decompiler / api_client splits | `dfa95e4` / `8588f57` / `b47c415` |
| r41 | gui.py 3-way mixin + M4 log + r39 alias integration + docs | `019a1f7`..`a38f6e1` |
| r42 | rpgm × 2 / 3 progress / 2 reports caps + checker per-language + docs | `9726113`..`fa818c2` |
| r43 | 3 audit-tail tests + plugin stdout cap + docs | `6a4236e` / `e4acb0e` / `924a998` |
| r44 | 3 漏网 JSON caps + plugin cap char-vs-byte + zh-tw generic fallback + docs × 3 + CI matrix + PyInstaller smoke | `1cec42d`..`c2c1fbc` |
| r45 | test_file_processor split + .gitattributes + CHANGELOG_FULL archive + build.py --clean + pre-commit + constants.md extend + engine_guide/dataflow refresh + verify_workflow + rpyc_decompiler cap + docs sync | `13405dc`..`ec542ad` |
| **r45 audit-tail** | r41-r45 累计深度审计 fix — CI 漏 test_ui_whitelist + run_all() 补 + build.py symlink + PyYAML 披露 + sandbox recommendation | `3ce823f` / `bd9d6e1` |

### 🟡 未修（r46+ 候选）

- **真实桌面 user-click GUI smoke**（r41-r45 **五轮积压**）— human 或 computer-use
- 非中文目标语言端到端验证（r39-r44 五层锁死，r45 docs 记录，需真实 API）
- A-H-3 Medium/Deep / S-H-4 Breaking
- RPG Maker plugin commands / 加密 RPA
- r45 audit 4 optional MEDIUM：`.tsv` cap / UI whitelist 混合目录 / multibyte plugin cap ja+ko+emoji / alias priority
- `tests/test_runtime_hook.py` 794 预防性拆分（接近 800 soft limit，比 test_translation_state 765 更紧迫）
- CI workflow 实跑验证（需 GitHub push access）
- pre-commit hook 本地启用（开发者运行 `scripts/install_hooks.sh`）

---

## 📋 Round 46 建议执行顺序

**推荐优先**（r41-r45 五轮积压的 UX 层）：**真实桌面 GUI user-click smoke test**

两条路径：
1. **Human 手工点击**（推荐）— 15 分钟，不 disruptive，结果最可信
2. **computer-use agent 代点击**（备选）— agent 有空 + user 不忙时尝试 `mcp__computer-use__request_access` → 截屏 → 点击验证

**r46 候选方向**（无需外部资源）：
1. **r45 audit-tail 回溯验证**（~30 分钟）— 验证 CI 现在真跑 22 独立 suite / symlink check 边界 / docs 准确性
2. **r45 4 optional MEDIUM gap**（~2h）
3. **`test_runtime_hook.py` 794 预防性拆分**（~1h，接近 800 更紧迫）
4. **Round 46 起始审计**（~3h）— 回溯验证 r45 audit-tail 2 commits

**大项（独立一轮）**：
5. **非中文目标语言端到端验证**（需 API + 游戏）
6. **A-H-3 Medium/Deep / S-H-4 Breaking**（需 API + 游戏）
7. **CI workflow 实跑验证**（需 GitHub push access）

---

## ✅ 整体质量评估（第 45 轮 + audit-tail 末）

- **5 轮欠账累计清零**：r44 闭环 14 轮 docs × 4 / CI Windows，r45 闭环 25 轮 CHANGELOG_FULL / .gitattributes / pre-commit / constants 扩 / engine_guide / dataflow_translate / build --clean，**audit-tail 闭环 CI 覆盖 regression（r45 Commit 1 / Commit 8 sync 缺失）**
- **生产打包**：r44 PyInstaller build 成功 + gui.py smoke（95%），r45 加 `verify_workflow.py` 和 `build.py --clean-only`（audit-tail 加 symlink 防御）
- **JSON loader 真实全覆盖**：r45 末 **22/22**（r37-r44 21 + r45 rpyc_decompiler；audit agent 独立 grep 验证 25 A-sites + 0 B-sites）
- **审计趋势**：**连续 6 轮（r35 末 / r40 末 / r43 / r44 / r45 / r41-r45 累计）0 CRITICAL correctness**；HIGH / MEDIUM 全部**同轮 fix**；r41-r45 累计审计首次发现 CI 覆盖 regression — 独立 grep + 跨 commit 审计依然找真实 issue
- **测试覆盖**：413 保持；23 测试文件；**所有测试 < 800 保持**；test_ui_whitelist 加 run_all() 对齐其他 22 suites
- **多语言 5 层契约 + 插件 3 通道 bound + 22/22 JSON cap + 6 大 docs + CI 28 steps + 开发者工具链** 全栈闭环
- **文档同步**：CLAUDE / `.cursorrules` / HANDOFF / CHANGELOG / CHANGELOG_FULL / docs × 5 均现行

**R31-45 + audit-tail 十五轮累积**：2 H bug + 9 M 加固包 + 2 "收尾包" + 4 大文件拆 + 1 GUI mixin + r42 JSON cap + r43-r45 累计 3 次专项审计 + r44 10 项 + r45 11 项维护清算 + **r41-r45 累计审计 1 CRITICAL CI regression fix + 3 MEDIUM defense**；多语言 5 层 + 插件 3 通道 + 22/22 JSON cap + 6 大 docs + CI 双 OS + 开发者工具链全栈闭环。主流程 steady-state；r46 候选主要是真实 UX 验证 + audit 回溯 + 非 zh 端到端。

---

## 🎯 下次新对话接手指南

**必读顺序**（上下文从零开始）：

1. **本文件（`HANDOFF.md`）** — 尤其 "📋 Round 46 建议执行顺序" + "🔴 r45 末尾深度审计发现（已全部 fix）" + "架构健康度总览"
2. **`CLAUDE.md`** — 项目身份 + 9 大开发原则 + r41-r45 + audit-tail 关键特性累积
3. **`CHANGELOG_RECENT.md`** — r43/r44/r45 详细 + r45 audit-tail section
4. **（按需）** `docs/constants.md`（阈值速查）/ `docs/quality_chain.md`（checker + sandbox）/ `docs/roadmap.md`（引擎 + 架构 TODO）/ `docs/engine_guide.md`（plugin 三通道）/ `docs/dataflow_translate.md`（per-language dispatch）

**r46 起点关键数据**：
- git HEAD：`bd9d6e1 docs(round-45-audit): MEDIUM fixes`
- 本地 main 领先 origin/main：**12 commits** 未推送
- 测试：413 自动化 + 75 tl_parser + 51 screen = 539 断言；23 测试文件；全绿
- 文件大小：**所有源码 < 800；所有测试 < 800**（`test_runtime_hook.py` 794 最接近）
- PyInstaller build：r44 验证过，`dist/` 已被 `build.py --clean-only` 清；下次 build 需重新 `python build.py`
- 外部环境：Python 3.14.3（MSYS2 ucrt64），`pyinstaller 6.19.0` + `pyyaml` 已 `pip install --break-system-packages`

**r46 建议优先级排序**：

1. 🟢 **真实桌面 GUI user-click smoke test**（human 或 computer-use 代点击）— 5 轮积压的 UX 验证
2. 🟡 **r46 起始审计 / r45 audit-tail 回溯验证**（30 分钟 — 30 验证 CI 现在 28 steps 包含 test_ui_whitelist，symlink check 边界，docs 精确性）
3. 🟡 **`test_runtime_hook.py` 794 预防性拆分**（1 小时 — 比 test_translation_state 765 更紧迫）
4. 🟡 **r45 4 optional MEDIUM gap**（2 小时 — `.tsv` cap / UI 混合目录 / multibyte ja+ko+emoji / alias priority）
5. 🟠 **非中文目标语言端到端验证**（需 API + 游戏）
6. 🟠 **A-H-3 Medium/Deep / S-H-4 Breaking**（需 API + 游戏）

**本文件由第 45 轮末尾 audit-tail 最终定稿生成，作为第 46 轮起点。**
