# 交接笔记（第 48 轮结束 → 第 49 轮起点）

**目标读者**：下次新对话接手这个项目的 AI / 开发者

**当前时间锚点**：第 48 轮 4 step 全部完成（4 commits + Final push）。本地 main 与 origin/main 同步（r48 共 4 commits 已 push）。若您在新对话里看到这份文档，意味着上次工作结束于此处。

---

## 项目当前状态（一句话）

纯 Python 零依赖多引擎游戏汉化工具，**440 个自动化测试 + tl_parser 75 + screen 51 内建自测全绿**（共 566 断言点）。第 48 轮 Auto mode 下 4 step 综合执行（D 方案深度优化）：r47 audit 4 gap close（G1.1 cap±1 边界 + G2.1 normalization-dedup + G3.1 newline-cap exact + L1 csv.Error 显式 catch + r47 print typo fix）/ **TOCTOU helper 抽取**到 `core/file_safety.py` 并扩展 defense 到 csv+jsonl+json 三个 readers / r48 三维度审计 **首次 security CRITICAL 同轮 fix**（r47 TOCTOU mock target stale 修复 + 1 MEDIUM coverage ValueError fail-open）/ docs sync。**连续 9 轮 0 CRITICAL correctness**；CSV bypass vector 防御从 csv-only 扩展到 csv+jsonl+json **三 readers 全 MITIGATED**；CI workflow 30→**31** steps。

---

## 第 48 轮 4 Step 总览

| Step | 内容 | Commit | 测试 |
|------|------|--------|------|
| 1 | r47 audit 4 gap close + r47 print 修正 | `60cdc72` | 427→433 (+6) |
| 2 | TOCTOU helper extract + jsonl/json 扩展 + 4 unit + 2 regression | `321ab5d` | 433→**439** (+6) |
| 3 | r48 三维度审计 + **CRITICAL（mock target stale）+ MEDIUM（ValueError）同轮 fix** | `34d9707` | 439→**440** (+1) |
| 4 | docs sync（本 commit）— CHANGELOG / HANDOFF / CLAUDE | (本) | 440 |

详细见 [CHANGELOG_RECENT.md](CHANGELOG_RECENT.md) 第四十八轮 section。

---

## 第 20 ~ 48 轮成果索引

详细记录见 [CHANGELOG_RECENT.md](CHANGELOG_RECENT.md)（r44-r48 详细 + r43 摘要）+ [_archive/CHANGELOG_FULL.md](_archive/CHANGELOG_FULL.md)（r1-r45 摘要 + r43 detail）。摘要：

| 轮 | 主题 | 测试数 |
|----|------|-------|
| 20-30 | CRITICAL 修复 / HIGH 收敛 / 大文件拆 / A-H-3 Minimal / 冷启动加固 | 266 → 302 |
| 31-35 | 运行时注入 / UI whitelist / 字体打包 / v2 schema / DB language / 多语言外循环 | 302 → 376 |
| 36-39 | H bug 修复 / M 防御加固 / 收尾包 + 多语言 prompt per-language | 376 → 396 |
| 40-42 | pre-existing 大文件拆 4/4 + GUI mixin / JSON cap 收尾 / checker per-language | 396 → 405 |
| 43 | r36-r42 累计三维度审计 + 3 test 补 + plugin stdout cap | 405 → 409 |
| 44 | r43 审计 + 3 漏网 JSON cap + plugin cap rename + CI Windows + PyInstaller smoke | 409 → 413 |
| 45 | 11 项维护清算 + r41-r45 累计 audit-tail（CI 覆盖 regression 首次发现） | 413 保持 |
| 46 | r45 typo + hooks + test_runtime_hook 拆 + 4 G + r46 audit + GUI smoke + docs | 413 → 419 |
| 47 | r43 archive + 7 LOW gap + TOCTOU code + r47 audit + test_state 拆 + docs | 419 → 427 |
| **48** | **r47 audit 4 gap + TOCTOU helper extract + r48 audit (1 CRIT same-round fix) + docs** | **427 → 440** |

---

## 🟢 r48 关键里程碑

### Step 2：TOCTOU helper 抽取 + 扩展 defense 到三 readers

r47 Step 2 D3 把 csv_engine._extract_csv 加 inline `os.fstat(f.fileno())` TOCTOU defense（4 bypass vector 中 TOCTOU 升级 ACCEPTABLE doc → MITIGATED code）。但 _extract_jsonl 和 _extract_json_or_jsonl 仍用 `read_text()` 一步操作 — 实际有相同 TOCTOU 风险（read_text 内部 open + read，attacker 在 stat→open 之间扩文件可绕过 cap）。

