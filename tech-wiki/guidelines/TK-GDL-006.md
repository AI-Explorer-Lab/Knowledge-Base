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
        "referenced_at": "2026-07-19T03:27:52Z",
        "revision": 3,
        "used_in": "generation",
        "workflow_id": "20260719-110212-66531cfe"
      }
    ],
    "validations": []
  },
  "id": "TK-GDL-006",
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
        "from_id": "PJ-GDL-95F3672ED87E",
        "from_path": "docs/knowledge/guidelines/PJ-GDL-95F3672ED87E.md",
        "reason": "修正 Archiver 自动归档的知识层级和非标准哈希编号",
        "to": "layer1",
        "to_id": "TK-GDL-006",
        "to_path": "tech-wiki/guidelines/TK-GDL-006.md"
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
    "archival",
    "commit-gating",
    "auditability",
    "evidence",
    "workflow"
  ],
  "title": "仅在提交成功后归档仓库变更证据",
  "type": "guideline",
  "updated_at": "2026-07-18T16:39:46Z",
  "updated_by": "zhangsan"
}
```

# 仅在提交成功后归档仓库变更证据

## 适用范围

需要归档验证结果和提交证据的编排流水线

## 问题

如果在提交成功前归档，记录可能会错误地表示一个从未真正存在过的持久化仓库状态。

## 处理方式

归档必须以已确认的提交成功为前置条件；提交完成后，再把提交身份与已验证的任务证据一起记录。

## 结果

归档证据始终对应真实存在的提交状态，避免产生虚假的完成记录。

## 分层依据

该规则可以被不同项目的提交与归档流水线复用，属于通用技术知识，因此归入 Layer 1。
