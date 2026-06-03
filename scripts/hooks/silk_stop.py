#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""silk-starry Stop hook: 本轮结束时，从 transcript 里嗅探"用户纠正"，记为升级候选。

只**追加候选**到 .claude/silk-starry/candidates.jsonl，绝不改 CLAUDE.md，绝不阻塞。
务必查 stop_hook_active 防死循环。失败静默退出 0。
"""
import json
import sys
import re
from pathlib import Path

# 用户在纠正 Claude 时的典型措辞
CORRECTION_MARKERS = [
    "不对", "不是这样", "应该", "别这样", "错了", "不要", "我说过", "重新",
    "actually", "no,", "that's wrong", "should be", "don't ", "instead",
]


def read_last_user_msgs(transcript_path: str, k: int = 6):
    msgs = []
    p = Path(transcript_path)
    if not p.exists():
        return msgs
    try:
        for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            # 兼容不同 transcript 结构: 取 role=user 的文本
            role = obj.get("role") or obj.get("type")
            if role == "user":
                content = obj.get("content") or obj.get("message", {}).get("content")
                text = ""
                if isinstance(content, str):
                    text = content
                elif isinstance(content, list):
                    text = " ".join(
                        c.get("text", "") for c in content if isinstance(c, dict)
                    )
                if text:
                    msgs.append(text)
    except Exception:
        return msgs
    return msgs[-k:]


def main():
    try:
        raw = sys.stdin.read()
    except Exception:
        raw = ""
    try:
        data = json.loads(raw) if raw else {}
    except Exception:
        data = {}

    if data.get("stop_hook_active"):
        sys.exit(0)  # 防死循环

    transcript = data.get("transcript_path", "")
    if not transcript:
        sys.exit(0)

    msgs = read_last_user_msgs(transcript)
    hits = []
    for m in msgs:
        low = m.lower()
        if any(mk in m or mk in low for mk in CORRECTION_MARKERS):
            hits.append(m.strip()[:200])

    if not hits:
        sys.exit(0)

    cand_dir = Path.cwd() / ".claude" / "silk-starry"
    cand_dir.mkdir(parents=True, exist_ok=True)
    cand_file = cand_dir / "candidates.jsonl"

    # 去重 + 限制总条目数，防止文件无限增长
    MAX_ENTRIES = 500
    existing_texts = set()
    existing_lines = []
    if cand_file.exists():
        for ln in cand_file.read_text(encoding="utf-8", errors="replace").splitlines():
            if not ln.strip():
                continue
            existing_lines.append(ln)
            try:
                existing_texts.add(json.loads(ln).get("text", ""))
            except Exception:
                pass

    new_lines = []
    for h in hits:
        if h not in existing_texts:
            existing_texts.add(h)
            new_lines.append(json.dumps({"source": "stop-correction", "text": h}, ensure_ascii=False))

    if not new_lines:
        sys.exit(0)
    merged = (existing_lines + new_lines)[-MAX_ENTRIES:]
    cand_file.write_text("\n".join(merged) + "\n", encoding="utf-8")

    # Stop hook 的 stdout 不进上下文，这里只写文件；不阻塞。
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(0)
