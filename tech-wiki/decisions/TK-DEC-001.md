---
schema_version: 1
id: TK-DEC-001
title: Catalog 必须由源文件确定性生成
type: decision
scope: tech
domain: knowledge-governance
maturity: draft
status: active
risk_level: low
owner: knowledge-core-team
created_at: 2026-07-11
updated_at: 2026-07-11
applicable_phases: [IMPLEMENT, BUILD_VERIFY]
applicable_conditions: [生成知识目录和治理报告]
not_applicable_conditions: [临时本地搜索结果]
tags: [catalog, deterministic-build]
source_references: [{type: specification, ref: plan/enterprise-knowledge-base-spec.md}]
supersedes: []
superseded_by: null
---
# Catalog 必须由源文件确定性生成
## 结论
Catalog 不接受人工编辑，相同输入必须生成完全相同的输出。
## 背景与问题
人工目录容易与知识事实产生漂移。
## 适用条件
所有正式 Catalog 和治理报告。
## 不适用条件
一次性的本地查询展示。
## 详细说明
生成器必须使用稳定排序且不得写入当前时间等非确定数据。
## 验证方式
连续生成两次并比较文件摘要。
## 来源
企业级知识库治理规格。
## 决策背景
知识库需要同时服务人和 Agent。
## 约束条件
Git 文件是唯一可迁移的事实载体。
## 候选方案
人工目录、数据库目录和源文件自动生成目录。
## 最终选择
从源文件和证据自动生成目录。
## 选择理由
该方案可审计、可重复且不绑定平台。
## 代价和后果
所有目录变更都需要运行生成工具。
## 重新决策条件
当 Git 不再作为知识事实来源时重新评估。
