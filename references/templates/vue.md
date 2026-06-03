# 模板：Vue 3 + TypeScript 前端 CLAUDE.md 骨架

> 探测信号：`package.json` 含 vue/vite。填完做减法。

```markdown
# CLAUDE.md

## 项目概述
<一句话 + Vue 3 + TS + 构建(Vite) + UI 库(Element Plus/…)>

## 构建与运行
- 安装依赖：<pnpm install / npm i>
- 启动开发：<pnpm dev>
- 运行测试：<pnpm test>
- 提交前必跑：<pnpm lint && pnpm type-check && pnpm test>

## 代码偏好（仅列与默认不同的）
- 组件用 `<script setup>` + Composition API。
- 单个组件不超过 200 行，超了拆子组件。
- 优先编辑现有组件，新建前先查 `src/components` 有没有现成的（防止仓库混乱漂移）。
- 状态管理用 <Pinia>；禁止引入 <Redux/Vuex 混用>。

## UI / 设计约定（按需）
- 间距用 8px 的倍数；交互元素必须有 hover/focus/disabled 状态。

## 禁区
- 不要改自动生成的 API 类型（`src/api/generated` 等）；改 schema 重新生成。
- 不要改 API 路由名 / 破坏向后兼容。

## 工作方式
- 影响 >3 文件先列计划。不确定停下来问。
```
