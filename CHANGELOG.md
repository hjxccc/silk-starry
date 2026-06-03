# Changelog

本项目遵循 [Keep a Changelog](https://keepachangelog.com/) 与语义化版本。

## [0.1.0] - 2026-06-03
首个公开版本。

### 能力
- **生成 / 审查 / 进化 / 编排** 四大动作 + 三层级支持（个人全局 / 项目 / 本地 CLAUDE.md）。
- 9 个脚本：`scan` · `audit` · `locate` · `conflicts` · `introspect` · `memory_digest` · `graduate` · `sync_targets` · `install_hooks`。
- 2 个轻量 hook：`silk-starry_session_start`（开场提醒）· `silk-starry_stop`（嗅探纠正存候选）。
- 5 个技术栈模板 + 通用兜底；Karpathy 12 条行为契约可选注入。

### 「超越官方」六项
- 防泄密（凭证转写成禁区）· 字节预算+下沉建议 · 跨文件冲突治理 · 加载自省 · 跨工具 AGENTS.md 同步 · 记忆→CLAUDE.md 升级闭环。

### 测试
- 触发率 20/20；Darwin 9 维评分 ~87；对抗输入 24/24 无崩溃；7015 文件仓库 scan 1.1s。
- 在 12+ 真实开源仓库、6 种技术栈上验证；含 vs `/init`、vs 专家手写、中性效果 A/B。

### 已知边界
- 「让 Claude 少犯错」的效果是条件性的（详见 README「诚实的边界」）。
- 跨 runtime（Codex/Cursor）实跑、长期纵向漂移未在本版验证。
