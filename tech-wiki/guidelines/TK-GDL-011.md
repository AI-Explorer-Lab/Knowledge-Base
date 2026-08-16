```knowledge-metadata
{
  "archive_idempotency_key": "36d3161843a8e9c63ef9f8ab0d2e7713ded3db739faea50f73a8fc8c0ea58166",
  "conflict_status": "none",
  "created_at": "2026-07-23T15:30:45Z",
  "evidence": {
    "contributors": [
      "orchestrator",
      "demo-reviewer",
      "zhangsan"
    ],
    "references": [
      {
        "contributor": "demo-reviewer",
        "project_id": "live-demo",
        "referenced_at": "2026-07-25T07:32:09Z",
        "revision": 1,
        "used_in": "generation",
        "workflow_id": "audit-e2e-20260725"
      },
      {
        "contributor": "zhangsan",
        "project_id": "account",
        "referenced_at": "2026-08-15T10:42:54Z",
        "revision": 1,
        "used_in": "generation",
        "workflow_id": "20260815-183253-8b028e7e"
      },
      {
        "contributor": "zhangsan",
        "project_id": "accounting",
        "referenced_at": "2026-08-16T05:11:03Z",
        "revision": 1,
        "used_in": "generation",
        "workflow_id": "accounting-20260816-105748-2caa7bfa"
      }
    ],
    "validations": []
  },
  "id": "TK-GDL-011",
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
    "task:20260722-201541-0c813afa",
    "commit:f26a945cd8ff1905aeae58c691efb14891e682d8",
    "validation:1",
    "validation:2"
  ],
  "tags": [
    "frontend",
    "vue",
    "filter-count",
    "input-normalization",
    "derived-state",
    "component-testing"
  ],
  "title": "按有效输入语义派生筛选条件计数",
  "type": "guideline"
}
```

# 按有效输入语义派生筛选条件计数

## 适用范围

适用于 Vue 等响应式前端中需要展示已启用筛选条件数量的列表或搜索组件。

## 问题

直接按控件数量或简单真值统计，容易把仅含空白的文本误判为有效条件，也可能导致清空或重置后仍显示计数提示；若另建独立计数状态，还会产生与真实筛选状态不同步的问题。

## 处理方式

从各筛选字段的当前值派生计数，为每个字段明确有效性规则，文本类输入先去除首尾空白再判断；仅在计数大于零时渲染提示，并让重置操作通过清空原筛选状态自然归零。组件测试应覆盖任意组合、全部启用、空白文本、无条件和重置，并回归既有请求与交互行为。

## 结果

提示数量始终反映实际有效筛选条件，空白输入与重置状态处理一致，同时避免计数逻辑干扰筛选请求及其他既有功能。

## 分层依据

筛选状态派生、输入规范化、条件渲染和组件回归测试是可跨项目及前端业务复用的技术实践。
