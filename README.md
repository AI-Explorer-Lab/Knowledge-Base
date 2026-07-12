# Knowledge-Base

这是一个以 Markdown、YAML、Git 和 Pull Request 为基础的企业知识治理仓库。知识正文保持对人友好，验证事实独立记录，成熟度和生命周期通过明确策略治理，Catalog 与报告由 Python 工具确定性生成。

第一次了解本项目，建议先阅读 [大白话项目介绍](docs/项目介绍.md)；要了解人工与 Harness 两种实际使用方式，可阅读 [知识使用示例](docs/知识使用示例.md)；通过表单操作请查看 [网页使用说明](docs/网页使用说明.md)；查询命令、Front Matter、Evidence、配置和 Policy 的全部字段时，请查看 [参数完整说明](docs/参数说明.md)；完整设计见 [企业级知识库动态治理方案](plan/enterprise-knowledge-base-spec.md)，代码结构与数据流见 [架构说明](docs/architecture.md)。

## 当前能力

- 五种知识类型：`model`、`decision`、`guideline`、`pitfall`、`process`；
- 三档成熟度：`draft`、`verified`、`proven`；
- 五种生命周期状态：`active`、`review_due`、`disputed`、`deprecated`、`archived`；
- JSON Schema、正文结构、路径、全局 ID、Evidence 和替代引用校验；
- Evidence 事件幂等追加，以及重复 ID 不同内容的冲突保护；
- 从 Evidence 与 Policy 动态计算最近验证、最近复核和下次复核时间；
- 独立项目、证据组和贡献者的成熟度候选判断；
- 失败与冲突证据触发即时查询安全保护；
- 确定性 Catalog、待复核报告和可审查的状态变更提案；
- 自动化测试与 GitHub Actions 校验。
- 本地 FastAPI 管理网页、动态知识表单、Evidence 表单和治理建议面板。

## 快速开始

需要 Python 3.9 或更高版本。项目当前使用名为 `knowledge-base` 的 Conda 环境；首次安装时执行：

```bash
conda create -n knowledge-base python=3.11 -y
conda activate knowledge-base
python -m pip install --upgrade pip setuptools
python -m pip install -e '.[dev]'
```

运行完整检查：

```bash
conda activate knowledge-base
knowledge lint
knowledge build-catalog
pytest -q
```

以后进入项目只需激活已有环境：

```bash
conda activate knowledge-base
```

安装命令中的 `-e` 表示以可编辑模式安装当前项目。安装工具会读取 `pyproject.toml` 的 `[project.scripts]` 配置，并在当前 Conda 环境的可执行目录中生成 `knowledge` 命令；该命令实际调用 `knowledge_governance.cli:main`。因此先激活环境后，可以直接使用 `knowledge lint`、`knowledge web` 等子命令，无需写 Python 文件路径。

## 启动管理网页

```bash
conda activate knowledge-base
cd /Users/mon/Documents/Knowledge-Base
knowledge web
```

