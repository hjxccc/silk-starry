#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""silk-starry: 跨文件冲突治理（B8）。扫全仓 CLAUDE.md / rules，检测互相矛盾的规则。

用法:  python conflicts.py <项目根>

按若干"规则轴"（缩进/引号/命名风格/分支/包管理器）抽取每个文件声明的值；同一轴出现 ≥2 个
不同值且分布在 ≥2 个文件 → 报"潜在冲突"。文章共识：**暴露冲突让用户选一个，别取平均**。
若某文件显式声明"覆盖/override"（B6 monorepo 覆盖语义），则标为【有意覆盖】而非冲突。

这是启发式检测，产出"待你判断"的潜在冲突，不自动改任何文件。只读。
"""
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist",
             "build", "target", ".idea", ".trellis", ".playwright-mcp"}

# 每个"轴"：canonical 值 → 匹配正则（在某文件命中即视为该文件声明了这个值）
AXES = {
    "缩进": {
        "2-space": r"2[\s-]*(?:空格|spaces?)",
        "4-space": r"4[\s-]*(?:空格|spaces?)",
        "tab": r"(?:制表符|\btabs?\b)(?!le)",
    },
    "引号": {
        "single": r"单引号|single\s*quote",
        "double": r"双引号|double\s*quote",
    },
    "命名风格": {
        "camelCase": r"camelCase|小驼峰|驼峰",
        "snake_case": r"snake_case|下划线命名",
        "kebab-case": r"kebab-case|短横线命名",
    },
    "主分支": {
        "main": r"\bmain\b\s*分支|分支\s*\bmain\b|origin/main",
        "master": r"\bmaster\b\s*分支|分支\s*\bmaster\b|origin/master",
        "develop": r"\bdevelop\b\s*分支|分支\s*\bdevelop\b|origin/develop",
    },
    "包管理器": {
        "pnpm": r"(?:用|使用|prefer|use)\s*pnpm",
        "npm": r"(?:用|使用|prefer|use)\s*npm\b",
        "yarn": r"(?:用|使用|prefer|use)\s*yarn",
        "bun": r"(?:用|使用|prefer|use)\s*bun\b",
    },
}
OVERRIDE_RE = re.compile(r"覆盖|override|overrides?\b", re.I)


def collect_files(root: Path):
    out = []
    import os
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in SKIP_DIRS]
        for f in fn:
            if f in ("CLAUDE.md", "CLAUDE.local.md") or (
                f.endswith(".md") and Path(dp).name == "rules" and Path(dp).parent.name == ".claude"
            ):
                out.append(Path(dp) / f)
    return out


def main():
    if len(sys.argv) < 2:
        print("用法: python conflicts.py <项目根>")
        sys.exit(1)
    root = Path(sys.argv[1]).resolve()
    if not root.is_dir():
        print(f"不是目录: {root}")
        sys.exit(1)

    files = collect_files(root)
    print(f"# 跨文件冲突检测 {root}\n扫描 {len(files)} 个 CLAUDE.md/rules 文件\n")

    # axis -> value -> list of (file, line_no, line_text, is_override)
    found = {ax: {} for ax in AXES}
    for f in files:
        try:
            lines = f.read_text(encoding="utf-8", errors="replace").splitlines()
        except Exception:
            continue
        for i, ln in enumerate(lines, 1):
            ov = bool(OVERRIDE_RE.search(ln))
            for ax, vals in AXES.items():
                for val, pat in vals.items():
                    if re.search(pat, ln, re.I):
                        found[ax].setdefault(val, []).append(
                            (f.relative_to(root), i, ln.strip()[:70], ov))

    conflicts = 0
    overrides = 0
    for ax, valmap in found.items():
        # 去掉只在单一文件出现的值不算（需跨文件）
        distinct_vals = [v for v in valmap]
        if len(distinct_vals) < 2:
            continue
        files_involved = {hit[0] for v in valmap for hit in valmap[v]}
        if len(files_involved) < 2:
            continue
        # 是否有显式覆盖声明
        has_override = any(hit[3] for v in valmap for hit in valmap[v])
        tag = "【有意覆盖 B6】" if has_override else "🟡 潜在冲突"
        if has_override:
            overrides += 1
        else:
            conflicts += 1
        print(f"## {tag} — 轴「{ax}」出现 {len(distinct_vals)} 个不同值")
        for val, hits in valmap.items():
            for rel, i, txt, ov in hits:
                ovm = " [声明覆盖]" if ov else ""
                print(f"  - [{val}] {rel}:{i}{ovm}  «{txt}»")
        print()

    if conflicts == 0 and overrides == 0:
        print("✅ 未发现跨文件规则冲突。")
    else:
        print(f"小结：{conflicts} 个潜在冲突、{overrides} 个有意覆盖。")
        if conflicts:
            print("处理建议：**别取平均**——选一个（通常更近/更新/更具体的层），在另一处删除或显式声明覆盖。")
    sys.exit(1 if conflicts else 0)


if __name__ == "__main__":
    main()
