```knowledge-metadata
{
  "applicability": {
    "path_globs": [],
    "project_ids": [
      "accounting"
    ],
    "stages": [
      "generation",
      "spec_evaluation",
      "architecture_evaluation"
    ],
    "technologies": []
  },
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
      },
      {
        "contributor": "zhangsan",
        "project_id": "accounting",
        "referenced_at": "2026-07-20T05:10:25Z",
        "revision": 4,
        "used_in": "stage_b_real_rule_validation",
        "workflow_id": "stage-b-real-rule-20260720-tk-gdl-004"
      }
    ],
    "validations": [
      {
        "contributor": "zhangsan",
        "project_id": "accounting",
        "result": "passed",
        "revision": 4,
        "source": "Loop-Engineering: pytest targeted delivery approval/diff/subject tests; 3 passed on 2026-07-20",
        "validated_at": "2026-07-20T05:10:25Z",
        "workflow_id": "stage-b-real-rule-20260720-tk-gdl-004"
      }
    ]
  },
  "id": "TK-GDL-004",
  "layer": "layer1",
  "maturity": "verified",
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
  "revision": 4,
  "rule_owner": "zhangsan",
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
  "updated_at": "2026-07-20T05:09:18Z",
  "updated_by": "zhangsan"
}
```

# 将代码变更审批绑定到精确的 Diff 哈希和提交主题

## 适用范围

适用于 Accounting 项目中会创建真实 Git 提交的自动化、队列交付或编排工作流。

## 约束

提交前必须让人工审批同时绑定精确的 cumulative Diff SHA-256 和预期的单行提交主题；任一值发生变化时，原审批立即失效，必须重新审查，交付器不得继续提交。

## 反例

只记录“已同意”而不保存 Diff 哈希，或审批后改变提交主题仍复用旧审批，均不满足本规则。仅用于查看且不会创建提交的任务不由本规则阻断。

## 验证方法

运行交付测试，至少覆盖审批内容与实际暂存 Diff 一致时成功、审批后内容被篡改时拒绝，以及最终提交主题与审批主题一致。

## 维护责任

维护人 `zhangsan` 负责在交付模型、Diff 计算或 review schema 变化后复核本规则。

## 结果

最终提交在内容和语义上都与人工审查过的产物保持一致，并可通过哈希和提交主题追溯。

## 分层依据

该规则源于 Accounting 的真实交付流程；当前先明确绑定 Accounting 项目，后续只有经过其他项目独立验证后才扩大适用范围。
