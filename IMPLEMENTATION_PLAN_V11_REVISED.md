# 第十一轮实施方案 v2（修订版）

基于 review 反馈修订。主要变更：
- 阶段一增加闭包重构工作量（TranslationContext）
- 阶段二推迟到功能性改进之后
- 阶段七+八增加 prompt 风险防护和 glossary 兼容性
- 执行顺序调整为 1 → 3 → 4 → 5 → 6 → 2 → 7 → 8
- 进度条增加 ASCII fallback

---

## 修订后执行顺序

| 阶段 | 方向 | 主题 | 预估改动量 | 风险 |
|------|------|------|-----------|------|
| **1** | 技术债务 | main.py 拆分（含闭包重构） | ~700 行迁移+重构 | **已完成** |
| **2** | 漏翻优化 | 回写失败根因分析 + 数据采集 | ~150 行新增 | **已完成**（28条失败，降95%） |
| **3** | 漏翻优化 | 基于根因的 patcher 匹配增强 | ~200 行修改 | **已完成**（前缀剥离+转义引号+3f fallback） |
| **4** | 用户体验 | config.json 配置文件支持 | ~250 行新增 | **已完成**（Config类+example.json+argparse None+3测试） |
| **5** | 用户体验 | Translation Review + 进度增强 | ~300 行新增 | **已完成**（ProgressBar+review_generator+2测试） |
| **6** | 技术债务 | 核心公共 API 类型注解 | ~200 行注解 | **已完成**（py.typed+mypy CI+全部公共API注解） |
| **7** | 多语言 | 目标语言参数化抽象层 | ~400 行修改 | **已完成**（lang_config.py+4语言+3测试+prompt零变更） |
| **8** | 多语言 | Prompt + Validator 多语言适配 | ~300 行修改 | **已完成**（中文/英文prompt分支+W442参数化+3测试+零变更验证） |

> **调整理由**：类型注解（原阶段二）推迟至阶段六，因为签名需对照真实代码核实且 mypy 初期为 informational，优先做功能性改进（漏翻优化 + UX）。

---

## 阶段一（修订）：main.py 拆分 — 含闭包重构

### 闭包依赖分析

以下嵌套函数访问了外层闭包变量，迁移时不能简单平移：

| 嵌套函数 | 外层函数 | 捕获的闭包变量 |
|---------|---------|--------------|
| `_translate_chunk()` | `translate_file()` | `client`, `system_prompt`, `glossary`, `all_warnings`, `translation_db`, `args` |
| `_translate_chunk_with_retry()` | `translate_file()` | 同上 + `checker_drop_ratio` 阈值 |
| `_translate_file_targeted()` | `translate_file()` | `client`, `system_prompt`, `glossary`, `all_warnings` |

### 解决方案：TranslationContext dataclass

将共享状态封装为显式上下文对象，替代闭包捕获：

```python
# translation_utils.py

@dataclass
class TranslationContext:
    """翻译引擎共享上下文，替代嵌套函数的闭包捕获"""
    client: "APIClient"
    system_prompt: str
    glossary: "Glossary"
    translation_db: "TranslationDB"
    args: argparse.Namespace
    all_warnings: list[str]       # 可变引用，多函数共享
    modified_lines: set[int]      # 可变引用，跨 chunk 追踪
```

迁移后的函数签名示例：

```python
# direct_translator.py

def _translate_chunk(
    ctx: TranslationContext,    # 替代闭包
    chunk_text: str,
    chunk_info: dict,
    prev_context: str,
) -> ChunkResult:
    # 原闭包变量 client → ctx.client
    # 原闭包变量 system_prompt → ctx.system_prompt
    ...
```

### 拆分方案（修订）

