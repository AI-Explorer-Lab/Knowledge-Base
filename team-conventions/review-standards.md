---
schema_version: 1
id: TM-GDL-003
title: 代码审查必须优先检查正确性安全性和回归风险
type: guideline
scope: team
domain: engineering
maturity: draft
status: active
risk_level: medium
owner: knowledge-core-team
maintainers: [knowledge-core-team]
created_at: 2026-07-12
updated_at: 2026-07-12
applicable_phases: [ARCHITECT, IMPLEMENT, BUILD_VERIFY, RELEASE]
applicable_conditions: [共享仓库中的变更需要人工或 Agent 审查]
not_applicable_conditions: [没有形成可交付变更的本地探索]
tags: [review, quality-gate]
source_references: [{type: team_convention, ref: team-conventions/review-standards.md}]
supersedes: []
superseded_by: null
polarity: recommend
---
# 代码审查必须优先检查正确性安全性和回归风险

## 结论

审查应先发现会造成错误、安全问题、数据损坏或回归的缺陷，再处理可维护性和风格建议。

## 背景与问题

如果审查只关注格式和个人偏好，高影响缺陷可能被低价值讨论淹没。

## 适用条件

团队共享代码、配置和知识发生变更。

## 不适用条件

尚未形成交付物的个人探索。

## 详细说明

审查意见应给出具体证据、影响范围和可执行建议。纯偏好不得伪装成强制缺陷。

## 验证方式

确认高风险路径有测试或其他可追溯证据，并复核变更边界和失败处理。

## 来源

团队审查约定。

## 具体行为

按正确性、安全性、回归风险、可维护性和风格的顺序审查并标注严重程度。

## 预期收益

把审查时间集中在最可能影响用户和生产环境的问题上。

## 例外情况

专门的格式化变更可以主要检查确定性和影响范围。
