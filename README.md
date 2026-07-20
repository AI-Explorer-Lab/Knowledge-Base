# Knowledge Base

一个面向 AI 工程团队的知识治理系统。项目以 Markdown、YAML 和 Git 作为业务事实源，为知识的创建、浏览、引用、验证、修订、审计和生命周期治理提供统一规则，并同时提供 Web、API 与 CLI 三种入口。

## 核心能力

- 使用分层目录、结构化元数据和 Markdown 正文保存知识。
- 使用全景目录、分层目录和完整条目实现渐进式读取。
- 通过 `draft → verified → proven` 成熟度和当前修订的引用、验证证据管理可信度。
- 通过 Vue 页面完成人工录入、浏览、成员管理和受控治理。
- 通过 FastAPI 统一执行身份校验、权限检查、预览、提交和失败恢复。
- 通过 Python CLI 支持引用、验证、索引、冲突、归档和生命周期治理。
- 通过 Git 历史与追加式 `log.md` 同时保留文件变更和业务动作审计。

## 总体架构

```text
浏览器 / 人工操作                       Agent / 自动化工作流
        │                                      │
        ▼                                      ▼
Vue 3 + TypeScript                    Python Governance CLI
Vite 开发入口 :8888                            │
        │ /api                                 │
        ▼                                      │
FastAPI :8000                                  │
Controller → Service → 身份、权限与可靠提交编排 │
        └──────────────────┬───────────────────┘
                           ▼
              tools/knowledge_governance.py
       元数据、路径、成熟度、证据、索引与生命周期规则
                           │
                           ▼
       Markdown + YAML + catalog + log.md + Git
                    业务事实源
                           │
                           └── SQLite（可选运行状态，不保存知识正文）
```

### 逻辑分层

| 层级 | 职责 | 主要位置 |
|---|---|---|
| 表现层 | 页面、路由、表单和交互状态 | `web/frontend/src/` |
| API 控制层 | HTTP 路由、请求与响应模型 | `backend/controller/`、`backend/domain/` |
| 应用服务层 | 身份与角色复核、预览、提交、管理用例 | `backend/service/` |
| 治理领域层 | 元数据、路径、证据、成熟度、索引、归档和冲突规则 | `tools/knowledge_governance.py` |
| 基础设施层 | 配置、写锁、数据库、日志和异常处理 | `backend/config/`、`backend/database/`、`backend/middlewares/` |
| 事实数据层 | Markdown 条目、YAML 配置、目录和追加式审计 | 仓库根目录及各知识分层目录 |

Web 与 CLI 共用治理内核。前端不会直接拼接或写入 Markdown；FastAPI 负责可信身份和用例编排，治理模块负责稳定的领域规则，避免不同入口产生不一致的数据格式。

### 知识模型

系统从三个相互独立的维度描述知识：

- 存储范围：个人、团队约定、跨项目技术、业务领域和当前项目。
- 知识类型：`model`、`decision`、`guideline`、`pitfall`、`process`。
- 成熟度：`draft`、`verified`、`proven`。

每次受控修订都会形成新的 `revision`。历史证据可以保留，但只有与当前修订匹配的引用和验证才能推动当前版本的成熟度。

### 可靠写入

一次提交可能同时影响知识文件、分层目录、全景目录、运行状态和审计日志。项目通过以下机制降低文件型存储的不一致风险：

1. 服务端根据身份、范围、层级和类型派生目标路径，不接受客户端任意文件路径。
2. 预览阶段完成校验、ID 分配、路径计算并签发短时凭证。
3. 提交阶段重新校验身份、权限、配置和预览上下文。
4. 仓库级写锁串行化 Web 与 CLI 的写操作。
5. 单文件使用原子替换，多文件失败时使用快照执行补偿回滚。
6. 预览 nonce 防止重复提交，`base_digest` 防止覆盖较新的修订。
7. 成功操作追加写入审计日志，并保留 Git 可审查差异。

## 目录结构

```text
Knowledge-Base/
├── start.sh                         # 本地一键启动前后端
├── .knowledge-config.yaml           # 成员、角色和业务领域配置
├── knowledge-catalog.md             # 全景索引
├── log.md                           # 追加式业务审计
├── tools/
│   └── knowledge_governance.py      # 共享治理内核与 CLI
├── backend/
│   ├── main.py                      # FastAPI 组装与生命周期
│   ├── controller/                  # HTTP API
│   ├── service/                     # 应用服务与可靠写入编排
│   ├── config/                      # 分环境配置
│   ├── database/                    # 可选 SQLite 运行状态
│   ├── template/                    # 知识正文模板
│   └── tests/                       # 后端测试
├── web/frontend/
│   ├── src/views/                   # 页面
│   ├── src/components/              # UI 组件
│   ├── src/composables/             # 会话与流程状态
│   ├── src/api/                     # API 客户端
│   └── src/__tests__/               # 前端测试
├── tests/
│   └── test_knowledge_governance.py # 治理规则回归测试
└── <knowledge directories>/         # 按范围和类型组织的知识文件
```

## 本地运行

### 1. 准备环境

需要：

