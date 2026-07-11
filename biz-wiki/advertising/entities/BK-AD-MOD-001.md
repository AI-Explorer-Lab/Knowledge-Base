---
schema_version: 1
id: BK-AD-MOD-001
title: 广告活动是预算与投放规则的聚合根
type: model
scope: biz
domain: advertising
maturity: draft
status: active
risk_level: medium
owner: advertising-product
created_at: 2026-07-11
updated_at: 2026-07-11
applicable_phases: [ARCHITECT, IMPLEMENT]
applicable_conditions: [设计广告活动领域模型]
not_applicable_conditions: [仅展示外部广告平台只读数据]
tags: [campaign, aggregate]
source_references: [{type: business_confirmation, ref: AD-DOMAIN-2026-01}]
supersedes: []
superseded_by: null
---
# 广告活动是预算与投放规则的聚合根
## 结论
预算和投放规则的业务一致性由广告活动聚合统一维护。
## 背景与问题
分散修改预算和规则会产生不可投放的中间状态。
## 适用条件
平台内创建和修改广告活动。
## 不适用条件
只读同步外部平台数据。
## 详细说明
外部调用应通过广告活动暴露的业务操作修改内部对象。
## 验证方式
通过业务不变量测试和产品负责人评审确认。
## 来源
AD-DOMAIN-2026-01。
## 实体或概念定义
广告活动表示围绕共同目标组织的预算与投放配置集合。
## 属性
活动 ID、状态、预算、时间范围和投放规则。
## 关系
广告活动包含投放单元并引用目标受众。
## 不变量
启用状态下预算必须为正且投放时间必须有效。
## 权威来源
广告产品负责人确认的领域定义 AD-DOMAIN-2026-01。
