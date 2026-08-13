```knowledge-metadata
{
  "archive_idempotency_key": "56c0efcbc162eadcc2e3dfee7454e72fb6d4f8dfa93add8bdf7235e5423e3ee5",
  "conflict_status": "none",
  "created_at": "2026-08-13T04:25:27Z",
  "evidence": {
    "contributors": [
      "orchestrator"
    ],
    "references": [],
    "validations": []
  },
  "id": "TK-PTF-003",
  "layer": "layer1",
  "maturity": "draft",
  "project_id": "read-notes",
  "promotion": {
    "candidate": false,
    "previous_layers": [],
    "target_layer": null,
    "target_path": null
  },
  "revision": 1,
  "scope": "team",
  "source_references": [
    "task:20260813-121910-760917a7",
    "validation:1",
    "commit:65ad076915b9fd0bb354bedf40f0dda1690611b2"
  ],
  "tags": [
    "test-evidence",
    "acceptance",
    "verification",
    "ci"
  ],
  "title": "新增测试代码不等于测试与构建已经通过",
  "type": "pitfall"
}
```

# 新增测试代码不等于测试与构建已经通过

## 适用范围

适用于要求回归测试、命令行验收和交付审计的软件变更。

## 问题

测试文件和用例的存在只能证明覆盖意图，不能证明测试实际执行成功，也不能排除既有测试失败或运行命令错误。

## 处理方式

归档前实际执行验收命令和测试命令，并保存成功结果，将运行证据与对应提交关联；缺少执行证据时标记为待确认。

## 结果

验收结论具有可核查的运行证据，避免把测试覆盖误判为测试成功。

## 分层依据

区分测试代码、实际执行结果与交付结论适用于不同技术栈和项目的验证流程，属于跨项目通用技术知识。
