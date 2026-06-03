#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""silk-starry: Auto Memory 体检（记忆系统管家）。

对齐官方 autoDream 的四阶段整合逻辑，但做成**按需 + 只读 + 人在环**：官方 autoDream 是后台
定时（24h + 5 会话）才整合，silk-starry 让你随时一键查体检表，且绝不自动改/删——删记忆是官方 agent 的职责。

用法:
  python memory_doctor.py [项目根目录]            # 自动推导该项目的 auto-memory 目录
  python memory_doctor.py --memory-dir <dir>       # 直接指定 memory 目录
  python memory_doctor.py [项目根] --stale-days 45 # 自定义"陈旧"阈值（默认 30 天）

检查项（全部只读、建议式）:
  1. MEMORY.md 索引体检：行数(>200)/字节(>25KB) —— 官方只加载前 200 行/25KB，超了后面读不到。
  2. topic 文件 frontmatter：缺 description（Sonnet 召回的唯一依据，缺了几乎不会被选中）/
     缺或非法 type（应 ∈ user|feedback|project|reference）。
  3. 陈旧：mtime 超过 --stale-days 的文件 —— 记忆永不自动过期，老记忆带"可能过时"风险，宜复核。
  4. 孤儿 topic：存在于 memory/ 但 MEMORY.md 索引里没引用 —— 不会被高效召回。
  5. 失效指针：MEMORY.md 索引指向的文件已不存在。
  6. 相对日期气味：条目含 昨天/今天/上周/recently —— autoDream 会转绝对日期，未转的是隐患。
  7. 记忆相关 settings 体检 + autoMemoryDirectory 安全（只能全局配；项目级配 = 劫持写入风险）。
