#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""silk-starry: 跨工具记忆同步盘点（B2）。一处维护，多工具受益。

AGENTS.md 已是事实标准（进 Linux Foundation AAIF，20+ 工具）。Claude Code 不读 AGENTS.md，
社区标准做法是在 CLAUDE.md 顶部 `@AGENTS.md` 导入，避免一份约定在多个工具各写一遍漂移。

四大主流 agent 读的就是 silk-starry 管的这两份文件：
  - Claude Code → CLAUDE.md（原生）
  - Codex (OpenAI) → AGENTS.md
  - OpenCode (sst) → AGENTS.md（无则回退读 CLAUDE.md）；全局 ~/.config/opencode/AGENTS.md
  - OpenClaw → AGENTS.md（工作区主指令文件，配合 SOUL.md/MEMORY.md）
所以「CLAUDE.md + AGENTS.md 打通」即等于覆盖这四个平台。

用法:
  python sync_targets.py <项目根>                    # 盘点 + 建议（只读）
  python sync_targets.py <项目根> --add-agents-import  # 安全动作：给 CLAUDE.md 顶部加一行 @AGENTS.md

设计原则（保守）:
  - 默认只盘点 + 给建议，不改任何文件。
  - 唯一的写动作是 `--add-agents-import`（幂等地往 CLAUDE.md 加一行 `@AGENTS.md`），非破坏性。
  - 对 Cursor/Copilot 等只做"建议"，不替你复制正文（复制全文会造成多份漂移）。
"""
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# 各工具的记忆/指令文件（相对项目根）。
# 前四个是用户最常问的主流 agent；silk-starry 直接管 CLAUDE.md + AGENTS.md，正好覆盖它们。
TARGETS = {
    "Claude Code": ["CLAUDE.md", ".claude/CLAUDE.md", "CLAUDE.local.md"],
    "Codex (OpenAI)": ["AGENTS.md"],
    "OpenCode (sst)": ["AGENTS.md", "CLAUDE.md"],  # 无 AGENTS.md 时回退读 CLAUDE.md
    "OpenClaw": ["AGENTS.md", "SOUL.md", "MEMORY.md"],  # 工作区主指令=AGENTS.md
    "AGENTS.md (跨工具标准)": ["AGENTS.md"],
    "Cursor": [".cursor/rules", ".cursorrules"],
    "GitHub Copilot": [".github/copilot-instructions.md", ".github/instructions"],
    "Gemini CLI": ["GEMINI.md"],
    "Windsurf": [".windsurf/rules", ".windsurfrules"],
    "Cline": [".clinerules"],
}


def add_agents_import(claude_md: Path) -> str:
    text = claude_md.read_text(encoding="utf-8", errors="replace")
    if "@AGENTS.md" in text:
        return "already"
    lines = text.splitlines()
    # 插在第一个标题行之后；没有标题就插最前
    insert_at = 0
    for i, ln in enumerate(lines):
        if ln.lstrip().startswith("#"):
            insert_at = i + 1
            break
    new = lines[:insert_at] + ["", "@AGENTS.md  <!-- silk-starry: 跨工具共享约定，统一在 AGENTS.md 维护 -->"] + lines[insert_at:]
    claude_md.write_text("\n".join(new) + "\n", encoding="utf-8")
    return "added"


def main():
    args = sys.argv[1:]
    do_add = "--add-agents-import" in args
    args = [a for a in args if a != "--add-agents-import"]
    if not args:
        print("用法: python sync_targets.py <项目根> [--add-agents-import]")
        sys.exit(1)
    root = Path(args[0]).resolve()
    if not root.is_dir():
        print(f"不是目录: {root}")
        sys.exit(1)

    print(f"# 跨工具记忆盘点 {root}\n")
    present = {}
    for tool, paths in TARGETS.items():
        hits = [p for p in paths if (root / p).exists()]
        present[tool] = hits
        mark = "✅ " + ", ".join(hits) if hits else "—"
        print(f"  {tool:<26} {mark}")

    claude = root / "CLAUDE.md"
    agents = root / "AGENTS.md"
    has_claude = claude.exists()
    has_agents = agents.exists()

    print("\n## 建议")
    if has_agents and has_claude:
        imported = "@AGENTS.md" in claude.read_text(encoding="utf-8", errors="replace")
        if imported:
            print("  ✅ CLAUDE.md 已 @import AGENTS.md —— 跨工具核心约定单一来源，理想状态。")
        else:
            print("  ▶ CLAUDE.md 与 AGENTS.md 并存但未打通：建议在 CLAUDE.md 顶部 `@AGENTS.md` 导入，"
                  "把工具无关核心放 AGENTS.md（Cursor/Copilot/Codex 都读它），CLAUDE.md 只补 Claude 专属。"
                  " 可加 --add-agents-import 自动加这行。")
    elif has_agents and not has_claude:
        print("  ▶ 只有 AGENTS.md：建议建一个 CLAUDE.md 用 `@AGENTS.md` 导入 + 补 Claude 专属规则。")
    elif has_claude and not has_agents:
        print("  ▶ 只有 CLAUDE.md：若团队还用 Cursor/Copilot/Codex，建议把**工具无关**的核心约定抽到 "
              "AGENTS.md，再让 CLAUDE.md `@AGENTS.md` 导入——一处维护多工具受益。")
    else:
        print("  ▶ 还没有 CLAUDE.md/AGENTS.md：用 generate 先建 CLAUDE.md；多工具团队可同时建 AGENTS.md。")

    # 其他工具镜像（只建议，不复制正文）
    others = [t for t in ("Cursor", "GitHub Copilot", "Gemini CLI") if not present[t]]
    if (has_agents or has_claude) and others:
        print(f"  ▶ 未配置 {', '.join(others)}：如团队用到，可生成**指向 AGENTS.md 的指针**（如 Cursor 规则里"
              " 引用、Copilot 用 applyTo 指向），不要复制全文，避免多份漂移。（silk-starry 默认不替你写他工具配置。）")

    if do_add:
        print("\n## 执行 --add-agents-import")
        if not has_agents:
            print("  跳过：没有 AGENTS.md 可导入。")
        elif not has_claude:
            print("  跳过：没有 CLAUDE.md。请先 generate。")
        else:
            r = add_agents_import(claude)
            print("  已是导入状态，未改动。" if r == "already" else "  ✅ 已在 CLAUDE.md 顶部加入 `@AGENTS.md`。")


if __name__ == "__main__":
    main()
