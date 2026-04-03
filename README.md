# 多引擎游戏汉化工具

一个纯 Python 的游戏自动汉化工具，支持 **Ren'Py**、**RPG Maker MV/MZ**、**CSV/JSONL 通用格式**，通过 LLM API 翻译为简体中文。

**零依赖**（纯标准库）| **图形界面 + 命令行** | **五大 LLM 提供商** | **多引擎自动检测** | **55+ 项翻译校验** | **断点续传** | **并发翻译**

---

## 特性一览

- **三种翻译模式**：direct-mode（整文件翻译）、tl-mode（tl 框架翻译）、retranslate（残留英文补翻）
- **四阶段一键流水线**：试跑 → 闸门评估 → 全量翻译 → 自动补翻
- **占位符保护**：`[var]`、`{tag}`、`%(name)s` 等 Ren'Py 语法标记在翻译前替换为安全令牌，翻译后精确还原
- **密度自适应**：低对话密度文件自动切换定向翻译模式，避免 AI 注意力被代码稀释
- **术语一致性**：自动提取角色名、支持外部词典、翻译记忆自动学习、锁定术语 + 禁翻片段
- **完整质量链**：发送前占位符保护 → 返回后 ResponseChecker → 回写后 55+ 项结构校验 → chunk 自动重试（截断时自动拆分）
- **漏翻归因分析**：每条未翻译行自动归因（AI 未返回 / Checker 丢弃 / 回写失败）
- **日志分级控制**：`--verbose` 输出 DEBUG 详情（dry-run 时含每文件密度/费用明细 + 直方图），`--quiet` 仅输出 WARNING 及以上
- **AI 自动术语抽取**：试跑阶段后 AI 自动从译文中提取高频术语补充词典
- **Ren'Py 7→8 show 修复**：自动为空 ATL 块的 `show` 语句补加冒号（RENPY-020 规则）
- **多引擎支持**：Ren'Py（direct/tl/retranslate 三模式）+ RPG Maker MV/MZ（事件指令+数据库+System）+ CSV/JSONL 通用格式，`--engine auto` 自动检测
- **CoT 思维链翻译**：`--cot` 启用直译→校正→意译三步流程，提升长难句和文化改编质量
- **字体配置可定制**：`--font-config font_config.json` 自定义字号/布局参数，tl-mode 使用 `translate None` 覆盖模板（不修改 gui.rpy）
- **会话级翻译缓存**：相同原文自动命中缓存，减少重复 API 调用，跨文件术语一致性自动保障
- **GUI 增强**：实时进度条、自适应轮询（50/200ms）、日志自动裁剪（5000→3000 行）、优雅终止（保存进度后退出）
- **Screen 文本翻译**：`--tl-screen` 翻译 screen 中 tl 框架无法提取的裸英文（`text`/`textbutton`/`tt.Action` Tooltip），作为 tl-mode 补充覆盖剩余 ~5% UI 文本

---

## 快速开始

### 环境要求

- Python >= 3.9
- 无第三方依赖（纯标准库）

### 三种启动方式

```bash
# 方式一：图形界面（推荐）
python gui.py                  # 或双击 多引擎游戏汉化工具.exe

# 方式二：中文交互菜单
START.bat

# 方式三：命令行
python main.py --game-dir "E:\Games\MyGame" --provider xai --api-key YOUR_KEY --tl-mode --tl-lang chinese --workers 5
```

### 先估费再翻译

```bash
# 扫描文件、估算 token 和费用（不调用 API，无需 API key）
python main.py --game-dir "E:\Games\MyGame" --provider xai --dry-run

# 详细分析：每文件对话密度 + 翻译策略 + 密度分布直方图 + 术语预览
python main.py --game-dir "E:\Games\MyGame" --provider xai --dry-run --verbose
```

---

## 翻译模式

### Direct-mode（整文件翻译）

将完整 `.rpy` 文件发给 AI，AI 自行识别可翻译内容，以 JSON 返回翻译结果，程序 Patch 回原文件。

