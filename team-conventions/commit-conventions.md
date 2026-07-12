---
schema_version: 1
id: TM-GDL-002
title: Git 提交必须单一目的且说明可验证结果
type: guideline
scope: team
domain: engineering
maturity: draft
status: active
risk_level: low
owner: knowledge-core-team
maintainers: [knowledge-core-team]
created_at: 2026-07-12
updated_at: 2026-07-12
applicable_phases: [IMPLEMENT, BUILD_VERIFY, RELEASE]
applicable_conditions: [变更需要提交到团队 Git 仓库]
not_applicable_conditions: [仅在本地进行尚未准备提交的探索]
tags: [git, commit]
source_references: [{type: team_convention, ref: team-conventions/commit-conventions.md}]
supersedes: []
superseded_by: null
polarity: recommend
---
# Git 提交必须单一目的且说明可验证结果

## 结论

每个提交应服务一个清晰目的，提交信息说明做了什么，交付说明同时记录实际执行的验证。

## 背景与问题

混合多个目标的提交难以审查、回滚和追溯，缺少验证说明会让审核人无法判断交付风险。

## 适用条件

代码、配置或知识变更准备进入共享 Git 历史。

## 不适用条件

尚未提交的本地探索过程。

## 详细说明

功能、重构和机械格式化应尽量拆分。不得把秘密、个人本地配置或无关生成文件提交到仓库。

## 验证方式

提交前检查差异和状态，确认提交范围与信息一致，并记录测试结果。

## 来源

团队 Git 协作约定。

## 具体行为

提交前检查 `git diff`，使用明确的祈使式摘要，并保持一个提交一个目的。

## 预期收益

提高审查、回滚和问题定位效率。

## 例外情况

自动生成且必须与源文件同步的产物可以与源变更放在同一提交中。
