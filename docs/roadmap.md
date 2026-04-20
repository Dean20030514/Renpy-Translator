> 仅在讨论新功能规划时加载此文档。

# 后续引擎路线图

## 已完成

**阶段零~四（19 轮迭代，r20 前）**：Ren'Py 全功能支持
（direct/tl/retranslate/screen + 四阶段流水线 + RPA 解包打包 + rpyc
反编译 + lint 集成 + 自定义引擎插件）+ RPG Maker MV/MZ（事件指令 +
8 种数据库 + System.json）+ CSV/JSONL 通用格式 + 引擎抽象层
（EngineProfile/TranslatableUnit/EngineBase）+ 266 测试。

**阶段五（r20-r44 架构硬化 + 多语言完整栈）**：
- r20-r24 CRITICAL/HIGH 收敛 + 大文件拆分
- r25-r30 综合加固 + A-H-3 Minimal + test_all 拆分
- r31-r35 运行时注入（translations.json + v2 envelope） + tl_inject
  hook + 字体打包 + 多语言 DB schema + side-by-side editor + 多语言
  外循环
- r36-r42 深度 bug + M 级防御包（5 轮审计驱动，21/21 user-facing +
  internal JSON loader size caps 全覆盖，checker per-language，
  插件三通道 bound，gui.py 拆 mixin 架构）
- r43-r44 累计 3 维度专项审计（**连续 3 轮 0 CRITICAL/0 HIGH**：
  r35 末 / r40 末 / r43） + audit-tail 合流修复（plugin cap char-
  vs-byte 澄清 + test coverage 补齐 + 3 漏网 JSON loader cap 补齐）
- 测试 266 → **413**（tl_parser 75 + screen 51 = 539 断言点；23
  测试文件）

## 优先级排序

| 优先级 | 引擎 | 占比 | 难度 | 依赖 | 状态 |
|--------|------|------|------|------|------|
| ✅ P0 | Ren'Py | ~35% | — | — | 已完成 |
| ✅ P0 | RPG Maker MV/MZ | ~25% | 低 | 纯标准库 | 已完成 |
| ✅ P0 | CSV/JSONL 通用 | 覆盖全部 | 最低 | 纯标准库 | 已完成 |
| 🟡 P1 | RPG Maker VX/Ace | ~5% | 中 | `rubymarshal`（可选） | 待实现 |
| 🟡 P1 | Wolf RPG Editor | ~5% | 中 | 自定义二进制解析 | 待实现 |
| 🟡 P1 | Godot | ~3% | 低 | 纯标准库 | 待实现 |
| 🟢 P2 | Unity（XUnity） | ~10% | 低 | XUnity 导出文本 | 待实现 |
| 🟢 P2 | Kirikiri 2/Z | ~5% | 中 | 参考 VNTextPatch | 待实现 |
| 🟢 P2 | TyranoBuilder | ~3% | 低 | .ks 脚本 | 待实现 |
| 🔵 P3 | Unreal Engine | ~5% | 高 | uasset 工具 | 暂不计划 |
| 🔵 P3 | HTML5 / 浏览器 | ~3% | 最低 | JS/JSON 解析 | 按需 |

## 各引擎实现要点

**RPG Maker VX/Ace（P1）**：Ruby Marshal 格式（`.rxdata`/`.rvdata`/`.rvdata2`），需 `rubymarshal`。建议先只读支持（提取 → CSV），后续做直接回写。

**Wolf RPG Editor（P1）**：自定义二进制（`.wolf`/`.dat`）。建议通过 WolfTrans 导出格式 → CSVEngine 间接支持。

**Godot（P1）**：`.tscn`/`.gd`/`.tres` 均为文本格式，纯标准库。`.gd` 中 `tr("...")` 需正则提取，Godot CSV 翻译表可直接用 CSVEngine。

**Unity / XUnity（P2）**：不做 AssetBundle 解析。支持 XUnity AutoTranslator 导出的 `original=translation` 文本文件。

**Kirikiri 2/Z（P2）**：`.ks` 是文本格式可直接正则提取，`.scn` 二进制通过 VNTextPatch 导出 CSV。

**TyranoBuilder（P2）**：`.ks` 脚本格式类似 Kirikiri，实现方案相近。

## 架构 TODO（非引擎）

与引擎扩展正交的架构项：

| 优先级 | 项目 | 前置 | 状态 |
|--------|------|------|------|
| 🟠 P1 | PyInstaller 打包 smoke + GUI manual smoke test | r41 GUI mixin 拆分生产验证 | **r41/r42/r43/r44 4 轮积压**，需 pip install + 人工点击或 computer-use |
| 🟠 P1 | 非中文目标语言端到端验证（ja / ko / zh-tw） | r39 prompt + r41 alias + r42 checker + r43-r44 zh-tw 隔离 + generic fallback 五层 code-level contract 已锁死 | 需真实 API key + 真实游戏 |
| 🟡 P2 | A-H-3 Medium / Deep（adapter 让 Ren'Py 走 generic_pipeline） | — | 需真实 API + 游戏验证 |
| 🟡 P2 | S-H-4 Breaking（强制所有 plugins 走 subprocess，retire importlib） | — | dual-mode 已稳定，用户拍板破坏性变更 |
| 🟡 P2 | CI Windows runner（GitHub Actions 跑 23 测试文件） | 需 repo access | 14 轮欠账 |
| 🟢 P3 | RPG Maker Plugin Commands（code 356） | — | 需真实 MV/MZ 游戏样本 |
| 🟢 P3 | 加密 RPA / RGSS 归档 | — | 需加密游戏样本 |
| 🔴 监控 | Pickle 白名单 `_codecs.encode` / `copyreg._reconstructor` 理论链式攻击 | — | 暂不修 |
| 🔴 监控 | HTTP 响应体 64 KB 精度偏差 | — | 暂不修 |
