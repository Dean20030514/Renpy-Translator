> 仅在讨论新功能规划时加载此文档。

# 后续引擎路线图

## 已完成

阶段零~四（19 轮迭代）：Ren'Py 全功能支持（direct/tl/retranslate/screen + 四阶段流水线 + RPA 解包打包 + rpyc 反编译 + lint 集成 + 自定义引擎插件）+ RPG Maker MV/MZ（636 行，事件指令 + 8 种数据库 + System.json）+ CSV/JSONL 通用格式（317 行）+ 引擎抽象层（EngineProfile/TranslatableUnit/EngineBase）+ 266 测试。

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