```
main.py (~2400 行)
  ├─ 保留：CLI 入口 + argparse + setup_logging + 路由 (~400 行)
  ├─ 迁移 → direct_translator.py (~800 行)
  │    ├─ translate_file(ctx, file_path, ...)   ← 接收 ctx 而非闭包
  │    ├─ _translate_file_targeted(ctx, ...)
  │    ├─ _translate_chunk(ctx, ...)             ← 不再是嵌套函数
  │    ├─ _translate_chunk_with_retry(ctx, ...)  ← 不再是嵌套函数
  │    ├─ ChunkResult dataclass
  │    └─ run_pipeline(args)                     ← 创建 ctx 并传递
  ├─ 迁移 → tl_translator.py (~600 行)
  │    ├─ run_tl_pipeline(args)
  │    ├─ build_tl_chunks(...)
  │    ├─ _build_fallback_dicts(...)
  │    └─ _match_string_entry_fallback(...)
  ├─ 迁移 → retranslator.py (~300 行)
  │    ├─ retranslate_file(...)
  │    ├─ find_untranslated_lines(...)
  │    └─ build_retranslate_chunks(...)
  └─ 迁移 → translation_utils.py (~250 行)
       ├─ TranslationContext dataclass           ← 新增
       ├─ ProgressTracker 类
       ├─ _restore_placeholders_in_translations()
       ├─ _strip_char_prefix() + _CHAR_PREFIX_RE
       ├─ _filter_checked_translations()
       ├─ _deduplicate_translations()
       └─ 常量：CHECKER_DROP_RATIO_THRESHOLD 等
```

### one_click_pipeline.py 同步更新

**实际决策**：保留 main.py re-export，one_click_pipeline.py 继续通过 `from main import ...` 引用。

理由：re-export 保证了所有 `from main import` 的向后兼容性，包括 test_all.py 和 one_click_pipeline.py。虽然方案原建议"直接改"，但实际验证表明 re-export 方案更稳妥，不破坏现有测试。

### 验证方法（修订）

1. `python test_all.py` — 53 个测试全通过
2. `python tests/smoke_test.py` — 13 个测试全通过
3. `python tl_parser.py --test` — 75 个断言全通过
4. `python main.py --game-dir tests/tl_priority_mini/game --provider xai --dry-run` — dry-run 正常
5. **新增**：`grep -rn "from main import" *.py` — 确认无残留的旧 import
6. 对比拆分前后 `wc -l` 总行数

### 风险控制（修订）

- ⚠️ 不再标记为"纯迁移"，明确标记为**闭包重构 + 迁移**
- TranslationContext 仅封装引用，不复制数据，`all_warnings` 和 `modified_lines` 使用可变引用确保共享
- 先写 TranslationContext，再逐个迁移函数，每迁移一个跑测试

---

## 阶段二（修订编号，原阶段三）：回写失败根因分析

### 前置条件确认

在实施分析之前，需确认 `translation_db.json` 中是否包含以下诊断字段：

| 字段 | 当前是否存在 | 若不存在的处理 |
|------|------------|--------------|
| `status="writeback_failed"` | ❓需确认 | 如果不存在该 status，需先在 `apply_translations` 中添加失败记录 |
| AI 返回的 `line`（行号） | ❓需确认 | 分析 WF-01 必需 |
| AI 返回的 `original`（原文） | 应该存在 | 分析 WF-02/03 必需 |
| 文件路径 | 应该存在 | 定位必需 |

**关键动作**：阶段二开始前，先 `view` 真实的 `translation_db.py` 和一个实际的 `translation_db.json` 样本，确认字段覆盖度。如果不足，第一步是增强数据采集，第二步才是分析。

### 两步实施策略

**步骤 A**（如果现有数据不足）：
1. 在 `file_processor/patcher.py` 的 `apply_translations` 匹配失败路径中，增加 diagnostic 记录
2. 用测试项目跑一次 direct-mode，采集完整的失败诊断数据
3. 产出：带 diagnostic 字段的 `translation_db.json`

**步骤 B**（分析）：
1. 运行 `analyze_writeback_failures.py`
2. 产出：分类统计报告
3. 根据真实数据决定阶段三的修复优先级

### 失败类型分类框架（不变）