```bash
# 基本用法
python main.py --game-dir "E:\Games\MyGame" --provider xai --api-key YOUR_KEY

# 指定模型和风格
python main.py --game-dir "E:\Games\MyGame" --provider xai --api-key YOUR_KEY \
    --model grok-4-1-fast-reasoning --genre adult

# 断点续传
python main.py --game-dir "E:\Games\MyGame" --provider xai --api-key YOUR_KEY --resume

# 并发翻译（加速大文件）
python main.py --game-dir "E:\Games\MyGame" --provider xai --api-key YOUR_KEY \
    --workers 3 --rpm 600 --rps 10

# 加载外部词典 + 复制资源 + 保存日志
python main.py --game-dir "E:\Games\MyGame" --provider xai --api-key YOUR_KEY \
    --dict terms.csv --copy-assets --log-file output/translate.log

# 排除特定文件
python main.py --game-dir "E:\Games\MyGame" --provider xai --api-key YOUR_KEY \
    --exclude "tl/*" "*.bak"
```

**适用场景**：没有 tl 翻译框架的项目；AI 看到完整代码上下文，自然知道 `screen say(who, what):` 中的 `say` 是 screen 名不能翻译。

### tl-mode（tl 框架翻译）

扫描 Ren'Py 官方翻译框架 `tl/<lang>/` 中的空翻译槽位，AI 翻译后精确回填到对应行。

```bash
# 从头开始
python main.py --game-dir "E:\Games\MyGame" --provider xai --api-key YOUR_KEY \
    --tl-mode --tl-lang chinese --workers 5

# 断点续跑
python main.py --game-dir "E:\Games\MyGame" --provider xai --api-key YOUR_KEY \
    --tl-mode --tl-lang chinese --workers 5 --resume
```

**适用场景**：已通过 Ren'Py SDK（`renpy.sh launcher` → 「Generate Translations」）在 `tl/<lang>/` 下生成翻译框架的项目。

**注意**：含 `\n` 换行的多行条目会标注 `[MULTILINE]` 标签，提示 AI 保留换行结构。

**优势**：
- 翻译行精确定位到行号，不存在"回写失败"问题
- 回填精度远高于 direct-mode（行号定位 vs 文本匹配）
- 引号剥离保护：AI 有时返回带外层引号的译文，回填前自动剥离，防止 `""text""` 格式错误
- StringEntry 四层 fallback 匹配（精确 → strip → 去占位符令牌 → 转义规范化）
- 翻译后自动清理修改过的 `.rpyc`/`.rpymc`/`.rpyb` 缓存（强制 Ren'Py 重编译），可用 `--no-clean-rpyc` 禁用

### Screen 文本翻译（`--tl-screen`）

tl 框架只提取 Say 对话和 `_()` 包裹的字符串，screen 定义中的裸 `text "..."`、`textbutton "..."`、`tt.Action("...")` 不会被提取。`--tl-screen` 直接修改源文件中的英文字符串，补充覆盖 tl-mode 遗漏的 UI 文本。

```bash
# 与 tl-mode 联用（推荐）：先翻译对话，再补充 screen 文本
python main.py --game-dir "E:\Games\MyGame" --provider xai --api-key YOUR_KEY \
    --tl-mode --tl-lang chinese --workers 5 --tl-screen

# 独立运行（已完成 tl-mode 后补充）
python main.py --game-dir "E:\Games\MyGame" --provider xai --api-key YOUR_KEY --tl-screen
```

**注意**：
- Screen 翻译**直接修改源 .rpy 文件**（自动创建 `.bak` 备份），游戏更新后需重新执行
- 自动跳过 `_()` 包裹的文本（已由 tl 框架的 `translate strings:` 块覆盖）
- 支持 `--dry-run` 预览（仅扫描统计，不调用 API）
- 支持 `--resume` 断点续传

### Retranslate（补翻模式）

扫描已翻译文件中残留的英文对话行，构建小 chunk 精准补翻。

```bash
python main.py --game-dir "E:\Games\MyGame" --output-dir "E:\Games\MyGame" \
    --provider xai --api-key YOUR_KEY --retranslate
```

每条残留英文行附带 ±3 行上下文，构建 ≤20 行的小 chunk，发送专用 prompt（每行标注 `>>>` 必须翻译）。原地回写，自动 `.bak` 备份。

### CSV/JSONL 通用格式

用任何外部工具（Translator++、VNTextPatch、GARbro 等）导出为 CSV/JSONL，用本工具做 AI 翻译，再用原工具回灌。**一天覆盖所有引擎**。

```bash
# CSV 翻译（单文件）
python main.py --engine csv --game-dir texts.csv --provider xai --api-key KEY

# CSV 翻译（整个目录）
python main.py --engine csv --game-dir /path/to/csvs/ --provider xai --api-key KEY

# JSONL 翻译
python main.py --engine jsonl --game-dir texts.jsonl --provider xai --api-key KEY
```

