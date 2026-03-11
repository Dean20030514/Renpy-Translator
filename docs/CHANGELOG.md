# 更新日志

所有重要变更记录在此文件中。格式基于 [Keep a Changelog](https://keepachangelog.com/)。

---

## [3.0.0] — 2026-03

### 新增
- **RPA 解包**：`unrpa.py` 支持 RPA-2.0/3.0 存档解包，多线程(12)，`--scripts-only` 过滤
- **运行时 Hook 生成**：`gen_hooks.py` 生成 4 种 Hook 脚本
  - 语言切换器 Hook：注入游戏首选项菜单
  - 字体配置 Hook：自动设置中文字体
  - RPYC 提取 Hook：运行时提取 .rpyc 为 .rpy
  - 默认语言 Hook：设置启动语言
- **三级速率限制**：`RateLimiter` 支持 RPM/RPS/TPM 精确限速
- **批量 JSON 翻译模式**：`--batch-mode --batch-size` 合并多条为单次 API 请求
- **递归批次分裂**：API 失败时自动递归拆分重试
- **自定义 Prompt 模板**：`--prompt-template` 加载 JSON 格式提示词模板
- **屏幕文本提取**：extract.py 自动识别 screen 块中的 UI 文本（按钮/标签/tooltip）
- **断点续传**：translate.py 和 pipeline.py 支持 `--resume` 从中断处继续
- **翻译记忆引擎**：`--tm` 参数加载翻译记忆，精确/模糊匹配
- **翻译质量评分**：`quality_score()` 对译文自动打分
- **上下文窗口打包**：相邻台词捆绑提供角色上下文
- **角色语气绑定**：翻译时保持角色特有的语气和措辞
- **英文残留上下文检测**：感知纯英文名词不误报为残留
- **智能换行修复**：autofix 保持原文换行结构
- **术语一致性校验**：字典术语不一致自动报警 + 修复
- **merge.py 质量冲突解决**：多翻译源合并时按质量评分选择最优
- **validate.py --autofix**：校验时直接修复常见问题
- **extract.py 失败文件追踪**：提取失败的文件单独记录
- **patch.py --resume**：回填支持断点续传
- **菜单新功能**：menu.ps1 新增 RPA 解包 / Hook 生成 / 构建中文包 / 字体替换 / 中英对比 / TM 构建（18 项功能）
- **build_memory.py**：新增 TM 构建 CLI 工具，支持从 JSONL 和 tl 目录构建翻译记忆
- **pipeline.py 集成**：`--unrpa` / `--gen-hooks` / `--font` 全流程串联
- **build.py 集成**：`--gen-hooks` / `--font` / `--rtl` 一步构建含 Hook 的中文包
- **PACKAGE.bat 修复**：便携包正确包含 `src/` 目录

### 改进
- translate_api.py 支持 `--rpm` / `--rps` / `--tpm` 速率限制参数
- translate_api.py 支持 `--prompt-template` 自定义提示词
- launcher.ps1 构建步骤自动生成 Hook
- menu.ps1 升级到 v3.0，新增辅助工具分类
- 代码质量：消除未使用导入/变量，预编译正则，精确异常捕获
- 133 个测试全部通过

## [0.2.0] — 2025-01

### 新增
- 云端 API 翻译支持（DeepSeek / Grok / OpenAI / Claude）
- 免费机器翻译支持（Google / Bing / DeepL）
- 交互式菜单界面（`START.bat` / `menu.ps1`）
- 翻译记忆 (TM) 引擎，支持精确/模糊匹配
- SQLite KV 缓存，避免重复翻译
- 多级质量检查（`MultiLevelValidator`）
- 自适应速率控制（API 调用限速）
- 英文残留检测与修复工具（`fix_english_leakage.py`）
- 字体替换工具（`replace_fonts.py`）
- 一键安装脚本（`INSTALL_ALL.bat` / `smart_installer.ps1`）
- 一键流水线（`pipeline.py`）
- 术语字典生成工具（`generate_dict.py`）
- Rich 彩色日志和进度条
- 语义占位符签名（`placeholder.py`）
- VS Code Tasks 集成（`.vscode/tasks.json`）

### 改进
- CLI 统一入口 `renpy-tools <command>`
- 翻译 prompt 优化，减少过翻和漏翻
- 批次分割支持按 token 数计算
- QA 报告输出 JSON / TSV / HTML 三种格式
- 回填支持多工作线程并行

### 修复
- 占位符检测遗漏嵌套标签的问题
- JSONL 编码探测在 GBK 文件上的错误
- 合并冲突时保留最优翻译

---

## [0.1.0] — 2024

### 新增
- 基础文本提取（`extract.py`）
- Ollama 本地翻译（`translate.py`）
- 字典预填充（`prefill.py`）
- 翻译验证（`validate.py`）
- 自动修复（`autofix.py`）
- RPY 回填（`patch.py`）
- 游戏包构建（`build.py`）
