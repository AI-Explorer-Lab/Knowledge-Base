```knowledge-metadata
{
  "conflict_status": "none",
  "created_at": "2026-07-18T16:06:29Z",
  "evidence": {
    "contributors": [
      "orchestrator",
      "zhangsan"
    ],
    "references": [
      {
        "contributor": "zhangsan",
        "project_id": "accounting",
        "referenced_at": "2026-07-19T03:27:50Z",
        "revision": 3,
        "used_in": "generation",
        "workflow_id": "20260719-110212-66531cfe"
      },
      {
        "contributor": "zhangsan",
        "project_id": "accounting",
        "referenced_at": "2026-07-19T10:17:59Z",
        "revision": 3,
        "used_in": "generation",
        "workflow_id": "20260719-173617-0d8e6e51"
      },
      {
        "contributor": "zhangsan",
        "project_id": "accounting",
        "referenced_at": "2026-07-19T13:48:44Z",
        "revision": 3,
        "used_in": "generation",
        "workflow_id": "20260719-213209-46bf6a8b"
      }
    ],
    "validations": []
  },
  "id": "TK-GDL-005",
  "layer": "layer1",
  "maturity": "draft",
  "project_id": "accounting",
  "promotion": {
    "candidate": false,
    "previous_layers": [
      {
        "actor": "zhangsan",
        "changed_at": "2026-07-18T16:39:46Z",
        "from": "layer3",
        "from_id": "PJ-GDL-AB7584B73A10",
        "from_path": "docs/knowledge/guidelines/PJ-GDL-AB7584B73A10.md",
        "reason": "修正 Archiver 自动归档的知识层级和非标准哈希编号",
        "to": "layer1",
        "to_id": "TK-GDL-005",
        "to_path": "tech-wiki/guidelines/TK-GDL-005.md"
      }
    ],
    "target_layer": null,
    "target_path": null
  },
  "revision": 3,
  "scope": "team",
  "source_references": [
    "task:20260719-000039-922e51b2",
    "validation:1"
  ],
  "tags": [
    "branch-isolation",
    "scope-control",
    "no-push",
    "no-merge",
    "canary"
  ],
  "title": "在独立分支中运行真实状态 Canary，禁止合并和推送",
  "type": "guideline",
  "updated_at": "2026-07-18T16:39:46Z",
  "updated_by": "zhangsan"
}
```

# 在独立分支中运行真实状态 Canary，禁止合并和推送

## 适用范围

需要实际操作仓库 Git 状态的 Harness 验证

## 问题

验证用 Canary 可能意外影响共享历史，或把与验收无关的仓库变更一并带入结果。

## 处理方式

每次 Canary 都应运行在独立的 codex/<task-id> 分支，严格限制为已声明的文件级变更范围，并在整个验证流程中禁止 merge 和 push。

## 结果

系统可以验证真实提交行为，同时不会影响共享分支、远端仓库和无关文件。

## 分层依据

该规则适用于不同项目中的真实仓库验证流程，属于跨项目通用技术知识，因此归入 Layer 1。
