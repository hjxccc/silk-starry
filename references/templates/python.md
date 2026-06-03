# 模板：Python 项目 CLAUDE.md 骨架

> 探测信号：`requirements.txt` / `pyproject.toml` / `setup.py`。填完做减法。

```markdown
# CLAUDE.md

## 项目概述
<一句话 + Python 版本 + 主框架（FastAPI/Django/Flask/CLI…）>

## 构建与运行
- 创建环境：<python -m venv .venv / uv venv / poetry install>
- 安装依赖：<pip install -r requirements.txt / uv pip sync / poetry install>
- 启动：<cmd>
- 运行测试：<pytest -q>
- 提交前必跑：<ruff check . && ruff format --check . && pytest -q>

## 代码偏好（仅列与默认不同的）
- 日志用 <loguru>，不用标准 logging（原因：统一格式/异步）。
- 数据库用 <原生 SQL + PyMySQL>，不用 ORM（如项目如此约定）。
- 异步任务用 <RQ>，不用 Celery。
- 单文件不超过 <300> 行，超了拆模块。

## 禁区
- 不要自动 `pip install`，新依赖先和我确认并写进 requirements。
- 不要改自动生成的迁移（`alembic/versions/` 等）；改 schema 重新生成。
- 不要删看似无用的函数（可能是入口/被动态调用）。

## 工作方式
- 影响 >3 文件先列计划。不确定停下来问。
```
