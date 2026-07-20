```knowledge-metadata
{
  "archive_idempotency_key": "6696756e94e2d7d0f67735d3cbdd00ff72c798d0c78d1b1d2fb2919319b26d3e",
  "conflict_status": "none",
  "created_at": "2026-07-19T13:48:20Z",
  "evidence": {
    "contributors": [
      "orchestrator"
    ],
    "references": [],
    "validations": []
  },
  "id": "TK-GDL-010",
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
    "task:20260719-213209-46bf6a8b",
    "commit:3944e412666cb12c6b1e78aed6be795ed5a840f8",
    "validation:1"
  ],
  "tags": [
    "destructive-action",
    "confirmation",
    "early-return",
    "side-effects",
    "component-testing"
  ],
  "title": "将破坏性操作的确认设计为既有流程的前置守卫",
  "type": "guideline"
}
```

# 将破坏性操作的确认设计为既有流程的前置守卫

## 适用范围

适用于前端列表、详情页等通过异步接口执行删除或其他不可逆操作的交互。

## 问题

如果确认逻辑没有位于副作用之前，取消后仍可能调用接口、刷新数据或显示成功提示；如果确认分支重新实现删除流程，又容易传错实体 ID，或破坏既有的成功处理、分页回退和异常处理。

## 处理方式

在任何副作用发生前展示包含可识别对象上下文的确认信息；用户取消时立即返回，用户确认时将原实体 ID 交给既有执行路径而不复制后续逻辑。组件测试应分别模拟取消和确认，取消分支断言接口、刷新及成功提示均未发生，确认分支断言 ID 正确并回归既有后续行为。

## 结果

降低误操作风险，保证取消路径无副作用，同时让确认路径继续复用并保留已有的删除后处理与错误处理。

## 分层依据

确认守卫、无副作用取消和复用既有异步流程的做法适用于不同前端框架与业务项目，属于跨项目可复用的技术知识。
