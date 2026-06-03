#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""silk-starry SessionStart hook: 把"待审升级候选 + CLAUDE.md 体检提醒"注入上下文。

SessionStart 的 stdout 会被加入 Claude 的上下文（这是少数能回注的 hook 之一）。
本 hook 只读 + 打印提醒，绝不改任何文件。失败时静默退出 0，不打断会话。
"""
import json
import sys
import time
from pathlib import Path


def main():
    cwd = Path.cwd()
    notes = []

    # 1. 待审候选
    cand = cwd / ".claude" / "silk-starry" / "candidates.jsonl"
    if cand.exists():
        try:
            lines = [l for l in cand.read_text(encoding="utf-8").splitlines() if l.strip()]
            if lines:
                notes.append(f"silk-starry: 有 {len(lines)} 条待审 CLAUDE.md 升级候选，"
                             f"可让我用 evolve 动作集中处理。")
        except Exception:
            pass

    # 2. 根 CLAUDE.md 体检提醒（>200 行 或 >30 天没动）
    claude_md = cwd / "CLAUDE.md"
    if claude_md.exists():
        try:
            n = claude_md.read_text(encoding="utf-8", errors="replace").count("\n") + 1
            if n > 200:
                notes.append(f"silk-starry: 根 CLAUDE.md {n} 行(>200)，建议 audit 精简。")
            age_days = (time.time() - claude_md.stat().st_mtime) / 86400
            if age_days > 30:
                notes.append(f"silk-starry: 根 CLAUDE.md 已 {int(age_days)} 天未更新，"
                             f"可做一次 audit 体检。")
        except Exception:
            pass

    if notes:
        # additionalContext 会被注入；同时打印到 stdout 兜底
        out = "\n".join("• " + s for s in notes)
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": out,
            }
        }))
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(0)
