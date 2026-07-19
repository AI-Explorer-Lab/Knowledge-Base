# 技术知识分类清单

> 本文件是 Layer 1 技术知识的 Layer B 索引。受治理区块由知识治理工具维护，每条知识展示 ID、标题、类型、成熟度、范围、所有者、标签和路径。

## 技术立场标签

- `patterns`：这条知识主要推荐跨项目可复用的正确方案；
- `anti-patterns`：这条知识主要警告应避免的技术做法，并提供替代方案；
- 不设置：中性技术知识，可以同时介绍模式、反模式、原理或背景。

技术立场是与五种知识类型相互独立的可选标签。新建 Layer 1 知识统一按知识类型生成 ID 和目录；标签只保存在元数据中，用于检索和模板提示。已有 `patterns/`、`anti-patterns/` 目录继续兼容，无需迁移。

<!-- knowledge-index:start -->
## 活跃知识

| ID | 标题 | 类型 | 成熟度 | 范围 | 所有者 | 标签 | 路径 |
|---|---|---|---|---|---|---|---|
| `TK-AP-001` | 编辑框不要设计为右下角手动拖拽，改为高度随内容增减 | `guideline` | `draft` | `team` | `-` | web, frontend, ai, design | `tech-wiki/anti-patterns/TK-AP-001.md` |
| `TK-DEC-001` | 后端架构设计模板 | `decision` | `draft` | `team` | `-` | backend, architecture, design, development | `tech-wiki/decisions/TK-DEC-001.md` |
| `TK-DEC-002` | 开发时使用python的版本为3.12 | `decision` | `draft` | `team` | `-` | python, development, backend | `tech-wiki/decisions/TK-DEC-002.md` |
| `TK-DEC-003` | 前端开发语言用vue3+type script | `decision` | `draft` | `team` | `-` | fronten, vue, development | `tech-wiki/decisions/TK-DEC-003.md` |
| `TK-GDL-002` | 隐藏镜像层方案 | `guideline` | `draft` | `team` | `-` | frontend, design, ai, web | `tech-wiki/guidelines/TK-GDL-002.md` |
| `TK-GDL-003` | bash生成脚本一键运行前后端 | `guideline` | `draft` | `team` | `-` | frontend, backend, script | `tech-wiki/guidelines/TK-GDL-003.md` |
| `TK-GDL-004` | 将代码变更审批绑定到精确的 Diff 哈希和提交主题 | `guideline` | `draft` | `team` | `-` | approval, diff-hash, commit-subject, integrity, git | `tech-wiki/guidelines/TK-GDL-004.md` |
| `TK-GDL-005` | 在独立分支中运行真实状态 Canary，禁止合并和推送 | `guideline` | `draft` | `team` | `-` | branch-isolation, scope-control, no-push, no-merge, canary | `tech-wiki/guidelines/TK-GDL-005.md` |
| `TK-GDL-006` | 仅在提交成功后归档仓库变更证据 | `guideline` | `draft` | `team` | `-` | archival, commit-gating, auditability, evidence, workflow | `tech-wiki/guidelines/TK-GDL-006.md` |
| `TK-GDL-007` | 端到端扩展区间筛选时统一查询与计数语义 | `guideline` | `draft` | `team` | `-` | range-filter, pagination, query-consistency, backend | `tech-wiki/guidelines/TK-GDL-007.md` |
| `TK-GDL-008` | 区间输入采用前后端双层校验并保留旧行为 | `guideline` | `draft` | `team` | `-` | client-validation, server-validation, backward-compatibility, form-reset | `tech-wiki/guidelines/TK-GDL-008.md` |
| `TK-GDL-001` | 知识治理脚本只使用 Python 标准库 | `guideline` | `draft` | `team` | `-` | python, governance, dependency | `tech-wiki/patterns/TK-GDL-001.md` |
| `TK-PTF-001` | 新增测试代码不等于测试与构建已经通过 | `pitfall` | `draft` | `team` | `-` | test-evidence, build-verification, acceptance, ci | `tech-wiki/pitfalls/TK-PTF-001.md` |
<!-- knowledge-index:end -->
