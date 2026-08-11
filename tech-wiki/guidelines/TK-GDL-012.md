```knowledge-metadata
{
  "archive_idempotency_key": "610d4ef1e950acd7ab461abe253d6fec8ef8d7e8c1cc0072b12dd4b6320598c2",
  "conflict_status": "none",
  "created_at": "2026-07-25T07:32:07Z",
  "evidence": {
    "contributors": [
      "orchestrator"
    ],
    "references": [],
    "validations": []
  },
  "id": "TK-GDL-012",
  "layer": "layer1",
  "maturity": "draft",
  "project_id": "live-demo",
  "promotion": {
    "candidate": false,
    "previous_layers": [],
    "target_layer": null,
    "target_path": null
  },
  "revision": 1,
  "scope": "team",
  "source_references": [
    "task:audit-e2e-20260725",
    "commit:b22b6a94b23d07a17ee8772edac2ce68116c7768",
    "validation:1"
  ],
  "tags": [
    "money-formatting",
    "integer-arithmetic",
    "fixed-width",
    "input-validation",
    "boundary-testing"
  ],
  "title": "使用整数运算格式化最小货币单位",
  "type": "guideline"
}
```

# 使用整数运算格式化最小货币单位

## 适用范围

适用于将整数表示的美分、分或其他最小货币单位转换为固定小数位展示字符串的跨项目场景。

## 问题

使用浮点数换算货币可能引入精度风险，直接拼接余数又容易遗漏前导零，导致 5 美分等输入无法稳定显示为两位小数。

## 处理方式

先拒绝负数等不支持的输入，再通过整数除法或 divmod 分离主单位与余数，并使用固定宽度格式补足余数位；测试应覆盖零、个位余数、跨主单位边界和较大整数。

## 结果

金额格式化不依赖浮点精度，最小货币单位始终保持规定的小数位数，非法输入也具有明确行为。

## 分层依据

整数货币单位换算、定宽补零和边界测试适用于不同项目与货币格式化实现，属于跨项目通用技术知识。
