<!-- 修改后执行 cp CLAUDE.md .cursorrules -->
# 多引擎游戏汉化工具 — AI 全局上下文

## 项目身份

纯 Python（零第三方依赖，≥3.9）多引擎游戏汉化工具。~15,000 行核心代码，307 个自动化测试。支持 Ren'Py / RPG Maker MV/MZ / CSV/JSONL，五大 LLM（xAI/OpenAI/DeepSeek/Claude/Gemini）+ 自定义引擎插件（`--sandbox-plugin` 可选 subprocess 沙箱，stderr 读取有 10 KB 上限防 OOM）。Direct-mode 漏翻率 4.01%，tl-mode 翻译成功率 99.97%。HTTPS 调用默认启用持久连接池（节省 ~90s 握手/600 次调用）+ 响应体 32 MB 硬上限。`core/translation_db.py` 线程安全（RLock）+ 原子写入（temp + os.replace）。`main.py` 所有引擎统一走 `engines.resolve_engine(...).run(args)` 单一入口。`tests/test_all.py` 为 meta-runner，实际测试分布在 5 个聚焦文件（api / file_processor / translators / glossary-prompts-config / translation-state），每个均 < 800 行。`--emit-runtime-hook` opt-in 可生成 `translations.json` + `resources/hooks/inject_hook.rpy`（与 extract_hook 闭环），支持不改游戏源文件的运行时注入模式。

## 开发原则

1. **宁可漏翻也不误翻** — 不确定的条目保留原文
2. **数据驱动** — 改动前收集数据，改动后验证数据，不拍脑袋定阈值
3. **隔离变量** — 每次只改一个东西，验证独立效果
4. **不破坏已有功能** — 新功能用开关控制（CLI 参数），默认行为不变
5. **安全优先** — checker 不通过就丢弃、回写前校验、原地操作前备份
6. **先读再写** — 涉及参考项目借鉴时，先完整阅读其源码和文档再给方案
7. **方案先行** — 给出改动方案和受影响函数列表，等用户确认后再写代码
8. **最小改动** — 不做不必要的重构、不加不需要的注释、不改不相关的代码
9. **零依赖** — 坚持纯标准库，不引入第三方包

## 模块调用关系 + 职责

