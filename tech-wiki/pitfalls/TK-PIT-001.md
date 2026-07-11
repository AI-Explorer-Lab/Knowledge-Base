---
schema_version: 1
id: TK-PIT-001
title: 不要把知识引用次数当作验证次数
type: pitfall
scope: tech
domain: knowledge-governance
maturity: draft
status: active
risk_level: medium
owner: knowledge-core-team
created_at: 2026-07-11
updated_at: 2026-07-11
applicable_phases: [ARCHITECT, ARCHIVE]
applicable_conditions: [评估知识成熟度]
not_applicable_conditions: [仅统计知识曝光量]
tags: [evidence, maturity]
source_references: [{type: specification, ref: plan/enterprise-knowledge-base-spec.md}]
supersedes: []
superseded_by: null
---
# 不要把知识引用次数当作验证次数
## 结论
引用只能表示知识被发现，不能证明采用后的结果正确。
## 背景与问题
按引用量晋级会强化已有热门知识并掩盖失败结果。
## 适用条件
成熟度计算和默认推荐排序。
## 不适用条件
仅分析目录使用情况时可以单独统计引用量。
## 详细说明
只有具备方法、结果和来源的成功验证才能提供正向晋级证据。
## 验证方式
检查晋级候选的依据中不包含单纯 referenced 事件。
## 来源
企业级知识库治理规格。
## 触发条件
用事件数量或查询热度直接计算成熟度。
## 问题现象
高曝光但未验证的知识被错误提升。
## 根本原因
混淆了发现、采用和结果验证。
## 复现方式
为 Draft 仅追加 referenced 事件并运行生命周期评估。
## 规避或修复方法
分别保存事件类型且只让有效 validated_success 提供正向证据。
## 修复验证
仅含引用事件的 Draft 不会产生晋级候选。