**支持格式**：CSV（含 TSV）、JSONL、JSON 数组。列名自动匹配（original/source/text/en 等别名），支持 UTF-8 BOM。输出为 `translations_zh.csv` 或 `translations_zh.jsonl`。

### RPG Maker MV/MZ

自动检测 RPG Maker 游戏目录，提取对话（401/405 事件指令合并）、选项（102）、数据库（角色/物品/技能等 8 种 JSON）、系统文本（System.json）。

```bash
# 自动检测引擎（RPG Maker MV 或 MZ）
python main.py --engine auto --game-dir "E:\Games\RPGMakerGame" --provider xai --api-key KEY

# 显式指定引擎
python main.py --engine rpgmaker --game-dir "E:\Games\RPGMakerGame" --provider xai --api-key KEY

# dry-run 预估
python main.py --engine rpgmaker --game-dir "E:\Games\RPGMakerGame" --provider xai --dry-run
```

**注意**：翻译后需手动安装中文字体到 `www/fonts/` 目录，工具会在翻译完成后给出提示。

---

## 一键流水线

`one_click_pipeline.py` 按四阶段自动执行完整翻译流程：

```bash
python one_click_pipeline.py --game-dir "E:\Games\MyGame" \
    --provider xai --api-key YOUR_KEY --model grok-4-1-fast-reasoning --clean-output
```

| 阶段 | 说明 |
|------|------|
| **Stage 1: 试跑批次** | 按风险评分自动挑选高风险文件先跑小批量，验证 API 连通性和翻译质量 |
| **Stage 1.5: 自动术语抽取** | 试跑完成后 AI 自动从译文中提取高频术语，补充到 glossary |
| **Stage 2: 闸门评估** | 结构错误阻断，漏翻比例超阈值仅告警（不中断） |
| **Stage 3: 全量批处理** | 翻译全项目；低密度文件（< 20%）自动走定向翻译模式 |
| **Stage 4: 补翻轮** | 扫描残留英文行，精准补翻，原地回写 |

**输出产物**：

```
output/projects/<project_name>/
  ├── stage2_translated/    # 翻译结果
  ├── _pipeline/
  │   ├── pilot_input/      # 试跑输入
  │   ├── pilot_output/     # 试跑输出
  │   ├── pilot.log         # 试跑日志
  │   └── full.log          # 全量日志
  └── pipeline_report.json  # 阶段结果与闸门状态
```

**常用参数**：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--pilot-count` | 20 | 试跑文件数 |
| `--gate-max-untranslated-ratio` | 0.08 | 闸门允许的最大漏翻比例 |
| `--clean-output` | 否 | 开始前清理输出目录 |
| `--min-dialogue-density` | 0.20 | 低密度阈值（低于此值走定向翻译） |
| `--package-name` | CN_patch_game | 输出 zip 包名 |

| `--tl-mode` | 否 | 流水线中使用 tl-mode 翻译 |

其余参数（`--dict` / `--exclude` / `--copy-assets` / `--target-lang` 等）透传到 `main.py`。

---

## Ren'Py 7→8 升级扫描

独立工具，扫描 `.rpy` 中的 Python 2 → 3 兼容性问题（20 条规则），支持自动修复。

包含 RENPY-020 规则：自动为空 ATL 块的 `show` 语句补加冒号（Ren'Py 8 要求 `show` 后跟 ATL 块时必须带冒号）。

```bash
# 仅扫描报告
python -m tools.renpy_upgrade_tool ./game

