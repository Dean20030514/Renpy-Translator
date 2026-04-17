# 贡献指南

感谢考虑向本项目贡献代码。本指南汇总了开发环境、工作流、检查清单与提交规范，确保改动不破坏现有稳定性与既定原则。

---

## 环境要求

- **Python**：3.9 或更高
- **第三方依赖**：**零**。坚持纯标准库，PR 中引入任何 `requirements` 或 `pip install` 调用会被驳回
- **OS**：开发主要在 Windows 上进行，但代码需保证 Linux / macOS 也能跑通测试
- **编码**：所有 `.py` / `.md` 文件使用 UTF-8（无 BOM）

---

## 九大开发原则（摘自 `CLAUDE.md`）

任何 PR 必须遵守以下原则：

1. **宁可漏翻也不误翻** — 不确定的条目保留原文，不要硬塞翻译
2. **数据驱动** — 改动前收集数据，改动后验证数据，不拍脑袋定阈值
3. **隔离变量** — 每次只改一个东西，验证独立效果
4. **不破坏已有功能** — 新功能用 CLI 开关控制，默认行为不变
5. **安全优先** — checker 不通过就丢弃、回写前校验、原地操作前备份
6. **先读再写** — 涉及参考项目借鉴时，先完整阅读源码和文档再给方案
7. **方案先行** — 给出改动方案和受影响函数列表，等维护者确认后再写代码
8. **最小改动** — 不做不必要的重构、不加不需要的注释、不改不相关的代码
9. **零依赖** — 坚持纯标准库，不引入第三方包

---

## 工作流

### 1. 开 issue / 讨论方案

对于非 trivial 的改动（修复超过 20 行，或新增功能），**先开 issue 讨论方案**，不要直接发 PR。按 Issue 模板列出：

- 改动目的
- 受影响的模块 / 函数 / 文件
- 兼容性影响（是否改变默认行为）
- 测试策略

### 2. 分支策略

- 从 `main` 创建特性分支，命名格式 `feat/xxx` 或 `fix/xxx`
- 一个 PR 只做一件事（遵循"隔离变量"原则）

### 3. 开发

遵循[修改代码前的检查清单](#修改代码前的检查清单)逐项核对。

### 4. 测试

**运行测试套件**：

```bash
python tests/test_all.py              # 核心单元测试（95 用例）
python tests/test_engines.py          # 引擎层测试（62 用例）
python tests/test_rpa_unpacker.py     # RPA 解包（14 用例）
python tests/test_rpyc_decompiler.py  # rpyc 反编译（17 用例）
python tests/test_lint_fixer.py       # lint 修复（15 用例）
python tests/test_tl_dedup.py         # tl 去重（10 用例）
python tests/test_batch1.py           # 批次功能（18 用例）
python tests/test_translation_editor.py # 交互式校对（13 用例）
python tests/test_custom_engine.py    # 插件系统（11 用例）
python tests/smoke_test.py            # 冒烟测试（13 用例）
```

**测试要求**：

- 全部测试必须绿，不允许 "测试个别失败但不影响主流程" 的 PR
- 修 bug 必须先补回归测试，再改实现（RED → GREEN → IMPROVE）
- 新增功能至少覆盖 happy path + 1 个边界 / 错误路径

### 5. 提交

**提交信息格式**（Conventional Commits）：

```
<type>: <description>

<optional body>
```

`type` 可以是：`feat` / `fix` / `refactor` / `docs` / `test` / `chore` / `perf` / `ci` / `security`。

示例：

- `fix: pipeline 子包反向 import 修正，恢复一键流水线 Stage 3`
- `security: SafeUnpickler 白名单替换 pickle.loads，关闭 RPA/rpyc pickle RCE 向量`
- `feat: RPG Maker VX/Ace 引擎初步支持（需 Ruby Marshal 解析）`

### 6. 更新 CHANGELOG

改动合入前必须更新 `CHANGELOG_RECENT.md`：

- 小改动追加到最近一轮
- 大改动（新增模块 / 引擎 / 工具）新开一轮

---

## 修改代码前的检查清单

PR 描述中必须逐项勾选：

- [ ] 已列出要修改的文件和函数
- [ ] 未引入任何第三方依赖
- [ ] 未改变任何默认行为，或新增功能由 CLI 开关控制
- [ ] 所有新增 / 修改的函数有类型注解
- [ ] 有对应的测试用例
- [ ] 原地修改文件前有 `.bak` 备份逻辑（如适用）
- [ ] checker 不通过的翻译被丢弃（而非强行使用）
- [ ] 更新了 `CHANGELOG_RECENT.md`
- [ ] `python tests/test_all.py` 及相关测试全绿

---

## 代码风格

- Python：PEP 8
- 命名：函数 / 变量用 `snake_case`，类用 `PascalCase`，常量 `UPPER_SNAKE_CASE`
- 类型注解：公共函数签名必须有（内部辅助函数推荐）
- 注释：解释**为什么**这么做，不解释**做了什么**（代码本身表达）
- 文档字符串：所有公共函数和类必须有 docstring
- 文件大小：单文件控制在 800 行以内，超过需要拆分

---

## 引入新引擎

如果计划新增一个引擎（例如 Wolf RPG、Godot），请：

1. 先阅读 `docs/engine_guide.md`
2. 在 `docs/roadmap.md` 中找到对应的 P1/P2/P3 定位
3. 实现 `engines/<name>_engine.py`，继承 `EngineBase` + 定义 `EngineProfile`
4. 在 `engines/engine_detector.py` 中注册
5. 配套 `tests/test_engines.py` 补测试
6. 更新 README 的引擎支持列表

---

## 报告安全问题

**不要** 通过公开 issue 报告安全漏洞。请参照 [`SECURITY.md`](SECURITY.md) 的流程。

---

## 其他

- 按需加载文档索引见 `CLAUDE.md` 顶部
- 历史决策见 `CHANGELOG_RECENT.md`（最近 3 轮）和 `_archive/CHANGELOG_FULL.md`（全量）
- 架构 / 数据流图见 `docs/` 下 7 个专题文档