**r48 Step 2 D 方案选最优项 — DRY + 全面加固**：

- **新建 `core/file_safety.py`**（80 行 stdlib-only）：
  - `check_fstat_size(file_obj, max_size) -> tuple[bool, int]`
  - 返回 (within_limit, observed_size)
  - fail-open on `(OSError, ValueError)` (r48 Step 3 audit-fix 加 ValueError)
  - 文档化 `<= max_size` (not `<`) 边界
- **`engines/csv_engine.py` 三 extract methods 全 MITIGATED**：
  - `_extract_csv` r47 inline → r48 helper（byte-equivalent 重构）
  - `_extract_jsonl` 加 `with open + check_fstat_size + read`
  - `_extract_json_or_jsonl` 加 `with open + check_fstat_size + read`
- **CI workflow** 30 → 31 steps（+ Run file safety tests）
- **测试** 433 → 439（+6 = 4 file_safety unit + 2 jsonl/json regression）

CSV bypass vector 安全态势：
- r47 末: 3 ACCEPTABLE + 1 MITIGATED（仅 csv MITIGATED）
- **r48 末: 3 ACCEPTABLE + 1 MITIGATED（扩展到 csv + jsonl + json 三 readers 全 MITIGATED）**

### Step 3：r48 audit 首次 security CRITICAL 同轮 fix

r48 起始三维度审计找到 **真实 issue**：

- **CRITICAL Security**: r47 commit `0341c08` 的 `test_csv_engine_rejects_toctou_growth_attack` mock target `engines.csv_engine.os.fstat` 在 r48 Step 2 helper 抽取后失效 — 实际 fstat call 移到 `core.file_safety.os.fstat`，原 mock 不拦截真实 syscall，**测试 spuriously pass**！
  - **同轮 fix**: 改 mock target 为 `core.file_safety.os.fstat` + 加注释防 future refactoring 重演
  - **验证**: ad-hoc mock-call counter 显示 helper 的 fstat 现被精确拦截 1 次
- **MEDIUM Coverage + LOW Correctness**（同根因）：file_safety helper 的 fileno() 可能抛 ValueError（io.StringIO/BytesIO），原 except OSError 不 cover
  - **同轮 fix**: `except OSError` → `except (OSError, ValueError)` + docstring rationale + 1 unit test
- 2 个 LOW informational 推 r49

**审计连续性**：
- 连续 9 轮 0 CRITICAL **correctness**（r35 末 / r40 末 / r43 / r44 / r45 / r41-r45 累计 / r46 / r47 / **r48**）
- r48 首次 security CRITICAL — 但是 test-mock-only 失效，不是真实代码 bug；同轮 fix
- 体现"自审价值"：审计跨 commit 的 refactoring 影响时找出真实 issue（同 r45 audit-tail 模式）

### Step 1：r47 audit gap 全闭合 + print 修正

r47 audit 推迟的 4 gap + r47 自身的 print typo 一并修：
- G1.1 cap±1 boundary 完整 pin `>` 操作符 3 件套
- G2.1 normalization-dedup 验证 `_normalise_ui_button`（lower + strip + whitespace-collapse）+ frozenset union 自然 dedup
- G3.1 newline-cap exact boundary（cap-1+\n / cap exact+\n 都 NOT trigger）
- L1 csv.Error explicit catch + regression test（operator-facing log "CSV 解析错误" vs generic "解析失败"）
- r47 print "ALL 53"→"ALL 55" cosmetic fix + 注释说明

---

## 推荐的第 49+ 轮工作项

r48 4 step 闭合了 r47 留下的所有欠账（4 audit gap + audit）+ 推进了 TOCTOU defense（helper 抽取 + 扩展到 jsonl/json）+ 同轮 fix r48 audit 1 CRITICAL + 1 MEDIUM。剩下都是 r49+ 候选。

### 🟢 短平快（无外部资源）

1. **r48 audit 2 LOW informational 处理**（推迟自 r48 Step 3，~30 min）：
   - Coverage L1: Unicode NFC/NFD normalization in `_normalise_ui_button` — 设计选择文档化（已 ASCII-dominant；可选加 doc note）
   - Security L1: csv.Error explicit catch informational — 不影响功能，可选记录
