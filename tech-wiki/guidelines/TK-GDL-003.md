```knowledge-metadata
{
  "conflict_status": "none",
  "created_at": "2026-07-15T14:31:23Z",
  "evidence": {
    "contributors": [
      "zhangsan"
    ],
    "references": [
      {
        "contributor": "zhangsan",
        "project_id": "accounting",
        "referenced_at": "2026-07-18T16:06:34Z",
        "revision": 2,
        "used_in": "generation",
        "workflow_id": "20260719-000039-922e51b2"
      },
      {
        "contributor": "zhangsan",
        "project_id": "accounting",
        "referenced_at": "2026-07-19T03:27:49Z",
        "revision": 2,
        "used_in": "generation",
        "workflow_id": "20260719-110212-66531cfe"
      }
    ],
    "validations": []
  },
  "id": "TK-GDL-003",
  "layer": "layer1",
  "maturity": "draft",
  "promotion": {
    "candidate": false,
    "previous_layers": [],
    "target_layer": null,
    "target_path": null
  },
  "revision": 2,
  "scope": "team",
  "source_references": [
    "团队实战经验总结"
  ],
  "tags": [
    "frontend",
    "backend",
    "script"
  ],
  "technical_direction": "patterns",
  "title": "bash生成脚本一键运行前后端",
  "type": "guideline",
  "updated_at": "2026-07-17T04:54:54Z",
  "updated_by": "zhangsan"
}
```

# bash生成脚本一键运行前后端

## 模式摘要

生成bash脚本一键运行前后端，且端口号保持一致
## 复用条件

当一个项目里既设计里后端，又设计了前端的时候
## 收益与代价

通过bash脚本一键启动前后端，节省时间
