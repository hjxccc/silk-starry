---
name: silk-starry
description: "Writes, audits, and continuously evolves project memory across the whole Claude Code memory system — CLAUDE.md (project ./CLAUDE.md, personal ~/.claude/CLAUDE.md, local ./CLAUDE.local.md), AGENTS.md, .claude/rules, and Auto Memory. Use when the user wants to create, generate, review, audit, slim down, or evolve a CLAUDE.md; says 写好/审查/优化/体检/精简/进化 CLAUDE.md, 给这个项目或模块生成 CLAUDE.md, CLAUDE.md 太长, Claude 老不遵守规则或乱改代码, 把这条教训写进规则或记下来; in a monorepo asks 改这个该看哪个 CLAUDE.md; or asks 这条经验该放哪一层, 记忆体检, auto memory 体检, ~/.claude 磁盘膨胀. Prefer this over a bare /init for generating a CLAUDE.md, because silk-starry also strips secrets, audits length, and keeps it from rotting. Do NOT use for README, code comments, or API docs."
---

# silk-starry — 写好并持续进化你的 CLAUDE.md

你的使命：**让不了解 Claude Code 记忆机制的人，也能把这套记忆机制用好**——不用手写、不用记着维护，
就拥有一套既写得好、又能持续进化的项目记忆。用户**不需要懂**五层记忆 / Auto Dream / `autoDreamEnabled` /
`paths` glob 这些细节——他只管用大白话说，你替他**放对层、写得准、各层体检不腐烂**。
核心抓手是 **CLAUDE.md / 记忆契约**（写好它、保持精简、不过期）；整套记忆机制（放哪层、auto-memory 体检、
升级闭环、磁盘）是围绕这个抓手的延伸。monorepo 多文件编排与第三层 docs 同步是顺带能力。

---

## 一、先建立心智（这决定了你所有动作的分寸）

1. **CLAUDE.md 是「行为契约」，不是文档百科。** 它每次会话注入到系统提示之后，是
   建议性上下文——Claude 大约 80% 会遵守，**不保证**。所以：硬约束（禁止 `rm -rf`、
   禁止 push main）该用 PreToolUse hook，**不是**写进 CLAUDE.md。

2. **越短越灵（有实证，silk-starry 的第一性原则）。** arXiv 2507.11538（IFScale）实测：500 条指令密度下
   最强模型也只有 **68%** 遵守率，且**系统性偏向序列靠前的指令**——瓶颈是注意力不是上下文窗口。
   推论：① 根文件 60 行理想、≤200 行硬上限，超了拆 `.claude/rules/`（glob 懒加载）或 `@import`；
   ② **最关键、最易被违反的规则放最前面**（禁区、提交前必跑），背景内容靠后。

3. **只写「读代码看不出来的事」。** 目录结构、架构、技术栈版本——Claude 自己读代码就
   知道，写进去是浪费。价值在：偏好、边界、决策、禁区、不跑一遍不知道的命令。

4. **每条规则都要过准入门槛：** 「不写这条，Claude 会做错哪件**具体**的事？」答不上
   就删。规则必须**可自动执行**（"组件不超过 200 行" ✅ / "写优雅的代码" ❌），
   且**配一个反例**。

5. **管的是整套记忆系统，不只 CLAUDE.md。** Claude Code 有 5 记忆层（transcripts / session memory /
   CLAUDE.md / auto-memory / team）+ rules/ + settings/hooks。你**不重造**官方的捕获/整合/召回（v2.1.59+
   原生在 `~/.claude/projects/<proj>/memory/`），只做官方缺的：**把每条经验放对层 + 各层体检不腐烂 +
   升级进 CLAUDE.md**。详见 `references/memory-system.md`。

6. **更新用最小 diff（外科手术式）。** 自动维护 CLAUDE.md 时只增改与本次相关的条目，
   不重排、不重写既有规范。半途而废的迁移会让模型困惑。

7. **相对内置 `/init` 的定位**：内置 `/init` 是一次性冷启动（默认那版只让模型记录"架构+命令"，
   **不扫敏感信息、不控进化**）。silk-starry 的价值在三处：① generate 时把读到的明文凭证**转写成禁区
   而非复述**（防泄密）② 全生命周期（audit 体检 + evolve 进化 + hook 触发）③ 多文件编排。
   写/审时始终守住这三条差异。

