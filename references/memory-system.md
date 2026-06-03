# 记忆系统管家：管好 Claude Code 整套记忆，而不只 CLAUDE.md

> silk-starry 的扩展定位。核心心法：**记忆功能其实是「配置系统」，不是「学习」**——你/Claude 在用不同的层
> 配置 Claude 在你环境里的行为。silk-starry 的活：①把每条经验**放到正确的层** ②各层**保持干净不腐烂**
> ③捕获**毫不费力** ④**不重造**官方已有的捕获/整合。
> 依据见 `参考文章`：[A2] 记忆全景、[A3] 源码级解析、[A1] CLAUDE.md 宪法。

## 一、记忆全景（5 记忆层 + 4 控制层）

| 层 | 谁写 | 自动加载 | 大小 | silk-starry 怎么帮 |
|---|---|---|---|---|
| **Transcripts** 完整对话(JSONL) | 系统 | ❌ grep 查 | MB–GB | `disk_hygiene` 体检膨胀 |
| **Session Memory** 会话摘要 | 后台代理 | ✅ 相关时 | 10–100KB | 了解即可，silk-starry 不干预 |
| **CLAUDE.md**(全局/项目/local/子目录) | 你 | ✅ 每次 | ≤200 行 | generate / audit / evolve（核心） |
| **Auto Memory**(MEMORY.md+topic) | Claude | ✅ 每次 | ~25KB | `memory_digest` 挖候选 + `memory_doctor` 体检 + `graduate` 收尾 |
| **Team Memory** | 团队 | ✅ | — | 了解即可 |
| .claude/**rules/**(paths glob) | 你 | 懒加载 | — | audit 拆分 + introspect 预测 |
| **settings.json**(权限/记忆开关) | 你 | 强制 | — | `memory_doctor` 体检记忆相关开关 |
| **hooks** | 你 | 强制 | — | `install_hooks` 装提醒 |
| **磁盘**(debug//file-history/) | 系统 | — | 可达 300GB | `disk_hygiene` 揪真凶 |

## 二、「这条经验该放哪层」决策树（route —— 让"随时记住"不费力）

用户说"记住 X"时，按顺序判断 X 该落到哪：

1. **必须 100% 执行**（禁 push main、禁删 migration）→ **不是记忆**，是 `PreToolUse` hook（settings.json）。
2. **只在编辑某类文件/目录时才相关**（"`*.vue` 组件 ≤200 行"）→ `.claude/rules/<topic>.md` + `paths:`。
3. **团队共享 + 长期稳定 + 该进 git**（构建命令、架构约束、团队规范、禁区）→ **项目 `./CLAUDE.md`**。
4. **个人、跨所有项目**的偏好（默认包管理器、commit 语气、回复风格）→ `~/.claude/CLAUDE.md`。
5. **个人、只这个项目**的私有偏好（本地 URL、测试账号、调试怪癖）→ `./CLAUDE.local.md`（确保在 `.gitignore`）。
6. **反复出现的教训/纠正**，还没稳定 → 先**留在 Auto Memory**（官方自动记），出现 ≥2 次再 `graduate` 进 CLAUDE.md。
7. **外部系统位置**（Linear 看板、Slack 频道、Grafana）→ Auto Memory 的 `reference` 类，一般不进 CLAUDE.md。
8. **易变信息**（API 文档、配置清单）→ 别抄进 CLAUDE.md，用 `@path` import 引源文件（抄了就会过期）。

> 判断三连问（来自官方）：① 只对我、还是全团队？② 只这个项目、还是所有项目？③ 能进 git 吗？
> 硬约束永远走 hook，不靠 CLAUDE.md（它只 ~80% 遵守）。

## 三、各层"保持不腐烂"的工具

- **`python scripts/memory_doctor.py [项目根]`** —— Auto Memory 体检（对齐官方 autoDream 四阶段，按需+只读）：
  MEMORY.md 是否超 200 行/25KB、topic 是否缺 `description`（缺了 Sonnet 召回不到）、陈旧(>N 天)、
  孤儿/失效指针、相对日期气味、记忆相关 settings + `autoMemoryDirectory` 安全。**何时跑**：任务收尾、
  感觉 MEMORY.md 乱了、Claude 引用了过期事实时。
- **`python scripts/disk_hygiene.py`** —— `~/.claude` 磁盘膨胀体检：分清"可安全清理的历史/日志"
  （`file-history/`、`debug/`、transcripts）和"绝不能动的记忆/插件"，给 `cleanupPeriodDays` 建议 + 安全清理命令。
  **何时跑**：Claude 变慢、磁盘告警、`~/.claude` 体积可疑时。**记忆本体很小，膨胀从来不是它的锅。**
- 已有：`memory_digest`（挖升级候选）、`graduate`（升级后清理记忆，双安全闸）、`introspect`（预测加载+字节预算）。

## 四、记忆相关 settings 速查

| 设置 | 作用 | silk-starry 建议 |
|---|---|---|
| `CLAUDECODEDISABLEAUTOMEMORY` | =1 关闭 Auto Memory | 想让 Claude 自动积累经验就设 0 |
| `autoDreamEnabled` | 后台整合（去重/转绝对日期/解矛盾） | 建议 true，否则记忆易腐 |
| `cleanupPeriodDays` | 旧 transcripts/快照自动清理周期 | 设个 7~30，防磁盘膨胀 |
| `autoMemoryDirectory` | 自定义记忆存储位置 | **只能在全局 `~/.claude/settings.json` 配**；项目级配 = 劫持写入风险（memory_doctor 会报警） |

## 五、🔴 红线
- **不重造捕获**：逐轮提取、autoDream 整合、Sonnet 召回都是官方做掉的；silk-starry 只做"放对层 + 体检 + 升级"。
- **绝不自动删记忆**：memory_doctor / disk_hygiene 全只读，只给建议和命令，由用户执行。
- **绝不**把 `autoMemoryDirectory` 写进项目级 settings。
- 升级闭环仍守 `evolution-playbook.md` 的人在环：先给 diff、等确认、再最小 diff 写入。
