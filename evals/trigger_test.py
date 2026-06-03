#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Windows 安全的触发率评测（绕开 skill-creator run_eval 的 asyncio socket bug）。

对每条 query 同步跑 `claude -p ... --output-format json`，拿 session_id，读该 session 的
transcript JSONL，检查是否出现 Skill(silk-starry) 调用 = 触发。用系统提示让模型"决定用哪个
skill、相关就调用、调用后即可停"，避免真正执行任务的高成本。

用法: python trigger_test.py <eval.json> [skill_name]
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

SKILL = sys.argv[2] if len(sys.argv) > 2 else "silk-starry"
EVAL = sys.argv[1] if len(sys.argv) > 1 else "trigger-eval.json"
PROJECTS = Path.home() / ".claude" / "projects"
SYS = ("评测模式：判断这条请求该用哪个 skill。如果有相关 skill 就调用它（调用即可，"
       "调用后无需完成后续任务，可直接停下）；若没有相关 skill，就用一两句话直接回答，不要调用任何工具。")


def find_transcript(session_id, after_ts):
    """按 session_id 找 transcript 文件（文件名含 session_id）。"""
    for f in PROJECTS.glob(f"**/{session_id}.jsonl"):
        return f
    # 兜底：找 after_ts 之后最新修改、不是本评测会话的
    cands = [f for f in PROJECTS.glob("**/*.jsonl") if f.stat().st_mtime >= after_ts]
    cands.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    return cands[0] if cands else None


def triggered_in(transcript, skill):
    if not transcript or not transcript.exists():
        return None
    txt = transcript.read_text(encoding="utf-8", errors="replace")
    # 找 Skill 工具调用且 skill 名匹配
    for line in txt.splitlines():
        if '"Skill"' in line and skill in line:
            return True
    return False


def run_query(q):
    env = dict(os.environ)
    env.pop("CLAUDECODE", None)
    env["PYTHONUTF8"] = "1"
    t0 = time.time()
    try:
        p = subprocess.run(
            ["claude", "-p", q, "--output-format", "json", "--append-system-prompt", SYS],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=200, env=env, cwd=str(Path.home()),
        )
    except subprocess.TimeoutExpired:
        return None, "timeout"
    try:
        d = json.loads(p.stdout)
        sid = d.get("session_id")
    except Exception:
        return None, "parse-fail"
    tr = find_transcript(sid, t0 - 2)
    return triggered_in(tr, SKILL), sid


def main():
    evalp = Path(EVAL)
    if not evalp.is_absolute():
        evalp = Path(__file__).parent / EVAL
    queries = json.loads(evalp.read_text(encoding="utf-8"))
    rows = []
    for i, item in enumerate(queries, 1):
        q, exp = item["query"], item["should_trigger"]
        trig, info = run_query(q)
        ok = (trig == exp) if trig is not None else None
        rows.append((i, exp, trig, ok, q[:42]))
        mark = "?" if ok is None else ("✅" if ok else "❌")
        print(f"{mark} #{i:<2} 期望={'触发' if exp else '不触发'} 实际={trig} | {q[:42]}", flush=True)

    valid = [r for r in rows if r[3] is not None]
    trig_q = [r for r in valid if r[1]]
    notrig_q = [r for r in valid if not r[1]]
    recall = sum(1 for r in trig_q if r[2]) / len(trig_q) if trig_q else 0
    spec = sum(1 for r in notrig_q if not r[2]) / len(notrig_q) if notrig_q else 0
    acc = sum(1 for r in valid if r[3]) / len(valid) if valid else 0
    print("\n=== 汇总 ===")
    print(f"有效样本 {len(valid)}/{len(rows)}")
    print(f"应触发召回率 (should-trigger 命中): {recall:.0%}  ({sum(1 for r in trig_q if r[2])}/{len(trig_q)})")
    print(f"不应触发正确率 (near-miss 未误触发): {spec:.0%}  ({sum(1 for r in notrig_q if not r[2])}/{len(notrig_q)})")
    print(f"总准确率: {acc:.0%}")


if __name__ == "__main__":
    main()