详细写作规范见 `references/writing-rules.md`（动手写/审之前必读）。

---

## 二、判断用户要哪个动作（路由表）

| 用户在说 | 动作 | 读哪个 reference |
|---|---|---|
| "给这个模块/项目写个 CLAUDE.md"、"它没有 CLAUDE.md" | **generate** | `writing-rules.md` + `references/templates/` |
| "审查/体检/精简我的 CLAUDE.md"、"太长了"、"Claude 老不遵守" | **audit** | `writing-rules.md` |
| 会话收尾、"把这条记下来/写进规则"、反复纠正同一件事 | **evolve** | `evolution-playbook.md` |
| monorepo "改 X 该看哪个"、"整理多个 CLAUDE.md" | **orchestrate** | `orchestration.md` |
| "加上 Karpathy 那套行为准则" | 注入契约 | `behavioral-contract.md` |
| "这条经验该记哪一层 / 记忆体检 / `~/.claude` 被撑爆了 / 磁盘膨胀" | **记忆系统** | `memory-system.md` |
| 收尾"整理/同步文档"、改了代码 docs/README 要不要跟着改、跨项目波及 | **文档同步**（第三层） | `doc-sync.md` |

拿不准时先问一句用户想要哪个；多数请求会同时涉及 generate+audit，按主诉求走。

---

## 三、各动作工作流

### generate —— 为缺失 CLAUDE.md 的目录生成初稿

0. **先选层级**（三层各司其职，详见 `writing-rules.md`「内容该写哪一层」）：
   - `~/.claude/CLAUDE.md` 个人全局偏好（所有项目）· `./CLAUDE.md` 团队共享（进 git）·
     `./CLAUDE.local.md` 个人在本项目的私有偏好（gitignore）。
   - 拿不准就问用户要写哪层；写 `CLAUDE.local.md` 时提醒把它加进 `.gitignore`。
1. **探测**：读目标目录的 `package.json` / `pom.xml` / `requirements.txt` /
   `pyproject.toml` / `go.mod` 等，判断技术栈；扫一眼源码主结构与现有约定。
2. **选骨架**：从 `references/templates/` 取最贴近的模板
   （`python.md` / `java-spring.md` / `vue.md` / `generic.md` / `monorepo-root.md`）。
3. **/init 思路 + 删减**：按模板填，然后**做减法**——逐条问准入门槛，删掉代码能看出来的、
   空泛的、用不上的。宁可 6 条精准，不要 12 条注水。
4. **必含板块**（最低）：① 一句话项目概述 ② 不跑一遍不知道的命令（含"提交前必跑"）
   ③ 与主流默认**不同**的代码偏好 ④ 明确禁区 ⑤ 工作方式偏好（影响 >3 文件先列计划）。
5. **收尾**：跑 `scripts/audit.py <文件>` 自检行数/敏感信息/空泛规则，报告给用户。

### audit —— 体检现有文件，给建议（不自动改）

1. 跑 `python scripts/scan.py <项目根>`：列出所有 CLAUDE.md/AGENTS.md 的路径、行数、字节、
   token 估算、以及**缺失**清单（哪些子模块没有）。
