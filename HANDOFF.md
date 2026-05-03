# HANDOFF — Round 50 末 → Round 51 起点

<!-- VERIFIED-CLAIMS-START -->
tests_total: 507
test_files: 35
ci_steps: 38
assertion_points: 633
<!-- VERIFIED-CLAIMS-END -->

> **上方 fenced 块是声明数字的唯一位置**。其他文档（`CLAUDE.md` / `.cursorrules` / `CHANGELOG.md` / `_archive/EVOLUTION.md` / `README.md` 等）只能引用这些数字，**不能重新声明**。`scripts/verify_docs_claims.py` 在 pre-commit hook 自动检查，drift fails the commit。
>
> 字段定义（由 `verify_docs_claims.py` 静态推导）：
>
> - `tests_total` — `tests/test_*.py` + `tests/smoke_test.py` 中所有 top-level `def test_*` / `async def test_*` 的 AST 计数
> - `test_files` — `tests/test_*.py` + `tests/smoke_test.py` 文件数
> - `ci_steps` — `.github/workflows/test.yml` 中 `jobs.test.steps` 长度
> - `assertion_points` — `tests_total + sum((N assertions))`，第二项从含 `self-test` label 的 CI step 名称解析（当前 `tl_parser` 75 + `screen` 51 = 126）
>
> `--full` 模式额外实跑全部 CI `Run *` step 作 sanity gate。

---

## 状态一句话

纯 Python 零依赖多引擎游戏汉化工具。Round 50 末确立 **zero-debt closure 模式**（所有 audit findings 同轮 fix，no tier exemption）+ **整个 user-facing JSON ingestion surface 26 sites / 12 modules 全 TOCTOU MITIGATED**（自 r49 起）+ **连续 10 轮 0 CRITICAL correctness**（r35-r50）。

## 同步状态

- 本地 `main` == `origin/main`
- pre-commit hook 已激活（`git config core.hooksPath = .git-hooks`）
- 4 件套自动 enforce：py_compile + 800 行 cap + meta-runner + `verify_docs_claims --fast`

## 架构健康度（核心维度）

| 维度 | 状态 |
|------|------|
| 大文件（> 800 行） | ✅ 全 .py < 800（pre-commit + verify_docs_claims --fast 自动 enforce） |
| 数据完整性 | ✅ TranslationDB 线程安全（RLock）+ 原子写入（os.replace）+ schema v2 partial backfill |
| 反序列化安全 | ✅ 3 处 pickle 全白名单（`core/pickle_safe.py` + rpyc Tier 1+2 + rpa_unpacker） |
| 插件沙箱 | ✅ Dual-mode（importlib 快路径 + opt-in subprocess）+ 三通道防护（stdout 50M chars + stderr 10K + stdin lifecycle） |
| 多语言完整栈 | ✅ 5 层 code-level contract（prompt + alias-read + checker + zh-tw 隔离 + generic fallback） |
| OOM 防护 | ✅ 23/23 user-facing path-stat + 26 sites / 12 modules TOCTOU MITIGATED via `core.file_safety` 共享 helper |
| Mock target stale trap | ✅ CI grep step 兜底（防 r48 trap CLASS 复发） |
| 模块分层 | ✅ deferred import 保 layering（`file_processor` 不在 module load 时 import `core`） |
| docs claim drift | ✅ 4 项 prevention 自动化（pre-commit hook + `verify_docs_claims --fast`/`--full` + `VERIFIED-CLAIMS` 单一声称源） |
| debt closure | ✅ Round 50 起新规则强制：所有 findings 同轮 fix，零 deferred |
| 累计审计 | ✅ 连续 10 轮 0 CRITICAL correctness（r35-r50） |

## 推荐的 Round 51+ 工作项

> Round 50 完成时**零 deferred actionable items**。下列均为 r51+ 候选新工作。

### 🟢 短平快（无外部资源）

1. **Round 51 起始审计** — 回溯验证 r50 7 findings fix + 4 architectural decisions 是否在 production code path 上 robust
2. **CHANGELOG 5 轮滚动维护** — 删 r46 detail，加 r51 detail（保持稳态）

### 🟠 需真实 API + 游戏（独立一轮）

3. **非中文目标语言端到端验证**（生产 ja / ko / zh-tw） — r39-r48 多层契约已锁死
4. **A-H-3 Medium**：adapter 让 Ren'Py 走 generic_pipeline 6 阶段
5. **A-H-3 Deep**：完全退役 DialogueEntry
6. **S-H-4 Breaking**：强制所有 plugins 走 subprocess
7. **RPG Maker Plugin Commands (code 356)**
8. **加密 RPA / RGSS 归档**

### ⚫ 监控项（informational watchlist，not actionable debt）

- Pickle 白名单 `_codecs.encode` / `copyreg._reconstructor` 理论链式攻击
- HTTP 响应体 64 KB 精度偏差
- TOCTOU fstat 自身 race 窗口（极小 microsecond 级）
- Symlink path-swap TOCTOU（current codebase 无 exploit vector，本地 single-user 工具 not actionable）

---

## 关键文件路径速查

| 类别 | 路径 |
|------|------|
| AI 全局上下文 | `CLAUDE.md` / `.cursorrules`（byte-identical） |
| 本次交接 | `HANDOFF.md`（本文件） |
| 用户面文档 | `README.md`（中英双语） |
| 变更日志 | `CHANGELOG.md`（极简入口）+ `_archive/EVOLUTION.md`（r1-r50） |
| 全量历史 | `_archive/CHANGELOG_FULL.md` + `_archive/CHANGELOG_RECENT_r50.md` |
| 入口 | `main.py` / `gui.py`（mixin） / `one_click_pipeline.py` |
| 引擎抽象 | `engines/{engine_base, engine_detector, generic_pipeline, renpy_engine, rpgmaker_engine, csv_engine}.py` |
| 核心 | `core/{api_client, api_plugin, config, glossary, prompts, translation_db, translation_utils, lang_config, http_pool, pickle_safe, font_patch, runtime_hook_emitter, file_safety}.py` |
| 流水线 | `pipeline/{helpers, gate, stages}.py` |
| 测试 | `tests/test_all.py` meta-runner + 33 独立 suites |
| docs | `docs/ARCHITECTURE.md`（架构 + 数据流 + 校验链 + 引擎指南 + 测试体系）+ `docs/REFERENCE.md`（常量 + 错误码 + 路线图） |
| CI | `.github/workflows/test.yml`（双 OS matrix × 3 Python = 6 jobs）+ `scripts/verify_workflow.py` |
| 开发者工具 | `.gitattributes` + `.gitignore` + `build.py --clean-only` + `.git-hooks/pre-commit` + `scripts/{install_hooks.sh, verify_workflow.py, verify_docs_claims.py}` |

---

## 下次新对话接手指南

**必读顺序**（上下文从零开始）：

1. **本文件** — 当前状态 + 推荐工作项 + 文件路径
2. **`CLAUDE.md`** — 项目身份 + 10 大开发原则 + 模块图
3. **`docs/ARCHITECTURE.md`** + **`docs/REFERENCE.md`** — 架构与常量
4. **（按需）** `_archive/EVOLUTION.md` — 历史决策

**Round 51 关键约束**：
- audit findings 必须**同轮 fix，no tier exemption**（r50 起 written + enforced）
- 数字声称只在本文件 `VERIFIED-CLAIMS` 块声明
- 修改 `CLAUDE.md` 必须同步 `.cursorrules`
- pre-commit hook 已激活，会自动 enforce file-size cap + drift check
