# Knowledge Base Backend

FastAPI 后端负责可信身份、人工知识注入、成员权限管理、超级管理员受控修改，以及对现有 Markdown 治理能力的安全编排。Markdown、`.knowledge-config.yaml`、各级目录与 `log.md` 始终是业务事实来源；SQLite 只保存可选的后端运行状态。

## 本地启动

安装依赖后，推荐从知识库根目录一键启动前后端：

```text
./start.sh
```

浏览器统一访问 `http://127.0.0.1:8888`，`/api` 请求会转发给仅供本机使用的后端进程。按 `Ctrl+C` 会同时停止前后端。

如需单独调试后端，要求 Python 3.12，并从知识库根目录执行：

```text
python -m pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

默认开发身份是 `.knowledge-config.yaml` 中启用的 `zhangsan`，当前配置为 `super_admin`。如需切换，必须在启动进程前固定设置：

```text
KNOWLEDGE_AGENT__DEV_ACTOR=lisi python -m uvicorn backend.main:app --reload
```

浏览器请求头不能切换开发身份；角色和启用状态会在每次请求时重新读取。

## 配置

Dynaconf 从 `backend/config/app.yaml` 的 `environment`、`db`、`agent` 三个区段加载配置。环境变量使用 `KNOWLEDGE_` 前缀，嵌套字段使用双下划线，例如：

- `KNOWLEDGE_ENV=production`
- `KNOWLEDGE_AGENT__REPO_ROOT=/knowledge`
- `KNOWLEDGE_AGENT__PREVIEW_SECRET=<至少 32 字节随机值>`
- `KNOWLEDGE_AGENT__IDENTITY_HMAC_SECRET=<至少 32 字节随机值>`
- `KNOWLEDGE_DB__URL=sqlite+aiosqlite:////data/backend.db`
- `KNOWLEDGE_DB__CREATE_TABLES=false`

相对 SQLite 文件路径会锚定知识仓库根目录，而不是进程工作目录。建表只在 `db.create_tables=true` 的环境执行；开发和测试默认允许，生产默认禁止。启动时还会验证成员配置、至少一名启用的 Maintainer 或 Super Admin，以及固定开发身份确实为启用成员。

成员角色包括 `reader`、`contributor`、`maintainer` 和 `super_admin`。`super_admin` 只能由部署或仓库维护者直接修改 `.knowledge-config.yaml` 授予；成员接口不会接受该角色，也不能降级或停用已有超级管理员。

## 生产身份边界

生产环境必须由可信认证代理删除所有客户端自带的 `X-Knowledge-*` 请求头，完成登录校验后再注入：

- `X-Knowledge-Actor`：稳定成员 ID
- `X-Knowledge-Timestamp`：当前 Unix 时间戳
- `X-Knowledge-Signature`：`<timestamp>:<actor>` 的 HMAC-SHA256 十六进制签名

后端拒绝超时或无效签名，也不接受浏览器或代理传入角色；真实角色和状态始终来自 `.knowledge-config.yaml`。

## 主要接口

- `GET /api/health`：数据库与知识仓库健康状态
- `GET /api/me`：当前成员与可用能力
- `GET /api/knowledge`：按 Layer 或关键词浏览当前有效知识；人工只读且不写引用证据
- `GET /api/knowledge/options`：知识类型、可用层级、Layer 1 可选技术立场标签和 Layer 2 业务领域；新知识统一按知识类型派生目录，旧 Layer 1 方向目录继续兼容
- `POST /api/business-domains`：Maintainer 新增 Layer 2 业务领域并记录审计日志
- `PATCH /api/business-domains/{domain_id}`：Super Admin 修改业务领域名称、说明或启用状态
- `POST /api/knowledge/preview`：预校验并签发短时预览凭证
- `POST /api/knowledge/manual`：再次校验后原子写入知识、目录与日志
- `GET /api/knowledge/{knowledge_id}`：完成页的人工只读查看，不计为 Agent 消费且不写 evidence
- `GET/POST/PATCH /api/members`：Maintainer 成员权限管理
- `GET /api/super-admin/knowledge`：Super Admin 查询有效和已归档知识
- `GET /api/super-admin/knowledge/{knowledge_id}`：Super Admin 读取完整知识、版本和治理状态
- `POST /api/super-admin/knowledge/{knowledge_id}/preview`：预览知识修改、路径和成熟度影响
- `POST /api/super-admin/knowledge/{knowledge_id}/commit`：校验短时凭证和原版本后原子提交修改
- `POST /api/super-admin/knowledge/{knowledge_id}/actions`：执行提升、退回、归档、恢复和冲突治理动作
- `GET /api/super-admin/audit`：只读查询追加式审计记录

超级管理员修改知识后，`revision` 自动增加，`maturity` 回到 `draft`。旧引用和验证继续保留，但只有与当前 `revision` 一致的证据可以推动成熟度。知识文件、分类目录、全景目录和 `log.md` 在同一仓库写锁内更新；日志失败时修改会回滚。

## 测试

测试全部使用临时知识仓库，不向正式知识库写入样例数据：

```text
python -m pip install -r backend/requirements-dev.txt
python -m pytest -q backend/tests tests
```

## Docker 构建与部署

构建上下文必须是知识库根目录：

```text
docker build -f backend/Dockerfile -t knowledge-base-backend .
```

生产运行时将真实知识仓库作为持久卷挂载，并显式传入生产配置和两个随机密钥：

```text
docker run --rm -p 8000:8000 \
  -v /absolute/path/to/Knowledge-Base:/knowledge \
  -e KNOWLEDGE_ENV=production \
  -e KNOWLEDGE_AGENT__REPO_ROOT=/knowledge \
  -e KNOWLEDGE_AGENT__PREVIEW_SECRET=... \
  -e KNOWLEDGE_AGENT__IDENTITY_HMAC_SECRET=... \
  knowledge-base-backend
```

生产环境由迁移或发布流程负责数据库表结构；不要为方便而开启自动建表。仓库挂载目录必须允许后端原子替换文件，并保证同一仓库的所有实例共享 `.knowledge-write.lock`。

## 故障排查

- 启动时报成员配置错误：检查 `.knowledge-config.yaml` 的 `version`、成员 ID、角色、状态和至少一名启用 Maintainer 或 Super Admin。
- 开发身份被拒绝：确认 `KNOWLEDGE_AGENT__DEV_ACTOR` 对应启用成员，且启动后没有尝试用请求头切换身份。
- Layer 2 没有可选领域：Layer 2 会始终显示；请由 Maintainer 在知识注入页点击“新增业务领域”，Contributor 需联系 Maintainer。
- 预览后无法提交：表单、成员角色、受控目录或配置发生变化时必须重新预览；服务端会拒绝旧上下文。
- 健康检查返回 503：核对仓库挂载、配置文件、SQLite 路径权限和数据库连通性。
- 写入失败：使用响应中的 `request_id` 检索结构化日志；服务会回滚知识文件、目录和日志，释放失败的预览预约以便安全重试。
- 超级管理接口返回 403：确认当前可信身份在 `.knowledge-config.yaml` 中明确配置为启用的 `super_admin`；不能通过前端或请求体临时提升权限。
- 管理员修改返回 409：目标知识在预览后发生了变化，请重新加载详情并重新预览，不能覆盖较新的 revision。
