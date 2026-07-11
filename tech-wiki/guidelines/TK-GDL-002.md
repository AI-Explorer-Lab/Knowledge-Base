---
schema_version: 1
id: TK-GDL-002
title: FastAPI 后端项目应按职责分层组织
type: guideline
scope: tech
domain: backend-architecture
maturity: verified
status: active
risk_level: medium
owner: knowledge-core-team
maintainers: [backend-team]
created_at: 2026-07-11
updated_at: 2026-07-11
applicable_phases: [ARCHITECT, IMPLEMENT, BUILD_VERIFY, RELEASE]
applicable_conditions:
  - 项目需要提供长期运行的 FastAPI HTTP 服务
  - 项目包含鉴权、业务编排、数据库访问或外部 API 集成
  - 项目需要独立部署、持续集成和运行期配置
not_applicable_conditions:
  - 仅提供本地命令行工具或一次性脚本
  - 没有 HTTP API、在线鉴权、数据库或服务部署需求
  - 小型验证性原型尚未形成稳定业务边界
tags: [python, fastapi, backend, layered-architecture, dynaconf]
source_references:
  - type: user_provided_template
    ref: conversation:backend-architecture-template-2026-07-11
supersedes: []
superseded_by: null
polarity: recommend
---
# FastAPI 后端项目应按职责分层组织

## 结论

需要长期运行并包含鉴权、业务逻辑和数据访问的 FastAPI 后端，应按照配置、接口、应用服务、领域对象、数据访问和基础设施职责分层。HTTP 层不得直接操作数据库，业务服务不得依赖 FastAPI 请求对象，核心业务规则不得散落在 `utils` 中。

该目录模板是后端服务的推荐起点，不是所有 Python 项目的强制结构。对于只有本地 CLI、Markdown 处理或一次性任务的项目，应使用更小的结构，避免提前引入 FastAPI、数据库和部署设施。

## 背景与问题

后端项目在规模增长后，容易把请求参数、业务判断、数据库操作、鉴权和工具函数写在同一个模块中。这样会导致 API 难以测试、业务逻辑无法复用、数据库替换困难，并让异常处理和权限检查出现遗漏。

本指导原则来源于团队提供的后端架构模板，并按本知识库的治理边界进行了补充：明确每层依赖方向，区分同步和异步资源管理，限制 `utils` 的职责，避免配置文件保存秘密，并说明什么时候不应该使用完整后端架构。

## 适用条件

- 服务使用 FastAPI 对外提供 HTTP API；
- 需要读取用户身份并实施鉴权；
- 存在可以独立测试的业务用例；
- 需要访问数据库或外部服务；
- 需要容器化、持续集成或多环境部署。

## 不适用条件

- 项目只是本地命令行工具，例如当前知识库治理 CLI；
- 项目只包含少量无状态函数或一次性数据处理脚本；
- 尚未确定 API、业务边界和持久化需求的实验项目；
- 为了“目录看起来完整”而提前创建没有实际职责的空层。

## 详细说明

### 推荐目录结构

一级缩进表示文件夹，二级缩进表示文件，三级缩进表示文件内的主要职责、方法或配置。API 文件应继续按业务场景拆分，不要把所有接口放进一个文件。