# 自动修复并备份
python -m tools.renpy_upgrade_tool ./game --fix --backup
```

---

## 中文交互启动器

`START.bat` 提供 9 种模式的中文菜单，适合不想记命令行参数的用户：

| 模式 | 说明 |
|------|------|
| 1 | Ren'Py 主流程翻译（从头开始） |
| 2 | Ren'Py 主流程翻译（断点续跑） |
| 3 | Ren'Py 仅扫描与费用估算（Dry-run） |
| 4 | Ren'Py 一键流水线（试跑 + 闸门 + 全量 + 补翻） |
| 5 | Ren'Py tl-mode 翻译（从头开始） |
| 6 | Ren'Py tl-mode 翻译（断点续跑） |
| 7 | Ren'Py 7→8 升级扫描 |
| 8 | RPG Maker MV/MZ 翻译 |
| 9 | CSV/JSONL 通用格式翻译 |

---

## 支持的 API

| 提供商 | `--provider` | 默认模型 | 输入/输出价格 ($/M tokens) |
|--------|-------------|---------|--------------------------|
| xAI | `xai` / `grok` | grok-4-1-fast-reasoning | $0.20 / $0.50 |
| OpenAI | `openai` | gpt-4o-mini | $0.15 / $0.60 |
| DeepSeek | `deepseek` | deepseek-chat | $0.14 / $0.28 |
| Claude | `claude` | claude-sonnet-4 | $3.00 / $15.00 |
| Gemini | `gemini` | gemini-2.5-flash | $0.15 / $0.60 |

支持 `--input-price` / `--output-price` 自定义价格覆盖。

**重试策略**：指数退避 + 随机 jitter，优先使用 `Retry-After` 响应头，等待时间上限 60 秒。

---

## 项目架构

```
┌──────────────────────────────────────────────────────────────┐
│  入口层                                                       │
│  START.bat → start_launcher.py     中文交互启动器（7 种模式） │
│  main.py                           CLI 入口 + 路由            │
│  one_click_pipeline.py             四阶段流水线 CLI            │
├──────────────────────────────────────────────────────────────┤
│  翻译引擎层  translators/                                     │
│  direct.py             direct-mode 整文件翻译引擎（含 dry-run）│
│  retranslator.py       补翻引擎（残留英文检测 + 精准补翻）    │
│  tl_mode.py            tl-mode 翻译框架槽位引擎               │
│  screen.py             screen 文本翻译引擎                     │
│  tl_parser.py          tl/ 框架状态机解析器                    │
│  renpy_text_utils.py   Ren'Py 文本分析公共函数                │
├──────────────────────────────────────────────────────────────┤
│  核心层  core/                                                │
│  api_client.py         多提供商 API 客户端 + 限流 + 计费      │
│  config.py             全局配置                                │
│  lang_config.py        语言配置                                │
│  prompts.py            Prompt 模板工厂（支持外部覆写）         │
│  glossary.py           术语表 + 翻译记忆 + 锁定/禁翻          │
│  translation_db.py     翻译元数据 JSON 存储                    │
│  translation_utils.py  公共辅助（ChunkResult/ProgressTracker） │
├──────────────────────────────────────────────────────────────┤
│  基础设施层                                                   │
│  file_processor/         拆分/回写/校验/占位符保护（4 子模块） │
│  pipeline/               一键流水线拆分包（helpers/gate/stages）│
├──────────────────────────────────────────────────────────────┤
│  工具层  tools/                                               │
│  font_patch.py           字体补丁（gui.*_font 改写）           │
│  renpy_upgrade_tool.py   Ren'Py 7→8 升级扫描 + 自动修复       │
│  review_generator.py     翻译审校报告生成                      │
│  verify_alignment.py     零 API 验证策略测试                   │
│  revalidate.py           对已有输出重跑闸门                    │
│  patch_font_now.py       独立运行字体补丁                      │
├──────────────────────────────────────────────────────────────┤
│  测试层                                                       │
│  test_all.py             综合模块测试（71 用例）               │
│  tests/smoke_test.py     冒烟测试（13 用例）                   │
│  test_single.py          单文件端到端测试                      │
└──────────────────────────────────────────────────────────────┘
```

### 模块调用关系

```
start_launcher.py
  ├─ main.py（模式 1-3, 5-6）
  │    ├── core/api_client.py          API 调用 + 限流 + 用量统计
  │    ├── file_processor/             拆分 + 回写 + 校验 + 占位符保护（包）
  │    ├── translators/tl_parser.py    tl-mode 解析 + 精确回填
  │    ├── core/prompts.py             Prompt 模板构建
  │    ├── core/glossary.py            术语表管理
  │    ├── core/translation_db.py      翻译元数据记录
  │    └── tools/font_patch.py         可选字体补丁
  │
  ├─ one_click_pipeline.py（模式 4）→ 委托 pipeline/ 包
  │    ├── pipeline/helpers.py         公共工具（日志/路径/归因）
  │    ├── pipeline/gate.py            闸门评估（file_processor 校验）
  │    ├── pipeline/stages.py          四阶段执行（pilot→gate→full→retranslate）
  │    ├── 调用 main.py（subprocess，分阶段执行）
  │    ├── core/translation_db.py      漏翻归因分析
  │    ├── tools/font_patch.py         打包前字体补丁
  │    └── main.py imports             retranslate_file（补翻阶段）
  │
  └─ tools/renpy_upgrade_tool.py（模式 7，独立工具）