浏览器打开 [http://127.0.0.1:8000](http://127.0.0.1:8000)。网页提供知识列表、新建与编辑表单、Evidence 记录和生命周期建议；默认只允许本机访问，详细说明见 [网页使用说明](docs/网页使用说明.md)。

## 常用命令

校验整个知识库：

```bash
knowledge lint
```

重新生成根目录、技术域和业务域 Catalog，以及待复核报告：

```bash
knowledge build-catalog
```

记录普通引用事件：

```bash
knowledge record-event \
  --id TK-GDL-001 \
  --type referenced \
  --contributor user:alice \
  --reference order-service#182
```

记录成功验证。验证事件必须提供项目、场景、证据组、验证方式、结果摘要和可追溯来源：

```bash
knowledge record-event \
  --id TK-GDL-001 \
  --type validated_success \
  --event-id EVT-20260711-001 \
  --contributor user:alice \
  --project order-service \
  --scenario-id duplicate-order-delivery \
  --evidence-group-id order-release-2026-07 \
  --validation-method integration_test \
  --result-summary '重复投递测试通过，业务状态仅变化一次' \
  --reference order-service#205
```

查看生命周期和成熟度候选：

```bash
knowledge evaluate-lifecycle
```

为指定知识生成可审查的状态变更提案：

```bash
knowledge propose-transition --id TK-GDL-001
```

所有命令默认使用当前目录作为仓库根目录，也可以把全局参数放在子命令之前：

```bash
knowledge --root /path/to/knowledge-base lint
```

## 创建知识

1. 从 `templates/` 中选择对应类型模板，并复制到与 `scope`、`type` 一致的目录；
2. 分配全局唯一 ID，填写 Front Matter、适用边界、验证方式和类型特有段落；
3. 运行 `knowledge lint`；
4. 运行 `knowledge build-catalog` 并提交生成结果；
5. 通过 Pull Request 请求 Owner 或 CODEOWNER 审核。

成熟度变化只修改元数据，不移动文件；项目知识提升为跨项目知识时创建新的正式条目；知识只有在经过废弃保留期后才移动到 `archive/`。

## 数据权威边界

| 数据 | 权威来源 |
|---|---|
| 结论、适用条件、Owner、`maturity`、`status` | 知识 Markdown |
| 引用、采用、成功、失败、复核事实 | `evidence/*.yaml` |
| 复核周期、晋级阈值和保留期 | `policies/*.yaml` |
| 最近验证、最近复核、下次复核 | Evidence 与 Policy 的运行时计算结果 |
| Catalog 和治理报告 | 自动生成结果 |

`record-event` 不直接修改成熟度和生命周期状态，`evaluate-lifecycle` 只计算候选，正式状态变化必须通过 Pull Request。若存在未解决的失败或冲突事件，查询和 Catalog 会立即停止把相关知识作为默认推荐，但正式状态仍需经过审批修改。

## 目录结构

```text
.
├── .knowledge-config.yaml       # 仓库级配置
├── schemas/                     # Knowledge、Evidence 和 Policy Schema
├── policies/                    # 成熟度、复核、保留和风险策略
├── templates/                   # 五类知识模板
├── team-conventions/            # 团队约定
├── tech-wiki/                   # 跨项目技术知识
├── biz-wiki/                    # 业务域知识
├── evidence/                    # 动态证据事件
├── contributions/              # 待审批提案与冲突
├── reports/                     # 自动生成的治理报告
├── archive/                     # 退出活跃检索的历史知识
├── src/knowledge_governance/    # Python 治理内核
├── tests/                       # 自动化测试
├── feature/                     # 非当前版本前置的未来优化
└── plan/                        # 完整治理规格
```

## Python 模块

- `repository`：发现并加载知识、Evidence、配置和策略；
- `validator`：执行 Schema、结构和跨文件一致性检查；
- `evidence`：幂等追加事件并形成有效事件视图；
- `lifecycle`：计算派生时间、证据独立性、阻断条件和转换候选；
- `catalog`：确定性生成目录和报告；
- `cli`：提供统一命令入口。
- `web/controller`：提供 FastAPI 页面和 API 路由；
- `web/domain`：使用 Pydantic 校验请求和响应；
- `web/service`：编排知识创建、编辑、Evidence 与生命周期用例；
- `web/mapper`：在表单对象和 Markdown 文件之间转换；
- `web/middlewares`：提供请求日志和当前用户依赖。

## 测试与持续集成

本地运行：

```bash
pytest -q
```

测试覆盖事件幂等、冲突事件 ID、派生时间、独立验证晋级、安全状态转换、仓库 Lint、Catalog 确定性、网页启动、Pydantic 条件校验、知识创建编辑、元数据保留、Evidence 写入和治理候选。GitHub Actions 会执行 Lint、重建 Catalog、检查生成文件是否有未提交差异并运行测试；因此人工修改 Catalog 或忘记重新生成都会导致检查失败。

## 当前范围与未来优化

当前版本定位为可运行的最小治理内核，不包含 Web 管理平台、向量数据库、自动语义裁决或细粒度读取权限。后续候选能力记录在 [feature/2026-07-11.md](feature/2026-07-11.md)，应依据真实规模和协作数据逐步引入。
