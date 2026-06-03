#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""silk-starry: 升级闭环的"清理来源"步骤（B1 graduation pipeline 的机械部分）。

当一条 auto-memory 记忆**已经过你确认、升级写进了 CLAUDE.md** 之后，用本脚本把它从 memory
删除，腾出官方 200 行/25KB 预算，并保持 MEMORY.md 索引一致（删掉指向它的指针行）。

用法:
  python graduate.py <memory文件名或路径> [项目根]        # 预演(dry-run)：只打印将删什么
  python graduate.py <memory文件名或路径> [项目根] --confirm  # 真正删除文件 + 清理 MEMORY.md 指针

安全约束:
  - 默认 dry-run，必须 --confirm 才动文件。
  - **只允许操作 auto-memory 目录内的文件**，目标在目录外一律拒绝。
  - 这一步只做"升级后清理来源"，不写 CLAUDE.md（写入是模型给你看 diff 后做的，本脚本不碰）。
"""
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def canonical_git_root(start: Path) -> Path:
    cur = start if start.is_dir() else start.parent
    for p in [cur, *cur.parents]:
        if (p / ".git").exists():
            return p
    return start


def derive_key(root: Path) -> str:
    s = str(canonical_git_root(root.resolve()))
    for ch in (":", "\\", "/"):
        s = s.replace(ch, "-")
    return s


def memory_dir_for(root: Path) -> Path:
    return Path.home() / ".claude" / "projects" / derive_key(root) / "memory"


def main():
    args = [a for a in sys.argv[1:]]
    confirm = "--confirm" in args
    args = [a for a in args if a != "--confirm"]
    if not args:
        print("用法: python graduate.py <memory文件名或路径> [项目根] [--confirm]")
        sys.exit(1)
    target_arg = args[0]
    root = Path(args[1]).resolve() if len(args) > 1 else Path.cwd()
    mem_dir = memory_dir_for(root)

    if not mem_dir.is_dir():
        print(f"未找到 auto-memory 目录: {mem_dir}")
        sys.exit(1)

    # 解析目标：既支持纯文件名，也支持绝对/相对路径
    cand = Path(target_arg)
    target = cand if cand.is_absolute() else (mem_dir / target_arg)
    target = target.resolve()

    # 安全：必须在 memory 目录内
    if mem_dir.resolve() not in target.parents:
        print(f"拒绝：目标 {target} 不在 auto-memory 目录内（{mem_dir}）。本脚本只清理记忆目录。")
        sys.exit(1)
    if not target.is_file():
        print(f"文件不存在: {target}")
        sys.exit(1)

    entry = mem_dir / "MEMORY.md"
    # 找出 MEMORY.md 里指向该文件的指针行
    pointer_hits = []
    if entry.exists():
        fname = target.name
        for i, ln in enumerate(entry.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if fname in ln:
                pointer_hits.append((i, ln.strip()))

    print(f"# graduate（升级后清理来源）\nmemory 目录: {mem_dir}")
    print(f"目标记忆文件: {target.name}\n")
    print("将删除该 topic 文件，并从 MEMORY.md 删除以下指针行:")
    if pointer_hits:
        for i, ln in pointer_hits:
            print(f"  - L{i}: {ln[:90]}")
    else:
        print("  （MEMORY.md 里没有指向它的指针行）")

    if not confirm:
        print("\n(dry-run 未改动。确认无误后加 --confirm 执行。)")
        print("提醒：执行前请确认这条记忆**已经升级写进 CLAUDE.md**，否则会丢失。")
        return

    # 执行：删指针行 + 删文件
    if pointer_hits and entry.exists():
        kept = [ln for i, ln in enumerate(
            entry.read_text(encoding="utf-8", errors="replace").splitlines(), 1)
            if target.name not in ln]
        entry.write_text("\n".join(kept) + "\n", encoding="utf-8")
    target.unlink()
    print(f"\n✅ 已删除 {target.name} 并清理 MEMORY.md 指针。预算已腾出。")


if __name__ == "__main__":
    main()
