<!-- 感谢贡献！请填写以下信息 -->

## 这个 PR 做了什么
<!-- 一句话说明解决的问题 / 加的能力 -->

## 类型
- [ ] 修 bug
- [ ] 新能力（脚本/模板/审计规则/触发场景）
- [ ] 文档
- [ ] 其他：

## 自检（必须）
- [ ] `python -m py_compile skills/silk-starry/scripts/*.py skills/silk-starry/scripts/hooks/*.py` 通过
- [ ] 涉及脚本：对**畸形/边界输入**做了兜底，不会崩
- [ ] 涉及写文件/删文件/改 git：保留了「人在环 + 最小 diff + 默认 dry-run」
- [ ] 涉及 SKILL.md/references：保持 runtime 中立（不写绑定单一 agent 的措辞）
- [ ] 没有引入个人/本机/真实项目信息或凭证

## 怎么验证的
<!-- 命令 + 预期输出 -->
