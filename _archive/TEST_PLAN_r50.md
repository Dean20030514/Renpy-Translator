# 测试方案（Round 50 末归档快照）

> **本文件已精简**。原始未删节版（39 KB / 600 行，含每个 test 函数的逐项描述、"五、待补充测试用例（TODO）"过时段、详细触发条件 fixture 描述）可通过 git 恢复：
> `git log --oneline _archive/TEST_PLAN_r50.md` 找重写本文件之前的 commit hash → `git show <hash>:_archive/TEST_PLAN_r50.md`。
>
> **当前测试体系**：见 [docs/ARCHITECTURE.md §8](../docs/ARCHITECTURE.md)
> **当前测试数 / CI 步骤 / 断言点**：见 [HANDOFF.md](../HANDOFF.md) 顶部 `VERIFIED-CLAIMS` 块（**单一声称源**）
>
> **核心理念**：测试代码本身就是规范。逐个 `def test_*` 描述会 drift；要查"某 test 实际验证什么"请直接读 `tests/test_*.py`。

---

## 一、测试体系总览（r50 末）

### 测试文件结构

| 类别 | 文件 | 覆盖范围 | 需 API |
|------|------|----------|--------|
| **Meta-runner** | `tests/test_all.py` | 调用下方 6 focused suites 的 `run_all()`，打印总计 | 否 |
| **Focused suites**（meta 聚合） | `test_api_client.py` | core.api_client（APIConfig / UsageStats / RateLimiter / JSON 解析 / 定价 / HTTP / 连接池 / API Key 隔离） | 否 |
| | `test_file_processor.py` | splitter / checker / patcher / validator | 否 |
| | `test_translators.py` | direct chunk / tl_parser / retranslator / screen / pipeline 冒烟 | 否 |
| | `test_glossary_prompts_config.py` | glossary（基础 / dedup / 线程安全 / Ren'Py 扫描）/ locked_terms / prompts / config / lang_config | 否 |
| | `test_translation_state.py` | ProgressTracker / TranslationDB / dedup / StringEntry fallback / progress bar / review HTML | 否 |
| | `test_runtime_hook.py` | runtime hook emit + filter（v1 schema） | 否 |
| **引擎独立 suite** | `test_engines.py` | EngineProfile / TranslatableUnit / EngineDetector / RenPyEngine / EngineBase / generic_pipeline / checker 参数化 / prompts addon | 否 |
| | `test_engines_rpgmaker.py` | RPGMakerMVEngine + glossary RPG Maker | 否 |
| | `test_csv_engine.py` | CSV / JSONL / JSON 三 readers + TOCTOU 防御 | 否 |
| **运行时注入** | `test_runtime_hook_filter.py` | 运行时 hook UI 白名单 filter | 否 |
| | `test_runtime_hook_v2_schema.py` | v2 envelope schema | 否 |
| **多语言** | `test_progress_tracker_language.py` | language-aware ProgressTracker（r35 C1 + r36 H1 byte-identical 迁出） | 否 |
| | `test_translation_db_language.py` | TranslationDB schema v2 language 字段 | 否 |
| | `test_multilang_run.py` | `--target-lang zh,ja,zh-tw` 外层语言循环 | 否 |
| | `test_override_categories.py` | `_OVERRIDE_CATEGORIES` 分派表 | 否 |
| **HTML 校对** | `test_translation_editor.py` | 导出 / 提取 / 导入 / 转义（v1） | 否 |
| | `test_translation_editor_v2.py` | v2 envelope 编辑（11 测试 byte-identical 迁移） | 否 |
| | `test_merge_translations_v2.py` | v2 多语言合并工具 | 否 |
| **插件** | `test_custom_engine.py` | 加载 / 配置 / 调用 | 否 |
| | `test_sandbox_response_cap.py` | subprocess 沙箱 + 三通道 cap | 否 |
| **TOCTOU / OOM** | `test_file_safety.py` | core.file_safety helper + 12 C4 expansion sites | 否 |
| | `test_file_safety_c5.py` | 11 C5 tools+internal sites | 否 |
| | `test_ui_whitelist.py` | UI 按钮白名单（r45 拆出） | 否 |
| **预处理工具** | `test_rpa_unpacker.py` | RPA-3.0/2.0 解包 + ZIP Slip 防护 | 否 |
| | `test_rpyc_decompiler.py` | RPYC 二进制 + RestrictedUnpickler + Tier1/Tier2 | 否 |
| | `test_lint_fixer.py` | lint 7 错误模式解析 + 修复 | 否 |
| | `test_tl_dedup.py` | tl-mode 跨文件去重 | 否 |
| | `test_batch1.py` | RPA 打包 + 默认语言 + JSON 解析重试 + lint 集成 | 否 |
| **集成** | `test_direct_pipeline.py` | direct-mode 集成 | 否 |
| | `test_tl_pipeline.py` | tl-mode 集成 | 否 |
| **冒烟** | `smoke_test.py` | validate_translation 所有 W/E Code + strings 统计 | 否 |
| **Drift 防御自测** | `test_verify_docs_claims.py` | scripts/verify_docs_claims.py 自测 | 否 |
| **端到端**（CI 不跑） | `test_single.py` | 单文件完整翻译流程（API → 回写 → 校验） | **是** |