| 类型代号 | 描述 | 判定条件 |
|---------|------|---------|
| `WF-01` | 行号偏移过大 | original 存在于文件但偏移 > ±3 行 |
| `WF-02` | 原文被截断 | AI 返回的 original 是文件中文本的子串 |
| `WF-03` | 原文被修改 | AI 返回的 original 与文件中任何行都不匹配 |
| `WF-04` | 引号嵌套冲突 | 原文含转义引号 `\"` 或嵌套引号 |
| `WF-05` | 跨行文本 | 原文跨越多行（含 `\n` 或三引号） |
| `WF-06` | 重复原文冲突 | 同一原文出现在多个位置，已被前面的匹配消费 |
| `WF-07` | 编码不一致 | Unicode 规范化差异 |
| `WF-08` | 其他 | 未归入以上类别 |

### 涉及文件

| 文件 | 改动类型 | 改动描述 |
|------|---------|---------|
| `analyze_writeback_failures.py` | 新增 | 分析脚本（~150 行） |
| `file_processor/patcher.py` | 增强 | 匹配失败时记录 diagnostic（如果现有数据不足） |
| `translation_db.py` | 增强 | diagnostic 字段支持（如果需要） |

---

## 阶段三（修订编号，原阶段四）：patcher 匹配增强

**内容不变**，但增加一条约束：

> **硬性前提**：必须在阶段二产出真实分类数据后才开始编码。如果实际数据显示 WF-01 占比 < 10%，则跳过"自适应搜索半径"改进，优先做占比最高的类型。

### difflib.SequenceMatcher 性能考量

review 指出第五遍全文模糊搜索可能在大文件上较慢。增加优化措施：

```python
# 第五遍仅对前四遍全部失败的条目执行
# 性能保护：文件 > 2000 行时，仅搜索 ±50 行范围（而非全文）
MAX_FUZZY_SEARCH_LINES = 2000
FUZZY_SEARCH_RADIUS = 50

def _fuzzy_match_fallback(
    ai_original: str,
    file_lines: list[str],
    ai_line: int,
) -> int | None:
    if len(file_lines) > MAX_FUZZY_SEARCH_LINES:
        # 大文件：限制搜索范围
        start = max(0, ai_line - FUZZY_SEARCH_RADIUS)
        end = min(len(file_lines), ai_line + FUZZY_SEARCH_RADIUS)
        search_range = range(start, end)
    else:
        search_range = range(len(file_lines))
    
    best_ratio = 0.0
    best_line = None
    for i in search_range:
        # 提取引号内文本再比较（跳过代码行）
        quoted = _extract_quoted_text(file_lines[i])
        if not quoted:
            continue
        ratio = difflib.SequenceMatcher(None, ai_original, quoted).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_line = i
    
    return best_line if best_ratio >= 0.85 else None
```

---

## 阶段四（修订编号，原阶段五）：config.json

### Config.get() 逻辑修订

review 指出"区分默认值 vs 用户传入"较复杂。采用建议：argparse 全部设为 `default=None`，三层合并。

```python
# main.py argparse 修改
parser.add_argument('--workers', type=int, default=None)  # 原 default=1
parser.add_argument('--rpm', type=int, default=None)      # 原 default=60
# ...

# config.py 合并逻辑
DEFAULTS = {
    "workers": 1,
    "rpm": 60,
    "rps": 5,
    "timeout": 180.0,
    "temperature": 0.1,
    "max_chunk_tokens": 4000,
    "genre": "adult",
    "target_lang": "zh",
    "min_dialogue_density": 0.20,
    # ...
}

class Config:
    def get(self, key: str) -> Any:
        """三层合并：CLI(非None) > 配置文件 > DEFAULTS"""
        cli_val = getattr(self._cli_args, key, None)
        if cli_val is not None:
            return cli_val
        if key in self._file_config:
            return self._file_config[key]
        return DEFAULTS.get(key)
```

这样 argparse 的 `default=None` 天然区分了"用户传入"和"未传入"，无需猜测。

### .gitignore 建议

```
# 用户配置（不提交）
renpy_translate.json

# 示例配置（提交）
# renpy_translate.example.json  ← 不忽略
```

---

## 阶段五（修订编号，原阶段六）：Review HTML + 进度增强

### ProgressBar GBK 兼容修订