- Conda；
- Python 3.12；
- Node.js 与 npm；
- `curl`；
- macOS 或其他支持当前文件锁实现的类 Unix 环境。

创建项目使用的 Conda 环境并安装依赖：

```bash
conda create -n knowledge-base python=3.12
conda run -n knowledge-base python -m pip install -r backend/requirements-dev.txt
npm --prefix web/frontend install
```

`.knowledge-config.yaml` 必须至少包含一名已启用的 Maintainer 或 Super Admin。开发环境使用启动时固定的成员身份；如需指定已配置成员，可在启动前设置：

```bash
export KNOWLEDGE_AGENT__DEV_ACTOR=<member-id>
```

浏览器请求头不能在运行期间切换开发身份。

### 2. 启动前后端

在项目根目录执行：

```bash
./start.sh
```

启动脚本会检查依赖和端口，先启动后端并等待健康检查，再启动前端。可访问：

- Web：`http://127.0.0.1:8888`
- 健康检查：`http://127.0.0.1:8888/api/health`
- API 文档：`http://127.0.0.1:8888/api/docs`

按 `Ctrl+C` 会停止前后端进程。

### 3. 分别启动服务

单独调试后端：

```bash
conda run --no-capture-output -n knowledge-base \
  python -m uvicorn backend.main:app \
  --reload --reload-dir backend \
  --host 127.0.0.1 --port 8000
```

单独调试前端：

```bash
npm --prefix web/frontend run dev -- --host 127.0.0.1 --port 8888 --strictPort
```

Vite 默认把 `/api` 代理到 `http://127.0.0.1:8000`。可通过 `VITE_API_PROXY_TARGET` 调整代理目标。

## 使用入口

### Web

Web 界面提供以下主要流程，实际可见范围由当前成员角色决定：

- 创建：填写元数据和正文，预览服务端派生结果，确认后提交。
- 浏览：按层级或关键词查找当前有效知识并查看详情。
- 权限：维护普通成员和业务领域配置。
- 超级管理：受控修订、提升、退回、归档、恢复、冲突处理和审计查询。

人工浏览不会被记录为 Agent 已真实使用该知识的证据。

### API

开发环境的 OpenAPI 文档位于 `/api/docs`。主要 API 分组包括：

- `/api/health`：服务和仓库健康检查；
- `/api/me`：当前身份与能力；
- `/api/knowledge`：浏览、预览、创建和详情；
- `/api/members`：成员管理；
- `/api/business-domains`：业务领域管理；
- `/api/super-admin`：受控治理和审计。

生产环境不开放 OpenAPI 页面，并要求可信认证代理清理客户端传入的身份头，再注入带时间戳和 HMAC 签名的身份断言。真实角色始终从仓库配置读取。

### CLI

查看治理命令：

```bash
conda run -n knowledge-base python tools/knowledge_governance.py --help
```

CLI 与 Web 写入共用仓库锁和治理规则。治理命令可能修改知识文件、索引、审计日志或 `.knowledge-governance-state.json`；其中 `lint` 即使不带 `--fix` 也会更新调度状态。不要为了演示直接在包含真实数据的仓库执行写命令，测试应使用临时仓库。

## 测试与构建

后端与治理测试使用临时知识仓库，不应写入正式知识数据：

```bash
conda run -n knowledge-base python -m pytest -q backend/tests tests
```

前端测试：

```bash
npm --prefix web/frontend test
```

前端类型检查与生产构建：

```bash
npm --prefix web/frontend run build
```

通用差异检查：

```bash
git diff --check
```

## 配置与部署

后端使用 `KNOWLEDGE_` 前缀读取环境变量，嵌套配置使用双下划线。例如：

```text
KNOWLEDGE_ENV=production
KNOWLEDGE_AGENT__REPO_ROOT=/knowledge
KNOWLEDGE_AGENT__PREVIEW_SECRET=<random-secret>
KNOWLEDGE_AGENT__IDENTITY_HMAC_SECRET=<random-secret>
KNOWLEDGE_DB__URL=sqlite+aiosqlite:////data/backend.db
```

Docker 构建上下文必须是项目根目录：

```bash
docker build -f backend/Dockerfile -t knowledge-base-backend .
```

生产部署需要注意：

- 将真实知识仓库挂载为持久卷，并允许服务执行原子文件替换；
- 为预览凭证和生产身份分别配置足够长度的随机密钥；
- 由可信代理完成认证并注入签名身份，不能信任浏览器自报角色；
- 多实例必须共享知识仓库、写锁、预览 nonce 和审计状态，并确认底层文件系统支持共享锁语义；
- 数据库迁移由发布流程负责，生产环境不应自动建表。

更完整的后端配置和接口说明见 [`backend/README.md`](backend/README.md)。

## 当前边界

- 当前检索以结构化目录、筛选和文本匹配为主，不包含向量检索。
- 当前仓库提供知识治理能力，不是完整的 Agent 工作流编排平台。
- 系统不会自动执行 Git Commit、Push、创建 PR 或远端合并。
- Markdown 是知识事实源；SQLite 只适合作为可重建或可替换的运行状态。
- 单仓库写入通过全局锁串行化，适合知识规模和写频率可控的团队场景。
