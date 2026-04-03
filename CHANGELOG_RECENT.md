<!-- 维护规则：每完成新一轮开发后，把最新轮次追加到"详细记录"段，
     同时把最老的一轮从"详细记录"压缩为一行并入"演进摘要"。
     始终保持最近 3 轮的详细记录。 -->

# 变更日志（精简版）

## 项目演进摘要

- 第一轮：质量校验体系 — W430/W440/W441/W442/W251 告警 + E411/E420 术语锁定
- 第二轮：功能增强 — 结构化报告 + translation_db + 字体补丁
- 第三轮：降低漏翻率 — 12.12% → 4.01%（占位符保护 + 密度自适应 + retranslate）
- 第四轮：tl-mode — 独立 tl_parser + 并发翻译 + 精确回填
- 第五轮：tl-mode 全量验证 — 引号剥离修复 + 99.97% 翻译成功率
- 第六轮：代码优化 — chunk 重试 + logging + 模块拆分 + 术语提取
- 第七轮：全量验证 — 99.99% 成功率（未翻译 25→7，Checker 丢弃 4→2）
- 第八轮：代码质量 — 消除重复 + 大函数拆分 + validator 结构化 + 测试 36→42
- 第九轮：深度优化 — 线程安全 + O(1) fallback + API 错误处理 + 测试 42→50
- 第十轮：功能加固 — 控制标签确认 + CI 零依赖 + 跨平台路径 + 测试 50→53
- 第十一轮：main.py 拆分 — 2400→233 行 + Config 类 + Review HTML + 类型注解 + 多语言
- 第十二轮：引擎抽象层 — EngineProfile + EngineBase + RPG Maker MV/MZ + CSV/JSONL + GUI
- 第十三轮：四项优化 — pipeline review.html + 可配置字体 + tl/none 模板 + CoT
- 第十四轮：Ren'Py 专项 — 五阶段升级（基础重构 + 健壮性 + 性能 + 质量 + 体验）
- 第十五轮：nvl clear ID 修正 — 8.6+ say-only → 7.x nvl+say 哈希自动修正
- 第十六轮：screen 文本翻译 — screen_translator.py + 缓存清理 .rpymc 补全

## 详细记录

### 第十七轮：项目结构深度重构
190. 根目录 25→5 .py：core/(7模块) + translators/(6模块) + tools/(扩充3模块)
191. 消除 re-export 兼容层 + 循环依赖
192. 162 测试全绿零回归

### 第十八轮：预处理工具链 + 翻译增强
193-198. `tools/rpa_unpacker.py`（RPA-3.0/2.0 解包）+ `tools/rpyc_decompiler.py`（双层反编译）+ `tools/renpy_lint_fixer.py`（lint 集成 + 自动修复）
199-203. `--file-workers` 文件级并行 + locked_terms 预替换 + tl-mode 跨文件去重
204-206. Hook 模板：`extract_hook.rpy` + `language_switcher.rpy`
207-209. 测试 162→225（test_rpa_unpacker 14 + test_rpyc_decompiler 17 + test_lint_fixer 15 + test_tl_dedup 10）

### 第十九轮：翻译后工具链 + 插件系统
210. `tools/rpa_packer.py`（RPA-3.0 纯标准库打包 + 自动收集 + 往返验证）
211. `tools/translation_editor.py`（HTML 交互式校对：导出/浏览器编辑/JSON 导入回写）
212. 自定义翻译引擎插件（`custom_engines/` + 双层接口 + 安全限制）+ `--provider custom --custom-module`
213. 默认语言设置（`default_language.rpy` 自动生成，集成到流水线）
214. Lint 修复流水线集成（`_run_lint_repair_phase` + `--no-lint-repair`）
215. JSON 解析失败拆分重试（`_should_retry` 新增 returned==0 判断）
216-218. 测试 225→266（test_batch1 18 + test_translation_editor 13 + test_custom_engine 11）

## 已回滚

- prompt 强制覆盖指令（CRITICAL RULE）— 降低 AI 返回率 5pp，已撤回
