> 仅在修改翻译模式（direct/tl/retranslate）时加载此文档。

# 三种翻译模式数据流

## Direct-mode（默认）

```
run_pipeline(args) 入口
  ├─ 初始化：APIClient / Glossary / ProgressTracker / TranslationDB
  ├─ 扫描 .rpy → 排除引擎(renpy/lib/) → 排除 --exclude → tl-priority 过滤
  ├─ 按文件大小升序排列（小文件优先积累翻译记忆）
  └─ 逐文件翻译：
      translate_file() 入口（translators/direct.py）
        ├─ 文件名 ∈ SKIP_FILES_FOR_TRANSLATION → [SKIP-CFG] 直接复制
        ├─ calculate_dialogue_density() < 阈值 → _translate_file_targeted()（定向翻译）
        └─ 密度 ≥ 阈值 → split_file() → 逐 chunk 翻译：
            _translate_chunk_with_retry()（自动重试；截断时自动拆分重试）
              ├─ _should_retry() → (should, needs_split) 元组
              ├─ needs_split=True → _split_chunk()（label 边界 > 空行 > 二等分）→ 分别翻译 → 合并
              └─ _translate_chunk()
                    ├─ prev_context: 前一 chunk 末尾 5 行（上下文连贯性）
                    ├─ protect_placeholders() → __RENPY_PH_N__ 令牌
                    ├─ client.translate()（API 调用）
                    ├─ restore_placeholders()
                    ├─ check_response_item() + check_response_chunk()
                    └─ 不通过 → 丢弃保留原文，status="checker_dropped"
                    → ChunkResult dataclass 封装返回值
      apply_translations()（行级回写，四遍匹配；第四遍全文扫描跳过 modified_lines）
      validate_translation()（50+ 项校验）
      glossary.update_from_translations()（翻译记忆学习）
```

**密度自适应路由**：阈值 `--min-dialogue-density` 默认 0.20。低密度（多代码少对话）→ 提取对话行 + ±3 行上下文定向翻译；高密度 → 整文件按块拆分全量翻译。

## tl-mode（`--tl-mode --tl-lang chinese`）

```
run_tl_pipeline(args) 入口（translators/tl_mode.py）
  ├─ scan_tl_directory() 扫描 tl/<lang>/*.rpy（排除 common.rpy）
  ├─ get_untranslated_entries() 筛选空槽位
  │   ├─ DialogueEntry: translation == ""
  │   └─ StringEntry: new == ""
  ├─ build_tl_chunks()：按文件分组，每 chunk ≤ 30 条
  │   └─ 含 `\n` 的多行条目自动添加 [MULTILINE] 标记
  ├─ ThreadPoolExecutor 并发翻译（--workers 控制线程数）
  │   └─ per-chunk: protect → API → restore(id/original/zh) → check_response_item
  ├─ 匹配阶段：
  │   ├─ DialogueEntry: identifier hash 精确匹配
  │   └─ StringEntry: 四层 fallback（精确 → strip → 去占位符令牌 → 转义规范化）
  └─ fill_translation() 行级精确回填
      └─ str.replace 只替换第一个 "" → "译文"（保留缩进/character 前缀）
      └─ 引号剥离保护：ASCII ""、弯引号 ""、全角 ＂＂
  └─ postprocess_tl_directory()：移除 nvl clear + 补 pass
  └─ fix_nvl_ids_directory()：修正 nvl clear 翻译块 ID（8.6+ say-only → 7.x nvl+say 哈希）
```

**关键设计**：
- tl_parser.py 状态机（IDLE/DIALOGUE/STRINGS/SKIP），UTF-8 BOM 处理
- 回填精度远高于 direct-mode（行号精确定位 vs 文本匹配），消除回写失败类漏翻
- .bak 备份（首次回填前创建，不覆盖已有）；独立进度 tl_progress.json
- 并发安全：RateLimiter / UsageStats / ProgressTracker 均自带 threading.Lock
- nvl clear ID 修正：8.6+ say-only 哈希 → 7.x nvl+say 哈希

## Retranslate 补翻模式（`--retranslate`）

```
retranslate_file()（translators/retranslator.py）
  ├─ find_untranslated_lines()：检测残留英文行
  │   └─ 排除 auto/hover/idle 定义行、image 路径行、screen 布局属性行
  ├─ build_retranslate_chunks()：每 chunk ≤ 20 行漏翻行 + ±3 行上下文，合并重叠区间
  ├─ 专用 retranslate prompt（>>> 标记行必须翻译，上下文仅参考）
  │   └─ Round 39: build_retranslate_system_prompt(lang_config=) 按
  │       lang_config.code 分路 — zh / zh-tw 保中文模板 byte-identical；
  │       非 zh（ja / ko）用 generic 英文模板
  ├─ 原地补翻，.bak 自动备份（不覆盖已有）
  └─ 独立进度文件 retranslate_progress.json
```

## Response Checker（`file_processor::check_response_item`）

Round 42 M2 phase-4 为 checker 加 `lang_config` kwarg（default None）:

```
check_response_item(item, line_offset=0, placeholder_re=None, lang_config=None):
  ├─ 原文非空检查
  ├─ 译文非空检查
  │   ├─ lang_config=None (r41 default): zh = item.get("zh", "")  # 硬编码路径
  │   └─ lang_config=<LanguageConfig> (r42 per-language):
  │        zh = resolve_translation_field(item, lang_config) or ""
  │        # 按 lang_config.field_aliases 顺序查 → fallback generic
  │        # ["translation", "target", "trans"]
  ├─ 占位符集合一致性
  └─ 不通过 → 返回 warnings list，caller 丢弃（保留原文计漏翻）
```

**调用路径**：
- tl_mode `_translate_one_tl_chunk` 传 `ctx.lang_config`（r39）
- generic_pipeline chunk loop 传 `lang_config=lang_config`（r42）
- 其他 direct-mode / retranslate / screen 路径默认 `None`（zh 硬编码）

**Round 43-r44 测试契约**：
- zh-tw 拒 bare `"zh"` 字段（`field_aliases` 不含，防 Simplified/Traditional 混淆）
- zh-tw 接受 generic `"translation"` / `"target"` / `"trans"` 字段
- Mixed-language item（`{"ja": "x", "ko": "y"}`）按 `field_aliases` first-match
