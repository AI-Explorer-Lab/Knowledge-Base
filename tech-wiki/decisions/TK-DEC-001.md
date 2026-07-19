```knowledge-metadata
{
  "conflict_status": "none",
  "created_at": "2026-07-14T07:02:47Z",
  "evidence": {
    "contributors": [
      "zhangsan"
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
