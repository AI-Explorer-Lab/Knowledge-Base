```knowledge-metadata
{
  "archive_idempotency_key": "5fb5c947505d53efd432f3db58de058c40c0e2241ea24586edf76fca20597295",
  "conflict_status": "none",
  "created_at": "2026-07-25T07:32:08Z",
  "evidence": {
    "contributors": [
      "orchestrator",
      "zhangsan",
      "local-user"
    ],
    "references": [
      {
        "contributor": "zhangsan",
        "project_id": "accounting",
        "referenced_at": "2026-08-13T02:40:40Z",
        "revision": 1,
        "used_in": "generation",
        "workflow_id": "20260813-094134-9cfef825"
      },
      {
        "contributor": "local-user",
        "project_id": "read-notes",
        "referenced_at": "2026-08-13T04:25:28Z",
        "revision": 1,
        "used_in": "generation",
        "workflow_id": "20260813-121910-760917a7"
      },
      {
        "contributor": "zhangsan",
        "project_id": "account",
        "referenced_at": "2026-08-15T10:42:55Z",
        "revision": 1,
        "used_in": "generation",
        "workflow_id": "20260815-183253-8b028e7e"
      }
    ],
    "validations": []
  },
  "id": "TK-PTF-002",
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
    "validation:1"
  ],
  "tags": [
    "shell-quoting",
    "variable-expansion",
    "data-integrity",
    "test-data",
    "ci"
  ],
  "title": "避免 Shell 插值破坏含美元符号的测试数据",
  "type": "pitfall"
}
```

# 避免 Shell 插值破坏含美元符号的测试数据

## 适用范围

适用于通过 Shell 命令、脚本、CI 参数或 heredoc 传递含美元符号字符串的任务描述、测试期望值和结构化数据。

## 问题

未正确引用的 `$0`、`$1` 等内容会在到达程序前被 Shell 展开，使美元金额示例变成 Shell 路径或空缺字符串，造成需求与验证数据失真。

## 处理方式

使用单引号、禁用插值的 heredoc 或可靠的结构化序列化传递含 `$` 的文本；生成后检查关键期望值，并在需要审计时校验输入摘要或保存原始载荷。

## 结果

货币字符串和其他含美元符号的数据能够原样穿过自动化链路，避免因预处理展开产生隐蔽的测试或需求错误。

## 分层依据

Shell 引用和数据传输完整性问题与具体项目无关，可复用于脚本、CI 和测试生成流程，属于跨项目通用技术知识。
