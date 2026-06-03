# 安全策略 / Security Policy

silk-starry 是一个会**读写项目文件、处理潜在敏感信息（CLAUDE.md 里可能有凭证）、并能触发 git 操作建议**的工具，因此安全很重要。

## 设计上的安全保证
- **永远人在环**：所有对 CLAUDE.md 的写入、对 auto-memory 的删除，前面都会给你看 diff 并等确认；hook 只产出候选，**绝不**自动改写 CLAUDE.md。
- **不复述凭证**：生成/审查时读到的明文密钥、口令、内网 IP 会被转写成「禁止硬编码凭证」的禁区规则，而**不是**写进会提交 git 的文件。
- **`graduate.py` 两道安全闸**：删除记忆前，①目标必须在 auto-memory 目录内 ②默认 dry-run，必须显式 `--confirm`。已对路径穿越（`../../`）做拒绝测试。
- **脚本默认只读**（除明确的写动作：install_hooks / graduate --confirm / sync_targets --add-agents-import）。

## 报告漏洞
如果你发现安全问题（如脚本会越界删除文件、会泄露凭证、路径穿越绕过），请**不要**直接开公开 issue。
- 通过 GitHub 的 **Security → Report a vulnerability**（Private vulnerability reporting）提交，或
- 邮件联系维护者（见仓库 profile）。

我们会在合理时间内响应。请附复现步骤、影响范围、受影响版本。

## 使用者注意
- silk-starry 维护的 CLAUDE.md 通常**提交进 git 团队共享**，请勿在其中放真实密钥；个人/机密放 `CLAUDE.local.md` 并 gitignore。
- 运行 `sync_targets.py --add-agents-import` / `install_hooks.py` 会修改目标项目的文件（CLAUDE.md / `.claude/settings.json`），运行前请确认。
