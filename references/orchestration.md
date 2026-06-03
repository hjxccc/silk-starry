# 多 CLAUDE.md 编排（monorepo）

> 顺带能力：当一个仓库有多个 CLAUDE.md（根 + 子模块）时，怎么定位、分层、共存。
> 配套脚本：`scripts/locate.py`（就近定位）、`scripts/scan.py`（全仓盘点）。

## 目录
- [就近原则](#就近原则)
- [根 vs 子模块分层](#根-vs-子模块分层)
- [冲突处理](#冲突处理)
- [导航索引](#导航索引)
- [AGENTS.md 共存](#agentsmd-共存)
- [典型场景：混栈 monorepo](#典型场景混栈-monorepo)

## 就近原则
"改某个文件该看/改哪个 CLAUDE.md？"——答案是**从仓库根到该文件所在目录路径上的所有
CLAUDE.md**，越靠近文件的越具体、权重越高。

`python scripts/locate.py <文件路径>` 会返回这条链，例如改
`acme-platform/web-app/src/x.vue`：
```
1. acme-platform/CLAUDE.md          (根：跨仓共享规范)
2. acme-platform/web-app/CLAUDE.md  (子：前端框架/测试/禁区) ← 最相关
```
新增规则时也按这条链决定写哪一层：只影响前端的 → 写子模块；跨所有仓的 → 写根。

## 根 vs 子模块分层
| 层 | 放什么 |
|---|---|
| **根 CLAUDE.md** | 跨仓共享：commit 格式、全局禁区、分支协作约定、"什么场景看哪个子模块文档"的导航索引 |
| **子模块 CLAUDE.md** | 该模块特定：技术栈偏好、构建/测试命令、框架约定、本模块禁区 |
| **`~/.claude/CLAUDE.md`** | 跨**项目**的个人偏好（通用行为契约适合放这里，别塞进每个项目根） |
| **`.claude/rules/*.md`** | 按 glob 懒加载的细则（如 `# Glob: **/*.java`），避免主文件膨胀 |

每个文件仍各自受 ≤200 行约束。子目录 CLAUDE.md 按需懒加载（进入该目录才注入），所以
monorepo 里多个子 CLAUDE.md 不会一次性全塞进 context——这是 monorepo 友好的关键。

## 冲突处理（B8）
- 加载是**拼接不是覆盖**，就近层只是软权重略高。**不要依赖加载顺序**让两条矛盾规则"自动正确"。
- 跑 `python scripts/conflicts.py <项目根>` 检测跨文件矛盾（缩进/引号/命名/分支等轴）。
  按文章共识：**暴露冲突让用户选一个，别取平均**，并把另一个标记清理。
- 同一规则在根和子重复出现 → 提示收敛到一处（通常留在更具体的那层，或都收进根）。

## monorepo 覆盖语义（B6，借 Codex AGENTS.override.md）
官方 CLAUDE.md 只能拼接累加，没有"子目录替换父级"。当某子模块**确实**要与根约定相悖
（如 legacy 子项目用完全不同的风格），不要让它和根"打架"，而是**显式声明覆盖**：
- 在子模块 CLAUDE.md 里写明：「本目录覆盖根规则 X：用 Y（原因：…）」，关键词带"覆盖/override"。
- 这样 `conflicts.py` 会把它识别为 **【有意覆盖】** 而非"潜在冲突"，不误报。
- 只在真有必要时用；能统一就统一——"半途而废的迁移让模型困惑"。

## 导航索引
在根 CLAUDE.md 顶部放一个"场景 → 看哪个文件"的小索引（模板见
`assets/index-template.md`），帮 Claude 和人快速路由。保持精简，只列子模块入口，不复制内容。

## AGENTS.md 共存 / 跨工具同步（B2）
- **Claude Code 只读 CLAUDE.md，不读 AGENTS.md**。AGENTS.md 是跨工具开放标准
  （Codex/Cursor/Copilot/Gemini 等 20+ 工具，已进 Linux Foundation AAIF），很多项目会生成并托管它。
- **先盘点**：`python scripts/sync_targets.py <项目根>` 列出各工具记忆文件现状 + 给打通建议。
- 不要把内容复制两份。推荐工具无关核心放 AGENTS.md，CLAUDE.md 顶部 `@AGENTS.md` import
  （`--add-agents-import` 可安全自动加这一行），再在下面追加 Claude 专属规则。
- 对 Cursor（`.cursor/rules` + globs）/ Copilot（`*.instructions.md` + applyTo）：**只生成指向
  AGENTS.md 的指针，不复制全文**——复制会造成多份漂移。silk-starry 默认不替你写他工具配置，需显式开启。
- 若 AGENTS.md 有托管块（如 trellis 的 `<!-- TRELLIS:START/END -->`），**别手改托管块**，
  那是工具自动维护的。silk-starry 只动 CLAUDE.md 和非托管区域。

## 典型场景：混栈 monorepo
设想一个 monorepo（多子仓，Java/Python/Vue 混栈），审查常见现状：
- 根有 CLAUDE.md(跨仓管理) + 可能有 AGENTS.md(被某工具托管)。
- 子模块文档不齐：部分后端子仓有完整 CLAUDE.md；**前端子仓常缺 CLAUDE.md**（只有 AGENTS.md 模板）；
  少数模块完全无 `.claude`。
- 出现指向**项目外文件**的外部引用（如 `<repo 外的某规范.txt>`）——审查应标记为脆弱依赖。

编排建议：
1. 用 `scan.py` 盘点缺失 → 优先给缺文档的前端子仓 `generate` 一份 Vue 模板 CLAUDE.md。
2. 根 CLAUDE.md 加导航索引：哪个子仓看哪个文档、共享规范指向哪里。
3. 把跨仓重复的规范（如数据库迁移约定）收敛：要么各子仓 `@import` 一份共享 rule，
   要么在根统一说明，避免多份漂移。
4. 被工具托管的 AGENTS.md 托管块不动；子仓的 AGENTS.md 模板可让 CLAUDE.md `@import` 后补充框架规范。
