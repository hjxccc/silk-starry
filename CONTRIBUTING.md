# 贡献指南 / Contributing

欢迎贡献！silk-starry 是一个 Claude Code skill，主体是 `SKILL.md` + `references/` + `scripts/`。

## 本地结构
```
skills/silk-starry/
├── SKILL.md          主指令（改它要保持 ≤ 500 行、runtime 中立）
├── references/       按需加载的参考（一层深引用，>100 行加 TOC）
└── scripts/          确定性逻辑（Python，Windows UTF-8 安全，默认只读）
```

## 提交前自检
```bash
# 1) 所有脚本可编译
python -m py_compile skills/silk-starry/scripts/*.py skills/silk-starry/scripts/hooks/*.py

# 2) plugin 清单合法（需 Claude Code CLI）
claude plugin validate .

# 3) 冒烟：对一个样例 CLAUDE.md 跑 audit
python skills/silk-starry/scripts/audit.py path/to/CLAUDE.md
```

## 代码约定
- **脚本**：纯 Python 标准库（不引第三方依赖）；顶部 `sys.stdout.reconfigure(encoding="utf-8")` 保 Windows 兼容；
  子进程/文件读取用 `errors="replace"` + try/except 兜底，**对抗输入不能崩**（见已有的健壮性测试思路）。
- **SKILL.md / references**：遵守 skill 自己鼓吹的写作规范——可执行、配反例、显式失败分支、🔴 标记关键检查点、
  不写「在 Claude Code 里」这类绑定单一 runtime 的措辞（保持跨 agent 中立）。
- **安全**：任何会**写文件 / 删文件 / 改 git** 的改动，必须保留「人在环 + 最小 diff + 默认 dry-run」。

## 加新东西
- **新技术栈模板** → 放 `references/templates/<stack>.md`，骨架对齐现有模板。
- **新审计规则** → 加到 `scripts/audit.py`，并补一个会触发它的反例 + 一个不该触发的正例。
- **新触发场景** → 加进 `evals/trigger-eval.json`（标 `should_trigger`），重点放刁钻 near-miss。

## PR 流程
1. Fork → 建分支 → 改动保持小而聚焦（单一主题）。
2. 跑上面的自检。
3. PR 描述写清：解决什么问题、怎么验证的。

## 行为准则
参与本项目即同意遵守 [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)。
