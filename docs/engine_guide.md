> 仅在新增引擎支持时加载此文档。

# 新增引擎开发指南

## 核心设计原则

1. **Ren'Py 代码零改动**：现有三条管线不重构，通过薄包装类接入新架构
2. **浅抽象、参数化差异**：只抽象 I/O 层（提取/回写），翻译中间流程通用。引擎差异通过 `EngineProfile` 参数化，非继承多态
3. **零依赖约束不破坏**：核心框架 + RPG Maker MV/MZ + CSV 全部标准库。第三方库引擎作为可选功能
4. **最小新增文件**：整个抽象层新增 ~7 个文件，不改现有结构

## EngineProfile 数据类

引擎差异的参数化描述，让 `protect_placeholders()` 和 `validate_translation()` 根据引擎调整行为。

| 字段 | 类型 | 用途 |
|------|------|------|
| `name` | `str` | 引擎标识符（`"renpy"` / `"rpgmaker_mv"` / `"csv"`） |
| `display_name` | `str` | 用户可见名称 |
| `placeholder_patterns` | `list[str]` | 占位符正则列表，用于 `protect_placeholders` 参数化 |
| `skip_line_patterns` | `list[str]` | 不翻译的行模式正则 |
| `encoding` | `str` | 文件默认编码 |
| `max_line_length` | `int \| None` | 译文行宽限制 |
| `prompt_addon_key` | `str` | 引擎专属 prompt 片段查找 key |
| `supports_context` | `bool` | 提取时是否提供上下文行 |
| `context_lines` | `int` | 上下文行数（默认 3） |

辅助方法：`compile_placeholder_re()` / `compile_skip_re()` 将列表编译为单个正则。

内置 Profile：`RENPY_PROFILE`、`RPGMAKER_MV_PROFILE`、`CSV_PROFILE`，注册在 `ENGINE_PROFILES` 字典中。

## TranslatableUnit 数据类

所有非 Ren'Py 引擎共用的文本单元（Ren'Py 有自己的 DialogueEntry / StringEntry 体系）。

| 字段 | 类型 | 用途 |
|------|------|------|
| `id` | `str` | 全局唯一标识（RPG Maker: JSON path，CSV: 行号/ID 列） |
| `original` | `str` | 原文 |
| `context` | `str` | 上下文行 |
| `file_path` | `str` | 来源文件相对路径 |
| `speaker` | `str` | 说话人/角色名 |
| `metadata` | `dict` | 引擎专属元数据（write_back 的定位关键），通用流水线只透传不碰 |
| `translation` | `str` | 翻译结果 |
| `status` | `str` | `"pending"` / `"translated"` / `"checker_dropped"` / `"ai_not_returned"` / `"skipped"` |

## EngineBase 抽象基类

**必须实现**：`_default_profile()` → EngineProfile、`detect(game_dir)` → bool、`extract_texts(game_dir)` → list[TranslatableUnit]、`write_back(game_dir, units, output_dir)` → int

**可选覆写**：`post_process()`（默认无操作）、`run(args)`（默认走 generic_pipeline）、`dry_run()`（默认统计 extract 结果）

## 新引擎添加流程（7 步）

1. 新建 `engines/xxx_engine.py`：继承 EngineBase，实现四个抽象方法
2. 新建 EngineProfile：在 `engine_base.py` 添加 `XXX_PROFILE`，注册到 `ENGINE_PROFILES`
3. 更新 `engine_detector.py`：`detect_engine_type()` + `create_engine()` + `resolve_engine()` manual_map
4. 更新 `core/prompts.py`：在 `_ENGINE_PROMPT_ADDONS` 添加引擎 prompt
5. 可选：更新 `core/glossary.py` 添加角色/术语扫描
6. 新增测试：在 `tests/test_engines.py` 添加检测、提取、回写测试
7. 更新文档：README "支持引擎"列表 + CLI `--engine` choices

## 零依赖约束处理

