```knowledge-metadata
{
  "conflict_status": "none",
  "created_at": "2026-07-13T08:28:19Z",
  "evidence": {
    "contributors": [
      "zhangsan"
    ],
    "references": [
      {
        "contributor": "zhangsan",
        "project_id": "accounting",
        "referenced_at": "2026-07-18T16:06:31Z",
        "revision": 1,
        "used_in": "generation",
        "workflow_id": "20260719-000039-922e51b2"
      },
      {
        "contributor": "zhangsan",
        "project_id": "accounting",
        "referenced_at": "2026-07-19T03:27:50Z",
        "revision": 1,
        "used_in": "generation",
        "workflow_id": "20260719-110212-66531cfe"
      },
      {
        "contributor": "zhangsan",
        "project_id": "accounting",
        "referenced_at": "2026-07-19T10:17:56Z",
        "revision": 1,
        "used_in": "generation",
        "workflow_id": "20260719-173617-0d8e6e51"
      },
      {
        "contributor": "zhangsan",
        "project_id": "accounting",
        "referenced_at": "2026-07-19T13:48:41Z",
        "revision": 1,
        "used_in": "generation",
        "workflow_id": "20260719-213209-46bf6a8b"
      }
    ],
    "validations": []
  },
  "id": "PK-ZS-GDL-001",
  "layer": "layer0p",
  "maturity": "draft",
  "owner_id": "zhangsan",
  "promotion": {
    "candidate": false,
    "previous_layers": [],
    "target_layer": null,
    "target_path": null
  },
  "scope": "personal",
  "source_references": [
    "zhangsan 的本地调试复盘"
  ],
  "tags": [
    "debug",
    "api",
    "port"
  ],
  "title": "调试 API 前先检查 8000 端口",
  "type": "guideline"
}
```

# 调试 API 前先检查 8000 端口

调试本地 API 前，先检查 8000 端口是否已被占用，避免把端口冲突误判为应用启动失败。
