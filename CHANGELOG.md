# Changelog

最新数字（测试数 / 文件数 / CI 步骤 / 断言点）见 [HANDOFF.md](HANDOFF.md) 顶部 `VERIFIED-CLAIMS` 块。完整历史见 [_archive/](_archive/)。

## 最近 5 轮（仅高亮，详细见归档）

- **Round 50** — Zero-debt closure 模式确立（所有 audit findings 同轮 fix，no tier exemption）；r49 6 项 deferred 全 closure；2 latent fixture bug 同轮 fix；CI Mock target consistency check
- **Round 49** — Drift prevention 工具自动化（pre-commit + verify_docs_claims --fast/--full + VERIFIED-CLAIMS 单一声称源）；file_safety helper 推广 26 sites / 12 modules 全 TOCTOU MITIGATED
- **Round 48** — TOCTOU helper 抽取到 core/file_safety.py；首次 security CRITICAL 同轮 fix；audit-tail 补拆 800 行越限测试文件
- **Round 47** — TOCTOU 升级 ACCEPTABLE doc → MITIGATED code（csv_engine fstat 二次校验）；test_translation_state 拆 progress_tracker_language
- **Round 46** — install_hooks 启用；test_runtime_hook 拆 v2_schema；真实桌面 GUI smoke via computer-use（5 轮积压闭合）

## 阶段总览

详见 [_archive/EVOLUTION.md](_archive/EVOLUTION.md)。

| 阶段 | 轮次 | 主题 |
|------|------|------|
| 阶段零 | r1-r10 | 翻译质量基线 |
| 阶段一 | r11-r17 | 架构成型（main.py 拆分 + 引擎抽象 + GUI） |
| 阶段二 | r18-r19 | 工具链补全（RPA/rpyc/lint/editor/插件） |
| 阶段三 | r20-r30 | 安全与稳健化（pickle 白名单 + ZIP Slip + 大文件拆分 + 沙箱） |
| 阶段四 | r31-r35 | 多语言与运行时注入（v2 schema + 外层语言循环） |
| 阶段五 | r36-r42 | 防御加固与契约化（OOM cap + checker per-language） |
| 阶段六 | r43-r45 | 累计审计期（CI Windows + plugin char/byte 澄清） |
| 阶段七 | r46-r48 | Auto Mode 综合执行（GUI smoke + TOCTOU helper） |
| 阶段八 | r49 | Drift Prevention 自动化（4 项工具 + 26 sites MITIGATED） |
| 阶段九 | r50 | Zero-Debt Closure 模式确立 |

## 归档索引

- [_archive/EVOLUTION.md](_archive/EVOLUTION.md) — r1-r50 演进概览（无 commit hash，保 round 编号）
- [_archive/CHANGELOG_RECENT_r50.md](_archive/CHANGELOG_RECENT_r50.md) — Round 50 末归档的最近 5 轮详细
- [_archive/CHANGELOG_FULL.md](_archive/CHANGELOG_FULL.md) — r1-r45 总览表 + r19/r43 完整正文
- [_archive/TEST_PLAN_r50.md](_archive/TEST_PLAN_r50.md) — Round 50 末归档的测试覆盖明细
