# 常见问题排查 Troubleshooting

本文汇总了在 Windows + PowerShell 环境下使用本工具链时的常见问题与解决方案。

## 构建失败：检测到双载或残留 .zh.rpy

症状：`build.py` 报错，提示镜像模式与 TL 模式互斥或检测到 `.zh.rpy` 残留。

解决：

- 如果使用镜像模式（推荐），请确保项目目录中不含 `.tl/zh_CN` 文件夹；
- 如果使用 TL 模式，请不要提供 `--zh-mirror`；
- 清理旧的 `*.zh.rpy` 或 `.tl/zh_CN` 后重试。

## 预填失败：sqlite3 不可用或报错

症状：使用 `--dict-backend sqlite` 时异常（极少见）。

解决：

- 改用内存模式：去掉 `--dict-backend sqlite` 即可；
- 或更换 Python 发行版（标准发行版一般内置 sqlite3）。

## 可选依赖未安装

症状：

- `--ac-ui-substrings` 提示缺少 `pyahocorasick`；
- `split_jsonl_for_llm.py` 提示缺少 `tiktoken`。

解决：

- 这些功能是可选项，未安装时会自动降级；
- 如需开启，请在你的环境中安装对应包后重试。

## QA 报告不包含 HTML

原因：默认只输出 JSON/TSV。需显式传入 `--qa-html PATH`。

示例（PowerShell）：

```pwsh
python tools/validate.py outputs/extract/project_en_for_grok.jsonl outputs/prefilled/prefilled.jsonl --qa-json outputs/qa/qa.json --qa-tsv outputs/qa/qa.tsv --qa-html outputs/qa/qa.html
```

## 中文/英文间距、全角/半角问题很多

说明：QA 会对中英混排空格、全角/半角标点进行提示（WARN）。可在回填前先统一标点与空格，或在词典中加入规范写法以减少重复修复。

## 性能问题：慢或占用内存高

建议：

- 提取/回填时启用并发：`--workers auto`；
- 根据机器内存设置合适的 `--chunk-size`；
- 预填使用 `--dict-backend sqlite` 以避免载入超大字典到内存。

## 编码/路径包含中文

- 本工具链使用 UTF-8；建议在 Git/编辑器中统一为 UTF-8；
- PowerShell 路径请加引号，例如：`"e:/项目/demo"`；
- `.rpy` 建议使用 UTF-8（无 BOM/有 BOM均可，Ren'Py 能识别）。

## 菜单不一致/缺失台词报告

- 如果报告菜单项缺失或跳转目标不一致，请检查 EN/CN 两侧 `menu:` 下的选项文本与 `jump/call` 目标；
- 缺失的菜单文本会计入“缺失台词报告”，请在翻译 JSONL 中补齐对应项。

## VS Code 任务的常见参数

- Extract：项目根、glob、排除目录；支持并发（脚本参数 `--workers auto` 已支持）。
- Prefill：源 JSONL、字典目录、输出；可选 `--dict-backend sqlite`。
- Validate：源 EN JSONL、译文 JSONL、QA 输出路径。
- Patch：项目根、译文 JSONL、输出目录；高级模式 `--advanced` 默认开启 TL 分文件输出。
- Build：项目根、输出目录、`--zh-mirror` 指向镜像译文目录、语言 `zh_CN`。

若遇到未覆盖的问题，请附上报错栈与命令行参数开 Issue。