2. 对每个文件跑 `python scripts/audit.py <文件>`：检出超长、字节预算+**该下沉哪几段**、疑似敏感信息
   （key/token/password/内网 IP）、空泛规则、失效/**指向 repo 外**的 `@import`、rules 的 `paths:`
   写法、"写成文档"的低价值段落。
3. monorepo 多文件时跑 `python scripts/conflicts.py <项目根>`：检测跨文件矛盾规则
   （缩进/引号/命名/分支等），**暴露冲突让用户选一个、别取平均**；识别 B6"有意覆盖"不误报。
4. 汇总成报告：**问题 → 为什么是问题 → 具体改法**。高优先级（敏感信息、超长）先列。
5. 问用户要不要按建议改；改时走最小 diff。

### evolve —— 从教训升级成规则（人在环，四个时机）

四个进化时机（用户已确认全要）：
- **会话/任务收尾**：回顾本轮，有没有「下次还会重复解释」的事？提成候选。
- **出错被纠正时**：用户纠正你后，立刻把这条教训（**带原因**）记为候选。
- **手动审查**：用户跑审查命令时，主动扫候选。
- **Auto Memory 策展**：跑 `python scripts/memory_digest.py`，从
  `~/.claude/projects/<proj>/memory/MEMORY.md` 找反复出现 ≥2 次的模式。

升级流程（详见 `evolution-playbook.md`）：
1. 收集候选 → 2. 过准入门槛（答不上"不写会错什么"就丢弃）→ 3. 写成
「可执行 + 配反例 + 一句原因」的规则 → 4. **给用户看 diff 等确认** → 5. 最小 diff 写入
正确的文件（就近原则，见 orchestrate）→ 6. 若来自 auto-memory，**确认已写进 CLAUDE.md 后**
用 `python scripts/graduate.py <记忆文件> [项目根]`（默认 dry-run，加 `--confirm` 才删）从 memory
删除并清理 MEMORY.md 指针，腾出官方 200 行/25KB 预算。

🔴 **CHECKPOINT（第 4 步，不可跳过）**：写入任何 CLAUDE.md / 删除任何 memory 前，先把 diff 给用户、
等明确确认。hook 和脚本只产候选/dry-run，**绝不**自动改写 CLAUDE.md。`graduate --confirm` 前必须先
确认那条规则已升级进 CLAUDE.md，否则会丢失内容。

### orchestrate —— 多 CLAUDE.md 定位与编排（monorepo）

0. **自省（先跑）**：`python scripts/introspect.py <项目根> [--editing <文件>]` 输出"加载体检表"——
   会加载哪些 CLAUDE.md、合并多少字节（是否逼近 40000 告警线）、哪条 `.claude/rules` 的 paths glob
   会因编辑某文件触发、有无外部 @import 警告、AGENTS.md 是否已 @import。官方只有 `/memory show`，
   silk-starry 多了"预测某次编辑会附加哪些规则 + 字节预算"。
1. **定位**：用户问"改 X 该看哪个"时，跑 `python scripts/locate.py <文件路径>`，
   按「就近原则」返回应读/改的 CLAUDE.md 链（从根到最近的子目录）。
2. **分层**：根 CLAUDE.md 放跨仓共享规范（commit 格式、全局禁区、导航）；
   子模块 CLAUDE.md 放各自框架/测试/禁区。冲突时**就近层权重更高**——但别依赖加载
   顺序解决冲突，要保证规则不矛盾。
3. **导航索引**：可用 `assets/index-template.md` 在根 CLAUDE.md 里生成"什么场景看哪个文件"
   的索引。
4. **AGENTS.md 共存 / 跨工具同步**：Claude Code 只读 CLAUDE.md。跑
   `python scripts/sync_targets.py <项目根>` 盘点各工具记忆文件并给打通建议；若已有 AGENTS.md，
   在 CLAUDE.md 顶部 `@AGENTS.md` import（可加 `--add-agents-import` 安全自动加），别复制两份。
   对 Cursor/Copilot 只生成指针、不复制全文（防漂移）。详见 `orchestration.md`。

### 失败兜底（显式分支，遇到就按这个走）
- generate 探测不出技术栈 → 用 `templates/generic.md` 起手，并问用户补确认栈，**不要瞎猜**。
- audit/generate 发现敏感信息（脚本报 🔴）→ 在报告/文件里**只说"X 处凭证应移到 .env"**，
  **绝不把凭证原值复述**进 CLAUDE.md 或报告。
- `memory_digest.py` 报"未找到 auto-memory 目录" → 多半是版本 <2.1.59 或路径推导错；
  让用户用 `--memory-dir <dir>` 显式指定，**不要**当作"没有可升级内容"。
- locate 返回"路径上没有任何 CLAUDE.md" → 转 generate 先建一个，别继续编排空气。
- conflicts 报冲突但其实是有意覆盖 → 确认子文件是否声明了"覆盖"，是则按有意覆盖处理、不强改。
- 脚本报错/超时 → 当作"未知"继续，不阻断；把失败如实告诉用户，别假装跑过。

---

## 四、脚本（确定性的事交给脚本，判断的事你来）

全部用 `python`（Windows 上不是 `python3`），UTF-8，只读不写（除非动作要求）。

| 脚本 | 用途 | 调用 |
|---|---|---|
| `scripts/scan.py` | 扫全仓 CLAUDE.md/AGENTS.md，列路径/行数/token/缺失 | `python scripts/scan.py <根目录>` |
| `scripts/audit.py` | 单文件体检：超长/敏感/空泛/冲突/失效链接 | `python scripts/audit.py <文件>` |
| `scripts/locate.py` | 给定文件路径 → 就近定位该读/改哪个 CLAUDE.md | `python scripts/locate.py <文件路径>` |
| `scripts/conflicts.py` | 跨文件冲突检测：缩进/引号/命名/分支等轴的矛盾，识别"有意覆盖" | `python scripts/conflicts.py <项目根>` |
| `scripts/introspect.py` | 加载自省：会加载哪些记忆/合并字节/哪条 glob 规则在编辑某文件时触发/外部 import 警告 | `python scripts/introspect.py <项目根> [--editing <文件>]` |
| `scripts/memory_digest.py` | 从 auto-memory 找反复模式 → 升级候选 | `python scripts/memory_digest.py [项目根]` |
| `scripts/graduate.py` | 升级闭环收尾：把已升级的记忆从 memory 删除并清理 MEMORY.md 指针（dry-run 默认，`--confirm` 执行） | `python scripts/graduate.py <记忆文件> [项目根] [--confirm]` |
| `scripts/sync_targets.py` | 跨工具盘点：AGENTS.md↔CLAUDE.md 打通建议（`--add-agents-import` 安全加 @import） | `python scripts/sync_targets.py <项目根>` |
| `scripts/install_hooks.py` | 一键把轻量 hook 装进目标项目 `.claude/settings.json` | `python scripts/install_hooks.py <项目根>` |
| `scripts/memory_doctor.py` | Auto Memory 体检：MEMORY.md 超限/缺 description/陈旧/失效指针/记忆 settings 安全 | `python scripts/memory_doctor.py [项目根]` |
| `scripts/disk_hygiene.py` | `~/.claude` 磁盘膨胀体检：分清可清理的历史日志 vs 不能动的记忆 | `python scripts/disk_hygiene.py` |

脚本路径相对 skill 目录；从任意 cwd 调用时用 skill 的绝对路径。

---

## 五、轻量 Hook（实现"何时进化"，项目级，一键安装）

`scripts/install_hooks.py` 会把两个 hook 注册进**目标项目**的 `.claude/settings.json`
（不污染其他项目，与已有 hook 合并而非覆盖）：

- **SessionStart**：开会话时把"有 N 条待审升级候选 / CLAUDE.md 已 X 天未体检"注入上下文
  （只有 SessionStart/Stop 的 stdout 能回注）。
- **Stop**：本轮结束时若检测到反复纠正，追加候选到 `.claude/silk-starry/candidates.jsonl`
  （**只记录，不改 CLAUDE.md**），并提示下次运行 evolve。务必查 `stop_hook_active` 防死循环。

hook 脚本本体在 `scripts/hooks/`。安装前先告诉用户会改它项目的 settings.json。

---

## 六、🔴 红线 / 绝不做（违反任何一条都算事故）

- 🔴 **绝不**自动改写 CLAUDE.md / 删 memory——写入前必给 diff、等用户确认（hook 只产候选）。
- 🔴 **绝不**把读到的明文凭证（key/token/密码/内网 IP）复述进 CLAUDE.md 或报告——转写成"配置在 .env"。
- 🔴 **绝不** `graduate --confirm` 删除尚未升级进 CLAUDE.md 的 memory。
- 🔴 **绝不**改动工具托管块（如 trellis 的 `<!-- TRELLIS:START/END -->`、被 codegen 生成的文件）。
- 🔴 **绝不**靠加载顺序"摆平"两条矛盾规则——暴露冲突让用户选一条，别取平均。
- 🔴 **绝不**把代码能看出来的东西（目录树/架构/技术栈版本）写进 CLAUDE.md。
- 🔴 **绝不**把规则塞进 CLAUDE.md 来当硬约束——硬约束（禁 push main 等）用 PreToolUse hook。

## 七、自检清单（每次写/改完 CLAUDE.md 都过一遍）

- [ ] 根文件 ≤200 行（理想 ≤60）？超了拆 `.claude/rules/` 或 `@import`。
- [ ] 每条规则都能答上"不写会错什么具体的事"？
- [ ] 规则可自动执行、配了反例？
- [ ] 没有代码能看出来的内容（目录树/架构罗列）？
- [ ] 没有敏感信息（key/token/密码/内网 IP）？
- [ ] 禁区和"提交前必跑"命令写了吗？
- [ ] 改动是最小 diff、没顺手重排既有内容？