```text
backend/
├── config/
│   ├── app.yaml
│   │   ├── db                    # 数据库连接的非敏感默认配置
│   │   ├── agent                 # Agent 或外部模型服务的非敏感配置
│   │   └── environment           # 当前配置环境名称及公共环境参数
│   └── config.py
│       ├── settings              # Dynaconf 配置实例
│       ├── load_environment()    # 根据环境加载对应配置
│       └── validate_settings()   # 启动前检查必需配置
│
├── constant/
│   ├── enums.py                  # 跨模块共享且稳定的枚举
│   └── values.py                 # 少量真正全局的常量
│
├── domain/
│   ├── req.py                    # FastAPI/Pydantic 请求模型
│   ├── res.py                    # FastAPI/Pydantic 响应模型
│   └── models.py                 # 与 HTTP 无关的领域值对象和参数对象
│
├── controller/
│   ├── health_api.py             # 健康检查接口
│   └── {business}_api.py         # 按业务场景拆分的 APIRouter
│       ├── router                # 当前场景的 APIRouter
│       └── endpoints             # 注入当前用户和应用服务依赖
│
├── service/
│   └── {business}_service.py
│       ├── execute_use_case()    # 编排业务用例
│       └── validate_business()   # 执行业务规则检查
│
├── middlewares/
│   ├── request_logging.py        # 请求 ID、耗时和结构化日志
│   ├── auth_dependency.py        # 获取并校验当前用户，供 Depends 注入
│   └── auth_handler.py           # 将认证与授权异常转换为统一响应
│
├── exceptions/
│   ├── business_exception.py     # 业务异常基类和具体错误类型
│   └── exception_handler.py      # 注册业务异常及未知异常处理器
│
├── mapper/
│   └── {database}_{entity}.py
│       ├── create()              # 新增
│       ├── get()                 # 查询单条
│       ├── list()                # 条件查询
│       ├── update()              # 更新
│       └── delete()              # 删除或软删除
│
├── utils/
│   └── {capability}.py           # 无业务状态、可独立复用的纯工具能力
│
├── database/
│   ├── session.py
│   │   ├── async_engine          # SQLAlchemy 异步 Engine
│   │   ├── async_session_factory # async_sessionmaker
│   │   └── get_session()         # FastAPI 异步依赖，负责提交、回滚和关闭
│   └── lifecycle.py
│       ├── init_database()       # 必要初始化或连通性检查
│       ├── close_database()      # 释放连接池
│       └── create_tables()       # 仅在明确允许的环境中建表
│
├── tests/                        # 单元、接口和集成测试
├── main.py                       # FastAPI 实例、路由、异常处理和 lifespan
├── Dockerfile                    # 可重复构建的运行镜像
├── Jenkinsfile                  # 团队实际使用 Jenkins 时提供
├── README.md                    # 启动、配置、测试、部署和故障排查
├── .gitignore
└── requirements.txt             # 仅在团队部署链强制要求时使用
```

### 分层依赖方向

推荐调用方向是：

```text
controller
→ service
→ mapper / 明确命名的基础能力
→ database 或外部系统
```

`domain` 中与 HTTP 无关的对象可以被 `service` 和 `mapper` 共同使用，但领域对象不得反向依赖 Controller。Controller 只负责协议转换、依赖注入和响应状态码；Service 负责编排业务用例；Mapper 负责持久化操作，不包含跨实体业务决策。

Service 不应被定义为“调用 utils 的一层”。它的主要价值是表达业务用例和事务边界。通用能力只有在无业务语义、无可变全局状态并且可以独立测试时，才进入 `utils`；否则应放回对应的 Service、Domain 或基础设施模块。

### 配置规则

`config.py` 使用 Dynaconf 加载环境配置时，应显式规定环境选择顺序，例如：启动参数或环境变量优先，其次才是本地默认值。数据库密码、API Key、Token 等秘密不得提交到 `app.yaml`，只能从环境变量或秘密管理服务读取。

`app.yaml` 应保存非敏感默认项和配置结构，例如：

```yaml
default:
  environment: local
  db:
    driver: postgresql+asyncpg
    pool_size: 5
  agent:
    timeout_seconds: 30

test:
  environment: test
  db:
    driver: sqlite+aiosqlite
```

配置加载后必须在应用启动前校验，缺少必需配置时快速失败，而不是等到第一次请求才报错。

### FastAPI 入口与生命周期

`main.py` 应保持轻量，只负责组装应用，不承载业务逻辑。推荐包含：

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_database()
    try:
        yield
    finally:
        await close_database()


