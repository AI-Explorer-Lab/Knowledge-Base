# 知识全景目录

> 本文件是 Agent 查询知识库的 Layer A 入口。知识分层和阶段查询路径来自微信公众号原文；Layer 0-P 按本项目要求调整为团队仓库内的成员子目录，个人知识团队可见但只允许所有者消费。

## 知识分层

| 层级 | 内容 | 位置 | 共享范围 |
|---|---|---|---|
| Layer 0-P | 个人偏好与个人知识 | `personal-prefernece/{用户名}/` | 团队可见；个人知识仅所有者消费 |
| Layer 0-T | 团队约定 | `team-conventions/` | 团队级，Git 共享 |
| Layer 1 | 技术知识 | `tech-wiki/` | 团队级，跨项目 |
| Layer 2 | 业务知识 | `biz-wiki/{domain}/` | 团队级，按领域组织 |
| Layer 3 | 项目知识 | `docs/knowledge/` | 项目级，随项目演进 |

## 渐进查询路径

```text
Layer A：读取本目录
→ Layer B：读取对应分类的 catalog.md
→ Layer C：按需读取完整知识条目
→ 必要时沿 source_references 追溯原始产物
```

## 各阶段推荐查阅路径

| 阶段 | 查询焦点 | 重点知识类型 |
|---|---|---|
| `ANALYSE_PRODUCT` | Layer 2 业务知识、历史需求 | `model`、`process`、`pitfall` |
| `ANALYSE_TECH` | Layer 1 技术知识、归档索引 | `decision`、`guideline(avoid)`、`pitfall` |
| `ARCHITECT` | 架构模式、实体关系 | `decision`、`model` |
| `IMPLEMENT` | 编码实践、团队约定 | `guideline`、`pitfall` |
| `BUILD_VERIFY` | 反模式库 | `pitfall`、`guideline(avoid)` |

每个阶段使用独立查询预算。原文没有给出具体预算数值。

## 分类入口

- Layer 0-P 个人偏好：`personal-prefernece/{用户名}/preferences.md`
- Layer 0-P 个人知识：`personal-prefernece/{用户名}/knowledge/catalog.md`
- Layer 0-T 团队约定：`team-conventions/`
- Layer 1 技术知识：`tech-wiki/catalog.md`
- Layer 2 业务知识：`biz-wiki/{domain}/catalog.md`
- Layer 3 项目知识：`docs/knowledge/catalog.md`

<!-- knowledge-summary:start -->
## 治理状态摘要

| 层级 | 活跃条目 | 归档条目 |
|---|---:|---:|
| Layer 0-P | 3 | 0 |
| Layer 1 | 5 | 0 |
| Layer 2 | 0 | 0 |
| Layer 3 | 0 | 0 |
<!-- knowledge-summary:end -->
