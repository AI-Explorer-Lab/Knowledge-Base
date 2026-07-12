---
schema_version: 1
id: TM-GDL-001
title: 代码变更必须遵循项目既有风格并保持最小范围
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
applicable_phases: [IMPLEMENT, BUILD_VERIFY]
applicable_conditions: [团队成员或 Agent 修改已有代码库]
not_applicable_conditions: [独立实验且尚未形成共享代码库]
tags: [coding-standard, maintainability]
source_references: [{type: team_convention, ref: team-conventions/coding-standards.md}]
supersedes: []
superseded_by: null
polarity: recommend
---
# 代码变更必须遵循项目既有风格并保持最小范围

## 结论

修改已有代码时必须优先遵循项目现有结构、命名、格式化和测试约定，并把变更限制在任务需要的最小范围内。

## 背景与问题

无关重构和个人风格替换会扩大审查面、增加回归风险，并掩盖真正的功能变化。

## 适用条件

团队成员或 Agent 修改现有项目。

## 不适用条件

尚未建立团队约定的隔离实验。

## 详细说明

修改前应检查项目配置、相邻代码和现有测试。发现更大范围问题时应单独记录，不与当前任务混合提交。

## 验证方式

运行项目格式化、静态检查和与改动相关的测试，并确认差异中没有无关文件。

## 来源

团队工程协作约定。

## 具体行为

保留既有风格，优先小范围修改，并通过项目已有工具验证。

## 预期收益

降低审查成本和回归风险，使提交意图清晰可追溯。

## 例外情况

格式化或迁移任务可以进行机械性批量修改，但必须与功能改动分离。
