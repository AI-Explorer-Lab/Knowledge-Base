```knowledge-metadata
{
  "archive_idempotency_key": "a270b8215abd1082b307e9dfc6734d64b393c29aef816a6d26eb796c5ee229a9",
  "conflict_status": "none",
  "created_at": "2026-08-15T10:42:52Z",
  "evidence": {
    "contributors": [
      "orchestrator",
      "zhangsan"
    ],
    "references": [
      {
        "contributor": "zhangsan",
        "project_id": "accounting",
        "referenced_at": "2026-08-16T05:11:00Z",
        "revision": 1,
        "used_in": "generation",
        "workflow_id": "accounting-20260816-105748-2caa7bfa"
      }
    ],
    "validations": []
  },
  "id": "TK-GDL-015",
  "layer": "layer1",
  "maturity": "draft",
  "project_id": "account",
  "promotion": {
    "candidate": false,
    "previous_layers": [],
    "target_layer": null,
    "target_path": null
  },
  "revision": 1,
  "scope": "team",
  "source_references": [
    "task:20260815-183253-8b028e7e",
    "commit:b442ba53cb9e3c78053f9246b345b59929fe2524",
    "validation:3"
  ],
  "tags": [
    "frontend",
    "state-management",
    "derived-state",
    "data-consistency",
    "number-formatting"
  ],
  "title": "让新增记录与汇总状态保持同一提交语义",
  "type": "guideline"
}
```

# 让新增记录与汇总状态保持同一提交语义

## 适用范围

适用于前端在提交表单后同时更新列表和聚合数值的本地状态管理场景。

## 问题

只更新账单列表而遗漏今日总额，或分别以过期状态计算两个结果，容易造成明细与汇总不一致。

## 处理方式

提交成功后将规范化的支出记录加入列表，并基于同一条记录或同一状态更新路径重新计算今日支出总额；将金额保持为可计算的数值，展示格式化限制在渲染层。测试应同时断言列表新增记录和汇总值变化。

## 结果

账单明细与今日支出总额在每次成功提交后保持一致，避免局部状态更新造成的显示错误。

## 分层依据

列表与聚合状态的一致性、不可变更新和展示层格式化是可跨项目复用的前端状态管理实践；具体“支出”字段仅是本次示例。