```python
class ProgressBar:
    def __init__(self, total: int, width: int = 40):
        self.total = total
        self.width = width
        self.current = 0
        self.cost = 0.0
        self._start_time = time.time()
        # 检测终端编码，GBK/CP936 下使用 ASCII fallback
        self._use_unicode = self._detect_unicode_support()
    
    def _detect_unicode_support(self) -> bool:
        """检测终端是否支持 Unicode 进度条字符"""
        try:
            encoding = sys.stderr.encoding or ''
            if encoding.lower() in ('utf-8', 'utf8'):
                return True
            # 尝试编码测试字符
            '█░'.encode(encoding)
            return True
        except (UnicodeEncodeError, LookupError):
            return False
    
    def _render(self) -> None:
        pct = self.current / self.total if self.total > 0 else 0
        filled = int(self.width * pct)
        if self._use_unicode:
            bar = '█' * filled + '░' * (self.width - filled)
        else:
            bar = '#' * filled + '-' * (self.width - filled)  # ASCII fallback
        elapsed = time.time() - self._start_time
        eta = (elapsed / self.current * (self.total - self.current)) if self.current > 0 else 0
        sys.stderr.write(
            f"\r[{bar}] {pct:.0%} | {self.current}/{self.total} "
            f"| ${self.cost:.2f} | ETA {eta/60:.0f}min"
        )
        sys.stderr.flush()
```

---

## 阶段六（修订编号，原阶段二）：类型注解

### 修订说明

- **推迟原因**：签名需对照真实代码逐个核实，且 mypy 初期为 informational
- **实施方式**：在阶段一拆分后，对每个新模块逐个添加注解。此时代码已稳定，不会被后续阶段频繁修改
- **签名核实**：实施时必须先 `view` 每个函数的真实代码，不凭记忆写签名
- 方案中的签名示例全部标记为 **[待核实]**，不作为实施依据

---

## 阶段七+八（修订）：多语言支持 — 增加风险防护

### 风险防护一：Prompt 语言保护

```python
# prompts.py 修订方案

def build_system_prompt(
    genre: str, glossary: Glossary, project_name: str,
    lang_config: LanguageConfig,
) -> str:
    if lang_config.code in ("zh", "zh-tw"):
        # 中文目标：保持现有中文 prompt 原样不动
        # 这是经过验证的 prompt，改动会影响 99.99% 的翻译精度
        return _build_chinese_system_prompt(genre, glossary, project_name, lang_config)
    else:
        # 非中文目标：使用英文基础模板
        return _build_generic_system_prompt(genre, glossary, project_name, lang_config)

def _build_chinese_system_prompt(genre, glossary, project_name, lang_config):
    """保持现有中文 prompt 逻辑不变"""
    # 现有的 SYSTEM_PROMPT_TEMPLATE.format(...) 逻辑原样保留
    # 仅替换"简体中文"为 lang_config.native_name（用于繁体中文）
    ...

def _build_generic_system_prompt(genre, glossary, project_name, lang_config):
    """新增的通用英文 prompt 模板"""
    ...
```

**核心原则**：`--target-lang zh` 时的 prompt 输出必须与当前版本逐字节一致（除了术语表动态内容）。

### 风险防护二：Glossary 字段兼容性

```python
# glossary.py 修订方案

class Glossary:
    # 读取时兼容旧字段名
    _FIELD_ALIASES = {
        "zh": ["zh", "chinese", "cn"],
        "ja": ["ja", "japanese", "jp"],
        "ko": ["ko", "korean", "kr"],
        "zh-tw": ["zh-tw", "zh_tw", "traditional_chinese"],
    }
    
    def _resolve_translation_field(self, item: dict, lang_code: str) -> str | None:
        """兼容读取：尝试多个字段名"""
        aliases = self._FIELD_ALIASES.get(lang_code, [lang_code])
        for alias in aliases:
            if alias in item:
                return item[alias]
        # 兜底：尝试 "translation" / "target" 通用字段名
        for generic in ("translation", "target", "trans"):
            if generic in item:
                return item[generic]
        return None
```

