```knowledge-metadata
{
  "conflict_status": "none",
  "created_at": "2026-07-14T07:02:47Z",
  "evidence": {
    "contributors": [
      "zhangsan",
      "demo-reviewer",
      "local-user"
    ],
    "references": [
      {
        "contributor": "zhangsan",
        "project_id": "accounting",
        "referenced_at": "2026-07-18T16:06:30Z",
        "revision": 1,
        "used_in": "generation",
        "workflow_id": "20260719-000039-922e51b2"
      },
      {
        "contributor": "zhangsan",
        "project_id": "accounting",
        "referenced_at": "2026-07-19T03:27:49Z",
        "revision": 1,
        "used_in": "generation",
        "workflow_id": "20260719-110212-66531cfe"
      },
      {
        "contributor": "zhangsan",
        "project_id": "accounting",
        "referenced_at": "2026-07-19T10:17:56Z",
        "revision": 1,
        "used_in": "generation",
        "workflow_id": "20260719-173617-0d8e6e51"
      },
      {
        "contributor": "zhangsan",
        "project_id": "accounting",
        "referenced_at": "2026-07-19T13:48:34Z",
        "revision": 1,
        "used_in": "generation",
        "workflow_id": "20260719-213209-46bf6a8b"
      },
      {
        "contributor": "zhangsan",
        "project_id": "accounting",
        "referenced_at": "2026-07-23T15:30:47Z",
        "revision": 1,
        "used_in": "generation",
        "workflow_id": "20260722-201541-0c813afa"
      },
      {
        "contributor": "demo-reviewer",
        "project_id": "live-demo",
        "referenced_at": "2026-07-25T07:32:10Z",
        "revision": 1,
        "used_in": "generation",
        "workflow_id": "audit-e2e-20260725"
      },
      {
        "contributor": "zhangsan",
        "project_id": "accounting",
        "referenced_at": "2026-08-13T02:40:41Z",
        "revision": 1,
        "used_in": "generation",
        "workflow_id": "20260813-094134-9cfef825"
      },
      {
        "contributor": "local-user",
        "project_id": "read-notes",
        "referenced_at": "2026-08-13T04:25:28Z",
        "revision": 1,
        "used_in": "generation",
        "workflow_id": "20260813-121910-760917a7"
      },
      {
        "contributor": "zhangsan",
        "project_id": "accounting",
        "referenced_at": "2026-08-16T05:10:59Z",
        "revision": 1,
        "used_in": "generation",
        "workflow_id": "accounting-20260816-105748-2caa7bfa"
      }
    ],
    "validations": []
  },
  "id": "TK-DEC-001",
  "layer": "layer1",
  "maturity": "draft",
  "promotion": {
    "candidate": false,
    "previous_layers": [],
    "target_layer": null,
    "target_path": null
  },
  "scope": "team",
  "source_references": [
    "项目经验总结"
  ],
  "tags": [
    "backend",
    "architecture",
    "design",
    "development"
  ],
  "technical_direction": "patterns",
  "title": "后端架构设计模板",
  "type": "decision"
}
```

# 后端架构设计模板

## 模式摘要

好的后端架构是保证日后项目可读性、可维护性、可扩展性的重要一环
## 复用条件

设计后端架构时的模板
## 收益与代价

提高项目可读性、可维护性、可扩展性，且所有后端能保持一致风格
## 验证案例

已有项目已经通过验证

## 最终决策

后端架构模板如下：
```
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
│   └── __init__.py                 # 初始化阶段仅保留持久化边界
│       ├── create()              # 新增
│       ├── get()                 # 查询单条
│       ├── list()                # 条件查询
│       ├── update()              # 更新
│       └── delete()              # 删除或软删除
│
├── utils/
│   └── __init__.py                 # 初始化阶段仅保留工具能力边界
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

初始化规则：`{business}` 必须替换为项目业务名。例如项目名为 `accounting` 时，创建 `accounting_api.py` 和 `accounting_service.py`。数据库设计和其他工具能力与后端骨架初始化相互独立；初始化阶段只创建 `mapper/__init__.py` 和 `utils/__init__.py`，不创建数据库实体 mapper 或能力占位文件。后续任务明确设计数据库实体或其他能力后，再向对应目录新增具体文件。
