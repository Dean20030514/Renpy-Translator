# Round 47 → Round 51 详细变更（Round 51 末归档快照）

> **本文件已精简**。原始未删节版可通过 git 恢复：
> `git log --follow --oneline _archive/CHANGELOG_RECENT_r51.md` 找重写本文件之前的 commit hash → `git show <hash>:_archive/CHANGELOG_RECENT_r51.md`（或 r50/r49 旧名 — `--follow` 自动跨 rename）。
>
> **r1-r51 演进摘要**：见 [EVOLUTION.md](EVOLUTION.md)
> **r1-r45 总览表**：见 [CHANGELOG_FULL.md](CHANGELOG_FULL.md)
> **当前 build / 数字 / 推荐工作**：见 [HANDOFF.md](../HANDOFF.md)
>
> **关于历史叙述中的文件名**：本文件叙述 r47-r51 当时改动时引用的 `docs/constants.md` / `docs/quality_chain.md` / `CHANGELOG_RECENT.md` 等文件，在 round 50 末 docs 重构时已被删除合并。等价当前文档：常量 → [`docs/REFERENCE.md`](../docs/REFERENCE.md)；架构/校验链 → [`docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md)；CHANGELOG_RECENT.md → 本文件（rename 后）。historical references 保留以维持 round 当时的真实叙述。
>
> **Round 51 删 r46**：5 轮滚动 cap（保 r47-r51）。r46 详细已落 git history；恢复方式同上。r46 高亮在 [EVOLUTION.md](EVOLUTION.md) 概览表已保留。

---

## Round 47 — 5 step 综合执行 + 7 项决策（一并 push origin）

**主线**：5 commits + 1 docs；最终 push 10 commits（r46 + r47）至 origin/main；测试净 +8。

1. **r43 detail 真实推 archive**（按 round 顺序插入 `_archive/CHANGELOG_FULL.md`，CHANGELOG_RECENT 删 125 行 detail）
2. r45 + r46 audit 7 LOW gap 全补（G1 boundary × 4 含 TOCTOU regression / G2 mixed × 2 / G3 multibyte × 2）
3. **TOCTOU 升级 ACCEPTABLE doc → MITIGATED code** — `engines/csv_engine.py` 加 `import os` + `_extract_csv` `with open(...)` 后加 `os.fstat(f.fileno()).st_size` 二次校验，4 bypass vector 现 **3 ACCEPTABLE + 1 MITIGATED**（symlink/OSError fail-open/units 累积 ACCEPTABLE + TOCTOU 现 MITIGATED）
4. r47 起始三维度审计（3 并行 Explore agent；0 CRITICAL/0 HIGH/3 MEDIUM coverage 推 r48 / 2 LOW correctness cosmetic / 1 LOW security informational；TOCTOU 加固代码确认有效；**连续 8 轮 0 CRITICAL correctness**）
5. `tests/test_translation_state.py` 765 → **599** 行预防性拆分（4 个 r35 C1 + r36 H1 ProgressTracker language-aware tests byte-identical 迁出 → 新 `tests/test_progress_tracker_language.py` 215 行 / 4 tests；CI workflow 29 → **30** steps）

---

## Round 48 — 4 step 综合执行 + 8 项决策（D 方案深度优化 + 一并 push origin）

**主线**：4 commits + 1 push；测试净 +12。

1. r47 audit 4 gap close（G1.1 cap±1 边界 × 2 + G2.1 normalization-dedup × 1 + G3.1 newline-cap exact × 2 + L1 csv.Error try/except 显式 catch + L1 regression + r47 print "ALL 53"→"ALL 55" cosmetic typo fix）
2. **TOCTOU helper 抽取**到新 `core/file_safety.py::check_fstat_size`（93 行 stdlib-only + `(OSError, ValueError)` fail-open）+ **扩展 TOCTOU defense** 从 csv-only 到 csv/jsonl/json **三 readers 全 MITIGATED**（_extract_csv 重构 byte-equivalent + _extract_jsonl + _extract_json_or_jsonl 改 `read_text` → `with open` + helper + read 加 fstat 二次校验）+ 4 unit tests + 2 jsonl/json TOCTOU regression + CI workflow 30 → **31** steps
3. r48 起始三维度审计 + **首次 security CRITICAL 同轮 fix**（r47 commit 加的 `test_csv_engine_rejects_toctou_growth_attack` mock target `engines.csv_engine.os.fstat` 在 r48 Step 2 helper 抽取后 stale — fstat call 移到 `core.file_safety.os.fstat`，原 mock 不拦截，**测试 spuriously pass**！同轮 fix 改 mock target + 加注释防 future 重演 + 验证 ad-hoc mock-call counter 显示 helper fstat 现被精确拦截 1 次；同时 fix 1 MEDIUM coverage：file_safety helper 加 ValueError fail-open + 1 unit test；2 LOW informational 推 r49）
4. docs sync — CHANGELOG_RECENT 加 r48 详细 + HANDOFF rewrite r49 起点 + CLAUDE.md `.cursorrules` 同步

### Round 48 audit-tail（用户反馈触发）

用户在 docs sync push 完成后指出"多个文件超过 800 行了"。`find + wc + awk` 核查发现 `tests/test_engines.py` 1090 + `tests/test_custom_engine.py` 1020 **远超 800 软限**，而 r45-r48 多次 HANDOFF/CHANGELOG/CLAUDE 错误声称"all tests < 800 maintained" — 根因：每轮加 tests 后只看 `print("ALL N PASSED")` 验证未跑 `wc -l` 核查，HANDOFF 声称基于最近一次 split 状态未持续核查全 directory；**与 r45 audit-tail CI 覆盖 regression 同性质**（跨 commit 累积无 tracker）；同轮 fix 拆分两文件（test_engines 1090 → 537 + 新 test_csv_engine 610 / 21 tests / test_custom_engine 1020 → 497 + 新 test_sandbox_response_cap 588 / 8 tests，byte-identical 拆分），CI workflow 31 → **33** steps，**所有 .py 现真正 < 800**；2 audit-tail commits（refactor + docs amend 记录教训）。

### Round 48 audit-2/3/4 三连（用户连续 feedback 触发 docs sync drift 修复链）

- **audit-2** "深度检查 r46-r48 三轮"触发 — 3 并行 agent 找 5 项数字漂移（440→439 测试 / 29→31 文件 / 33→32 误改 / 80→93 行 / 566→565 断言）+ 0 CRITICAL/HIGH 代码问题，1 commit 修
- **audit-3** "HANDOFF 里记录了吗"触发 — 发现 audit-2 加 4 项 r49 prevention 但 HANDOFF 只 sync 1/4 + awk 缺 `&& $2!="total"` 守卫，1 commit 修
- **audit-4** "确定再没有问题了是吧"触发 — 又 5 项 drift（CI 32 实际 33 audit-2 反向漂 / HANDOFF Step 3 测试数语义 / r49 编号 / CLAUDE/.cursorrules 漏 audit-2/3/4 段 / CHANGELOG 演进摘要漏 audit-tail 后续），1 commit 修

**连续 4 次都是手动同步漂移**，**反向证明 r49 必做 4 项自动 prevention 防再发生**：
- (a) file-size check `find + wc + awk '$1>800 && $2!="total"'` 加 `.git-hooks/pre-commit`
- (b) test-count check 累加 `ALL N`
- (c) HANDOFF/CHANGELOG 数字写前 grep/wc/verify
- (d) `scripts/verify_docs_claims.py` 独立工具

---

## Round 49 — drift prevention 工具自动化（C1+C2 prelude + C3-C7 主体）

**主线**：7 commits（已全 push origin/main）；测试净 +49（439→488）；test_files +1；ci_steps +1；assertion_points +25。

### C1 + C2 prelude — 4 项 prevention 工具落地

- (a) `.git-hooks/pre-commit` 加 file-size guard（>800 行 .py 直接 block）
- (b) `scripts/verify_docs_claims.py --fast` 静态推导 4 项 canonical 数字（AST `def test_*` count + yaml step count + glob test_files + step name `(N assertions)` 解析）对照 HANDOFF.md fenced VERIFIED-CLAIMS 块；`--full` (CI 实跑 gate) 双模
- (c) prevention rule 文档化
- (d) HANDOFF.md 顶部加 fenced VERIFIED-CLAIMS 块作单一声称源（CHANGELOG/CLAUDE/.cursorrules 引用而不再独立声称，n 路 docs drift → 1 路 grep）

C2 顺手修 r17 `9fa85ee` 起 pre-existing CI bug — `tl_parser` self-test 错 import：`from translators.tl_parser import _run_self_tests` 实际函数在 `translators._tl_parser_selftest.run_self_tests`，31 轮没人发现，audit 工具用上才出土，**反向证明 r49 工具价值**。

### C3 — 关 r48 推迟 2 LOW informational

csv.Error 已在 r48 Step 1 closed verified-already + `_normalise_ui_button` Unicode NFC/NFD design choice docstring + 1 regression 端到端钉住 NFC ≠ NFD 设计契约。

### C4 + C5 — file_safety helper 推广到 23 expansion sites

- **C4** 12 core sites 跨 8 modules（`core/font_patch.py::load_font_config` / `core/translation_db.py::TranslationDB.load` / `core/config.py::_load_config_file` / `core/glossary.py` 4 callers / `pipeline/gate.py` glossary / `engines/rpgmaker_engine.py` 2 sites / `gui_dialogs.py::_load_config` / `file_processor/checker.py::load_ui_button_whitelist`；+12 expansion regression 集中到 `tests/test_file_safety.py` — 所有 mock 统一打 `core.file_safety.os.fstat`，r49+ audit 单 grep `mock.patch.*os.fstat` 即可 verify）
- **C5** 11 tools+internal sites 跨 8 modules（`tools/merge_translations_v2.py` / `tools/translation_editor.py` 3 callers / `tools/review_generator.py` / `tools/analyze_writeback_failures.py` / `engines/generic_pipeline.py` / `core/translation_utils.py::ProgressTracker._load` / `translators/_screen_patch.py` / `pipeline/stages.py` 2 sites；+11 regression 拆到 NEW `tests/test_file_safety_c5.py` 防超 800 cap；CI workflow +1 step）

**整个 user-facing JSON ingestion surface 26 sites / 12 modules 现已全 TOCTOU MITIGATED**（attack window 从 path-based stat→open 全部缩到 fd-based fstat 微秒级；r46 audit 4 ACCEPTABLE → r47 csv only MITIGATED → r48 csv 3 readers MITIGATED → **r49 末 26 sites 全 MITIGATED via 共享 helper**）。

### C6 — r49 三维度起始审计 14 commits

3 并行 Explore agent；**0 CRITICAL ✓ 连续 9 轮维持** / 2 HIGH 同轮 fix：
- 4 lightweight tests 加 `active_src` filter 过滤注释行后再 match 防 comment-residual 删 active code 但留 string literal 注释 spuriously pass
- `scripts/verify_docs_claims.py::execute_all_ci_test_steps` 用 `subprocess.run(shell=True)` 加 30 行 docstring 文档化 trust contract（CI yaml repo-local trusted via PR review）

MEDIUM/LOW 推 r50 含 1 false positive + 1 真实 defer Security MEDIUM mock target stale trap class persists for new modules outside test_file_safety*.py。

### C7 — docs sync + r49 audit-tail

CHANGELOG_RECENT 加 r49 主体 detail + 演进摘要 r49 update 涵盖完整 C1-C7 + 用户指令"详细记录仅保留最新 5 轮"删 r43 摘要 + r44 详细共 247 行 + 维护规则注释 3→5 / HANDOFF 重写为 r50 起点 + 修 "本地未 push" drift / CLAUDE+.cursorrules byte-identical 双写 / docs/constants 标注 fstat helper 用户。

**🔴 r49 C7 audit-tail 同轮 fix**：跑 `verify_docs_claims --full` 时发现 r49 C2 引入的 self-recursion bug — `--full` 模式 `execute_all_ci_test_steps` 实跑全部 CI "Run *" steps 包括"Run verify_docs_claims --full"自身 step → subprocess 内调 --full 又调 execute → Windows WinError 32 文件锁 → 失败。同轮 fix `execute_all_ci_test_steps` 加 8 行 self-skip guard `if "verify_docs_claims" in run and "--full" in run: continue` + 1 unit regression 钉契约（又一个 audit 工具用上才出土的 case，类似 C2 修的 r17 起 tl_parser bug 模式）。

**Push 前 Q5 全套验证**通过：find file-size empty + 全 27 独立 suite + meta-runner 全 PASS + verify_docs_claims --full 实跑全 36 CI steps All claims match reality（含 self-skip guard 防递归实战验证有效）。

---

## Round 50 — Zero-Debt Closure 模式确立（3 commits + C4 deep-audit-tail）

**主线**：3 commits + 1 deep-audit-tail；测试净 +11（488→499）；ci_steps +1；assertion_points +11。

### 本轮起新规则（Zero-Debt Closure）

用户指令 + written + enforced：所有 audit findings (CRITICAL/HIGH/MEDIUM/LOW) 必须**同轮 fix，no tier exemption**。修正 r41-r49 默认 defer LOW/MEDIUM 的不成文做法（"推迟下轮" policy 没有 written rule 来源 — 是 r49 C6 audit 时自创的惯例，导致 r49 留 6 项 deferred actionable items 进 r50；r48 audit-tail / audit-2/3/4 chain 是此 pattern 副作用最严重案例）。新规则下：CRITICAL/HIGH 即时 block；MEDIUM/LOW 也必须同轮 fix；不能修的归 architectural decision 显式文档化（不算 debt）。

### C1 — 关 r49 6 项 audit-deferred actionable items + 同轮 fix 2 latent r49 C4 fixture bugs

- (1a) Mock target stale trap CLASS CI guard step（grep `mock\.patch.*os\.fstat` 防 r48 trap 复发） + 1 contract test
- (1b) 8 sites TOCTOU success-path test (4 glossary + 4 c5；新 `_patch_fstat_at_cap(cap_byte)` 上下文 helper)
- **🔴 同轮 fix 2 latent r49 C4 fixture bug**：`test_glossary_actors_json_rejects_toctou_growth_attack` (r49 C4) 调 `g.scan_game_directory(...)` — 但 `scan_game_directory` 是 Ren'Py .rpy character-define scanner，**完全不读 Actors.json**！Actors.json 由 `scan_rpgmaker_database` 处理。原 test pass 是 false-positive：function early-return（无 .rpy files），mock fstat 从未触发。`test_glossary_system_json_rejects_toctou_growth_attack` 同根因。同轮 fix method name 改为 `scan_rpgmaker_database`。**r49 C6 audit Coverage MEDIUM 2 误判 "FALSE POSITIVE 已覆盖"** — agent 看 test 函数存在就判 covered，未深查测试逻辑是否真触发 mock。
- (1c) cap-1/cap-exact site-level boundary closed by 1b
- (1d) verify_docs_claims malformed claim line edge case +2 unit test
- (1e) `core/file_safety.py::check_fstat_size` docstring +Caller contract 段
- (1f) `docs/constants.md` +symlink TOCTOU defense-in-depth informational note

### C2 — r50 三维度审计 8 commits + 7 findings 全部同轮 fix

3 并行 Explore agent 审计 r49 7 commits + r50 C1：

| Tier | Correctness | Coverage | Security |
|------|-------------|----------|----------|
| CRITICAL | 0 | 0 | 0 |
| HIGH | 0 | 1 | 0 |
| MEDIUM | 0 | 1 | 1 |
| LOW | 4 | 2 | 4 |

7 findings 同轮 fix（含 4 LOW，新规则首次执行）：
- Coverage HIGH-1: malformed line 4 scenarios → 1 parameterized test 5 cases
- Security MEDIUM-1: 1f symlink CLI args audit table + threat-model assessment
- Correctness LOW-2/3: 1a regex 扩 `patch.object` form + `_CLAIM_LINE_RE` strict end-of-value 防 "419.5" truncation
- Security LOW-2/4: docstring `ok=True` 双分支 example + self-recursion guard explicit step name

4 architectural decisions 文档化（18/26 sites helper-level + 8 representative jointly pin contract / "1c closed-by-1b" claim refined / implicit-exception test 可接受 / centralized helper 不可能有 caller-specific operator divergence）。

### C3 — docs sync + 5 轮滚动删 r45

CHANGELOG_RECENT.md 演进摘要 r50 一行 + r50 详细 section + **删 r45 detail (217 lines) + r45 audit-tail (58 lines) = 275 lines deleted** (5 轮滚动 cap)；HANDOFF.md rewrite 为 r51 起点 + 修 r49 末 "待 push" drift；CLAUDE+.cursorrules byte-identical 双写本段；docs/constants.md 已含 r50 1f / C2 改动。

### C4 — deep-audit-tail（用户"深度检查 r49+r50"触发）

3 并行 Explore agent 深度审计 r49+r50 全部 10 commits + 同轮 fix 1 个 r50 C2 自身引入的 **Security MEDIUM**：1a CI grep filter `grep -v "core\.file_safety"` 过于严格，对 future maintainer 用 `from core import file_safety; patch.object(file_safety.os, "fstat", ...)` 合法形式 false-positive；filter 改为 `grep -v "file_safety"` 兼容 qualified 形式（stale mock targeting `engines.X.os.fstat` 等 caller modules 仍被 catch — 它们 line 不含 "file_safety" 字眼）+ test_verify_docs_claims.py contract test 加 assertion 钉新 filter pattern + 钉旧 pattern 已删防 future revert。其他 deep-audit findings 全部 already-fixed / informational / architectural — 无新 actionable items。

**Push 前 Q5 全套验证**通过：find file-size empty (max 710 / `file_processor/checker.py`) + 全 27 独立 suite + meta-runner 全 PASS + verify_docs_claims --full 实跑全 36 CI steps All claims match reality。

**连续 10 轮 0 CRITICAL correctness 保持**（r35 末 / r40 末 / r43 / r44 / r45 / r41-r45 累计 / r46 / r47 / r48 / r49 / **r50**）。

---

## Round 51 — Repo rename sync + 11th 0-CRITICAL streak（5 commits）

**主线**：5 commits；测试净 +8（499→507）；test_files +1；ci_steps +1；assertion_points +8。

### 本轮交付

GitHub 仓库远端已重命名 `Renpy-Translator` → `Multi-Engine-Game-Translator`（用户在 r50 末 docs consolidation 之后操作），本地目录从 `Renpy汉化（我的）` 改为 `Multi-Engine Game Translator`。Round 51 把本地 self-references + project-wide logger namespace + docs 全部同步到位，并以 r50 zero-debt closure 模式首次执行"下轮验证"，r50 7 findings + 4 architectural decisions 全部确认在 production code path 上 robust。

### A1-A6 — Track A 仓库重命名 sync（5 commits）

- **A1** `git remote set-url origin https://github.com/Dean20030514/Multi-Engine-Game-Translator.git`（无 commit；旧 URL GitHub 自动 redirect 仍 work，但 canonical URL 已是新的）
- **A2** `pyproject.toml` `name = "multi-engine-game-translator"` + Repository URL + `renpy_translate.example.json $schema` URL（commit `c26aba3`）
- **A3** README "文档" / "Documentation" table 各加 1 行历史注解链 `_archive/EVOLUTION.md`（commit `2517384`）；CONTRIBUTING.md / SECURITY.md 实测无 stale ref，按"最小改动"原则不动
- **A4** Logger namespace 17 sites `getLogger("renpy_translator")` → `"multi_engine_translator"`（16 module-level + 1 test 函数内：core × 3 + engines × 5 + translators × 7 + main.py × 1 + tests/test_csv_engine.py × 1）（commit `aae13a0`）；`logging.getLogger(NAME)` 是 stdlib 纯标识符派发，无 derived behaviour，行为零变化；6 处上游归属 `anonymousException renpy-translator (MIT, 2024)` 完整保留（resources/hooks/{extract,inject,language_switcher} + tools/{renpy_lint_fixer, rpa_unpacker, rpyc_decompiler}）
- **A5+A6** 新 `tests/test_repo_rename_consistency.py`（4 contract tests / 项目约定 top-level `def test_*`）+ CI workflow `Run repo rename consistency tests` 步（37 → 38）（commit `2e20fa9`；HANDOFF VERIFIED-CLAIMS lockstep 同步 499→503 / 34→35 / 37→38 / 625→629）

### B1-B4 — Track B r51 起始三维度审计

- **B1 retro-verify**：r50 7 findings 落点全部仍存在（grep 7 site 全 hit）；3 核心 suites 全 PASS（test_verify_docs_claims 28 + test_file_safety 21 + test_file_safety_c5 15 = 64 tests）；4 architectural decisions 仍 informational/structural 无 demoting evidence
- **B2 三并行 Explore agent**（correctness / coverage / security）audit r50 + Track A 共 9 commits：

| Tier | Correctness | Coverage | Security |
|------|-------------|----------|----------|
| CRITICAL | 0 | 0 | 0 |
| HIGH | 0 | 1 | 0 |
| MEDIUM | 0 | 2 | 0 |
| LOW | 0 | 2 | 0 |

- **B3 5 Coverage findings 同轮处理**（Round 50 zero-debt rule 第二次执行 — 4 fix + 1 architectural decision）（commit `8a288e6`）：
  - COVERAGE-MEDIUM-1: SKIP_PARTS skip logic implicit only → 加 `test_skip_parts_excludes_pycache_dir` tempdir fixture（创 `__pycache__/orphan.py` + `build/orphan.py` + 顶层 `real_orphan.py` 作 positive control，验 SKIP_PARTS-bearing loop 只 catch control）
  - COVERAGE-MEDIUM-2: `UPSTREAM_ATTRIBUTION_FILES` 无 inverse exhaustiveness → 加 `test_upstream_attribution_files_list_is_exhaustive` 全 repo grep `.py` + `.rpy` (skip SKIP_PARTS + self) 找 "anonymousException"，assert found ⊆ listed
  - COVERAGE-LOW-1: self-skip 不显式 → 加 `test_self_skip_contract_pattern_present_in_self`，钉 invariant "pattern in self ⇒ self-skip needed"
  - COVERAGE-LOW-2: CI mock-target guard regex shape 无 unit pin → 加 `test_ci_mock_target_guard_catches_known_stale_forms`，三 fragment 钉（`mock\.patch.*os\.fstat` / `patch\.object` + `fstat` / `grep -v "file_safety"`）+ 反向 strict-filter 防回归（`grep -v "core\.file_safety"` 必须 NOT 存在，r50 C4 已删）
  - COVERAGE-HIGH-1: logger 行为测试 → **architectural decision 文档化于 module docstring**：`logging.getLogger(NAME)` 是 stdlib 纯标识符派发，无 derived behaviour 超出 name equality；静态 orphan grep（`test_logger_namespace_renamed_no_orphan_callsites`）+ pyproject/HANDOFF positive name-string assertion 已完整 pin 重命名；behavioural test 要么 tautological redundant 要么测 Python stdlib，不增 signal-to-noise
- **B4 mock-target stale trap CLASS 检查**：CI grep step 本地预跑（`grep -rEn "(mock\.patch.*os\.fstat|patch\.object\s*\(\s*[a-zA-Z_.]*os\s*,\s*[\"']fstat[\"'])" tests/*.py | grep -v "file_safety"`）empty — 0 stale mock targets，r50 防御链仍有效

### C1-C4 — Track C docs sync + 5 轮滚动维护

- **C1** `git mv _archive/CHANGELOG_RECENT_r50.md → CHANGELOG_RECENT_r51.md` + 内容 rewrite：删 r46 详细 section（5 轮滚动 cap，保 r47-r51）+ 加 r51 详细 section（本段）+ header 更新（r46-r50 → r47-r51 / r50 末 → r51 末归档快照）
- **C2** `_archive/EVOLUTION.md` 加 r51 一行
- **C3** `HANDOFF.md` rewrite 为 r52 起点（VERIFIED-CLAIMS 实测 ground-truth `verify_docs_claims --fast` 后填）+ Repository URL 更新 + 推荐 r52 工作项重新排序
- **C4** `CLAUDE.md` r50 → r51 段更新（zero-debt closure 现属常态化，连续 11 轮 0 CRITICAL correctness）+ `cp CLAUDE.md .cursorrules` byte-identical

### Round 51 数字与里程碑

- 测试 499 → **507**（+4 A5 contract test + 4 B3 audit-fix tests）
- test_files 34 → **35**（+1 `tests/test_repo_rename_consistency.py`）
- ci_steps 37 → **38**（+1 `Run repo rename consistency tests`）
- assertion_points 625 → **633**（= tests_total + 126 self-test 不变）
- **连续 11 轮 0 CRITICAL correctness 保持**（r35 - r51；新增 r51）
- repo 远端 `https://github.com/Dean20030514/Multi-Engine-Game-Translator`
- 本地目录 `C:\Users\16097\Desktop\Renpy翻译\Multi-Engine Game Translator`（旧 `Renpy汉化（我的）`）

### Round 51 audit-tail（同轮 fix Security MEDIUM 自食 r50 C4 模式）

Q5 sanity gate 跑 B4 (CI grep guard 本地预跑) 时发现 r51 A5 新加的 `tests/test_repo_rename_consistency.py` 自身 docstring / 注释 / assert 错误消息字面量包含 `mock.patch.*os.fstat` / `patch.object` 两个 form pattern（line 300/301/315/317/320/322），CI grep step `| grep -v "file_safety"` 第二级 filter 不 catch（因为这些行不含 "file_safety"），**push 后 GitHub Actions Mock target consistency check 步骤会 FAIL**。同 r50 C4 模式（CI filter 自身 false positive），新规则下同轮 fix：

- `.github/workflows/test.yml` Mock target 步加第三级 filter `| grep -v "test_repo_rename_consistency"`，豁免该 documentation-only 文件（与 `file_safety` 同性质 sanctioned exception；该文件零 mock 调用、纯 contract 引用）+ 16 行注释 docstring 解释 r51 audit-tail rationale + sanctioned exception 边界
- `tests/test_repo_rename_consistency.py::test_ci_mock_target_guard_catches_known_stale_forms` 加第 4 个 fragment assertion 钉新 filter 形状（`'grep -v "test_repo_rename_consistency"' in workflow`），防 future maintainer 不慎删除第三级 filter 致 CI 再次 self-trip
- 验证：本地预跑 `grep -rEn "..." tests/*.py | grep -v "file_safety" | grep -v "test_repo_rename_consistency"` empty；测试 8/8 PASS

教训：**新加 contract test 引用 CI guard 自身 regex 形状时，必须同步检查 CI guard 是否会 self-trip**。r51 v3 plan 的 Risk #4 mock-target trap CLASS 检查只跑了 r50 既有 filter 不含新文件，未预见新文件本身会引入新的 false-positive vector。

---

## 已回滚

无（r47-r51 所有 commits 全部保留在本地 main；r47-r50 已 push origin/main，r51 commits 待用户手动 push）。
