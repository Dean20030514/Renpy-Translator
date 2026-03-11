# 开发指南

本文档介绍项目架构、模块关系、代码规范和贡献流程。

---

## 项目架构

```
renpy-tools/
├── src/renpy_tools/          # 核心库（pip install -e .）
│   ├── __init__.py            # 版本号、公开 API
│   ├── cli.py                 # 统一 CLI 入口 (renpy-tools <cmd>)
│   ├── core/                  # 核心功能模块
│   │   ├── translator.py      #   OllamaTranslator — 本地 AI 翻译
│   │   ├── validator.py       #   MultiLevelValidator — 多级质量检查
│   │   └── patcher.py         #   SafePatcher — 安全回填 .rpy
│   ├── diff/                  # Diff 比对模块
│   │   └── parser.py          #   RPY 解析器（Dialogue / Block / ParsedFile）
│   └── utils/                 # 工具函数
│       ├── common.py          #   JSONL 读写、文本规范化、占位符正则
│       ├── cache.py           #   SQLite KV 缓存
│       ├── config.py          #   配置管理（ConfigManager）
│       ├── dict_utils.py      #   字典加载 / 匹配
│       ├── io.py              #   编码探测、文件读写
│       ├── logger.py          #   Rich 日志 + 自定义异常
│       ├── placeholder.py     #   占位符抽取 / 还原 / 语义签名
│       ├── prompts.py         #   翻译 prompt 模板 + load_prompt_template()
│       ├── rate_limiter.py    #   三级速率限制器（RPM/RPS/TPM）
│       ├── tm.py              #   翻译记忆 (TM) 引擎
│       └── ui.py              #   交互式 UI 辅助
│
├── tools/                     # 独立 CLI 脚本（可直接 python tools/xxx.py）
│   ├── extract.py             #   提取 .rpy 文本 → JSONL（含 screen 文本）
│   ├── prefill.py             #   字典预填充
│   ├── split.py               #   JSONL 分批（按 token 数）
│   ├── translate.py           #   Ollama 本地翻译（--resume / --tm / --use-optimized）
│   ├── translate_api.py       #   通用 API 翻译（速率限制 / 批量模式 / 自定义 prompt）
│   ├── translate_grok.py      #   Grok API 翻译
│   ├── translate_free.py      #   免费机翻（Google/Bing/DeepL）
│   ├── merge.py               #   合并多批次翻译结果（质量评分冲突解决）
│   ├── validate.py            #   翻译质量验证 → QA 报告（--autofix）
│   ├── autofix.py             #   自动修复占位符 / 格式 / 英文残留
│   ├── patch.py               #   将译文回填 .rpy（--resume 断点续传）
│   ├── build.py               #   构建中文版游戏包（--gen-hooks / --font / --rtl）
│   ├── gen_hooks.py           #   生成运行时 Hook 脚本（语言切换/字体/提取/默认语言）
│   ├── unrpa.py               #   RPA 存档解包（RPA-2.0/3.0，--scripts-only）
│   ├── pipeline.py            #   一键流水线（--resume / --unrpa / --gen-hooks）
│   ├── diff_dirs.py           #   中英 RPY 目录对比
│   ├── replace_fonts.py       #   替换游戏字体为中文字体
│   ├── fix_english_leakage.py #   检测 / 修复英文残留
│   ├── generate_dict.py       #   从已翻译 JSONL 生成术语字典
│   ├── build_memory.py        #   构建翻译记忆 (TM)
│   └── test_api_simple.py     #   API 连通性测试
│
├── tests/                     # pytest 测试（133 个）
│   ├── conftest.py            #   共享 fixtures
│   ├── test_core_modules.py   #   核心模块单元测试
│   ├── test_dict_utils.py     #   字典工具测试
│   ├── test_diff_parser.py    #   RPY 解析器测试
│   ├── test_diff_menu.py      #   菜单 / 选项解析测试
│   ├── test_integration.py    #   集成测试
│   ├── test_new_features.py   #   新特性回归测试
│   └── test_translate_integration.py  # 翻译集成测试
│
├── data/                      # 数据文件
│   ├── dictionaries/          #   术语字典
│   │   ├── common_terms.csv   #     CSV 格式
│   │   └── common_terms.jsonl #     JSONL 格式
│   ├── fonts/                 #   中文字体文件
│   └── prompt_template.json   #   自定义 Prompt 模板（OpenAI 格式）
│
├── docs/                      # 文档
├── outputs/                   # 运行时输出（git-ignored）
└── pyproject.toml             # 构建配置
```

