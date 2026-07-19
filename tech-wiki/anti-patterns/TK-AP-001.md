```knowledge-metadata
{
  "conflict_status": "none",
  "created_at": "2026-07-14T04:48:31Z",
  "evidence": {
    "contributors": [
      "zhangsan"
    ],
    "references": [
      {
        "contributor": "zhangsan",
        "project_id": "accounting",
        "referenced_at": "2026-07-18T16:06:33Z",
        "revision": 1,
        "used_in": "generation",
        "workflow_id": "20260719-000039-922e51b2"
      },
      {
        "contributor": "zhangsan",
        "project_id": "accounting",
        "referenced_at": "2026-07-19T03:27:52Z",
        "revision": 1,
        "used_in": "generation",
        "workflow_id": "20260719-110212-66531cfe"
      }
    ],
    "validations": []
  },
  "id": "TK-AP-001",
  "layer": "layer1",
  "maturity": "draft",
  "promotion": {
    "candidate": false,
    "previous_layers": [],
    "target_layer": null,
    "target_path": null
  },
  "scope": "team",
  "source_references": [
    "设计前端的经验总结"
  ],
  "tags": [
    "web",
    "frontend",
    "ai",
    "design"
  ],
  "title": "编辑框不要设计为右下角手动拖拽，改为高度随内容增减",
  "type": "guideline"
}
```

# 编辑框不要设计为右下角手动拖拽，改为高度随内容增减

## 反模式摘要

编辑框为右下角手动拖拽，应改为编辑框高度随内容增减

## 识别信号与危害

- 识别信号：文本框右下角有可以拖住的按钮
- 危害：当文字过长，文本框设计过窄时，文字无法完整显示

## 产生原因

AI自动生成的方案，没有给它限制

## 推荐替代方案

编辑框改为高度随内容增减

---

以下内容请继续按照所选知识类型填写。

## 适用场景

AI设计前端时

## 推荐做法

编辑框高度随内容增减

## 禁止做法
禁止设计拖拽式的文本框

## 检查方式

AI自己检察
