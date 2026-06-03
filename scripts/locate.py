#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""silk-starry: 给定一个文件/目录路径，按"就近原则"列出应读/改的 CLAUDE.md 链。

用法:  python locate.py <文件或目录路径> [仓库根]

从该路径向上走到仓库根（或文件系统根），收集路径上的每个 CLAUDE.md，
越靠近目标的越具体、权重越高（列在最后并标记 ← 最相关）。
只读。
"""
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

STOP_MARKERS = {".git", ".hg", ".svn"}


def outermost_repo_root(start: Path):
    """找最外层的 vcs 根（nested 子仓时取最外面那个），仅作展示提示用。"""
    cur = start if start.is_dir() else start.parent
    found = None
    for p in [cur, *cur.parents]:
        if any((p / m).exists() for m in STOP_MARKERS):
            found = p  # 不 break，继续向上找最外层
    return found


def main():
    if len(sys.argv) < 2:
        print("用法: python locate.py <文件或目录路径> [边界根]")
        sys.exit(1)
    target = Path(sys.argv[1]).resolve()
    # 可选的"边界根"：到此为止不再向上。不给则走到文件系统根。
    explicit_root = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else None

    start_dir = target if target.is_dir() else target.parent

    # 关键：Claude Code 实际从 cwd 一路向上加载 CLAUDE.md，**不受 .git 边界限制**
    # （monorepo 里子目录各有 .git 时尤其重要）。所以这里收集 start_dir 到边界根/文件系统根
    # 路径上的所有 CLAUDE.md。
    chain_dirs = [start_dir]
    cur = start_dir
    while cur.parent != cur:
        if explicit_root and cur == explicit_root:
            break  # 到达边界根，含它本身，不再向上
        cur = cur.parent
        chain_dirs.append(cur)
    chain_dirs = list(reversed(chain_dirs))  # 文件系统上层 → 最近

    repo = outermost_repo_root(target)
    print(f"# 定位: {target}")
    if repo:
        print(f"最外层 vcs 根: {repo}")
    print()

    hits = []
    for d in chain_dirs:
        for name in ("CLAUDE.md", "CLAUDE.local.md"):
            f = d / name
            if f.exists():
                hits.append(f)
    root = chain_dirs[0]  # 仅用于相对路径展示

    if not hits:
        print("路径上没有任何 CLAUDE.md。")
        print(f"建议: 用 generate 在 {start_dir} 或仓库根创建一份。")
        return

    print("应读/改的 CLAUDE.md（根 → 最近，越靠后越具体、权重越高）:")
    for i, f in enumerate(hits, 1):
        try:
            rel = f.relative_to(root)
        except ValueError:
            rel = f
        tag = "   ← 最相关，新增模块特定规则优先写这里" if i == len(hits) else ""
        print(f"  {i}. {rel}{tag}")
    print("\n规则: 只影响本目录/模块的规则 → 写最相关那个；跨整个仓库的 → 写仓库根。")


if __name__ == "__main__":
    main()
