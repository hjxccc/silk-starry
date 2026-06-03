#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""silk-starry: 盘点一个项目里所有 CLAUDE.md / AGENTS.md / CLAUDE.local.md。

用法:  python scan.py <项目根目录>

输出: 每个文件的路径/行数/token 估算，以及"缺失"清单（有源码但没有 CLAUDE.md 的一级子目录）。
只读，不改任何文件。Windows 上用 `python`（不是 python3），UTF-8。
"""
import os
import re
import subprocess
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

MEMORY_NAMES = {"CLAUDE.md", "CLAUDE.local.md", "AGENTS.md"}

# 敏感文件名模式（规范：明确清单；安全：私钥/凭证/连接配置优先）。
# 命中后检查是否被 git 跟踪 / 未忽略——补上 audit 只看 CLAUDE.md 的盲区。
SENSITIVE_FILE_RE = re.compile(
    r"(^\.env($|\.)|"            # .env / .env.local …（.env.example/.sample 例外见下）
    r".*\.pem$|.*\.key$|.*\.p12$|.*\.pfx$|.*\.keystore$|"
    r"^id_(rsa|dsa|ecdsa|ed25519)$|"   # SSH 私钥
    r"^\.mcp\.json$|^\.npmrc$|^\.pypirc$|"
    r"^credentials(\.json)?$|^secrets?\.(json|ya?ml|txt)$)",
    re.I,
)
SENSITIVE_SAFE_SUFFIX = (".example", ".sample", ".template", ".dist")
# 探测"这是个代码模块"的信号文件
CODE_SIGNALS = {
    "package.json", "pom.xml", "build.gradle", "requirements.txt",
    "pyproject.toml", "setup.py", "go.mod", "Cargo.toml", "composer.json",
}
SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build",
    "target", ".idea", ".vscode", ".trellis", ".playwright-mcp", ".pytest_cache",
}


def est_tokens(text: str) -> int:
    """粗估 token：中文按字、英文按 ~4 字符/token 混合估。够审查用即可。"""
    cjk = sum(1 for c in text if "一" <= c <= "鿿")
    other = len(text) - cjk
    return cjk + other // 4


def walk(root: Path):
    found = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if fn in MEMORY_NAMES:
                found.append(Path(dirpath) / fn)
    return found


def find_missing(root: Path):
    """一级子目录里像代码模块、但没有 CLAUDE.md 的，列为缺失。"""
    missing = []
    for child in sorted(root.iterdir()):
        if not child.is_dir() or child.name in SKIP_DIRS:
            continue
        has_code = any((child / s).exists() for s in CODE_SIGNALS)
        has_doc = (child / "CLAUDE.md").exists()
        if has_code and not has_doc:
            missing.append(child)
    return missing


def nearest_git_root(p: Path):
    """找文件最近的 .git 祖先（健壮：支持 monorepo 里嵌套的独立子仓）。"""
    for d in [p.parent, *p.parent.parents]:
        if (d / ".git").exists():
            return d
    return None


def git_ignored_tracked(gitroot: Path, f: Path):
    """返回 (ignored, tracked)。健壮：子进程异常一律当作未知(False)，不崩主流程。"""
    try:
        rel = str(f.relative_to(gitroot))
    except ValueError:
        rel = str(f)
    def run(args):
        try:
            return subprocess.run(["git", "-C", str(gitroot), *args],
                                  capture_output=True, timeout=10).returncode == 0
        except Exception:
            return False
    ignored = run(["check-ignore", "-q", rel])
    tracked = run(["ls-files", "--error-unmatch", rel])
    return ignored, tracked


def scan_sensitive_files(root: Path):
    """扫敏感文件并判断 git 暴露状态。返回 (high, warn) 两个列表。"""
    high, warn = [], []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if fn.lower().endswith(SENSITIVE_SAFE_SUFFIX) or fn.lower().endswith(".pub"):
                continue  # .env.example 样板、.pub 公钥 不算敏感
            # 标准敏感名 OR 文件名里嵌了 SSH 私钥标识（健壮：兜住被压扁路径的怪文件名）
            if not (SENSITIVE_FILE_RE.match(fn)
                    or re.search(r"id_(rsa|dsa|ecdsa|ed25519)", fn, re.I)):
                continue
            f = Path(dirpath) / fn
            gr = nearest_git_root(f)
            try:
                rel = f.relative_to(root)
            except ValueError:
                rel = f
            if gr is None:
                warn.append(f"{rel} —— 敏感文件（该目录无 git，留意别误加入其他仓）")
                continue
            ignored, tracked = git_ignored_tracked(gr, f)
            if tracked:
                high.append(f"{rel} —— 被 git 跟踪。若含密钥/口令，建议加 .gitignore 后 `git rm --cached` "
                            f"并轮换；若确认只含公开配置（如前端 VITE_ 变量）或属有意提交，可忽略本提示。")
            elif not ignored:
                warn.append(f"{rel} —— 未被 .gitignore 忽略，`git add .` 可能误提交。若是敏感文件建议加进 .gitignore。")
    return high, warn


def main():
    if len(sys.argv) < 2:
        print("用法: python scan.py <项目根目录>")
        sys.exit(1)
    root = Path(sys.argv[1]).resolve()
    if not root.is_dir():
        print(f"不是目录: {root}")
        sys.exit(1)

    files = walk(root)
    print(f"# 盘点 {root}\n")
    if not files:
        print("未发现任何 CLAUDE.md / AGENTS.md。")
    else:
        print(f"发现 {len(files)} 个记忆文件:\n")
        print(f"{'文件':<52} {'行数':>6} {'字节':>8} {'~token':>8}")
        print("-" * 78)
        total_tokens = 0
        total_bytes = 0
        for f in sorted(files):
            try:
                text = f.read_text(encoding="utf-8", errors="replace")
            except Exception as e:
                print(f"{str(f):<52} 读取失败: {e}")
                continue
            lines = text.count("\n") + 1
            nb = len(text.encode("utf-8"))
            tk = est_tokens(text)
            total_tokens += tk
            total_bytes += nb
            rel = f.relative_to(root)
            flag = "  ⚠超长" if (f.name.startswith("CLAUDE") and lines > 200) else ""
            print(f"{str(rel):<52} {lines:>6} {nb:>8} {tk:>8}{flag}")
        print("-" * 78)
        print(f"{'合计':<52} {'':>6} {total_bytes:>8} {total_tokens:>8}")
        # 合并字节逼近官方 40000 字符告警线时提示（CLAUDE.md 类合并注入）
        claude_bytes = sum(len(f.read_text(encoding='utf-8', errors='replace').encode('utf-8'))
                           for f in files if f.name.startswith("CLAUDE"))
        if claude_bytes > 40000 * 0.6:
            print(f"\n⚠ 所有 CLAUDE.md 合计约 {claude_bytes} 字节，逼近官方合并 40000 字符告警线"
                  f"（注意：子目录文件是按需懒加载，不一定同时全注入）。")

    missing = find_missing(root)
    if missing:
        print(f"\n## 缺失 CLAUDE.md 的代码模块 ({len(missing)}):")
        for m in missing:
            print(f"  - {m.relative_to(root)}/")
        print("\n建议: 对这些模块用 silk-starry 的 generate 动作生成初稿。")
    else:
        print("\n所有一级代码模块都有 CLAUDE.md。")

    # 敏感文件 git 暴露检查（建议性，非强制；补 audit 只看 CLAUDE.md 的盲区）
    s_high, s_warn = scan_sensitive_files(root)
    if s_high or s_warn:
        print(f"\n## 🔐 敏感文件检查（建议复核，非强制——有意提交可忽略）")
        if s_high:
            print("  被 git 跟踪（优先看一眼）：")
            for it in s_high:
                print(f"    - {it}")
        if s_warn:
            print("  未忽略 / 其他：")
            for it in s_warn:
                print(f"    - {it}")
    else:
        print("\n🔐 敏感文件检查：未发现 .env/私钥/凭证 类文件被 git 跟踪或未忽略。")


if __name__ == "__main__":
    main()