API 返回的 JSON 中翻译字段的读取同样使用此兼容逻辑，这样即使 AI 返回 `"zh"` 而非 `"ja"`，也能通过 fallback 读取。

### 回归验证（新增）

阶段八完成后，必须执行以下回归测试：

```bash
# 1. 中文 prompt 一致性验证
python -c "
from prompts import build_system_prompt
from glossary import Glossary
from lang_config import LANGUAGE_CONFIGS
g = Glossary()
# 生成当前版本 prompt
prompt_new = build_system_prompt('adult', g, 'test', LANGUAGE_CONFIGS['zh'])
# 与 git HEAD~1 版本对比（或保存基线）
assert prompt_new == BASELINE_PROMPT, 'Chinese prompt changed!'
"

# 2. 全部现有测试通过
python test_all.py && python tests/smoke_test.py && python tl_parser.py --test
```

---

## 新增文件清单（修订）

| 文件 | 阶段 | 描述 | 预估行数 |
|------|------|------|---------|
| `direct_translator.py` | 1 | direct-mode 引擎 | ~800（迁移+重构） |
| `tl_translator.py` | 1 | tl-mode 引擎 | ~600（迁移） |
| `retranslator.py` | 1 | 补翻引擎 | ~300（迁移） |
| `translation_utils.py` | 1 | 公共辅助 + TranslationContext + ProgressTracker + ProgressBar | ~350（迁移+新增） |
| `analyze_writeback_failures.py` | 2 | 回写失败分析工具 | ~150 |
| `config.py` | 4 | 配置文件管理 | ~150 |
| `renpy_translate.example.json` | 4 | 示例配置 | ~25 |
| `review_generator.py` | 5 | HTML 校对报告 | ~200 |
| `py.typed` | 6 | PEP 561 marker | 0 |
| `lang_config.py` | 7 | 语言配置 | ~200 |

---

## 修订后里程碑

| 里程碑 | 完成阶段 | 验收标准 |
|--------|---------|---------|
| **M1: 结构现代化** | 1 | **已达成** main.py 233 行（< 500 ✓）；拆分为 5 模块 + re-export 兼容；TranslationContext 替代闭包（`_translate_chunk` / `_should_retry` / `_translate_chunk_with_retry` / `_translate_one_tl_chunk` 已提升为模块级函数）；53 测试全通过 ✓ |
| **M2: 漏翻率优化** | 2+3 | **已达成** 回写失败 609→28 条（-95%）；前缀剥离+转义引号修复；测试 53→55 |
| **M3: 用户体验** | 4+5 | **已达成** 配置文件正常加载（3测试）+ ProgressBar（GBK安全）+ review.html 正常渲染（60 测试全通过） |
| **M4: 类型安全** | 6 | **已达成** 全部公共 API 注解 + py.typed + CI mypy informational |
| **M5: 多语言** | 7+8 | **已达成** LanguageConfig 抽象层 + 英文通用模板 + validator 参数化 + `--target-lang ja` 可生成日文 prompt；**中文 prompt 逐字节不变** ✓ |

---

## 修订变更汇总

| 项目 | 原方案 | 修订后 |
|------|--------|--------|
| 执行顺序 | 1→2→3→4→5→6→7→8 | **1→3→4→5→6→2→7→8**（类型注解推迟） |
| 阶段一复杂度 | "纯迁移" | **闭包重构 + 迁移**（TranslationContext） |
| 阶段二签名 | 凭记忆写 | 标记 **[待核实]**，实施时必须对照源码 |
| 阶段七 Prompt | 统一英文模板 | **中文保持不动**，非中文用英文模板 |
| 阶段八 Glossary | 字段名替换 | **兼容读取**旧字段名 + fallback |
| 进度条 | Unicode only | **ASCII fallback**（GBK 兼容） |
| Config.get() | 猜测默认值 | **argparse default=None** + 三层合并 |
| re-export | main.py 保留 | **直接更新** one_click_pipeline import |
| 回归验证 | 无 | 新增 **prompt 一致性验证**脚本 |
