```knowledge-metadata
{
  "archive_idempotency_key": "6571fbad5fda137638c2598e7655c09b9c3c5cf3afefae1ae0258a2ce6f323b7",
  "conflict_status": "none",
  "created_at": "2026-07-19T03:27:48Z",
  "evidence": {
    "contributors": [
      "orchestrator"
    ],
    "references": [],
    "validations": []
  },
  "id": "TK-GDL-008",
  "layer": "layer1",
  "maturity": "draft",
  "project_id": "accounting",
  "promotion": {
    "candidate": false,
    "previous_layers": [],
    "target_layer": null,
    "target_path": null
  },
  "revision": 1,
  "scope": "team",
  "source_references": [
    "task:20260719-110212-66531cfe",
    "commit:039e9ec40a560cda1e86a50c5a62804ef7201e5e",
    "validation:1"
  ],
  "tags": [
    "client-validation",
    "server-validation",
    "backward-compatibility",
    "form-reset"
  ],
  "title": "区间输入采用前后端双层校验并保留旧行为",
  "type": "guideline"
}
```

# 区间输入采用前后端双层校验并保留旧行为

## 适用范围

适用于前端表单向后端 API 提交可选数值区间的功能。

## 问题

仅在前端校验无法保护直接调用的 API，仅在后端校验又会产生不必要请求；重置不完整或空参数处理不当还可能破坏原有查询行为。

## 处理方式

前端在上下界同时存在且顺序非法时阻止请求并给出明确提示，重置时清空两项状态；后端独立校验数值范围和上下界顺序并返回清晰错误，未传参数时沿用原有行为。

## 结果

用户能即时发现输入错误，API 仍保持可靠防线，同时旧客户端和无金额条件的查询继续兼容。

## 分层依据

前后端职责划分、可选参数兼容和表单重置策略可用于多种项目的区间查询功能，属于通用技术知识。
