# 记忆系统管家：管好 Claude Code 整套记忆，而不只 CLAUDE.md

> silk-starry 的扩展定位。核心心法：**记忆功能其实是「配置系统」，不是「学习」**——你/Claude 在用不同的层
> 配置 Claude 在你环境里的行为。silk-starry 的活：①把每条经验**放到正确的层** ②各层**保持干净不腐烂**
> ③捕获**毫不费力** ④**不重造**官方已有的捕获/整合。
> 依据见 `参考文章`：[A2] 记忆全景、[A3] 源码级解析、[A1] CLAUDE.md 宪法。

## 一、记忆全景（5 记忆层 + 4 控制层）

| 层 | 谁写 | 自动加载 | 大小 | silk-starry 怎么帮 |
|---|---|---|---|---|
| **Transcripts** 完整对话(JSONL) | 系统 | ❌ grep 查 | MB–GB | `disk_hygiene` 体检膨胀 |
| **Session Memory** 会话摘要 | 后台代理 | ✅ 相关时 | 10–100KB | silk-starry 不干预；但它和 CLAUDE.md 共同决定**压缩后什么活下来**（见 §二·补） |
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
9. **希望每次上下文压缩/重置后都别丢的经验**（"记住我犯过的错和怎么修的"、"摘要聚焦 X 模块"）→ 写进项目
   `./CLAUDE.md` 的 **`## Compact Instructions`** 段（见 §二·补）。

> 判断三连问（来自官方）：① 只对我、还是全团队？② 只这个项目、还是所有项目？③ 能进 git 吗？
> 硬约束永远走 hook，不靠 CLAUDE.md（它是建议性上下文，多数情况遵守但**不保证**）。

## 二·补、压缩指令（Compact Instructions）：让经验熬过上下文重置

长会话到阈值会触发**压缩**——把整段历史重写成结构化摘要、替换原对话（源码 `compactConversation` /
`getCompactPrompt`）。压缩是**记忆机制行使控制力的关键时刻**：摘要写什么、丢什么，直接决定 Claude
"重置后还记不记得"你这次的关键决策和踩过的坑。

CLAUDE.md 在这里有一个**专属控制面**：写一个 `## Compact Instructions` 段。CLAUDE.md 每次都随上下文注入，
而压缩提示词正文里明确写着"included context 里若有额外摘要指令就照做"，并把 `## Compact Instructions` 当范例
（源码 `prompt.ts` 的 `BASE_COMPACT_PROMPT`）——于是这段就被那个压缩用的 forked agent 当成"书记员须知"遵守了。
（注：`/compact <自定义文字>` 是另一条路径，会被拼成 `Additional Instructions:` 直接附在 prompt 末尾，见
`getCompactPrompt`；两者都能影响摘要，但 CLAUDE.md 这段是**持久**的，每次压缩都生效。）

```markdown
## Compact Instructions
压缩时聚焦 typescript 代码改动；务必保留我犯过的错和对应的修复方式；
正在进行的迁移（旧 API → 新 API）的当前进度不要丢。
```

silk-starry 的活：
- **route**：用户说"压缩/清上下文后老是忘了正在干的迁移""每次 /compact 完就丢了我踩的坑"→ 引导写这一段。
- **写法**（同 CLAUDE.md 准入门槛）：只写**这个项目压缩时特别容易丢、又特别该留**的东西（进行中的迁移进度、
  反复踩的坑、本轮主线意图）；**别写通用废话**（"写好摘要""保留重要信息"——压缩 prompt 本来就这么要求）。
  控制在 2–4 行，越短越灵的原则在这里同样成立。
- **audit**：体检 CLAUDE.md 时若发现这段又长又空，按"可自动执行 + 配反例"的标准砍。
- **边界**：它只影响**摘要怎么写**，不是硬约束；要 100% 不丢的状态走别的层（Auto Memory / 文件）。

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