### 内建 self-test（CI 中独立 step）

| 文件 | 函数 | 断言数 |
|------|------|--------|
| `translators._tl_parser_selftest` | `run_self_tests` | 75 |
| `translators.screen` | `_run_self_tests` | 51 |

### 测试数据 fixture

| 文件 | 用途 |
|------|------|
| `tests/sample_triggers.rpy` + `_trans.rpy` | 触发各 W/E 代码的原文/译文样本（与 trans 文件逐行配对） |
| `tests/glossary_test.json` | 含 `locked_terms` / `no_translate` 的术语表 |
| `tests/sample_strings.rpy` | translate strings 块样本（6 条 old/new） |
| `tests/fixtures/strings_only/` | strings 统计隔离子目录（防其他 .rpy 污染） |
| `tests/tl_priority_mini/` | tl 优先模式最小目录结构 |
| `tests/artifacts/` | 实际项目 untranslated JSON（projz / tyrant） |
| `tests/zh_prompt_baseline.txt` | 中文 prompt 基线快照 |

---

## 二、边界值测试要点

### W430（长度比例 0.15 / 2.5）
- 译文 < 0.15 × 原文 → 异常短，告警
- 译文 > 2.5 × 原文 → 异常长，告警

### W442（中文占比 0.05）
- 译文中文字符占比 < 5% → 疑似未翻译，告警

### E411（锁定术语）
- `glossary.locked_terms` 中的 key 在原文出现，译文必须使用规定译名

### E420（禁翻片段）
- `glossary.no_translate` 中的片段在原文出现，译文须保留相同英文（大小写不敏感）

### W251（占位符顺序 vs 集合）
- 集合相同但顺序不同 → 仅告警（保留译文）
- 集合不同（缺失/多余） → E210/W211（错误）

详细 W/E 代码语义：见 [docs/REFERENCE.md §12](../docs/REFERENCE.md)。

---

## 三、测试执行方法

### 本地快速验证（无 API）

```bash
python tests/test_all.py                    # meta-runner ~5s
python scripts/verify_docs_claims.py --fast # docs claim 同步性 ~1s
```

### 本地完整 sweep（CI 跑此组）

```bash
# 各独立 suite 单独运行
python tests/test_engines.py
python tests/test_engines_rpgmaker.py
python tests/test_csv_engine.py
# ... 33 个独立 suite，逐个 python tests/<suite>.py

# 内建 self-test
python -c "from translators._tl_parser_selftest import run_self_tests; run_self_tests()"
python -c "from translators.screen import _run_self_tests; _run_self_tests()"

# Drift 防御 full mode
python scripts/verify_docs_claims.py --full
```

### CI

`.github/workflows/test.yml`：6 jobs（matrix `[ubuntu-latest, windows-latest]` × `[3.9, 3.12, 3.13]`）。

关键步骤：py_compile + meta + 22 独立 suite + 2 self-test + verify_docs_claims unit + `--full` + mock target consistency check + 零依赖检查 + mypy informational + integration dry-run。

### pre-commit hook（4 件套，~7-12s）

通过 `scripts/install_hooks.sh` 启用：
1. py_compile 所有 staged .py
2. file-size guard（>800 行 .py block）
3. meta-runner（`tests/test_all.py`）
4. `verify_docs_claims --fast`

详见 [.git-hooks/README.md](../.git-hooks/README.md)。

---

## 四、需 API 的端到端测试

`tests/test_single.py` 单文件完整翻译流程，需 `--api-key` 实际调用。CI 不跑（避免泄密 + 节省费用）。

执行：
```bash
python tests/test_single.py --api-key $XAI_API_KEY --provider xai
```

---

## 五、测试覆盖差距（已知 / r50 末视角）

- **GUI 自动化**：`gui.py` Tkinter UI 仅手动测试 + r46 真实桌面 GUI smoke via computer-use；未纳入 CI
- **PyInstaller build**：`build.py` 仅手动 `pip install pyinstaller --break-system-packages` + `python build.py` 验证（r44 33.9 MB 成功；当前 dist/ 已被 `--clean-only` 清）
- **非中文目标语言端到端**：5 层 code-level contract（r39-r48）已锁死，但端到端验证仍需真实 API + 真实游戏，未自动化
- **RPG Maker Plugin Commands (code 356)**：路线图 P3，需真实 MV/MZ 游戏样本

详见 [docs/REFERENCE.md §13.4 架构 TODO](../docs/REFERENCE.md)。
