```knowledge-metadata
{
  "archive_idempotency_key": "bac453e61b4c5863a9b6b7a48765674dfb0ece0a1c9006e5222943ef8157affe",
  "conflict_status": "none",
  "created_at": "2026-07-19T03:27:47Z",
  "evidence": {
    "contributors": [
      "orchestrator",
      "zhangsan"
    ],
    "references": [
      {
        "contributor": "zhangsan",
        "project_id": "accounting",
        "referenced_at": "2026-07-19T10:17:57Z",
        "revision": 1,
        "used_in": "generation",
        "workflow_id": "20260719-173617-0d8e6e51"
      }
    ],
    "validations": []
  },
  "id": "TK-GDL-007",
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
    "range-filter",
    "pagination",
    "query-consistency",
    "backend"
  ],
  "title": "端到端扩展区间筛选时统一查询与计数语义",
  "type": "guideline"
}
```

# 端到端扩展区间筛选时统一查询与计数语义

## 适用范围

适用于包含控制器、服务、数据访问和分页响应的列表查询接口。

## 问题

新增最小值和最大值条件时，如果参数未贯穿各层，或数据查询与总数统计使用了不同谓词，就会出现列表内容、组合筛选和分页 total 不一致。

## 处理方式

明确区间边界的包含语义，将可选参数贯穿请求模型、服务和数据访问层；数据查询与计数查询必须复用相同筛选条件，并测试单边界、双边界、与既有条件组合及分页场景。

## 结果

区间筛选可以稳定地与其他条件及分页组合，返回记录和筛选后总数保持一致。

## 分层依据

该做法适用于不同项目中的分层列表查询和分页接口，属于跨项目可复用的技术知识。
