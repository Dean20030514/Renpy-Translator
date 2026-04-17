# Security Policy / 安全策略

## Threat Model / 威胁模型

**English**

This project is a local single-user translation tool. It runs on the user's own machine, loads game files the user has chosen to translate, and talks to remote LLM APIs using API keys the user provides. The intended threat model is:

- **Trusted**: the user's own filesystem, the user-supplied API key, LLM API endpoints the user explicitly configures, and the user's own custom plugins under `custom_engines/`.
- **Untrusted**: game archive contents (`.rpa`, `.rpyc`), game scripts (`.rpy`), translation payloads returned by the LLM, and any file paths embedded in them.

Specifically, loading a **malicious RPA or rpyc archive** from an unknown source **must not** lead to arbitrary code execution, nor write files outside the output directory.

**中文**

本项目是**本地单用户**的翻译工具，运行在用户自己的机器上，加载用户选定的游戏文件，用用户提供的 API Key 调用远程 LLM。威胁模型：

- **可信**：用户自己的文件系统、用户提供的 API Key、用户明确配置的 LLM endpoint、用户自己放到 `custom_engines/` 下的插件
- **不可信**：游戏档案（`.rpa`、`.rpyc`）、游戏脚本（`.rpy`）、LLM 返回的翻译内容、以及这些数据中嵌入的任何文件路径

特别地，**加载来源不明的 RPA 或 rpyc 档案**绝不能导致任意代码执行或写入 `outdir` 之外的文件。

---

## Reporting a Vulnerability / 漏洞报告

**English**

Please report vulnerabilities **privately**, not through public issues.

- Preferred: GitHub Security Advisories (Private Vulnerability Reporting) on the project's repository
- Alternative: email the maintainer with subject `[SECURITY] <short title>`
- Do **not** disclose the vulnerability publicly until it has been addressed

Include in your report:

1. Affected file(s) and line number(s)
2. Attack prerequisites (what an attacker must control / provide)
3. Proof of concept (minimal, for reproduction only — do not include weaponised payloads)
4. Suggested mitigation if you have one
5. Your preferred credit name for the advisory

**Response time commitment**:

- Acknowledge receipt within **7 days**
- Initial assessment within **14 days**
- Fix and coordinated disclosure within **90 days** for confirmed vulnerabilities

**中文**

请通过**私密渠道**报告漏洞，不要直接开公开 issue。

- 推荐：GitHub Security Advisories（Private Vulnerability Reporting）
- 替代：邮件联系维护者，主题 `[SECURITY] <简要标题>`
- 请在问题修复前**不要公开披露**

报告请包含：

1. 受影响的文件和行号
2. 可利用条件（攻击者需要控制 / 提供什么）
3. 最小化 PoC（仅用于复现，不要带武器化载荷）
4. 可选：建议的缓解方案
5. 您希望在公告中使用的署名

**响应时间承诺**：

- **7 天内**确认收到
- **14 天内**完成初步评估
- **90 天内**对确认漏洞完成修复与协调披露

---

## Known Constraints / 已知限制

**English**

- **Custom plugins** (`custom_engines/`) run with the full privileges of the main process. Do not install plugins from untrusted sources.
- **Tier 1 rpyc decompilation** executes the game's bundled Python interpreter in a subprocess. The subprocess inherits the parent environment; do **not** point Tier 1 at games from untrusted sources while sensitive environment variables (including API keys) are set.
- **LLM translation output** is validated but not sandboxed. A compromised or adversarial LLM provider could in theory craft translations that bypass the 55+ validator checks and produce misleading but syntactically valid scripts.
- **PyInstaller-built exe** (`dist/多引擎游戏汉化工具.exe`) has not been code-signed; Windows SmartScreen may warn on first run.

**中文**

- **自定义插件**（`custom_engines/` 下的文件）以主进程完整权限运行。不要加载来源不明的插件。
- **Tier 1 rpyc 反编译**会启动游戏自带 Python 作为子进程。子进程会继承父进程环境（包括 API Key 等敏感环境变量），**不要**在设置了敏感环境变量的情况下对来源不明的游戏运行 Tier 1。
- **LLM 翻译结果**经过校验但未沙箱化。理论上被控制的 / 恶意的 LLM 提供商可以构造绕过 55+ 项校验的翻译，产生语法合法但误导性的脚本。
- **PyInstaller 构建的 exe**（`dist/多引擎游戏汉化工具.exe`）未做代码签名，Windows SmartScreen 可能在首次运行时警告。

---

## Hardening Applied / 已实施的加固

This section tracks security hardening that has been applied, so reviewers
can confirm the corresponding code paths are still protected.

- **`core/pickle_safe.SafeUnpickler`**: whitelist-based pickle loader used in
  place of `pickle.loads` for all untrusted archive / AST data.
- **RPA index reader** (`tools/rpa_unpacker.py`): uses `SafeUnpickler`,
  refuses unknown classes.
- **RPA extraction** (`tools/rpa_unpacker.unpack_rpa`): verifies every
  resolved destination path is contained within `outdir` (ZIP Slip guard).
- **Tier 2 rpyc loader** (`tools/rpyc_decompiler._RestrictedUnpickler`):
  whitelist strategy for builtins + real renpy/store classes mapped to
  harmless stubs.
- **Tier 1 helper script** (`_DECOMPILE_HELPER_SCRIPT`): inlines a minimal
  `_SafeUnpickler` class inside the injected subprocess code so that
  malicious rpyc payloads cannot reach `os.system` / `subprocess.Popen` /
  `builtins.eval` through pickle opcodes even inside the game's own Python.

---

## Scope Note / 范围说明

**English**: This policy covers the Python source code in this repository.
It does **not** cover vulnerabilities in upstream dependencies (there are
none — the project uses only the Python standard library), in the Ren'Py
runtime, in LLM provider APIs, or in the user's operating system.

**中文**：本策略覆盖本仓库的 Python 源代码。**不**覆盖上游依赖漏洞（本项目零依赖）、Ren'Py 运行时漏洞、LLM 提供商 API 漏洞、以及用户操作系统漏洞。
