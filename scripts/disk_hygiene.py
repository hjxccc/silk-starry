#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""silk-starry: ~/.claude 磁盘膨胀体检（记忆系统管家）。

背景（社区实证）: Auto Memory 本身很小（MEMORY.md ≤25KB），磁盘膨胀的真凶从来不是它，而是:
  - file-history/  文件快照历史（有用户累积到 300GB）
  - debug/         调试日志，从不自动清
  - projects/<x>/  里的 session transcripts（JSONL，可达 MB–GB）
silk-starry 帮你定位真凶、给安全清理建议，并提示用 cleanupPeriodDays 让官方自动清。

用法:
  python disk_hygiene.py                 # 体检 ~/.claude
  python disk_hygiene.py --base <dir>    # 指定根（默认 ~/.claude）
  python disk_hygiene.py --top 15        # 列出最大的 N 个子目录（默认 12）

只读：只统计、只建议，**绝不删除任何东西**。清理命令仅打印给你，由你自己执行。
"""
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

FILE_CAP = 800_000  # 单目录文件数超此值就停止精确统计，避免在超大目录上卡死


def human(n: int) -> str:
    f = float(n)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if f < 1024 or unit == "TB":
            return f"{f:.1f}{unit}" if unit != "B" else f"{int(f)}B"
        f /= 1024
    return f"{f:.1f}TB"


def dir_size(path: Path):
    """返回 (字节, 文件数, 是否被截断)。截断时 size/count 为已统计到的下限。"""
    total = count = 0
    truncated = False
    stack = [path]
    while stack:
        d = stack.pop()
        try:
            with __import__("os").scandir(d) as it:
                for e in it:
                    try:
                        if e.is_symlink():
                            continue
                        if e.is_dir(follow_symlinks=False):
                            stack.append(Path(e.path))
                        else:
                            total += e.stat(follow_symlinks=False).st_size
                            count += 1
                            if count >= FILE_CAP:
                                return total, count, True
                    except OSError:
                        continue
        except OSError:
            continue
    return total, count, truncated


# 已知目录的处置建议
DISPOSITION = {
    "file-history": ("🟢 可安全清理", "文件快照历史，非记忆。膨胀重灾区。"),
    "debug": ("🟢 可安全清理", "调试日志，非记忆，从不自动清。"),
    "shell-snapshots": ("🟢 可安全清理", "shell 快照，非记忆。"),
    "downloads": ("🟢 可清理", "下载缓存。"),
    "todos": ("🟡 谨慎", "任务列表，确认不用再清。"),
    "projects": ("🟡 部分可清", "含各项目 transcripts(JSONL,可 grep 后清) + memory/(别动！这是记忆)。"),
    "memory": ("🔴 别动", "这是你的 Auto Memory 记忆本体。"),
    "statsig": ("🟢 可清理", "特性开关缓存。"),
    "plugins": ("🔴 别动", "已装插件/skill。"),
    "skills": ("🔴 别动", "已装 skill。"),
}


def main():
    args = sys.argv
    base = Path.home() / ".claude"
    if "--base" in args:
        i = args.index("--base")
        if i + 1 < len(args):
            base = Path(args[i + 1]).expanduser().resolve()
    top = 12
    if "--top" in args:
        i = args.index("--top")
        if i + 1 < len(args):
            try:
                top = int(args[i + 1])
            except ValueError:
                pass

    print(f"# ~/.claude 磁盘体检\n根目录: {base}\n")
    if not base.is_dir():
        print(f"目录不存在: {base}")
        return

    rows = []
    grand = 0
    for child in base.iterdir():
        if child.is_symlink():
            continue
        if child.is_dir():
            size, count, trunc = dir_size(child)
            rows.append((child.name, size, count, trunc))
            grand += size
        else:
            try:
                grand += child.stat().st_size
            except OSError:
                pass
    rows.sort(key=lambda r: -r[1])

    print(f"总占用（含截断下限）: ~{human(grand)}\n")
    print("## 最大的子目录（大→小）")
    print("目录 | 大小 | 文件数 | 处置")
    print("---|---|---|---")
    bloat = []
    for name, size, count, trunc in rows[:top]:
        disp, why = DISPOSITION.get(name, ("⚪ 自行判断", ""))
        cnt = f"{count}{'+(截断)' if trunc else ''}"
        print(f"{name} | {human(size)} | {cnt} | {disp}")
        if disp.startswith("🟢") and size > 50 * 1024 * 1024:  # >50MB 的可清理目录
            bloat.append((name, size))

    # projects/ 里再钻一层：分清 transcripts vs memory
    projects = base / "projects"
    if projects.is_dir():
        sess_total = mem_total = 0
        for proj in projects.iterdir():
            if not proj.is_dir():
                continue
            for sub, acc in (("sessions", "s"), ("memory", "m")):
                p = proj / sub
                if p.is_dir():
                    s, _, _ = dir_size(p)
                    if acc == "s":
                        sess_total += s
                    else:
                        mem_total += s
            # transcripts 也可能直接是 *.jsonl
        print(f"\n## projects/ 细分")
        print(f"  - 所有 sessions/ transcripts 合计: ~{human(sess_total)}  → 🟢 可 grep 备查后清理")
        print(f"  - 所有 memory/ 记忆合计: ~{human(mem_total)}  → 🔴 别动（这是你的记忆，且很小）")

    print("\n## 建议")
    print("  1. 让官方自动清（推荐）: 在 ~/.claude/settings.json 加 \"cleanupPeriodDays\": 7 ，"
          "旧 transcripts/快照会按期清理。")
    if bloat:
        print("  2. 手动清理以下大目录（**只清非记忆的历史/日志**，命令请你自己执行）:")
        for name, size in bloat:
            print(f"     # {name} ~{human(size)}")
            print(f"     rm -rf \"{base / name}\"")
    print("  3. ⚠️ 永远不要删 memory/（Auto Memory 本体）和 plugins//skills/。")
    print("  4. transcripts 想留档就先 grep 出关键错误/解决方案，再清整目录。")


if __name__ == "__main__":
    main()
