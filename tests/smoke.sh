#!/usr/bin/env bash
# 功能冒烟测试：为每个确定性脚本造样本、真跑、并断言关键行为。
# 不只是"跑不崩"，而是"检对了"。CI 与本地均可跑：bash tests/smoke.sh
set -u
export PYTHONUTF8=1
ROOTDIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOTDIR" || exit 1
S=scripts
fail=0
pass=0

assert_contains() {  # assert_contains "<标签>" "<输出>" "<必须包含的子串>"
  local label="$1" out="$2" needle="$3"
  if printf '%s' "$out" | grep -qF -- "$needle"; then
    echo "  ✅ $label —— 命中「$needle」"; pass=$((pass+1))
  else
    echo "  ❌ $label —— 未命中「$needle」"; echo "$out" | head -20; fail=$((fail+1))
  fi
}

B=$(mktemp -d); ROOT="$B/proj"
mkdir -p "$ROOT/web" "$ROOT/api" "$ROOT/.claude/rules"
cat > "$ROOT/CLAUDE.md" <<'EOF'
# CLAUDE.md
## 代码偏好
- 用 4 空格缩进。
## 配置
- API_KEY=sk-live-abc123def456ghimoreentropy7890
## 禁区
- 不要改自动生成文件。
EOF
printf '# web\n- 用 2 空格缩进。\n' > "$ROOT/web/CLAUDE.md"
printf '# api\n- Go 错误必须 wrap。\n' > "$ROOT/api/CLAUDE.md"
printf '# AGENTS.md\n- 提交信息用英文。\n' > "$ROOT/AGENTS.md"
printf -- '---\npaths: ["**/*.go"]\n---\n- 提交 Go 前跑 go vet。\n' > "$ROOT/.claude/rules/go.md"

MEM="$B/memory"; mkdir -p "$MEM"
printf -- '- [双引号](feedback_q.md) — 双引号\n- [陈旧](project_stale.md) — 旧状态\n' > "$MEM/MEMORY.md"
printf -- '---\nname: q\ndescription: 字符串用双引号否则 CI 打回\nmetadata:\n  type: feedback\n---\n双引号。\n' > "$MEM/feedback_q.md"
printf -- '---\nname: stale\nmetadata:\n  type: project\n---\n冻结到上周。\n' > "$MEM/project_stale.md"

echo "# silk-starry 功能冒烟（样本: $ROOT）"
assert_contains "audit 揪出密钥"      "$(python $S/audit.py "$ROOT/CLAUDE.md" 2>&1)"            "敏感信息"
assert_contains "scan 列出文件"        "$(python $S/scan.py "$ROOT" 2>&1)"                       "CLAUDE.md"
assert_contains "conflicts 抓到冲突"   "$(python $S/conflicts.py "$ROOT" 2>&1)"                  "缩进"
assert_contains "locate 就近链"        "$(python $S/locate.py "$ROOT/api/x.go" 2>&1)"            "api"
assert_contains "introspect 规则触发"  "$(python $S/introspect.py "$ROOT" --editing "$ROOT/api/x.go" 2>&1)" "触发"
assert_contains "sync 认出 AGENTS"     "$(python $S/sync_targets.py "$ROOT" 2>&1)"               "AGENTS.md"
assert_contains "digest 列候选"        "$(python $S/memory_digest.py --memory-dir "$MEM" 2>&1)"  "feedback_q.md"
assert_contains "doctor 揪缺desc"      "$(python $S/memory_doctor.py --memory-dir "$MEM" 2>&1)"  "description"
assert_contains "install_hooks 写入"   "$(python $S/install_hooks.py "$ROOT" 2>&1)"              "SessionStart"
# disk_hygiene 读 ~/.claude，CI 上可能不存在，断言它优雅处理而非崩溃
assert_contains "disk_hygiene 能跑"    "$(python $S/disk_hygiene.py 2>&1 || true)"               ".claude"

rm -rf "$B"
echo
echo "冒烟结果: PASS=$pass  FAIL=$fail"
[ "$fail" -eq 0 ] && echo "✅ 全部通过" || { echo "❌ 有失败"; exit 1; }
