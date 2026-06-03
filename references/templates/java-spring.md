# 模板：Java / Spring Boot 项目 CLAUDE.md 骨架

> 探测信号：`pom.xml` / `build.gradle`，含 spring-boot。填完做减法。

```markdown
# CLAUDE.md

## 项目概述
<一句话 + JDK 版本 + 框架（Spring Boot 3.x / MyBatis-Plus / …）>

## 构建与运行
- 构建：<mvn clean install -DskipTests / ./gradlew build>
- 本地启动：<入口类 + profile，如 Main.java with `local`>
- 运行测试：<mvn test>
- 提交前必跑：<mvn verify 或 spotless/格式化 + 测试>

## 分支协作
- 开发分支 <xxx> ↔ 主分支 <origin/develop>；推送前先 pull。

## 代码偏好（仅列与默认不同的）
- 用 Lombok；格式化用 <google-java-format>。
- 建表/迁移走 <Liquibase>：已发布 changelog 禁止修改，新增 V0.0.x 修补。
- <租户字段 tenant_id 默认 1 / 字符集 utf8mb4_… 等团队硬约定>

## 禁区
- 不要改已发布的 Liquibase changelog 文件。
- 不要在已生成的 codegen 产物里手改（改模板或重新生成）。

## 工作方式
- 影响 >3 文件先列计划。不确定停下来问。
```
