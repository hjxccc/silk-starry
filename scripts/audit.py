#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""silk-starry: 体检单个 CLAUDE.md / AGENTS.md，输出问题清单（不改文件）。

用法:  python audit.py <文件路径>

检查项:
  1. 超长 (>200 行 / >60 行提示) + 字节预算 (单文件 25KB / 合并 40000 字符告警，对齐官方)
  2. 疑似敏感信息 (key/token/password/私钥/内网IP)
  3. 空泛规则 (无法自动执行的措辞)
  4. "写成文档" 的低价值段落 (目录树/架构罗列)
  5. 失效 / 指向 repo 外的 @import / 相对链接 (官方对外部 import 会拦截+警告)
  6. 疑似重复行
  7. .claude/rules/*.md 的 paths: frontmatter 写法校验 (对齐官方 paths 语义)
退出码: 有"高优先级"问题(敏感信息/超长)时返回 1，便于脚本串联。
"""
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# 官方常量 (claudemd.ts / memdir.ts)
MAX_MERGED_CHARS = 40000      # 合并所有 CLAUDE.md 的告警线 (官方仅告警不强截)
MAX_ENTRYPOINT_BYTES = 25000  # 单个 MEMORY.md 硬上限


def repo_root(start: Path):
    cur = start if start.is_dir() else start.parent
    for p in [cur, *cur.parents]:
        if (p / ".git").exists():
            return p
    return None


def agents_imported_as_main(path: Path) -> bool:
    """AGENTS.md 被同级 CLAUDE.md 用 `@AGENTS.md` 导入时，它才是真正注入的主记忆，
    长度也该受约束（uv/ruff/turso 等头部项目就是 CLAUDE.md → @AGENTS.md 这套）。"""
    if path.name.upper() != "AGENTS.MD":
        return False
    for sib in ("CLAUDE.md", ".claude/CLAUDE.md", "CLAUDE.local.md"):
        cm = path.parent / sib
        try:
            if cm.exists() and "@AGENTS.md" in cm.read_text(encoding="utf-8", errors="replace"):
                return True
        except Exception:
            pass
    return False


def section_sizes(lines):
    """按 ## 标题切段，返回 [(标题, 行数, 字节)]，用于"该下沉哪段"建议。"""
    secs, cur, buf = [], None, []
    for ln in lines:
        if re.match(r"^#{2,3}\s+\S", ln):
            if cur is not None:
                secs.append((cur, len(buf), len("\n".join(buf).encode("utf-8"))))
            cur, buf = ln.strip("# ").strip(), []
        elif cur is not None:
            buf.append(ln)
    if cur is not None:
        secs.append((cur, len(buf), len("\n".join(buf).encode("utf-8"))))
    return secs

VAGUE_PATTERNS = [
    r"写干净", r"写好(的)?代码", r"保持优雅", r"规范一点", r"注意性能", r"尽量",
    r"\bclean code\b", r"\bbest practice", r"\bproper(ly)?\b", r"\bgood code\b",
    r"高质量(?!的具体)", r"合理(地)?",
]
SENSITIVE_PATTERNS = [
    (r"(?i)(api[_-]?key|secret|password|passwd|token|access[_-]?key)\s*[:=]\s*\S+", "疑似密钥/口令"),
    (r"-----BEGIN [A-Z ]*PRIVATE KEY-----", "私钥"),
    (r"\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3})\b", "疑似内网 IP"),
    (r"(?i)mysql://\S+:\S+@", "含口令的数据库连接串"),
]
# 真正的文件树/目录树用的是制表符画线，markdown 表格(|)和代码围栏(```)不算
TREE_RE = re.compile(r"[│├└┌┐┘┤├┬┴┼]|├──|└──|^\s*\|?\s*[\w.\-/]+/\s*$")


def main():
    if len(sys.argv) < 2:
        print("用法: python audit.py <文件路径>")
        sys.exit(2)
    path = Path(sys.argv[1])
    if not path.is_file():
        print(f"文件不存在: {path}")
        sys.exit(2)

    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    n = len(lines)
    high = []   # 高优先级
    med = []    # 中
    low = []    # 低

    # 标记代码围栏内的行（这些行不参与"空泛/目录树/重复"检查，但仍扫敏感信息）
    in_fence = set()
    fenced = False
    for i, ln in enumerate(lines, 1):
        if ln.lstrip().startswith("```"):
            fenced = not fenced
            in_fence.add(i)
            continue
        if fenced:
            in_fence.add(i)

    # 1. 长度 + 字节预算
    # 认 CLAUDE.md / CLAUDE.local.md / 任何以 CLAUDE.md 结尾的命名（如 stack-CLAUDE.md）；
    # AGENTS.md 默认排除（独立的跨工具 onboarding 文档长度约束不同），但若被 sibling
    # CLAUDE.md 用 @AGENTS.md 导入当主记忆，则同样纳入长度检查。
    up = path.name.upper()
    is_claude = up.startswith("CLAUDE") or up.endswith("CLAUDE.MD") or agents_imported_as_main(path)
    nbytes = len(text.encode("utf-8"))
    if is_claude and n > 200:
        high.append(f"超长: {n} 行 (>200 硬上限)。遵守率会断崖下降，拆到 .claude/rules/ 或 @import。")
    elif is_claude and n > 60:
        low.append(f"偏长: {n} 行 (>60 理想值)。检查能否删减或拆分。")
    # 字节预算：单文件就逼近合并 40000 上限是危险信号（官方仅告警，silk-starry 主动提示下沉）
    over_budget = is_claude and (n > 200 or nbytes > MAX_MERGED_CHARS * 0.6)
    if is_claude and nbytes > MAX_MERGED_CHARS * 0.6:
        med.append(f"字节偏大: {nbytes} 字节，逼近官方合并 40000 字符告警线。"
                   f"建议把大段下沉到 .claude/rules/ 或子目录 CLAUDE.md，保持根文件最精简。")
    # B5: 超预算时给"该下沉哪几段"的具体建议（按字节排序的最大段）
    if over_budget:
        secs = sorted(section_sizes(lines), key=lambda s: s[2], reverse=True)
        big = [s for s in secs if s[2] > 400][:3]
        if big:
            tip = "；".join(f"「{t}」({b}字节)" for t, _, b in big)
            med.append(f"下沉建议: 最大的几段是 {tip}。把与特定语言/目录相关的下沉到带 paths: 的 "
                       f".claude/rules/<topic>.md，把通用全局段留在根文件——预计可显著降字节。")
    if path.name == "MEMORY.md" and nbytes > MAX_ENTRYPOINT_BYTES:
        high.append(f"MEMORY.md {nbytes} 字节 (>25KB 官方硬上限)，会被截断。它是索引，把详情移进 topic 文件。")

    # 2. 敏感信息（逐行，跳过被 HTML 注释包裹的行不特别处理）
    for i, ln in enumerate(lines, 1):
        for pat, label in SENSITIVE_PATTERNS:
            if re.search(pat, ln):
                high.append(f"L{i} 敏感信息({label}): {ln.strip()[:60]}")
                break

    # 3. 空泛规则（跳过代码围栏内）
    for i, ln in enumerate(lines, 1):
        if i in in_fence:
            continue
        for pat in VAGUE_PATTERNS:
            if re.search(pat, ln):
                med.append(f"L{i} 空泛规则(无法自动执行): {ln.strip()[:60]}")
                break

    # 4. 文档树罗列（真正的制表符画线；跳过表格/代码围栏）
    for i, ln in enumerate(lines, 1):
        if i in in_fence:
            continue
        if TREE_RE.search(ln):
            low.append(f"L{i} 疑似目录树罗列(Claude 读代码就知道): {ln.strip()[:50]}")

    # 5. 失效 / 外部 @import / 相对链接（官方对 repo 外 import 会拦截+弹窗警告）
    base = path.parent
    root = repo_root(path)
    for i, ln in enumerate(lines, 1):
        if i in in_fence:
            continue
        for m in re.finditer(r"@([\w./\\~-]+\.md)", ln):
            ref = m.group(1)
            if ref.startswith("~"):
                continue  # 用户级路径不校验
            target = (base / ref).resolve()
            if not target.exists():
                med.append(f"L{i} 失效 @import: {ref}")
            elif root and root not in target.parents and target != root:
                high.append(f"L{i} 外部 @import 指向 repo 外: {ref} —— 官方默认不加载(需批准+警告)，"
                            f"是脆弱依赖，建议把内容移进仓库或改用项目内文件。")
        for m in re.finditer(r"\]\((?!https?://)([^)]+\.md)\)", ln):
            ref = m.group(1)
            if not (base / ref).exists():
                med.append(f"L{i} 失效相对链接: {ref}")

    # 6. 重复行（非空、非标题、非代码围栏内）
    seen = {}
    for i, ln in enumerate(lines, 1):
        if i in in_fence:
            continue
        s = ln.strip()
        if len(s) > 15 and not s.startswith("#") and not s.startswith("|"):
            if s in seen:
                low.append(f"L{i} 与 L{seen[s]} 重复: {s[:50]}")
            else:
                seen[s] = i

    # 7. .claude/rules/*.md 的 paths: frontmatter 校验（对齐官方 paths 语义）
    in_rules = path.parent.name == "rules" and path.parent.parent.name == ".claude"
    if in_rules and lines and lines[0].strip() == "---":
        raw_paths = None
        for ln in lines[1:]:
            if ln.strip() == "---":
                break
            if ln.strip().lower().startswith("paths:"):
                raw_paths = ln.split(":", 1)[1].strip()
        if raw_paths is None:
            low.append("rules 文件无 paths: → 全局加载(等同 always-on)。若只对特定文件成立，加 paths: 限定省 context。")
        else:
            # 粗解析 [a, b] 或 单值
            vals = [v.strip().strip("'\"") for v in raw_paths.strip("[]").split(",") if v.strip()]
            if vals and all(v == "**" for v in vals):
                med.append("paths: 全是 `**` → 等同全局，paths 形同虚设。要么删 paths，要么写具体 glob。")
            for v in vals:
                if v.endswith("/**"):
                    low.append(f"paths 模式 `{v}` 的尾部 /** 可省略（官方 ignore 已递归匹配）。")
        if in_rules:
            low.append("提示：Project rules 的 paths glob 相对【项目根】，多个模式之间是 OR。")

    # 输出
    print(f"# 体检 {path}  ({n} 行, {nbytes} 字节)\n")
    def dump(title, items):
        if items:
            print(f"## {title} ({len(items)})")
            for it in items:
                print(f"  - {it}")
            print()
    dump("🔴 高优先级", high)
    dump("🟡 中优先级", med)
    dump("⚪ 低优先级 / 建议", low)
    if not (high or med or low):
        print("✅ 未发现明显问题。")
    else:
        print("修复建议: 高优先级(敏感信息/超长)先处理；空泛规则改写成可自动执行+配反例；"
              "失效链接修正或删除。改动走最小 diff。")
    sys.exit(1 if high else 0)


if __name__ == "__main__":
    main()
