```knowledge-metadata
{
  "archive_idempotency_key": "09ab7f24853cb54d43a2b4dfbc37bcf7a0008590e659e6d7d085a9b818305a91",
  "conflict_status": "none",
  "created_at": "2026-07-19T03:27:48Z",
  "evidence": {
    "contributors": [
      "orchestrator"
    ],
    "references": [],
    "validations": []
  },
  "id": "TK-PTF-001",
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
    "task:20260719-110212-66531cfe",
    "commit:039e9ec40a560cda1e86a50c5a62804ef7201e5e",
    "validation:1"
  ],
  "tags": [
    "test-evidence",
    "build-verification",
    "acceptance",
    "ci"
  ],
  "title": "新增测试代码不等于测试与构建已经通过",
  "type": "pitfall"
}
```

# 新增测试代码不等于测试与构建已经通过

## 适用范围

适用于验收条件要求回归测试和生产构建成功的软件变更。

## 问题

测试文件及用例的存在只能证明覆盖意图，不能证明它们已被执行，也不能排除既有测试失败或生产构建错误。

## 处理方式

归档验收前应保存后端测试、前端测试和生产构建命令的实际成功结果，并将执行结果与对应提交关联；缺少运行证据时应标记为待确认，而不是宣称全部通过。

## 结果

验收结论具有可核查的运行证据，避免把测试覆盖误当成测试成功。

## 分层依据

测试证据与验收结论的区分适用于不同技术栈和项目的交付流程，属于跨项目通用技术知识。
