```knowledge-metadata
{
  "applicability": {
    "path_globs": [
      "frontend/**"
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
      "vue",
      "typescript",
      "javascript"
    ]
  },
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
      },
      {
        "contributor": "zhangsan",
        "project_id": "accounting",
        "referenced_at": "2026-07-20T05:10:25Z",
        "revision": 2,
        "used_in": "stage_b_real_rule_validation",
        "workflow_id": "stage-b-real-rule-20260720-tk-gdl-009"
      }
    ],
    "validations": [
      {
        "contributor": "zhangsan",
        "project_id": "accounting",
        "result": "passed",
        "revision": 2,
        "source": "Accounting-Software: TransactionList component tests; 9 passed on 2026-07-20",
        "validated_at": "2026-07-20T05:10:25Z",
        "workflow_id": "stage-b-real-rule-20260720-tk-gdl-009"
      }
    ]
  },
  "id": "TK-GDL-009",
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
  "type": "guideline",
  "updated_at": "2026-07-20T05:09:18Z",
  "updated_by": "zhangsan"
}
```

# 将本地化数值格式化限制在展示层

## 适用范围

适用于 Accounting 前端列表、详情和报表中按地区规则展示金额或其他数值的场景。

## 约束

必须保留接口返回的原始数值，只在渲染展示文本时调用统一的本地化格式化器；筛选、删除、统计和接口参数必须继续使用未格式化的原始值。

## 反例

为显示千分位而直接改写业务对象中的 `amount`，或把带货币符号和分组符的字符串传回 API，均不满足本规则。后端生成面向用户的最终报表文本不属于前端展示层规则的适用路径。

## 验证方法

运行组件测试，断言整数、非定长小数和千分位金额的最终文本，并验证业务交互仍向 API 传递原始 ID 与数值。

## 维护责任

维护人 `zhangsan` 负责在地区、小数位、金额模型或前端组件边界变化后复核本规则。

## 结果

界面获得一致且可测试的本地化显示，同时格式化逻辑不会渗入数据传输、筛选、删除或统计计算。

## 分层依据

展示格式与业务数据分离具有跨项目价值，但当前真实验证来自 Accounting，因此先限制到 Accounting 前端路径和技术栈。
