```knowledge-metadata
{
  "applicability": {
    "path_globs": [
      "backend/**"
    ],
    "project_ids": [
      "accounting"
    ],
    "stages": [
      "generation",
      "spec_evaluation",
      "architecture_evaluation"
    ],
    "technologies": [
      "python",
      "fastapi"
    ]
  },
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
      },
      {
        "contributor": "zhangsan",
        "project_id": "accounting",
        "referenced_at": "2026-07-19T13:48:46Z",
        "revision": 1,
        "used_in": "generation",
        "workflow_id": "20260719-213209-46bf6a8b"
      },
      {
        "contributor": "zhangsan",
        "project_id": "accounting",
        "referenced_at": "2026-07-20T05:10:25Z",
        "revision": 2,
        "used_in": "stage_b_real_rule_validation",
        "workflow_id": "stage-b-real-rule-20260720-tk-gdl-007"
      }
    ],
    "validations": [
      {
        "contributor": "zhangsan",
        "project_id": "accounting",
        "result": "passed",
        "revision": 2,
        "source": "Accounting-Software: backend transaction controller/service/mapper tests; 31 passed on 2026-07-20",
        "validated_at": "2026-07-20T05:10:25Z",
        "workflow_id": "stage-b-real-rule-20260720-tk-gdl-007"
      }
    ]
  },
  "id": "TK-GDL-007",
  "layer": "layer1",
  "maturity": "verified",
  "project_id": "accounting",
  "promotion": {
    "candidate": false,
    "previous_layers": [],
    "target_layer": null,
    "target_path": null
  },
  "revision": 2,
  "rule_owner": "zhangsan",
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
  "type": "guideline",
  "updated_at": "2026-07-20T05:09:18Z",
  "updated_by": "zhangsan"
}
```

# 端到端扩展区间筛选时统一查询与计数语义

## 适用范围

适用于 Accounting 后端中包含控制器、服务、数据访问和分页响应的列表查询接口。

## 约束

新增最小值、最大值或其他区间条件时，必须明确边界是否包含，将可选参数贯穿请求模型、服务和数据访问层，并让数据查询与总数统计复用同一组筛选谓词。

## 反例

列表查询应用金额范围但 `total` 仍统计未筛选数据，或控制器接收参数而服务/mapper 丢失参数，均不满足本规则。没有分页和计数语义的纯单条查询不受本规则阻断。

## 验证方法

运行后端控制器、服务和 mapper 测试，覆盖单边界、双边界、非法上下界、与既有条件组合，以及记录列表和筛选后总数一致。

## 维护责任

维护人 `zhangsan` 负责在查询参数、分页协议或 mapper 签名变化后复核本规则。

## 结果

区间筛选能够稳定地与其他条件及分页组合，返回记录和筛选后总数保持一致。

## 分层依据

该规则是可复用的后端数据语义，但当前验证证据来自 Accounting，因此先限制到 Accounting 的后端路径和技术栈。