## 模块关系

```
CLI 入口 (cli.py / tools/*.py)
    │
    ├── core.translator ──→ utils.prompts（prompt 模板 + 自定义模板加载）
    │                   ──→ utils.common（JSONL/占位符）
    │                   ──→ utils.cache（翻译缓存）
    │                   ──→ utils.rate_limiter（RPM/RPS/TPM 限速）
    │
    ├── core.validator  ──→ utils.common（占位符正则、文本规范化）
    │                   ──→ utils.placeholder（语义签名）
    │
    ├── core.patcher    ──→ utils.io（编码探测）
    │                   ──→ utils.common（ID 查找）
    │
    ├── diff.parser     ──→ 独立解析，无外部依赖
    │
    ├── tools/unrpa.py  ──→ 独立 RPA 解包，无核心库依赖
    │
    └── tools/gen_hooks.py ──→ 独立 Hook 生成，无核心库依赖
```

## 数据流

```
[RPA 存档] (可选)
    → unrpa.py → 解包 .rpy/.rpyc 文件

.rpy 文件
    → extract.py → JSONL（每行一条文本：id + en，含 screen 文本标记）
    → prefill.py → 字典预填 zh 字段
    → split.py   → 分批 JSONL
    → translate*.py → 填充 zh 字段（支持速率限制 + 批量模式）
    → merge.py   → 合并各批次（质量评分冲突解决）
    → validate.py → QA 报告（可选 --autofix）
    → autofix.py → 自动修复
    → patch.py   → 回填 .rpy（支持 --resume）
    → build.py   → 打包中文版（可含 Hook 脚本）
```

---

## 开发环境搭建

```bash
# 1. 克隆项目
git clone <repo-url>
cd renpy-tools

# 2. 创建虚拟环境
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/macOS

# 3. 安装开发依赖
pip install -e ".[all,dev]"

# 4. 安装 pre-commit hooks
pip install pre-commit
pre-commit install
```

## 代码规范

- **格式化 / Lint**：ruff（配置见 `pyproject.toml`）
- **导入排序**：isort（isort profile = ruff）
- **Python 版本**：≥ 3.10，使用 `from __future__ import annotations`
- **类型注解**：公共 API 必须有类型注解
- **日志**：使用 `utils.logger.get_logger(__name__)`，不要用 `print()`
- **异常**：使用 `utils.logger` 中定义的自定义异常类

## 测试

```bash
# 运行全部测试
pytest

# 运行指定文件
pytest tests/test_core_modules.py

# 运行指定测试
pytest tests/test_core_modules.py::test_validator_check_placeholders -v

# 生成覆盖率报告
pytest --cov=src/renpy_tools --cov-report=html
```

测试约定：
- 文件名以 `test_` 开头
- 函数名以 `test_` 开头
- 使用 `conftest.py` 中的共享 fixtures（`project_root_path`、`tools_path` 等）
- 不使用 `sys.path.insert()`，依赖 `pyproject.toml` 中的 `pythonpath` 配置

## 提交规范

```
<type>: <简要描述>

type 可选值:
  feat     新功能
  fix      修复
  docs     文档
  refactor 重构
  test     测试
  chore    构建/CI/配置
```

## CI

GitHub Actions（`.github/workflows/ci.yml`）：
- **lint-test**：ruff lint + pytest（Python 3.10–3.13 × ubuntu/windows/macos）
- **e2e-demo**：端到端演示（提取 → 预填充 → 验证）

---

## 发布流程

1. 更新 `pyproject.toml` 和 `src/renpy_tools/__init__.py` 中的版本号
2. 更新 `docs/CHANGELOG.md`
3. 提交并打 tag：`git tag v0.x.0`
4. 推送：`git push && git push --tags`
