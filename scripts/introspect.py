#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""silk-starry: 加载自省 / 预测（官方只有 /memory show，silk-starry 做"体检 + 预测"）。

用法:
  python introspect.py <项目根>                 # 这个项目会加载哪些记忆、合并多少字节
  python introspect.py <项目根> --editing <文件>  # 额外预测：编辑该文件会触发哪些 paths glob 规则

输出一张"加载体检表"：always-on 的 CLAUDE.md 链、.claude/rules 的全局 vs 路径限定规则、
合并字节是否逼近官方 40000 告警线、外部 @import 警告、AGENTS.md 共存提示。只读，全是估算。

阈值对齐官方快照（会漂移），仅作告警。
"""
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

MAX_MERGED_CHARS = 40000


def parse_args(argv):
    if len(argv) < 2:
        print("用法: python introspect.py <项目根> [--editing <文件路径>]")
        sys.exit(1)
    root = Path(argv[1]).resolve()
    editing = None
    if "--editing" in argv:
        i = argv.index("--editing")
        if i + 1 < len(argv):
            editing = Path(argv[i + 1]).resolve()
    return root, editing


def glob_to_re(pat: str):
    """把 glob（含 ** / *）转 regex，对齐官方语义：尾部 /** 去掉、** 跨目录、* 单段。"""
    if pat.endswith("/**"):
        pat = pat[:-3]
    out, i = [], 0
    while i < len(pat):
        c = pat[i]
        if c == "*":
            if pat[i:i+2] == "**":
                out.append(".*")
                i += 2
                continue
            out.append("[^/]*")
        elif c in ".()+|^$@%{}[]\\":
            out.append("\\" + c)
        else:
            out.append(c)
        i += 1
    return re.compile("^" + "".join(out) + "($|/.*$)")


def read_paths_frontmatter(f: Path):
    """返回 (有frontmatter, paths列表 or None表示全局)。"""
    try:
        lines = f.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        return False, None
    if not (lines and lines[0].strip() == "---"):
        return False, None
    raw = None
    for ln in lines[1:]:
        if ln.strip() == "---":
            break
        if ln.strip().lower().startswith("paths:"):
            raw = ln.split(":", 1)[1].strip()
    if raw is None:
        return True, None  # 有 frontmatter 但无 paths → 全局
    vals = [v.strip().strip("'\"") for v in raw.strip("[]").split(",") if v.strip()]
    if not vals or all(v == "**" for v in vals):
        return True, None  # 全 ** → 全局
    return True, vals


def fbytes(f: Path) -> int:
    try:
        return len(f.read_text(encoding="utf-8", errors="replace").encode("utf-8"))
    except Exception:
        return 0


def main():
    root, editing = parse_args(sys.argv)
    if not root.is_dir():
        print(f"不是目录: {root}")
        sys.exit(1)

    print(f"# 加载自省 {root}")
    if editing:
        print(f"假设正在编辑: {editing}")
    print("（估算，阈值对齐官方快照，仅告警）\n")

    always = []   # (label, path, bytes)
    # always-on 的根级 CLAUDE 链
    for name in ("CLAUDE.md", ".claude/CLAUDE.md", "CLAUDE.local.md"):
        p = root / name
        if p.exists():
            always.append((name, p, fbytes(p)))

    # 子目录 CLAUDE.md（若指定编辑文件，沿链向上到 root）
    if editing:
        cur = editing.parent
        chain = []
        while True:
            if cur == root:
                break
            cm = cur / "CLAUDE.md"
            if cm.exists():
                chain.append(cm)
            if cur.parent == cur or root not in cur.parents:
                break
            cur = cur.parent
        for cm in reversed(chain):
            always.append((f"子目录(懒加载) {cm.relative_to(root)}", cm, fbytes(cm)))

    print("## always-on CLAUDE.md 链")
    if always:
        for label, p, b in always:
            print(f"  - {label:<40} {b:>6} 字节")
    else:
        print("  （根目录没有 CLAUDE.md —— 可用 generate 创建）")

    # .claude/rules
    rules_dir = root / ".claude" / "rules"
    global_rules, scoped_rules = [], []
    if rules_dir.is_dir():
        for f in sorted(rules_dir.glob("*.md")):
            has_fm, paths = read_paths_frontmatter(f)
            if paths is None:
                global_rules.append((f, fbytes(f)))
            else:
                scoped_rules.append((f, paths, fbytes(f)))

    print("\n## .claude/rules/")
    if not rules_dir.is_dir():
        print("  （无 rules 目录）")
    else:
        if global_rules:
            print("  全局加载（always-on）:")
            for f, b in global_rules:
                print(f"    - {f.name:<38} {b:>6} 字节")
        if scoped_rules:
            print("  路径限定（按 paths glob 懒加载）:")
            for f, paths, b in scoped_rules:
                hit = ""
                if editing:
                    rel = None
                    try:
                        rel = str(editing.relative_to(root)).replace("\\", "/")
                    except ValueError:
                        rel = editing.name
                    matched = any(glob_to_re(g).match(rel) for g in paths)
                    hit = "  ← 本次编辑【会触发】" if matched else "  （本次不触发）"
                print(f"    - {f.name:<30} paths={paths} {b}字节{hit}")

    # 字节预算：always-on 合计（根 CLAUDE 链 + 全局 rules）+ 命中的 scoped
    base_bytes = sum(b for _, _, b in always) + sum(b for _, b in global_rules)
    hit_bytes = 0
    if editing:
        for f, paths, b in scoped_rules:
            rel = str(editing.relative_to(root)).replace("\\", "/") if root in editing.parents else editing.name
            if any(glob_to_re(g).match(rel) for g in paths):
                hit_bytes += b
    total = base_bytes + hit_bytes
    print(f"\n## 字节预算（估算）")
    print(f"  always-on 合计: {base_bytes} 字节" + (f"；+本次触发 scoped: {hit_bytes} → {total}" if editing else ""))
    if total > MAX_MERGED_CHARS * 0.6:
        print(f"  ⚠ 逼近官方合并 40000 字符告警线，建议把大段下沉到 rules / 子目录 CLAUDE.md。")
    else:
        print(f"  ✅ 在 40000 告警线内（{int(total/MAX_MERGED_CHARS*100)}%）。")

    # 外部 @import 警告
    ext = []
    for _, p, _ in always:
        for i, ln in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            for m in re.finditer(r"@([\w./\\~-]+\.md)", ln):
                ref = m.group(1)
                if ref.startswith("~"):
                    continue
                tgt = (p.parent / ref).resolve()
                if tgt.exists() and root not in tgt.parents and tgt != root:
                    ext.append(f"{p.name} L{i}: @{ref}")
    if ext:
        print(f"\n## ⚠ 外部 @import（官方默认不加载，脆弱依赖）")
        for e in ext:
            print(f"  - {e}")

    # AGENTS.md 共存
    if (root / "AGENTS.md").exists():
        imported = any("@AGENTS.md" in p.read_text(encoding="utf-8", errors="replace")
                       for _, p, _ in always if p.name.startswith("CLAUDE"))
        print(f"\n## AGENTS.md 共存")
        print("  发现 AGENTS.md。" + ("✅ CLAUDE.md 已 @import。" if imported
              else "Claude Code 不读 AGENTS.md，建议在 CLAUDE.md 顶部 `@AGENTS.md` 导入，避免重复维护。"))


if __name__ == "__main__":
    main()
