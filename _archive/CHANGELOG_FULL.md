# CHANGELOG FULL — Round 1 → Round 45 Overview

> **本文件已精简**。原始未删节版（87 KB / 1260 行，含 r19/r43 完整正文段、r1-r45 各轮"功能/增强/修复"分类细节、Warning/Error Code 完整索引重复、已回滚段）可通过 git 恢复：
> `git log --oneline _archive/CHANGELOG_FULL.md` 找重写本文件之前的 commit hash → `git show <hash>:_archive/CHANGELOG_FULL.md`。
>
> **r46-r50 详细**：见 [CHANGELOG_RECENT_r50.md](CHANGELOG_RECENT_r50.md)
> **r1-r50 演进概览**：见 [EVOLUTION.md](EVOLUTION.md)
> **当前 Error/Warning Code 索引**：见 [docs/REFERENCE.md §12](../docs/REFERENCE.md)
> **当前架构 / 路线图**：见 [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md) + [docs/REFERENCE.md](../docs/REFERENCE.md)

---

## 改动总览（r1-r45）

| 轮次 | 主题 | 核心成果 |
|------|------|----------|
| 第一轮 | 质量校验体系 | W430/W440/W441/W442/W251 告警 + E411/E420 术语锁定 |
| 第二轮 | 功能增强 | 结构化报告 + translation_db + 字体补丁 |
| 第三轮 | 降低漏翻率 | 12.12% → 4.01%（占位符保护 + 密度自适应 + retranslate） |
| 第四轮 | tl-mode | 独立 tl_parser 解析器 + 并发翻译 + 精确回填 |
| 第五轮 | tl-mode 全量验证 | 引号剥离修复 + 后处理 + 99.97% 翻译成功率 |
| 第六轮 | 代码优化与新功能 | chunk 重试 + logging + 模块拆分 + 术语提取 + 退避优化 + show 修复 + 全文扫描安全性 + 截断阈值提升 + tl_parser 测试扩充 |
| 第七轮 | 全量验证（第六轮改进） | 99.99% 成功率（未翻译 25→7，Checker 丢弃 4→2）；9 条遗漏全为边界 case |
| 第八轮 | 代码质量八阶段优化 | 消除重复 + 大函数拆分 + validator 结构化 + Magic Number 收敛 + except 精细化 + 测试 36→42 + LICENSE/pyproject.toml + CI 增强 |
| 第九轮 | 深度优化六阶段 | 线程安全修复 + 深层重复消除（`_filter_checked` / `_deduplicate`）+ 性能 O(1) fallback + API 404/401/推理 timeout + 测试 42→50 + `has_entry` 封装 |
| 第十轮 | 功能加固与生态完善 | 控制标签覆盖确认 + CI 零依赖 + dry-run + 跨平台路径 + Glossary 连字符 + 信心度 + getpass 安全输入 + README 故障排查/调优/示例 + 测试 50→53 |
| 第十一轮 阶段一 | main.py 模块拆分 | main.py 2400→233 行，拆分为 `direct_translator` / `retranslator` / `tl_translator` / `translation_utils` 四个独立模块 + TranslationContext 闭包重构 |
| 第十一轮 阶段二+三 | 回写失败分析与修复 | diagnostic 记录 + analyze 工具 + 前缀剥离 + 转义引号正则 + 回写失败 609→28→~0 + 测试 53→55 |
| 第十一轮 阶段四 | config.json 配置文件 | Config 类（三层合并）+ resolve_api_key + renpy_translate.example.json + argparse default=None + 测试 55→58 |
| 第十一轮 阶段五 | Review HTML + 进度条 | ProgressBar（GBK/ASCII 自适应）+ review_generator.py（HTML 校对报告）+ direct_translator 集成 + 测试 58→60 |
| 第十一轮 阶段六 | 类型注解 | 全部公共 API 返回/参数注解 + py.typed PEP 561 + CI mypy informational |
| 第十一轮 阶段七 | 目标语言参数化 | LanguageConfig dataclass + 4 预置语言 + 文字检测 + resolve_translation_field + 测试 60→63 |
| 第十一轮 阶段八 | Prompt + Validator 多语言 | 中文/英文 prompt 分支 + W442 参数化 + 中文零变更验证 + 测试 63→66 |
| 第十二轮 | 阶段零四项优化 | chunk 截断自动拆分重试 + pipeline main() 拆分 + .rpyc 精确清理 + dry-run verbose 增强 + 测试 66→70 |
| 第十二轮 阶段一 | 引擎抽象层骨架 | EngineProfile + TranslatableUnit + EngineBase ABC + EngineDetector + RenPyEngine 薄包装 + `--engine` CLI |
| 第十二轮 阶段二 | CSV/JSONL + 通用流水线 | CSVEngine（CSV/TSV/JSONL/JSON 读写）+ generic_pipeline（6 阶段通用翻译）+ checker/prompts 参数化适配 |
| 第十二轮 阶段三 | RPG Maker MV/MZ | RPGMakerMVEngine（事件指令 401/405 合并 + 102 选项 + 8 种数据库 + System.json）+ glossary.scan_rpgmaker_database |
| 第十二轮 阶段四 | 文档 + 发布 | start_launcher.py 新增模式 8/9（RPG Maker / CSV）+ 全部文档更新 + 里程碑 M4 达成 |
| 第十二轮 结构整理 | 项目目录重构 | 根目录 .py 27→17：测试 → tests/ + 工具 → tools/ + 引擎抽象 → engines/ 包合并 + import 路径更新 |
| 第十二轮 GUI | 图形界面 + 打包 | gui.py Tkinter GUI（3 Tab + 内嵌日志 + 命令预览 + 配置加载）+ build.py PyInstaller 打包（32 MB 单文件 .exe） |
| 第十三轮 | 四项功能优化 | pipeline 集成 review.html + font_config.json 可配置 + tl/none 覆盖模板（不修改 gui.rpy）+ CoT 思维链翻译（`--cot`） |
| 第十四轮 | 全面优化（Ren'Py 专项） | 五阶段升级：基础重构 + 代码健壮性 + 性能优化 + 翻译质量 + 用户体验 |
| 第十五轮 | nvl clear 翻译 ID 修正 | `fix_nvl_translation_ids` 自动检测 8.6+ say-only 哈希并修正为 7.x nvl+say 哈希 + 管道集成 + 测试 71→75 |
| 第十六轮 | screen 文本翻译 + 缓存清理修复 | `screen_translator.py` screen 裸英文翻译（`--tl-screen`，含 text/textbutton/tt.Action/Notify 四模式）+ `_should_skip` 标签误杀修复 + 缓存清理 .rpymc 补全 + 流水线/启动器/打包集成 + 测试 75→87 |
| 第十七轮 | 项目结构深度重构 | 根目录 25→5 .py：core/(7 模块) + translators/(6 模块) + tools/(扩充 3 模块)，消除 re-export 兼容层 + 循环依赖，162 测试全绿 |
| 第十八轮 | 预处理工具链 + 翻译增强 | RPA 解包 + rpyc 反编译（双层策略）+ Ren'Py lint 集成 + 文件级并行翻译 + locked_terms 预替换 + 跨文件去重 + Hook 模板，测试 162→225 |
| 第十九轮 | 翻译后工具链 + 插件系统 | RPA 打包 + HTML 交互式校对 + 自定义翻译引擎 + 默认语言设置 + Lint 流水线集成 + JSON 解析失败拆分重试，测试 225→267 |
| 第二十轮 | CRITICAL 修复 + 治理文档 | pipeline 悬空 import 三处 + pickle RCE 三处（白名单）+ ZIP Slip 防护 + CONTRIBUTING/SECURITY，测试 266→280 |
| 第二十一轮 | Top 5 HIGH 收敛 | HTTP 连接池（~90s 节省）+ ProgressTracker 双锁解串行 + API Key 走 subprocess env + HTTP 重试 mock + P1 快照单调性，测试 280→286 |
| 第二十二轮 | 测试基础 + 响应体上限 | `MAX_API_RESPONSE_BYTES = 32 MB` + `read_bounded` 共享工具 + T-C-3 direct_pipeline + T-H-2 tl_pipeline 集成测试 |
| 第二十三轮 | A-H-4 Part 1 | `translators/direct.py` 1301→584 + 子模块 `_direct_chunk` / `_direct_file` / `_direct_cli` |
| 第二十四轮 | A-H-4 Part 2 | `translators/tl_mode.py` 928→558 + `tl_parser.py` 1106→532 + 子模块拆分 |
| 第二十五轮 | 七项 HIGH/MEDIUM 收敛 | A-H-1 尾巴 + A-H-6 UsageStats.to_dict + S-H-3 api_key_file 校验 + PF-H-2 direct log 句柄 + PF-C-2 validator 正则预编译 + T-H-1/T-H-3 新测试 |
| 第二十六轮 | 综合包 A+B+C | TranslationDB 三件套（RLock + 原子写 + line=0 + dirty flag）+ RPA 大小检查 + RPYC 白名单同步 + stages/gate 可见化 + screen.py 拆分 + quality_report 加锁 + patcher 反向索引 + RateLimiter 批量清理 |
| 第二十七轮 | 分层收尾 | A-H-2（3 wrapper 下沉 `file_processor/checker.py`）+ A-H-5（`tools/font_patch.py` → `core/font_patch.py`） |
| 第二十八轮 | A-H-3 Minimal 路由 + S-H-4 Dual-mode 插件沙箱 | `main.py` 潜伏 `os` bug 修复 + `--sandbox-plugin` opt-in |
| 第二十九轮 | Priority B 持续优化 | `tests/test_all.py` 2539 拆为 5 聚焦 suite + 49 行 meta-runner（113 tests / 1 命令）+ `tools/patch_font_now.py:27` bug 修复 + TEST_PLAN/dataflow_pipeline 刷新 |
| 第三十轮 | 冷启动审计 4 项 | `_SubprocessPluginClient` stderr 10 KB 上限 + Popen atexit 兜底 + http_pool except 收窄 + retranslator.quality_report 死代码清理 |
| 第三十一轮 | 竞品 hook_template 3 技巧 | checker UI 白名单 / 占位符漂移修正 / strip_tags L5 fallback + inject_hook.rpy 模板 + `--emit-runtime-hook` CLI |
| 第三十二轮 | UI 白名单 + v2 schema + 字体打包 + gui/config override | sidecar JSON 可配置 + `--runtime-hook-schema v2` 嵌套多语言 + emit 时拷 `tl_inject.ttf` + `zz_tl_inject_gui.rpy` init 999 覆盖 + Commit 1 prep（`default_resources_fonts_dir` helper 修 2 处 `__file__.parent` bug） |
| 第三十三轮 | v2 多语言工具链补齐 | `merge_translations_v2.py` 合并工具 + `--font-config` 透传 runtime hook + `translation_editor.py` v2 envelope 适配 + 拆 `test_translation_state.py` 运行时 hook 测试到新 `test_runtime_hook.py` |
| 第三十四轮 | TranslationDB schema v2 + 多语言 | `language` 字段 + 4-tuple 索引 + `has_entry` / `filter_by_status` / `upsert_entry` language-aware + editor HTML dropdown 多语言切换 + `_OVERRIDE_CATEGORIES` 泛化 |
| 第三十五轮 | 多语言外循环 + side-by-side | `ProgressTracker` language namespace + `--target-lang zh,ja,zh-tw` 逗号分隔 + main.py 外层循环 + editor checkbox 切换 side-by-side 多列 + `_OVERRIDE_CATEGORIES` 注册 `config_overrides` |
| 第三十六轮 | 深度审计 H1 + H2 | H1 跨语言 bare-key 污染 + H2 `_sanitise_overrides` `math.isfinite` 过滤 |
| 第三十七轮 | M 级防御加固包 M1-M5 | M1 TranslationDB.load() partial v2 backfill + M2 4 处 JSON loader 50 MB cap + M3 main.py try/finally restore + M4 CWD path whitelist + M5 empty-cell SKIP 语义 |
| 第三十八轮 | "收尾包"一轮清 | 拆 test_translation_editor.py 847→376 + 新 test_translation_editor_v2.py + M2 扩 4 处 + `config_overrides` 扩 bool + editor side-by-side mobile @media |
| 第三十九轮 | "收尾包 Part 2" | 拆 test_translation_state.py 850→681 + tl-mode/retranslate per-lang prompt（r35 挂起绿色小项）+ M2 phase-2 × 3 |
| 第四十轮 | pre-existing 大文件拆 3/4 | `tests/test_engines.py` 962→694 + `tools/rpyc_decompiler.py` 974→725 + `core/api_client.py` 965→642；`gui.py` 815 挂 r41，纯 refactor |
| 第四十一轮 | gui.py 拆 4/4 mixin 收官 + 3 项审计尾巴 | `gui.py` 815→489 拆为 `gui_handlers.py` / `gui_pipeline.py` / `gui_dialogs.py`（MRO mixin 架构）+ M4 OSError warning log + r39 alias integration test + suite count 口径统一 |
| 第四十二轮 | 内部 JSON loader cap 收尾 + checker per-language 化 | rpgm × 2 + 3 progress + 2 pipeline reports cap + `check_response_item` `lang_config` kwarg + 调用点透传 + 5 regression tests |
| 第四十三轮 | r36-r42 累计三维度专项审计 | 3 audit agent（correctness / tests / security）发现 3 test gap（zh-tw / mixed-lang / stat fallback）+ 1 defensive（plugin stdout 50 MB cap），0 CRITICAL/HIGH |
| 第四十四轮 | r43 审计 + 10 项综合清算 + 14 轮欠账 closed | 3 漏网 JSON cap（csv × 2 / gui_dialogs / ui_whitelist，真实 21/21）+ plugin cap rename `_CHARS` 澄清语义 + zh-tw generic fallback test + docs/constants/quality_chain/roadmap 三大刷新 + CI Windows matrix + PyInstaller build 33.9 MB exe 成功 + gui.py 3 s smoke 成功 |
| 第四十五轮 | 综合维护（11 项） | test_file_processor 830→560 拆 UI whitelist → test_ui_whitelist.py + .gitattributes LF policy + 扩 .gitignore + build.py --clean + pre-commit hook + docs/constants 扩 pricing+rate_limit+retry + 其他 docs 复查 + CI shell 一致性 + rpyc_decompiler:416 audit fix |

---

## 备注

- **r19 / r43 完整正文段已删除**（用户决策）；如需 round 19 RPA 打包/HTML 校对工具/插件系统的设计动机或 round 43 累计审计的 3 个 test gap 详情，用 `git show <hash>:_archive/CHANGELOG_FULL.md` 查阅
- **测试数演进**：r1 ~36 → r10 53 → r17 162 → r19 267 → r29 113（拆分后总数因测口径变化短暂下降）→ r45 413（详见 [HANDOFF.md](../HANDOFF.md) `VERIFIED-CLAIMS` 当前数）
- **架构里程碑**：M1（r12 阶段零）/ M2-M5（r12 阶段一-四）/ Round 17 项目结构重构 / Round 28 路由统一 + 沙箱 dual-mode / Round 41 源码全 < 800 行首次达成
