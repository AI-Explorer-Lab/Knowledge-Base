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
        "referenced_at": "2026-07-19T13:48:39Z",
        "revision": 3,
        "used_in": "generation",
        "workflow_id": "20260719-213209-46bf6a8b"
      }
    ],
    "validations": []
  },
  "id": "TK-GDL-004",
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
        "from_id": "PJ-GDL-67E08058975F",
        "from_path": "docs/knowledge/guidelines/PJ-GDL-67E08058975F.md",
        "reason": "修正 Archiver 自动归档的知识层级和非标准哈希编号",
        "to": "layer1",
        "to_id": "TK-GDL-004",
        "to_path": "tech-wiki/guidelines/TK-GDL-004.md"
      }
    ],
    "target_layer": null,
    "target_path": null
  },
  "revision": 3,
  "scope": "team",
  "source_references": [
    "task:20260719-000039-922e51b2",
    "commit:24524f8cd94a4b1ad28fe47941398bbfd44bcb8d",
    "validation:1"
  ],
  "tags": [
    "approval",
    "diff-hash",
    "commit-subject",
    "integrity",
    "git"
  ],
  "title": "将代码变更审批绑定到精确的 Diff 哈希和提交主题",
  "type": "guideline",
  "updated_at": "2026-07-18T16:39:46Z",
  "updated_by": "zhangsan"
}
```

# 将代码变更审批绑定到精确的 Diff 哈希和提交主题

## 适用范围

会创建真实 Git 提交的自动化或编排工作流

## 问题

笼统的审批可能在变更后失效，或被用于审查人未授权的代码内容和提交元数据。

## 处理方式

提交前必须让审批同时绑定精确的 Diff SHA-256 和预期的单行提交主题；任一值发生变化时，原审批立即失效并需要重新审查。

## 结果

最终提交在内容和语义上都与人工审查过的产物保持一致，并且可以通过哈希和提交主题追溯。

## 分层依据

该规则属于可被不同项目复用的通用技术治理知识，因此归入 Layer 1。
