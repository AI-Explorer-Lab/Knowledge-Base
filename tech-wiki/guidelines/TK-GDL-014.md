```knowledge-metadata
{
  "archive_idempotency_key": "9b72988ae15fcee3c7d8e6eef6c91893953a221470d30fc71766be3c06851b37",
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
  "id": "TK-GDL-014",
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
    "validation:1",
    "validation:2",
    "validation:3"
  ],
  "tags": [
    "frontend",
    "form-validation",
    "input-validation",
    "error-messaging",
    "boundary-testing"
  ],
  "title": "对金额和必填字段执行明确的前端校验",
  "type": "guideline"
}
```

# 对金额和必填字段执行明确的前端校验

## 适用范围

适用于包含金额、分类或其他必填字段的前端表单提交功能。

## 问题

仅依赖浏览器默认校验或在提交后静默失败，无法覆盖空值、零值、负数和非法格式，并会让用户不清楚为何保存失败。

## 处理方式

在提交处理前统一校验字段：金额必须解析为大于 0 的数字，分类必须包含非空内容，备注允许为空；校验失败时阻止保存，并在对应位置显示明确错误提示。使用组件测试覆盖空值、零值、负数、非法格式、空分类和合法输入。

## 结果

非法数据不会进入保存流程，用户能获得可理解的反馈，合法支出可以正常提交。

## 分层依据

表单输入校验、提交前阻断、错误提示和边界测试适用于不同前端项目，属于跨项目通用技术知识，而非特定 accounting 业务规则。
