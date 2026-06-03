#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""silk-starry: 从官方 Auto Memory 里挖"反复出现、值得升级进 CLAUDE.md"的候选。

用法:
  python memory_digest.py [项目根目录]        # 自动推导该项目的 auto-memory 目录
  python memory_digest.py --memory-dir <dir>  # 直接指定 memory 目录

官方 auto-memory 位置: ~/.claude/projects/<key>/memory/ ，其中 <key> 由项目绝对路径把
  ':' '\\' '/' 都替换成 '-' 得到（例: D:\\projects\\acme -> D--projects-acme）。

产出三层（对齐 Claude Code 官方 memdir 的召回方式：让模型读 header 清单按需判断，而非靠词频）：
  1) 文件清单 manifest（[type] 文件名 (多久前): description）—— 模型据此挑哪些值得升级
  2) ⭐ Errors & Corrections / Learnings 区段条目 —— 升级规则的最佳来源
  3) 其余原始 bullet —— 兜底
时效用"多久前"而非 ISO（模型对日期算术不敏感，"47 天前"才会触发陈旧推理）。只读。

注意: 这是启发式挖掘，产出的是**候选**，必须经准入门槛 + 用户确认才写入 CLAUDE.md。
"""
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def canonical_git_root(start: Path) -> Path:
    """auto-memory 按 git 仓库根派生 key（worktree 共享），不在仓库内则用路径本身。
    对应 ClaudeCode 源码 paths.ts: findCanonicalGitRoot(projectRoot) ?? projectRoot。"""
    cur = start if start.is_dir() else start.parent
    for p in [cur, *cur.parents]:
        if (p / ".git").exists():
            return p
    return start


def derive_key(project_root: Path) -> str:
    # projects/<key> 的 key = 绝对路径把 ':' '\\' '/' 都换成 '-'
    # （如 D:\projects\acme -> D--projects-acme）。
    s = str(canonical_git_root(project_root.resolve()))
    for ch in (":", "\\", "/"):
        s = s.replace(ch, "-")
    return s


def find_memory_dir(args):
    if "--memory-dir" in args:
        i = args.index("--memory-dir")
        if i + 1 >= len(args):
            print("--memory-dir 需要提供目录路径")
            sys.exit(1)
        return Path(args[i + 1]).expanduser().resolve()
    root = Path(args[1]).resolve() if len(args) > 1 else Path.cwd()
    key = derive_key(root)
    cand = Path.home() / ".claude" / "projects" / key / "memory"
    return cand


# session 记忆里最值得升级成规则的两个区段（源码 SessionMemory 模板）
PRIORITY_SECTIONS = ("Errors & Corrections", "Learnings")


def human_age(mtime_ms: float) -> str:
    """对齐源码 memoryAge：人类可读时效（模型对 ISO 不敏感，对'47 天前'敏感）。"""
    d = max(0, int((time.time() * 1000 - mtime_ms) // 86_400_000))
    return "今天" if d == 0 else ("昨天" if d == 1 else f"{d} 天前")


def parse_header(path: Path):
    """读 frontmatter 的 description / type（只读前 30 行，对齐源码 scanMemoryFiles）。"""
    desc, mtype = None, None
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()[:30]
    except Exception:
        return desc, mtype
    if not (lines and lines[0].strip() == "---"):
        return desc, mtype
    for ln in lines[1:]:
        if ln.strip() == "---":
            break
        if ln.lower().startswith("description:"):
            desc = ln.split(":", 1)[1].strip().strip("'\"") or None
        elif ln.strip().lower().startswith("type:"):
            mtype = ln.split(":", 1)[1].strip() or None
    return desc, mtype


def main():
    args = sys.argv
    mem_dir = find_memory_dir(args)
    print(f"# Auto-Memory 策展\nmemory 目录: {mem_dir}\n")
    if not mem_dir.is_dir():
        print("未找到该项目的 auto-memory 目录。可能原因:")
        print("  - 这个项目还没积累 auto memory；")
        print("  - 路径推导不对，用 --memory-dir 显式指定；")
        print("  - 该 Claude Code 版本 <2.1.59 不支持 auto memory。")
        return

    # 递归收集 .md（含 topic 子目录与 logs/），排除索引 MEMORY.md，按 mtime 新→旧
    files = [p for p in mem_dir.rglob("*.md") if p.name != "MEMORY.md"]
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        print("memory 目录里只有 MEMORY.md 或为空，暂无 topic 候选。")
        return

    # 1) header manifest：模型据此挑哪些文件值得细看/升级（官方召回的输入形态）
    print(f"## 文件清单 manifest（共 {len(files)} 个 topic 文件，新→旧）")
    print("格式: [type] 文件名 (多久前): description —— 模型据此判断哪些值得升级\n")
    for f in files[:200]:
        desc, mtype = parse_header(f)
        age = human_age(f.stat().st_mtime * 1000)
        tag = f"[{mtype}] " if mtype else ""
        rel = f.relative_to(mem_dir)
        line = f"- {tag}{rel} ({age})"
        if desc:
            line += f": {desc}"
        print(line)

    # 2) 抽取高价值区段条目
    bullets = []        # 全部
    priority = []       # 来自 Errors & Corrections / Learnings
    for f in files:
        lines = f.read_text(encoding="utf-8", errors="replace").splitlines()
        section = ""
        in_fm = False
        for idx, ln in enumerate(lines):
            raw = ln.strip()
            # 跳过开头的 frontmatter 块（--- ... ---），避免把 key: value 当候选
            if idx == 0 and raw == "---":
                in_fm = True
                continue
            if in_fm:
                if raw == "---":
                    in_fm = False
                continue
            if raw.startswith("#"):
                section = raw.lstrip("#").strip()
                continue
            s = raw.lstrip("-*").strip()
            if len(s) > 8 and not s.startswith("["):
                bullets.append(s)
                if any(ps.lower() in section.lower() for ps in PRIORITY_SECTIONS):
                    priority.append(s)

    if priority:
        print("\n## ⭐ 高价值候选（来自 Errors & Corrections / Learnings 区段，优先升级）")
        for b in priority[:25]:
            print(f"  - {b[:100]}")

    print("\n## 其余候选条目（原始 memory bullet，供你判断是否升级）")
    for b in bullets[:40]:
        print(f"  - {b[:100]}")

    print("\n下一步（对齐官方召回方式）: 先看 manifest，凭 description + 时效挑出确定有用的少数文件细读；"
          "对每条候选过准入门槛——'不写这条 Claude 会做错哪件具体的事?'，答得上且可执行的，"
          "写成规则给用户看 diff 后再写入 CLAUDE.md；升级后从 memory 删除对应条目腾空间。"
          "注意时效：'多天前'的记忆若涉及 file:line/代码行为，先核对当前代码再固化。")


if __name__ == "__main__":
    main()