```
gui.py (图形界面) ─── start_launcher.py (CLI 菜单) ─── tools/renpy_upgrade_tool.py (独立工具)
       │                      │
       └──────────────────────┘
                │ subprocess 调用
                ▼
main.py (CLI 入口) → engines.resolve_engine(args.engine or "auto").run(args)
  │
  ├── engines/ 多引擎抽象层（所有引擎统一入口，round 28 A-H-3 Minimal）
  │    ├── engines/engine_detector.py  (检测+路由)
  │    ├── engines/engine_base.py      (EngineProfile/TranslatableUnit/EngineBase)
  │    ├── engines/generic_pipeline.py (6 阶段通用流水线)
  │    ├── engines/renpy_engine.py     (Ren'Py 薄包装，内部路由 tl_mode/tl_screen/retranslate/direct)
  │    ├── engines/rpgmaker_engine.py  (RPG Maker MV/MZ)
  │    └── engines/csv_engine.py       (CSV/JSONL)
  │
  ├── translators/ Ren'Py 三条管线（由 RenPyEngine.run 内部调度）
  │    ├── translators/direct.py         (direct-mode 入口 + run_pipeline)
  │    │   ├── _direct_chunk.py        (chunk 级翻译/重试/拆分)
  │    │   ├── _direct_file.py         (file 级翻译 + targeted 低密度路径)
  │    │   └── _direct_cli.py          (dry-run 预览/统计)
  │    ├── translators/retranslator.py   (补翻)
  │    ├── translators/tl_mode.py        (tl-mode 入口 + run_tl_pipeline)
  │    │   ├── _tl_patches.py          (font / rpyc / language switch patches)
  │    │   └── _tl_dedup.py            (跨文件去重 + chunk 装配)
  │    ├── translators/screen.py         (screen 裸英文翻译入口 + re-export)
  │    │   ├── _screen_extract.py      (扫描 / 识别 / 跳过判断)
  │    │   └── _screen_patch.py        (翻译 / 替换 / 进度 / 备份)
  │    ├── translators/tl_parser.py      (tl 解析核心 + re-export)
  │    │   ├── _tl_postprocess.py      (nvl clear / 空块后处理)
  │    │   ├── _tl_nvl_fix.py          (Ren'Py 8.6 → 7.x 翻译 ID 修复)
  │    │   └── _tl_parser_selftest.py  (内置 75 条自测套件)
  │    └── translators/renpy_text_utils.py (文本分析)
  │
  └── core/ 共享基础设施
       ├── core/api_client.py（含自定义引擎加载）/ core/prompts.py / core/glossary.py
       ├── core/translation_db.py / core/translation_utils.py
       ├── core/config.py / core/lang_config.py / core/font_patch.py
       ├── core/http_pool.py（HTTPS 线程本地连接池） / core/pickle_safe.py（白名单反序列化）
       ├── file_processor/ (splitter/patcher/checker/validator)
       └── one_click_pipeline.py → pipeline/ (Ren'Py 四阶段流水线 + lint 修复 + 默认语言)

tools/   — review_generator / rpa_unpacker / rpa_packer / rpyc_decompiler
           renpy_lint_fixer / renpy_upgrade_tool / translation_editor
           verify_alignment / revalidate / patch_font_now / analyze_writeback
custom_engines/ — 用户自定义翻译引擎插件目录（example_echo.py 示例）
tests/   — test_all(meta) → api_client(19) + file_processor(36) + translators(24) + glossary_prompts_config(24) + translation_state(15) = 118
           + test_engines(62) + smoke(13) + rpa(16) + rpyc(18) + lint(15) + dedup(10) + batch1(18)
           + editor(13) + custom(20) + direct_pipeline(2) + tl_pipeline(2) = 307
```

**调用关系图中未标注职责的关键文件**：

| 文件 | 职责 |
|------|------|
| engines/renpy_engine.py | Ren'Py 薄包装，委托三条管线 |
| pipeline/helpers.py | 文件评分 / 试跑选择 / 扫描辅助 |
| pipeline/gate.py | 闸门评估 / 漏翻归因 / 报告生成 |
| pipeline/stages.py | 四阶段实现入口 |
| build.py | PyInstaller 打包为单文件 .exe |
| resources/hooks/ | Ren'Py Hook 模板（提取 + 语言切换） |

## 修改代码前的检查清单

- [ ] 列出要修改的文件和函数，等用户确认后再写代码
- [ ] 是否引入了第三方依赖？（禁止）
- [ ] 是否改变了默认行为？（需要 CLI 开关控制）
- [ ] 新增/修改的函数是否有类型注解？
- [ ] 是否有对应的测试用例？运行 `python tests/test_all.py` 确认零回归
- [ ] 原地修改文件前是否有 .bak 备份逻辑？
- [ ] checker 不通过的翻译是否被丢弃（而非强行使用）？
- [ ] 开发完成后是否更新了 CHANGELOG_RECENT.md？

## 已知限制

- GUI/build 仅手动测试，未纳入自动化
- 端到端测试需 API key，未进入 CI
- RPG Maker Plugin Commands(356) / JS 硬编码 / 加密归档暂不支持

## 按需加载文档索引

| 你在做什么 | 加载哪个文档 |
|-----------|-------------|
| 修改翻译模式（direct/tl/retranslate） | `docs/dataflow_translate.md` |
| 修改一键流水线或核心算法 | `docs/dataflow_pipeline.md` |
| 修改校验逻辑或 API 调用 | `docs/quality_chain.md` |
| 修改/新增校验规则（Error/Warning Code） | `docs/error_codes.md` |
| 调整阈值或常量 | `docs/constants.md` |
| 新增引擎支持 | `docs/engine_guide.md` |
| 讨论下一步做什么 | `docs/roadmap.md` |
| 了解历史决策 | `CHANGELOG_RECENT.md` |
| 修改测试体系 | `TEST_PLAN.md` |