app = FastAPI(lifespan=lifespan)
register_routers(app)
register_exception_handlers(app)
register_middlewares(app)
```

异步数据库生命周期应使用 `@asynccontextmanager`、异步生成器或框架支持的异步依赖，不能用普通 `@contextmanager` 包装 `AsyncSession`。请求级 Session 应保证异常回滚和最终关闭；是否自动提交应由团队事务策略统一规定，不能在不同 Mapper 中随意处理。

### 鉴权、日志和异常

获取当前用户适合使用 FastAPI `Depends`，因为它是请求级依赖；请求 ID、耗时和通用访问日志适合使用 Middleware。认证失败、权限不足、业务冲突和未知异常必须产生不同的稳定错误码，但未知异常响应不得泄露堆栈、SQL 或秘密配置。

日志至少应包含请求 ID、路由、状态码、耗时和经过脱敏的用户标识。密码、Token、Cookie、Authorization Header 和敏感业务字段不得写入日志。

### 数据访问与建表

Mapper 方法负责明确的数据库交互，并接收请求级 `AsyncSession`。业务 Service 决定一个用例中的操作顺序和事务边界。生产环境的表结构变更应优先使用数据库迁移工具，`create_tables()` 只适合本地开发、测试或经过明确批准的初始化场景。

### 依赖和交付文件

如果项目已经使用 `pyproject.toml` 管理依赖，就不应再人工维护一份内容重复的 `requirements.txt`。只有 Jenkins、容器平台或组织规范强制要求时，才从锁定依赖生成 `requirements.txt`。同理，团队未使用 Jenkins 时不需要创建空的 `Jenkinsfile`；应使用实际运行的 CI 平台配置。

Dockerfile 应使用非 root 用户、固定基础镜像范围、分层安装依赖，并通过环境变量注入运行配置。README 至少说明环境准备、配置项、数据库迁移、启动、测试、镜像构建和常见故障。

## 验证方式

采用此模板的后端项目至少应通过以下验证：

1. FastAPI 应用可以通过 `lifespan` 正常启动和关闭，数据库连接池得到释放；
2. Controller 测试可以替换 Service 依赖，不需要连接真实数据库；
3. Service 单元测试可以在不启动 FastAPI 的情况下运行；
4. Mapper 集成测试覆盖提交、回滚、查询和连接关闭；
5. 未认证、权限不足、业务异常和未知异常返回稳定且不泄密的响应；
6. 配置缺失时应用启动失败，并给出明确但不包含秘密的错误；
7. Docker 镜像能够构建并通过健康检查；
8. CI 执行格式检查、静态检查、单元测试和必要的集成测试；
9. 目录中的每一层都有实际职责，不存在只为满足模板而创建的空模块；
10. 通过架构评审确认当前项目确实满足本知识的适用条件。

## 来源

本知识根据团队在 2026-07-11 提供的 Python/FastAPI 后端架构模板整理。原模板规定了 `config`、`constant`、`domain`、`controller`、`service`、`middlewares`、`exceptions`、`mapper`、`utils`、`database`、`main.py`、Dockerfile、Jenkinsfile、README、`.gitignore` 和依赖文件等结构。

整理时保留了原始分层意图，并补充以下治理约束：仅在真实后端服务中使用；秘密配置不得进入 YAML；异步 Session 使用异步上下文；Service 不等同于 Utils 调用层；生产建表优先使用迁移；依赖和 CI 文件以实际工具链为准。

## 具体行为

- 在架构阶段先判断项目是否需要在线 API、鉴权、数据库和独立部署；
- 满足条件时，以推荐目录作为起点并按业务场景拆分 API；
- 保持 Controller、Service、Mapper 和 Database 的单向依赖；
- 使用 Dynaconf 管理多环境非敏感配置，秘密由环境变量或秘密服务提供；
- 使用 FastAPI `lifespan` 管理应用级资源，使用异步依赖管理请求级 Session；
- 为鉴权、异常、数据库事务和配置失败编写测试；
- 只创建实际使用的 Docker、Jenkins 和依赖管理文件。

## 预期收益

- API 协议、业务规则和数据库操作可以分别测试和修改；
- 当前用户、鉴权、异常和日志处理方式保持一致；
- 异步数据库连接和事务边界更容易审计；
- 多环境配置清晰且减少秘密泄露风险；
- 后续增加新业务场景时可以按相同方式扩展，而不需要继续堆积到单个文件；
- 避免把适用于大型在线服务的模板强加给简单 CLI 和脚本项目。

## 例外情况

小型 FastAPI 原型可以暂时合并 Controller 和 Service，但一旦出现数据库事务、复杂业务规则或多个调用入口，应重新拆分。只有单一数据库和极少查询时，Mapper 可以先按实体组织，不必提前引入复杂 Repository 抽象。

如果组织已经有统一脚手架、依赖注入框架、配置中心、迁移工具或 CI 平台，应优先遵循组织标准，并记录与本模板的差异。任何例外都不应破坏以下底线：秘密不入库、业务逻辑不写在 HTTP 路由里、异步资源正确关闭、错误响应不泄密、重要行为可测试。