"""
import json
import re
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# 复用 memory_digest 的目录派生 / 时效 / header 解析（同目录脚本）
sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from memory_digest import derive_key, human_age, parse_header  # noqa: E402
except Exception:  # 兜底：内联最小实现，保证独立可跑
    def derive_key(project_root):
        cur = project_root.resolve()
        root = cur
        for p in [cur, *cur.parents]:
            if (p / ".git").exists():
                root = p
                break
        s = str(root)
        for ch in (":", "\\", "/"):
            s = s.replace(ch, "-")
        return s

    def human_age(mtime_ms):
        d = max(0, int((time.time() * 1000 - mtime_ms) // 86_400_000))
        return "今天" if d == 0 else ("昨天" if d == 1 else f"{d} 天前")

    def parse_header(path):
        desc = mtype = None
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

MAX_LINES = 200
MAX_BYTES = 25 * 1024
VALID_TYPES = {"user", "feedback", "project", "reference"}
REL_DATE = re.compile(r"(昨天|今天|明天|前天|上周|下周|本周|这周|最近|目前|现在|"
                      r"yesterday|today|tomorrow|last week|next week|recently|currently)",
                      re.IGNORECASE)
AGE_MS = 86_400_000


def find_memory_dir(args):
    if "--memory-dir" in args:
        i = args.index("--memory-dir")
        if i + 1 >= len(args):
            print("--memory-dir 需要提供目录路径")
            sys.exit(1)
        return Path(args[i + 1]).expanduser().resolve()
    positional = [a for a in args[1:] if not a.startswith("--")
                  and args[args.index(a) - 1] != "--stale-days"]
    root = Path(positional[0]).resolve() if positional else Path.cwd()
    return Path.home() / ".claude" / "projects" / derive_key(root) / "memory"


def referenced_files(memory_md: Path):
    """从 MEMORY.md 索引里抽取被引用的 topic 文件名（[标题](xxx.md)）。"""
    refs = set()
    try:
        text = memory_md.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return refs
    for m in re.finditer(r"\(([^)]+?\.md)\)", text):
        refs.add(Path(m.group(1)).name)
    return refs


def read_global_settings():
    p = Path.home() / ".claude" / "settings.json"
    try:
        return json.loads(p.read_text(encoding="utf-8", errors="replace")), p
    except Exception:
        return None, p


def main():
    args = sys.argv
    stale_days = 30
    if "--stale-days" in args:
        i = args.index("--stale-days")
        if i + 1 < len(args):
            try:
                stale_days = int(args[i + 1])
            except ValueError:
                pass

    mem_dir = find_memory_dir(args)
    print(f"# Auto Memory 体检\nmemory 目录: {mem_dir}\n")

    red, yellow, info = [], [], []

    if not mem_dir.is_dir():
        print("未找到该项目的 auto-memory 目录。可能原因:")
        print("  - 这个项目还没积累 auto memory；")
        print("  - 路径推导不对，用 --memory-dir 显式指定；")
        print("  - 该 Claude Code 版本 <2.1.59 不支持 auto memory。")
        _settings_section(red, yellow, info)
        _emit(red, yellow, info)
        return

    memory_md = mem_dir / "MEMORY.md"
    refs = referenced_files(memory_md)

    # 1. MEMORY.md 索引体检
    if memory_md.exists():
        raw = memory_md.read_text(encoding="utf-8", errors="replace")
        nlines, nbytes = len(raw.splitlines()), len(raw.encode("utf-8"))
        msg = f"MEMORY.md 索引: {nlines} 行 / {nbytes} 字节"
        if nlines > MAX_LINES:
            red.append(f"{msg} —— 超过 200 行，**超出部分不会被加载**（官方只读前 200 行）。"
                       f"建议精简/合并，或让 autoDream 整合。")
        elif nbytes > MAX_BYTES:
            yellow.append(f"{msg} —— 超过 25KB 软上限，注意精简。")
        else:
            info.append(f"{msg} —— 在 200 行 / 25KB 预算内。")
    else:
        yellow.append("没有 MEMORY.md 索引文件 —— topic 文件将难以被高效召回（官方靠索引清单）。")

    # topic 文件
    topics = [p for p in mem_dir.rglob("*.md") if p.name != "MEMORY.md"]
    if not topics:
        info.append("没有 topic 记忆文件（只有索引或为空）。")
    else:
        info.append(f"共 {len(topics)} 个 topic 文件。")
    no_desc, bad_type, stale, rel_date, orphan = [], [], [], [], []
    on_disk = set()
    for f in topics:
        rel = f.relative_to(mem_dir)
        on_disk.add(f.name)
        desc, mtype = parse_header(f)
        if not desc:
            no_desc.append(str(rel))
        if mtype and mtype not in VALID_TYPES:
            bad_type.append(f"{rel} (type={mtype})")
        age_days = int((time.time() * 1000 - f.stat().st_mtime * 1000) // AGE_MS)
        if age_days > stale_days:
            stale.append((str(rel), age_days))
        try:
            body = f.read_text(encoding="utf-8", errors="replace")
        except Exception:
            body = ""
        if REL_DATE.search(body):
            rel_date.append(str(rel))
        if f.name not in refs and memory_md.exists():
            orphan.append(str(rel))

    # 2. frontmatter
    if no_desc:
        red.append(f"{len(no_desc)} 个 topic **缺 description** —— description 是 Sonnet 召回时"
                   f"唯一能看到的字段，缺了几乎不会被选中加载：\n      " + ", ".join(no_desc[:12]))
    if bad_type:
        yellow.append(f"{len(bad_type)} 个 topic 的 type 非法（应 ∈ {sorted(VALID_TYPES)}）：\n      "
                      + ", ".join(bad_type[:12]))

    # 3. 陈旧
    if stale:
        stale.sort(key=lambda x: -x[1])
        listed = ", ".join(f"{n}({d}天)" for n, d in stale[:12])
        yellow.append(f"{len(stale)} 个 topic 超过 {stale_days} 天未更新 —— 记忆永不自动过期，"
                      f"涉及 file:line/代码行为的需先核对现状再信任：\n      " + listed)

    # 6. 相对日期
    if rel_date:
        yellow.append(f"{len(rel_date)} 个 topic 含相对日期/时间词（昨天/最近/recently…）—— "
                      f"autoDream 会把相对日期转绝对，未转的将随时间失真：\n      " + ", ".join(rel_date[:12]))

    # 4 & 5. 孤儿 / 失效指针
    if orphan:
        yellow.append(f"{len(orphan)} 个 topic 不在 MEMORY.md 索引里（孤儿，召回效率低）：\n      "
                      + ", ".join(orphan[:12]))
    dead = [r for r in refs if r not in on_disk]
    if dead:
        red.append(f"MEMORY.md 索引有 {len(dead)} 个**失效指针**（指向的文件已不存在）：\n      "
                   + ", ".join(sorted(dead)[:12]))

    _settings_section(red, yellow, info)
    _emit(red, yellow, info)


def _settings_section(red, yellow, info):
    """7. 记忆相关 settings + autoMemoryDirectory 安全。"""
    gs, gp = read_global_settings()
    if gs is None:
        info.append(f"未读到全局 settings（{gp}）—— 记忆相关开关用默认值。")
    else:
        env = gs.get("env", {}) if isinstance(gs.get("env"), dict) else {}
        disable = str(env.get("CLAUDECODEDISABLEAUTOMEMORY", gs.get("CLAUDECODEDISABLEAUTOMEMORY", "")))
        if disable in ("1", "true", "True"):
            yellow.append("全局 settings 里 Auto Memory 被关闭（CLAUDECODEDISABLEAUTOMEMORY=1）——"
                          "若想让 Claude 自动积累经验，改成 0。")
        dream = gs.get("autoDreamEnabled")
        if dream is False:
            yellow.append("autoDreamEnabled=false —— 后台整合（去重/转绝对日期/解决矛盾）已关，"
                          "记忆更容易腐烂。建议开启。")
        elif dream is True:
            info.append("autoDreamEnabled=true —— 后台整合已开。")
        if "cleanupPeriodDays" not in gs:
            info.append("未设 cleanupPeriodDays —— 旧的 transcripts/快照不会自动清，"
                        "磁盘可能慢慢膨胀（用 disk_hygiene.py 体检）。")

    # autoMemoryDirectory 安全：只能在全局 settings 配；项目级配 = 劫持风险
    proj_settings = Path.cwd() / ".claude" / "settings.json"
    try:
        if proj_settings.exists():
            ps = json.loads(proj_settings.read_text(encoding="utf-8", errors="replace"))
            if "autoMemoryDirectory" in ps:
                red.append(f"🚨 安全：项目级 {proj_settings} 设置了 autoMemoryDirectory —— "
                           f"官方只允许在全局 ~/.claude/settings.json 配置，项目级配置可能被恶意仓库"
                           f"用来把记忆写入敏感目录。建议移除，挪到全局。")
    except Exception:
        pass


def _emit(red, yellow, info):
    if red:
        print("## 🔴 高优先级")
        for m in red:
            print(f"  - {m}")
    if yellow:
        print("\n## 🟡 建议处理")
        for m in yellow:
            print(f"  - {m}")
    if info:
        print("\n## ℹ️ 概况")
        for m in info:
            print(f"  - {m}")
    if not (red or yellow):
        print("\n✅ Auto Memory 体检通过：索引在预算内、frontmatter 完整、无失效指针。")
    print("\n下一步（人在环）: 🔴 项先处理；缺 description 的补上一句话摘要（决定能否被召回）；"
          "陈旧/相对日期项复核后让 autoDream 整合或手动精简；**silk-starry 绝不自动删记忆**——"
          "确认某条已升级进 CLAUDE.md 后，才用 graduate.py 清理。")


if __name__ == "__main__":
    main()
