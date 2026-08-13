```knowledge-metadata
{
  "archive_idempotency_key": "1403620afc8370fc40415db6973c0a9e901fabecd3d67c9ea9838f779f44d374",
  "conflict_status": "none",
  "created_at": "2026-08-13T04:25:27Z",
  "evidence": {
    "contributors": [
      "orchestrator"
    ],
    "references": [],
    "validations": []
  },
  "id": "TK-GDL-013",
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
    "validation:1"
  ],
  "tags": [
    "cli",
    "persistence",
    "state-management",
    "boundary-testing"
  ],
  "title": "为命令行持久化功能同时验证写入、读取和空数据状态",
  "type": "guideline"
}
```

# 为命令行持久化功能同时验证写入、读取和空数据状态

## 适用范围

适用于使用文件或其他持久化介质保存状态的命令行工具。

## 问题

只验证写入或只验证有数据时的输出，无法发现读取链路、数据格式或空数据处理中的错误。

## 处理方式

分别执行新增数据、读取数据和无数据状态的验收；同时测试公开函数与命令行入口，并确认持久化文件保存了预期内容。

## 结果

能够覆盖持久化、读取输出和空状态处理，降低命令行功能表面通过但实际链路不完整的风险。

## 分层依据

对命令行状态管理进行写入、读取和边界状态验证的方法可复用于不同项目，属于跨项目通用技术知识，而非当前笔记项目专属规则。