| 场景 | 处理 |
|------|------|
| RPG Maker VX/Ace 需 `rubymarshal` | 可选功能，缺依赖时 pip install 提示 |
| Unity AssetBundle 需 `UnityPy` | 不直接支持，通过 XUnity 导出文本间接支持 |
| Kirikiri .scn 需二进制解析 | 优先 .ks 文本格式，.scn 通过 VNTextPatch CSV |
| 老日系编码（Shift_JIS/EUC-JP） | EngineProfile.encoding 指定 |

## 命名与约定

- logging 前缀：`[ENGINE]` / `[DETECT]` / `[RPGM]` / `[CSV]` / `[PIPELINE]`
- CLI 参数：小写短横线分隔（`--engine`、`--placeholder-regex`）
- docstring：中文注释 + 英文 docstring 混合，模块头部有职责说明

## 自定义引擎插件（`--provider custom --custom-module NAME`）

自定义引擎插件是独立于 EngineBase 抽象的另一条扩展轴：插件提供
**API 调用**（如对接本地 LLM / 非标准 API），而引擎抽象处理
**格式解析**（提取什么文本 / 怎么回写）。两者正交，典型组合是
"Ren'Py 引擎 + custom provider"。

### 接口契约

放在 `custom_engines/<module>.py`，实现以下之一：

- `translate_batch(system_prompt: str, user_prompt: str) -> str | list[dict]`
  （推荐：整批调用，user_prompt 是 JSON 数组）
- `translate(text: str, source_lang: str, target_lang: str) -> str`
  （fallback：单句调用，宿主自动组装 JSON 数组）

### 两种运行模式（round 28 S-H-4）

| 模式 | CLI | 隔离级别 | 启动 | 适用场景 |
|------|------|---------|------|---------|
| **Legacy（默认）** | `--provider custom --custom-module NAME` | `importlib` 加载到宿主进程 | 零开销 | 信任的插件（自己写的 / 来源明确） |
| **Sandbox（opt-in）** | `--provider custom --custom-module NAME --sandbox-plugin` | 独立 subprocess + JSONL over stdin/stdout | ~100-150ms 启动 + ~5-15ms/call | 不信任的第三方插件，或处理敏感 API key |

### Sandbox 模式插件模板

为支持 sandbox 模式，插件需要加一个 `__main__` 分支实现 JSONL 协议：

```python
def translate_batch(system_prompt, user_prompt):
    # ... your translation logic ...
    return json.dumps(results, ensure_ascii=False)

def _plugin_serve():
    """Sandbox mode JSONL loop — read stdin line, write stdout line."""
    import sys, json
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        req = json.loads(line)
        if req.get("request_id") == -1:
            break  # shutdown sentinel
        try:
            result = translate_batch(req["system_prompt"], req["user_prompt"])
            resp = {"request_id": req["request_id"], "response": result, "error": None}
        except Exception as e:
            resp = {"request_id": req["request_id"], "response": None, "error": str(e)}
        print(json.dumps(resp, ensure_ascii=False), flush=True)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--plugin-serve":
        _plugin_serve()
```

完整示例参见 `custom_engines/example_echo.py`。

### 协议细节

- **Request**：`{"request_id": <int>, "system_prompt": <str>, "user_prompt": <str>}`
- **Response**：`{"request_id": <int>, "response": <str|null>, "error": <str|null>}`
- **Shutdown**：`{"request_id": -1}` + 关闭 stdin
- **超时**：宿主使用 `APIConfig.timeout`（默认 180s）；超时则 `proc.kill()` + `wait(2)` 清理
- **stderr 截断**：插件异常退出时宿主读取 stderr tail（< 10KB），错误消息 ≤ 600 字符（round 30 防 OOM 加固）
- **stdout per-line cap**：Round 43 + 44 给 `_SubprocessPluginClient._read_response_line` 加 `_MAX_PLUGIN_RESPONSE_CHARS = 50 * 1024 * 1024` 字符上限（**单位是 chars 不是 bytes** — Popen `text=True` 模式下 `readline(N)` 的 N 计算解码后的字符数；CJK 响应最坏字节数 ~150 MB）。超 cap 但无 newline 的响应被当 malformed 拒绝，raise `RuntimeError` 走宿主的 error-wrap 路径。与 stderr cap 配对 bound plugin 两条输出通道，防 OOM DoS。