2. **r49 候选扩展（1）**：把 `file_safety.check_fstat_size` helper 应用到其他 22+ user-facing JSON loaders（~3-4h）
   - rpgmaker_engine 2 处 / generic_pipeline / pipeline/stages 2 处 / core/font_patch / core/translation_db / core/glossary / tools/translation_editor / 等
   - 一致性升级 — 全面 TOCTOU defense
3. **r49 起始审计**（~3h）— 回溯验证 r48 4 commits（重点 Step 2 helper 抽取 + Step 3 audit-fix 是否再次引入 mock 漂移）

### 🟠 需真实 API / 游戏资源（独立一轮）

4. **非中文目标语言端到端验证**（生产 ja / ko / zh-tw）— r39-r48 多层契约已锁死
5. **A-H-3 Medium**：adapter 让 Ren'Py 走 generic_pipeline 6 阶段
6. **A-H-3 Deep**：完全退役 DialogueEntry
7. **S-H-4 Breaking**：强制所有 plugins 走 subprocess
8. **RPG Maker Plugin Commands (code 356)**
9. **加密 RPA / RGSS 归档**

### ⚫ 架构基础设施

10. **CI workflow 实跑验证**（已 push 至 origin，r49 接手时直接看 GitHub Actions 6 jobs × 31 steps 真实运行）
11. **pre-commit hook 实际启用**：r46 Step 2 已在本机启用，其他开发者需主动运行 `scripts/install_hooks.sh`

### 🔴 监控项（暂不修）

- Pickle 白名单 `_codecs.encode` / `copyreg._reconstructor` 理论链式攻击
- HTTP 响应体 64 KB 精度偏差
- TOCTOU fstat 自身 race 窗口（极小，r47-r48 已大幅缩小）

---

## 架构健康度总览（第 48 轮末）

| 维度 | 状态 | 最近确认 |
|------|------|---------|
| 分层违规 | ✅ 清零 | round 27 |
| 大文件（>800 行） | ✅ 源码 4/4 + 测试全 < 800（最大 `test_runtime_hook.py` 589） | round 47 |
| 数据完整性 | ✅ TranslationDB 线程安全 + 原子写入 + line=0 + r37 M1 partial v2 backfill | round 37 |
| 反序列化安全 | ✅ 3 处 pickle 全白名单 + r40 `_rpyc_shared` leaf 模块 | round 40 |
| 插件沙箱 | ✅ Dual-mode + r43-r44 stdout chars cap + r30 stderr 10KB cap + stdin lifecycle | round 45 audit-tail |
| 运行时注入 | ✅ 全套 r31-39 能力 | round 39 |
| 多语言完整栈 | ✅ r39 prompt + r41 alias-read + r42 checker + r43-r44 zh-tw 隔离 + generic fallback **5 层契约** + r46 G4 multi-alias + r47 G3 multibyte multi-script | round 47 |
| OOM 防护 / JSON loader 覆盖 | ✅ **23/23**（r37-r44 21 + r45 rpyc + r46 csv_engine 真实加固） | round 46 |
| **CSV bypass vector 安全态势** | ✅ **3 ACCEPTABLE + 1 MITIGATED 扩展到 3 readers**（r47 仅 csv，**r48 加 jsonl + json 全 MITIGATED via 共享 helper**） | round 48 |
| 路径信任边界 | ✅ r37 M4 CWD 白名单 + r41 OSError log + r45 build.py symlink check | round 45 |
| 潜伏 bug | ✅ 清零 | round 37 |
| 模块分层 | ✅ r40 rpyc/plugin tier + r41 GUI mixin + r42 checker deferred import 保 r27 A-H-2 + **r48 file_safety 新 core 模块** | round 48 |
| 测试覆盖 | ✅ **440 自动化** + tl_parser 75 + screen 51 = 566 断言点；**27 测试文件**（25 独立 suite + `test_all.py` meta；r48 新 `test_file_safety.py`） | round 48 |
| CI / 自动化 | ✅ 双 OS matrix × 3 Python = 6 jobs；**31 steps 含全 25 独立 suite**（r48 +1 file_safety step） | round 48 |
| 开发者体验 | ✅ r45 `.gitattributes` LF / `build.py --clean-only` / `.git-hooks/pre-commit` / `scripts/install_hooks.sh` / `verify_workflow.py`；hook 持续激活 | round 46 |
| 生产打包验证 | ✅ r44 PyInstaller build 33.9 MB exe；r46 Step 6 GUI smoke via computer-use 闭合 5 轮积压 UX 缺口 | round 46 |
| 文档完整性 | ✅ r44-r45-r46-r47-r48 大 docs 全刷新；CHANGELOG_RECENT 加 r48 详细 + 演进摘要追加 r48 | round 48 |
| 零依赖原则合规 | ✅ runtime modules 严格 stdlib-only；新 `core/file_safety.py` 仅 import os | round 48 |
| **累计审计** | ✅ **连续 9 轮 0 CRITICAL correctness**；r48 首次 security CRITICAL（test-mock-only，同轮 fix）；HIGH / MEDIUM 全部**同轮 fix 或推下轮** | **round 48** |