```

所有底层模块仅依赖 Python 标准库，无循环依赖。

---

## 翻译质量保障

### 占位符保护

翻译前将 Ren'Py 语法标记替换为安全令牌，翻译后精确还原：

```
原文: "[name] says: {color=#f00}Hello{/color}"
保护: "__RENPY_PH_0__ says: __RENPY_PH_1__Hello__RENPY_PH_2__"
还原: "[name] says: {color=#f00}你好{/color}"
```

### ResponseChecker（返回后校验）

- `check_response_item()`：占位符集合一致性 + 原文/译文非空
- `check_response_chunk()`：返回条数与期望条数一致性
- 不通过 → 丢弃该条，保留原文（宁可漏翻也不误翻）
- **chunk 自动重试**：API 错误或高丢弃率（drop rate 超阈值）时自动重试 1 次

### validate_translation（回写后校验，55+ 项）

| 类别 | 检查内容 | Error/Warning Code |
|------|----------|-------------------|
| 结构 | 行数一致、缩进保留、关键字保留 | — |
| 变量 | `[var]` 缺失 / 多余 | E210 / W211 |
| 标签 | `{tag}` 配对不一致 | E220 |
| 菜单 | `{#id}` 标识符不一致 | E230 |
| 格式 | `%(name)s` 占位符不一致 | E240 |
| 转义 | 转义序列不一致 | E250 |
| 顺序 | 占位符顺序偏差 | W251 |
| 术语 | 锁定术语未使用 / 禁翻片段被改 | E411 / E420 |
| 长度 | 译文长度比例异常 | W430 |
| 风格 | 模型自述 / 标点混用 / 中文占比低 | W440 / W441 / W442 |
| 缓存 | 缓存命中译文与原文不匹配 | W460 |
| 一致性 | 相同原文不同译文 | W470 |

### 漏翻归因分析

翻译完成后，每条未翻译行自动归因为：
- **AI 未返回**：AI 在响应中遗漏了该行
- **Checker 丢弃**：校验不通过被丢弃（保留原文）
- **回写失败**：翻译存在但回写到文件时匹配失败

归因数据写入 `pipeline_report.json` 和 `translation_db.json`。

---

## 术语表与词典

### 自动术语表

- 自动扫描 `define Character(...)` 和 `DynamicCharacter(...)` 提取角色名
- 翻译记忆：成功翻译的内容自动学习（按质量过滤）
- 每次 API 调用自动附带术语表（控制长度避免超 token）
- 线程安全，支持并发翻译

### glossary.json 结构

```json
{
  "characters": {"mc": "主角", "mother": "母亲"},
  "terms": {"Save Game": "保存游戏"},
  "memory": {"You enter the room.": "你走进了房间。"},
  "locked_terms": ["mc"],
  "no_translate": ["Discord"]
}
```

- `locked_terms`：锁定术语的 key 列表；译文必须使用规定译名，否则报 E411 错误
- `no_translate`：禁翻片段列表；原文含这些片段时译文须保留相同英文，否则报 E420 错误

### 外部词典格式

**CSV**（支持 `.csv` / `.tsv` / `.txt`）：
```csv
english,chinese
Save Game,保存游戏
Load Game,读取存档
```

**JSONL**：
```jsonl
{"en": "Save Game", "zh": "保存游戏"}
{"en": "Load Game", "zh": "读取存档"}
```

字段名支持多种别名：`en`/`original`/`source` 和 `zh`/`translation`/`target`。

---

## 输出结构

### direct-mode 输出

```
output/
├── game/                  # 翻译后的 .rpy（保持原目录结构）
├── glossary.json          # 术语表（自动维护）
├── translation_db.json    # 逐行翻译元数据
├── progress.json          # 断点续传进度
├── report.json            # 翻译报告（token 用量 + 费用）
└── warnings.txt           # 警告详情
```

### tl-mode 输出

tl-mode 直接修改 `tl/<lang>/` 下的文件（原地回填），不生成副本：
```
output/
├── glossary.json          # 术语表
├── translation_db.json    # 翻译元数据
├── tl_progress.json       # chunk 级断点续传进度
└── tl_mode_report.json    # tl-mode 翻译报告
```

### 一键流水线输出

```
output/projects/<project_name>/
├── stage2_translated/     # 翻译结果（保持原目录结构）
├── _pipeline/
│   ├── pilot_input/       # 试跑输入文件
│   ├── pilot_output/      # 试跑输出
│   ├── pilot.log          # 试跑阶段日志
│   ├── full.log           # 全量阶段日志
│   └── retranslate_*.json # 补翻进度和数据
├── pipeline_report.json   # 完整报告
└── CN_patch_game.zip      # 最终补丁包
```

---

## 参数完整说明

### main.py

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--game-dir` | 必填 | 游戏根目录（自动检测 `game/` 子目录，自动排除 `renpy/` 引擎文件） |
| `--provider` | 必填 | API 提供商：`xai`/`openai`/`deepseek`/`claude`/`gemini` |
| `--api-key` | — | API 密钥（dry-run 模式可不填） |
| `--model` | 自动 | 模型名称（留空使用提供商默认） |
| `--output-dir` | `output` | 输出目录 |
| `--genre` | `adult` | 翻译风格：`adult`/`visual_novel`/`rpg`/`general` |
| `--rpm` | 60 | 每分钟请求数限制 |
| `--rps` | 5 | 每秒请求数限制 |
| `--timeout` | 180 | API 超时秒数 |
| `--temperature` | 0.1 | 生成温度（低 = 一致性高） |
| `--max-chunk-tokens` | 4000 | 分块最大 token 数 |
| `--max-response-tokens` | 32768 | API 最大响应 token 数 |
| `--workers` | 1 | 并发翻译线程数 |
| `--resume` | — | 从上次中断处继续 |
| `--dry-run` | — | 仅扫描统计，预估费用 |
| `--retranslate` | — | 补翻模式 |
| `--tl-mode` | — | tl 框架翻译模式 |
| `--tl-lang` | `chinese` | tl 语言子目录名 |
| `--tl-priority` | — | 仅翻译 `tl/` 下的脚本 |
| `--min-dialogue-density` | 0.20 | 低密度阈值（低于此值走定向翻译） |
| `--dict` | — | 外部词典路径（可多个） |
| `--exclude` | — | 排除文件 glob 模式（可多个） |
| `--copy-assets` | — | 复制非 `.rpy` 资源文件 |
| `--patch-font` | — | 启用自动字体补丁 |
| `--font-file` | — | 指定字体文件路径 |
| `--target-lang` | `zh` | 目标语言代码 |
| `--log-file` | — | 日志输出文件 |
| `--input-price` | 自动 | 自定义输入价格 ($/M tokens) |
| `--output-price` | 自动 | 自定义输出价格 ($/M tokens) |
| `--verbose` | — | 输出 DEBUG 级别详细日志 |
| `--quiet` | — | 仅输出 WARNING 及以上日志 |
| `--stage` | `single` | 阶段标记（流水线内部使用） |
| `--tl-screen` | — | 翻译 screen 中的裸英文字符串（可与 `--tl-mode` 联用） |

---

## 设计解决的关键问题

### 文件拆分与密度自适应

- 按 `label` / `screen` / `init` / `translate` 等顶层块边界拆分
- 超大单块在空行处自动强制拆分
- 每块 < 4K tokens（可配置 `--max-chunk-tokens`）
- 行偏移量追踪，确保多块翻译结果精确重组
- chunk 间传递 `prev_context`（前一 chunk 末尾 5 行），保证跨块翻译连贯性
- 低密度文件（对话占比 < 20%）自动提取对话行 + 上下文，定向翻译
- 纯配置文件（`define.rpy` / `variables.rpy` / `screens.rpy` / `options.rpy` / `earlyoptions.rpy`）自动跳过

### 防止代码结构被修改

- AI 仅返回 JSON `[{"line": N, "original": "...", "zh": "..."}]`
- 程序只替换引号内文本（双引号/单引号/三引号/`_()` 包裹），不碰代码
- 替换前验证：原文必须在指定行精确匹配（±3 行模糊搜索）
- 第四遍全文扫描跳过已修改行，防止同一原文在多处出现时被重复替换
- 回写前安全转义（反斜杠、引号、换行）

### 并发与容错

- `--workers N` 支持文件内多 chunk 并行翻译
- 6 级 JSON 解析容错：直接解析 → Markdown 提取 → 括号搜索 → 尾逗号修复 → 逐对象提取 → 字段顺序容错
- 指数退避重试（429/5xx 错误）
- chunk 级断点续传，崩溃后 `--resume` 恢复
- ETA 进度显示

### 费用追踪

- 实时统计 input/output tokens
- 按提供商 + 模型精确定价（支持 20+ 模型）
- 推理模型 thinking tokens 按额外倍率计费
- `--dry-run` 预估费用（零 API 调用）
- 支持 `--input-price` / `--output-price` 自定义覆盖

---

## 组合式工作流

本工具负责「AI 翻译 + 校验」，可与其他工具组合：

### 模式 A：解包 → 本工具 → 字体补丁

1. 使用解包工具（unrpyc 等）获取 `.rpy` 源文件
2. 使用 `main.py` 或 `one_click_pipeline.py` 翻译
3. 使用 `projz` / `renpy-chinese-tl` 等项目的字体补丁方案打包

### 模式 B：SDK 生成 tl → 本工具 tl-mode → 原地回填（推荐）

1. 通过 Ren'Py SDK 生成 `tl/<lang>/` 翻译框架
2. `--tl-mode --tl-lang chinese --workers 5` 翻译空槽位
3. 支持多线程并发、断点续跑、`.bak` 自动备份
4. 后续可用 `renpy-translator` 做增量校对

### 模式 C：projz 扫描 → 本工具翻译 → projz 回写

1. `projz` 扫描项目生成 translate 脚本
2. 本工具翻译 `.rpy` 中的可见字符串
3. 交回 `projz` 回写或构建补丁包

### 模式 D：LinguaGacha / AiNiee 前处理 → 本工具翻译

1. 使用其他工具预处理（归一化、冗余清理、术语抽取）
2. 预处理后的 `.rpy` 交给本工具翻译
3. 结合上述任意模式完成最终打包

---

## 验证数据

以 The Tyrant（~140 文件）为测试项目：

| 模式 | 翻译成功率 | 费用 | 耗时 | 备注 |
|------|-----------|------|------|------|
| direct-mode | 95.99%（漏翻 4.01%） | — | — | 密度自适应 + retranslate 后 |
| tl-mode | **99.97%** | $2.73 | 73 min | 10 线程，grok-4-1-fast-reasoning |

**direct-mode 漏翻归因**：AI 未返回 71.1% / 回写失败 28.1% / Checker 丢弃 0.8%

**关键发现**：
- 对话密度是漏翻率最强相关因子（<10% 密度文件漏翻中位数 57.69%，≥40% 仅 4.54%）
- tl-mode 回填精度远高于 direct-mode，可消除"回写失败"类漏翻
- AI 约 14% 概率返回带外层引号的译文，已通过引号剥离保护修复

---

## 开发与测试

### Python 版本

Python >= 3.9，无第三方依赖（纯标准库：`threading` / `json` / `re` / `pathlib` / `urllib`）。

### 许可证

MIT License — 详见 [LICENSE](LICENSE)。

### 测试

```bash
# 快速验证（< 5 秒，无需 API）
python test_all.py           # 75 个单元+集成测试
python tests/smoke_test.py   # 13 个校验规则冒烟测试
python -m translators.tl_parser --test   # 75 个解析器断言
```

### CI

GitHub Actions 自动在 Python 3.9 / 3.12 / 3.13 上运行全部测试 + `py_compile` 语法检查 + 零依赖验证 + mypy 类型检查 + dry-run 集成测试。

### 配置文件（可选）

在游戏目录下放置 `renpy_translate.json` 可省去大量 CLI 参数：

```bash
# 复制示例配置
cp renpy_translate.example.json /path/to/game/renpy_translate.json
# 编辑后只需指定 game-dir 和 api-key
python main.py --game-dir /path/to/game --api-key YOUR_KEY
```

配置文件示例（完整参数见 `renpy_translate.example.json`）：

```json
{
    "provider": "xai",
    "api_key_env": "XAI_API_KEY",
    "model": "grok-4-1-fast-reasoning",
    "workers": 5,
    "rpm": 600,
    "rps": 10
}
```

**优先级**：CLI 参数 > 配置文件 > 默认值。API Key 通过 `api_key_env`（环境变量名）或 `api_key_file`（密钥文件路径）安全配置，不直接写入 JSON。

查找顺序：`--config path` > `<game-dir>/renpy_translate.json` > `<game-dir>/../renpy_translate.json`。

---

## 各提供商用法示例

```bash
# xAI (Grok) — 推荐，性价比最高
python main.py --game-dir "E:\Games\MyGame" --provider xai --api-key YOUR_KEY \
    --model grok-4-1-fast-reasoning --workers 5 --rpm 600 --rps 10

# OpenAI (GPT)
python main.py --game-dir "E:\Games\MyGame" --provider openai --api-key YOUR_KEY \
    --model gpt-4o-mini --workers 3 --rpm 500 --rps 10

# DeepSeek
python main.py --game-dir "E:\Games\MyGame" --provider deepseek --api-key YOUR_KEY \
    --model deepseek-chat --workers 3 --rpm 60 --rps 5

# Claude (Anthropic)
python main.py --game-dir "E:\Games\MyGame" --provider claude --api-key YOUR_KEY \
    --model claude-sonnet-4-20250514 --workers 2 --rpm 50 --rps 3

# Gemini (Google)
python main.py --game-dir "E:\Games\MyGame" --provider gemini --api-key YOUR_KEY \
    --model gemini-2.5-flash --workers 3 --rpm 60 --rps 5
```

---

## 性能调优

| 提供商 | 推荐 workers | 推荐 rpm | 推荐 rps | 说明 |
|--------|-------------|---------|---------|------|
| xAI | 5-10 | 600 | 10 | 限流宽裕，可高并发 |
| OpenAI | 3-5 | 500 | 10 | TPM 限制注意 token 用量 |
| DeepSeek | 3 | 60 | 5 | 限流较严，推理模型更慢 |
| Claude | 2-3 | 50 | 3 | RPM 限制严格 |
| Gemini | 3-5 | 60 | 5 | Free tier 限制较多 |

推理模型（如 `grok-*-reasoning`、`deepseek-reasoner`、`o3-mini`）自动将 timeout 提升到 300s。

---

## 故障排查

### API 超时

```
RuntimeError: API 调用失败，已重试 5 次
```

- 增大 `--timeout`（默认 180s，推理模型自动 300s）
- 减少 `--workers` 降低并发压力
- 检查网络代理设置

### 编码错误

```
UnicodeDecodeError: 'utf-8' codec can't decode byte ...
```

- 工具自动尝试 UTF-8 → UTF-8-sig → Latin-1 → GBK 四种编码
- 如仍报错，手动用文本编辑器将文件转为 UTF-8

### 进度文件损坏

```
[PROGRESS] 进度文件损坏，已重置
```

- 工具会自动重置损坏的 progress.json，无需手动处理
- 如需从头开始：删除 `output/progress.json` 或 `output/tl_progress.json`

### 漏翻率偏高

- 使用 `--tl-mode` 替代 direct-mode（99.99% vs 95.99%）
- 检查 `--min-dialogue-density` 阈值（默认 0.20）
- 运行一键流水线（自动试跑→闸门→全量→补翻）

### 词典文件不生效

- 确认文件路径正确（错误路径会显示 `[WARN] 词典文件不存在` 警告）
- CSV 格式：首行必须是 `english,chinese` 表头
- JSONL 格式：每行一个 `{"en": "...", "zh": "..."}` 对象

---

## 版本历史

详见 [CHANGELOG.md](CHANGELOG.md)。

### 第十五轮：nvl clear 翻译 ID 修正

- **问题**：Ren'Py 8.6+ 生成 .tl 模板时默认只用 Say 语句算哈希，但 7.x 会把 `nvl clear` 也纳入哈希，导致含 `nvl clear` 的翻译块静默失败
- **修复**：`fix_nvl_translation_ids` / `fix_nvl_ids_directory` 自动检测并修正 ID，已集成到 tl-mode 后处理链
- **测试**：71→75

### 第十四轮：全面优化（Ren'Py 专项）

- **基础重构**：新建 `translators/renpy_text_utils.py` 公共函数模块 + `pipeline/` 包拆分（helpers/gate/stages）+ dry-run 逻辑提取
- **代码健壮性**：收窄 10+ 处裸 `except`、`config.validate()` 类型/范围校验、GUI 优雅终止
- **性能优化**：会话级翻译缓存（相同原文自动命中）、GUI 自适应轮询（50/200ms）、日志裁剪（5000→3000 行）
- **翻译质量**：新增 E250（转义序列）/ W460（缓存一致性）/ W470（相同原文不同译文）校验规则，校验总数 55+
- **用户体验**：GUI 实时进度条、优雅终止（保存进度后退出）、测试用例 66→71
