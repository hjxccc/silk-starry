#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""silk-starry: 一键把轻量 hook 装进目标项目的 .claude/settings.json。

用法:
  python install_hooks.py <项目根目录>           # 安装
  python install_hooks.py <项目根目录> --remove   # 卸载
  python install_hooks.py <项目根目录> --dry-run   # 预览改动

行为:
  - 把 SessionStart(提醒) + Stop(嗅探纠正) 两个 hook 合并进项目 settings.json，
    与已有 hook 共存（不覆盖，按命令含 'silk_' 去重）。
  - 创建 .claude/silk-starry/ 候选目录。
  - 安装前会打印将要做的改动。settings.json 是项目级，只影响这个项目。
"""
import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

SELF = Path(__file__).resolve()
HOOK_DIR = SELF.parent / "hooks"
SESSION_HOOK = HOOK_DIR / "silk_session_start.py"
STOP_HOOK = HOOK_DIR / "silk_stop.py"
MARK = "silk_"  # 去重标记


def cmd_for(script: Path) -> str:
    # Windows/Unix 通用：用 python 调脚本，正斜杠路径避免被 shell 反斜杠转义
    return f'python "{script.as_posix()}"'


def entry(script: Path):
    return {"hooks": [{"type": "command", "command": cmd_for(script)}]}


def has_silk_starry(hook_list) -> bool:
    for grp in hook_list or []:
        for h in grp.get("hooks", []):
            if MARK in h.get("command", ""):
                return True
    return False


def strip_silk_starry(hook_list):
    out = []
    for grp in hook_list or []:
        kept = [h for h in grp.get("hooks", []) if MARK not in h.get("command", "")]
        if kept:
            out.append({**grp, "hooks": kept})
    return out


def main():
    if len(sys.argv) < 2:
        print("用法: python install_hooks.py <项目根目录> [--remove|--dry-run]")
        sys.exit(1)
    root = Path(sys.argv[1]).resolve()
    remove = "--remove" in sys.argv
    dry = "--dry-run" in sys.argv

    if not SESSION_HOOK.exists() or not STOP_HOOK.exists():
        print(f"找不到 hook 脚本: {HOOK_DIR}")
        sys.exit(1)

    claude_dir = root / ".claude"
    settings = claude_dir / "settings.json"
    data = {}
    if settings.exists():
        try:
            data = json.loads(settings.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"settings.json 解析失败，已中止以免破坏: {e}")
            sys.exit(1)

    if not isinstance(data.get("hooks", {}), dict):
        print("settings.json 中 hooks 字段不是对象格式，已中止以免破坏。")
        sys.exit(1)
    hooks = data.setdefault("hooks", {})
    ss = hooks.setdefault("SessionStart", [])
    st = hooks.setdefault("Stop", [])

    if remove:
        hooks["SessionStart"] = strip_silk_starry(ss)
        hooks["Stop"] = strip_silk_starry(st)
        action = "卸载 silk-starry hook"
    else:
        if not has_silk_starry(ss):
            ss.append(entry(SESSION_HOOK))
        if not has_silk_starry(st):
            st.append(entry(STOP_HOOK))
        action = "安装 silk-starry hook (SessionStart 提醒 + Stop 嗅探纠正)"

    print(f"# {action}")
    print(f"目标: {settings}")
    print("将写入的 hooks 段:")
    print(json.dumps({"hooks": {"SessionStart": hooks['SessionStart'],
                                "Stop": hooks['Stop']}}, ensure_ascii=False, indent=2))

    if dry:
        print("\n(--dry-run 未实际写入)")
        return

    claude_dir.mkdir(parents=True, exist_ok=True)
    settings.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    if not remove:
        (claude_dir / "silk-starry").mkdir(parents=True, exist_ok=True)
    print(f"\n✅ 已写入 {settings}")
    print("提示: hook 在新会话(或 /hooks 审阅后)生效。settings.json 只影响本项目。")


if __name__ == "__main__":
    main()