---

## 关键文件路径

| 类别 | 路径 |
|------|------|
| AI 全局上下文 | `CLAUDE.md` / `.cursorrules`（字节相同，r48 段已追加） |
| 本次交接 | `HANDOFF.md`（本文件） |
| 变更日志 | `CHANGELOG_RECENT.md`（r44/r45/r45-tail/r46/r47/r48 详细 + r43 摘要 + 演进摘要 r1-r48） |
| 全量变更历史 | `_archive/CHANGELOG_FULL.md`（r1-r45 摘要 + r43 detail） |
| 入口 | `main.py` / `gui.py`（r41 mixin） / `one_click_pipeline.py` |
| 核心 | `core/{api_client,api_plugin,config,glossary,prompts,translation_db,translation_utils,lang_config,http_pool,pickle_safe,font_patch,runtime_hook_emitter,**file_safety**}.py`（**r48 新 file_safety**） |
| 引擎抽象层 | `engines/{engine_base,engine_detector,generic_pipeline,renpy_engine,rpgmaker_engine,csv_engine}.py`（**r48 csv_engine 三 extract methods 全用 file_safety helper**） |
| 流水线 | `pipeline/{helpers,gate,stages}.py` |
| file_processor | `file_processor/{splitter,checker,patcher,validator}.py` |
| rpyc 反编译 | `tools/rpyc_decompiler.py` + `_rpyc_tier2.py` + `_rpyc_shared.py` |
| GUI（r41 mixin） | `gui.py` 489 + `gui_handlers.py` 73 + `gui_pipeline.py` 230 + `gui_dialogs.py` 140 |
| **测试（r48 末）** | `tests/test_all.py` meta-runner + **25 独立 suites**；**新 `test_file_safety.py` 5 tests**（r48 Step 2 + audit-fix） |
| docs（r44-r48 全刷） | `docs/constants.md` / `docs/quality_chain.md` / `docs/roadmap.md` / `docs/engine_guide.md` / `docs/dataflow_translate.md` |
| CI | `.github/workflows/test.yml`（双 OS matrix + **31 steps 含 25 独立 suite**）+ `scripts/verify_workflow.py` |
| 开发者工具 | `.gitattributes` + `.gitignore` + `build.py --clean-only` + `.git-hooks/pre-commit` + `scripts/install_hooks.sh` + `scripts/verify_workflow.py` |
| **r48 关键增量** | Step 1 audit-gap: `60cdc72` / Step 2 helper: `321ab5d` / Step 3 audit-fix (CRIT+MED): `34d9707` / Step 4 docs: 本 commit |

---

## 🔍 Round 48 commits 时间序

```
60cdc72 fix(round-48): close r47 audit 3 MEDIUM optional + 1 LOW informational gaps
        (Step 1 - 6 tests + L1 try/except + r47 print typo fix)
321ab5d feat(round-48): extract TOCTOU helper to core/file_safety + extend to jsonl/json loaders
        (Step 2 - new core/file_safety.py + csv_engine 3 methods + 4 unit + 2 regression)
34d9707 fix(round-48-audit): close 1 CRITICAL mock-target stale + 1 MEDIUM ValueError fail-open
        (Step 3 - r48 audit fixes; CRITICAL = r47 mock target post-r48 helper extract,
         MEDIUM = file_safety ValueError; +1 ValueError unit test)
{HEAD}  docs(round-48): sync CHANGELOG / HANDOFF / CLAUDE / .cursorrules
        (Step 4 - this commit)
```

---

## ✅ 整体质量评估（第 48 轮末）

