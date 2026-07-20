```knowledge-metadata
{
  "archive_idempotency_key": "a5d1fdca2943d14d302614565bcb24916710e0afa48e691b8024f0c2fc6aca64",
  "conflict_status": "none",
  "created_at": "2026-07-19T10:17:55Z",
  "evidence": {
    "contributors": [
      "orchestrator",
      "zhangsan"
    ],
    "references": [
      {
        "contributor": "zhangsan",
        "project_id": "accounting",
        "referenced_at": "2026-07-19T13:48:52Z",
        "revision": 1,
        "used_in": "generation",
        "workflow_id": "20260719-213209-46bf6a8b"
      }
    ],
    "validations": []
  },
  "id": "TK-GDL-009",
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
    "task:20260719-173617-0d8e6e51",
    "commit:16f50f3f7f394b3474b7b57058558f2fa5c67145",
    "validation:1"
  ],
  "tags": [
    "frontend",
    "presentation-layer",
    "localization",
    "number-formatting",
    "data-integrity"
  ],
  "title": "将本地化数值格式化限制在展示层",
  "type": "guideline"
}
```

# 将本地化数值格式化限制在展示层

## 适用范围

适用于前端列表、详情和报表中需要按地区规则展示金额或其他数值的场景。

## 问题

如果为获得千分位或固定小数位而直接修改原始数值，可能连带改变接口参数、筛选条件、统计计算和交互行为。

## 处理方式

保留接口返回的原始数值，仅在渲染展示文本时调用统一的本地化格式化器，并明确地区、小数位等选项；组件测试应断言整数、非定长小数和千分位场景的最终文本，同时保持业务操作继续使用原始值。

## 结果

界面获得一致且可测试的本地化显示，同时避免格式化逻辑渗入数据传输、筛选、删除或统计计算。

## 分层依据

展示格式与业务数据分离是可用于不同前端框架和业务项目的通用技术实践，属于跨项目技术知识。
