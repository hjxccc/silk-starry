# 进化手册：何时进化、怎么升级（人在环）

> 回答用户最关心的问题：「CLAUDE.md 在什么时候进化、怎么触发」。
> 配套脚本：`scripts/memory_digest.py`（从 auto-memory 挖候选）。

## 目录
- [核心闭环](#核心闭环)
- [四个进化时机](#四个进化时机)
- [候选 → 规则的升级流程](#候选--规则的升级流程)
- [准入门槛（必须过）](#准入门槛必须过)
- [与官方 Auto Memory 的分工](#与官方-auto-memory-的分工)
- [安全红线](#安全红线)

## 核心闭环
```
捕获(auto-memory / 纠正 / 收尾) → 策展(去重·过门槛·写成规则) → 用户确认 → 最小diff写入 → 清理来源
```
关键认知：**捕获已由官方 Auto Memory 原生做掉**（v2.1.59+，`~/.claude/projects/<proj>/memory/`，
Claude 自己写、跨 session 加载 `MEMORY.md` 前 200 行）。silk-starry 只做后半截——
把反复出现、值得固化的东西**策展并升级进 CLAUDE.md**。

## 四个进化时机
（用户已确认四个都要）

1. **会话/任务收尾**
   - 回顾本轮：有没有"下次还得重新解释"的事？有没有让用户纠正过的做法？
   - 把它们提成候选，**不立刻写**，列给用户。
   - 由 Stop/SessionEnd hook 提示（hook 只记录候选到 `candidates.jsonl`，不改文件）。

2. **出错被纠正时（最即时）**
   - 用户说"不对/不是这样/应该…"后，立刻把这条教训记为候选，**带上原因**
     （为什么之前错、正确做法是什么）。
   - 例：用户纠正"别用 logging，用 loguru" → 候选规则："本项目日志用 loguru，
     不用标准 logging（统一格式 + 异步）"。

3. **手动审查**
   - 用户主动要求审查时，扫 `candidates.jsonl` + 跑 `memory_digest.py`，集中升级一批。

4. **Auto Memory 策展（定期）**
   - 跑 `python scripts/memory_digest.py [项目根]`，从 `MEMORY.md` 找**出现 ≥2 次**
     的稳定模式（区分"单次教训"和"反复规律"——只有反复的才值得进 CLAUDE.md）。

## 候选 → 规则的升级流程
1. **收集**：合并三个来源的候选（hook 队列、本轮纠正、memory digest）。
2. **去重**：同义合并，避免和现有 CLAUDE.md 规则重复/冲突（重复就跳过，冲突就提示用户选）。
3. **过准入门槛**（见下）：答不上"不写会错什么"的直接丢弃。
4. **写成规则**：每条 = 可执行指令 + 一个反例（可选）+ 一句原因。
5. **定位目标文件**：用就近原则（见 `orchestration.md`）决定写进根还是某个子 CLAUDE.md，
   或该不该拆进 `.claude/rules/`。
6. **给用户看 diff**：明确"我打算在 X 文件加这几行"，**等确认**。
7. **最小 diff 写入**：只加新条目，不重排不重写既有内容。
8. **清理来源**：若来自 auto-memory，升级后从 memory 删掉对应条目腾空间；清空已处理的
   `candidates.jsonl` 条目。

## 准入门槛（必须过）
对每条候选问：

> **"不写这条，Claude 会做错哪件具体的事？"**

- 答得上 + 可自动执行 + 不是代码能看出来的 → 收。
- 答不上 / 太空泛 / 一次性 / 与默认一致 → 丢。
- 是硬约束（必须 100% 执行，如禁止 push main）→ **不进 CLAUDE.md，建议改用
  PreToolUse hook**（CLAUDE.md 只有 ~80% 遵守）。

宁缺毋滥：一份针对真实失败的 6 条，强过注水的 12 条。每加一条都在花 Claude 的注意力预算。

## 按官方 4 类记忆归类候选（对齐 memoryTypes，让升级更准）
auto-memory 用 4 类 taxonomy，升级候选时先归类，能更好判断该不该进 CLAUDE.md：
- **user**（用户角色/偏好/知识）→ 多属个人，通常**不进**团队 CLAUDE.md，留在 memory 或个人 `CLAUDE.local.md`。
- **feedback**（"别这样/继续这样"的工作指导，成功也记）→ **最该升级**进 CLAUDE.md/rules。升级时保留
  **Why:**（原因，判边界用）和 **How to apply:**（何时生效）。
- **project**（谁在做什么/为何/期限，衰减快）→ 偏临时，**一般不进** CLAUDE.md；相对日期要转绝对。
- **reference**（外部系统位置：Linear/Slack/Grafana）→ 视情况，常更适合留 memory 而非 CLAUDE.md。

**什么坚决不升级**（官方"什么不该存"清单，作准入硬过滤）：代码模式/架构/路径/结构（可 grep）、
git 史、调试 fix 配方、**已在 CLAUDE.md 的内容**、临时任务态。即便用户说"记下来"，若是 PR 列表/
活动摘要这类，也只提炼其中"surprising/non-obvious"的部分。

## 升级前先验证（漂移护栏，对齐官方 TRUSTING_RECALL）
候选若**点名了具体 file:line / 函数 / flag**，它只是"记忆写入时存在"的声明——升级进 CLAUDE.md 前
**先核对当前代码确实存在**（grep / 查文件）。已重命名/删除的，要么改写成不依赖具体符号的规则，要么丢弃。
"memory 说 X 存在" ≠ "X 现在存在"。

## 与官方 Auto Memory 的分工
| | Auto Memory | silk-starry evolve |
|---|---|---|
| 角色 | 自动**捕获**学到的经验 | **策展 + 升级**成强制规则 |
| 谁写 | Claude 自动 | 经用户确认后写 CLAUDE.md |
| 存储 | `~/.claude/projects/<proj>/memory/` | 项目 `CLAUDE.md` / `.claude/rules/` |
| 加载 | `MEMORY.md` 前 200 行每会话加载 | 全量注入（受 200 行约束） |

口诀（官方）：「记住某事」用 auto memory；「**加进 CLAUDE.md**」才显式升级——后者就是
silk-starry 干的活。不要禁用 auto memory（`autoMemoryEnabled`）来重造它。

### 关于捕获层的几个确定事实（据 Claude Code 源码，让 evolve 更准）
- **auto-memory 目录按 git 仓库根派生**：`<base>/projects/<把绝对路径的 :\/ 都换成 - 的 key>/memory/`，
  同一仓库的多个 worktree 共享一份。`memory_digest.py` 已据此解析（会向上找 `.git`）；
  也可用 `--memory-dir` 或读 settings 的 `autoMemoryDirectory` 覆盖。
- **session 记忆是固定模板**，含 `# Errors & Corrections` 和 `# Learnings` 两个区段——
  这是**最值得升级成规则的来源**（"用户纠正了什么 / 哪些方案失败别再试 / 什么有效"）。
  `memory_digest.py` 会优先把这两区段的条目列为高价值候选。
- **捕获层自带去重**：写 session 记忆时被明确要求"不要写已经在 CLAUDE.md 里的信息"。
  所以 evolve 从记忆升级时，天然不会把已有规则重复搬进 CLAUDE.md——你只需再做一次跨文件查重兜底。
- 捕获入口不止后台抽取，还有 `/remember`、`/dream`（蒸馏日志为 topic 文件）、以及助手模式的
  每日日志 `memory/logs/YYYY/MM/`。digest 时若存在 `logs/` 也值得扫一眼。

## 安全红线
- 进化**永远人在环**：hook 和脚本只产出候选，**绝不**自动改写 CLAUDE.md。
- 写入前必给用户看 diff。
- 升级的规则同样过敏感信息扫描（别把纠正里夹带的密钥写进去）。
