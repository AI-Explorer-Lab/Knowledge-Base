```knowledge-metadata
{
  "archive_idempotency_key": "5b63d6e77f505abb39cfcbeef372f1a4b3423aa6c01d69f1264bc9483f540247",
  "conflict_status": "none",
  "created_at": "2026-08-15T10:42:52Z",
  "evidence": {
    "contributors": [
      "orchestrator"
    ],
    "references": [],
    "validations": []
  },
  "id": "TK-PTF-004",
  "layer": "layer1",
  "maturity": "draft",
  "project_id": "account",
  "promotion": {
    "candidate": false,
    "previous_layers": [],
    "target_layer": null,
    "target_path": null
  },
  "revision": 1,
  "scope": "team",
  "source_references": [
    "task:20260815-183253-8b028e7e",
    "validation:1",
    "validation:2",
    "validation:3"
  ],
  "tags": [
    "validation",
    "npm",
    "dependency-management",
    "typescript",
    "vite",
    "vitest"
  ],
  "title": "不要在依赖未安装时把验证失败误判为代码缺陷",
  "type": "pitfall"
}
```

# 不要在依赖未安装时把验证失败误判为代码缺陷

## 适用范围

适用于使用 npm scripts、TypeScript、Vite 或 Vitest 的前端项目自动化验证。

## 问题

测试、类型检查或构建命令可能因 vitest、tsc 或 vite 不存在而以 exit code 127 失败；若不区分环境缺失与代码失败，会误判实现质量并浪费修复时间。

## 处理方式

执行验证前确认依赖已安装且命令可解析；发现 exit code 127 或类似缺失命令错误时，先修复验证环境并重新运行完整验证，再判断代码是否存在问题。记录每轮验证的命令、环境原因和最终结果。

## 结果

能够区分工具链故障与实现缺陷，最终结论基于真实的测试、类型检查和构建结果。

## 分层依据

识别命令缺失、修复依赖环境并重新验证是跨项目通用的工程实践，不依赖当前 accounting 的业务领域。