- **r47 留下欠账清零**：r47 audit 4 gap + audit；r48 自审找到 1 CRITICAL（test-mock）+ 1 MEDIUM 同轮 fix
- **TOCTOU defense 全面化**：从 r47 末"仅 csv MITIGATED"扩展到 r48 末"csv + jsonl + json 三 readers 全 MITIGATED via 共享 helper"
- **新模块 `core/file_safety.py`**：80 行 stdlib-only helper，DRY + 易测试 + 可扩展（r49 候选: 应用到其他 22+ user-facing JSON loaders）
- **审计趋势**：**连续 9 轮 0 CRITICAL correctness**；r48 首次 security CRITICAL — 但是 test-mock-only 失效，体现"跨 commit refactoring audit"价值
- **测试覆盖**：440（+13 net）；27 测试文件（25 独立 suite + meta + 新 file_safety + 之前的 v2_schema r46 / progress_tracker_language r47）
- **多语言 5 层契约 + 插件 3 通道 bound + 23/23 JSON cap + TOCTOU 全 readers MITIGATED + 7 大 docs + CI 31 steps + 开发者工具链** 全栈闭环

**R31-48 累积**：2 H bug + 9 M 加固包 + 2 "收尾包" + 4 大文件拆 + 1 GUI mixin + r42 JSON cap + r43-r48 累计 6 次专项审计 + r44 10 项 + r45 11 项 + r46 7 step + r47 5 step + **r48 4 step + helper 抽取**；多语言 5 层 + 插件 3 通道 + 23/23 JSON cap + TOCTOU 3 readers MITIGATED + 7 大 docs + CI 双 OS + GUI 真实 UX + 开发者工具链全栈闭环。主流程 steady-state；**r49 候选主要是 helper 应用到其他 loaders + 非 zh 端到端**。

---

## 🎯 下次新对话接手指南

**必读顺序**（上下文从零开始）：

1. **本文件（`HANDOFF.md`）** — 尤其 "推荐的第 49+ 轮工作项" + "🟢 r48 关键里程碑" + "架构健康度总览"
2. **`CLAUDE.md`** — 项目身份 + 9 大开发原则 + r41-r48 关键特性累积
3. **`CHANGELOG_RECENT.md`** — r44/r45/r45-audit-tail/r46/r47/r48 详细 + 演进摘要 r1-r48
4. **（按需）** `docs/constants.md` / `docs/quality_chain.md` / `docs/roadmap.md` / `docs/engine_guide.md` / `docs/dataflow_translate.md`

**r49 起点关键数据**：
- git HEAD：（Step 4 commit hash 待生成）
- 本地 main vs origin：r48 共 4 commits **已 push 至 origin/main**（r48 Final step）
- 测试：**440 自动化 + 75 tl_parser + 51 screen = 566 断言**；**27 测试文件**；全绿
- 文件大小：所有源码 / 测试 < 800（最大 `test_runtime_hook.py` 589）
- pre-commit hook：本机已启用（每 commit 自动跑 py_compile + meta-runner ~1s）
- PyInstaller build：r44 验证过；当前 dist/ 已被 `--clean-only` 清；下次 build 需 `python build.py`
- GUI runtime UX：r46 Step 6 端到端验证通过（仍 valid）
- CSV bypass vector：3 ACCEPTABLE + 1 MITIGATED（r47 csv-only → **r48 扩展到 csv+jsonl+json 三 readers 全 MITIGATED**）
- **新 helper `core/file_safety.py`**：80 行 stdlib-only，可扩展应用到其他 user-facing JSON loaders

**r49 建议优先级排序**：

1. 🟢 **r48 audit 2 LOW informational 处理**（~30 min）— Unicode normalization design doc + csv.Error informational
2. 🟢 **file_safety helper 应用到其他 22+ user-facing JSON loaders**（~3-4h）— 一致性升级 TOCTOU defense
3. 🟡 **r49 起始审计**（~3h）— 回溯验证 r48 4 commits（重点 Step 2 helper 抽取 + Step 3 audit-fix 影响范围）
4. 🟠 **非中文目标语言端到端验证**（需 API + 游戏）— 生产验证 5 层契约
5. 🟠 **A-H-3 Medium / Deep / S-H-4 Breaking**（需 API + 游戏）
6. ⚫ **CI workflow 实跑验证**（已 push 至 origin，可直接看 GitHub Actions 6 jobs × 31 steps 真实运行）

**本文件由第 48 轮末最终定稿生成，作为第 49 轮起点。**
