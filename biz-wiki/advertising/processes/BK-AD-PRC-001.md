---
schema_version: 1
id: BK-AD-PRC-001
title: 高预算广告活动发布必须经过双人复核
type: process
scope: biz
domain: advertising
maturity: draft
status: active
risk_level: high
owner: advertising-operations
created_at: 2026-07-11
updated_at: 2026-07-11
review_policy_override: {interval: 90d, reason: 高预算发布属于高风险业务操作}
applicable_phases: [BUILD_VERIFY, RELEASE]
applicable_conditions: [活动预算达到高预算阈值]
not_applicable_conditions: [沙箱和零消耗测试活动]
tags: [approval, high-budget]
source_references: [{type: process_document, ref: AD-OPS-2026-03}]
supersedes: []
superseded_by: null
---
# 高预算广告活动发布必须经过双人复核
## 结论
达到高预算阈值的广告活动必须由创建者之外的运营人员复核后发布。
## 背景与问题
配置错误可能在短时间内产生显著资金损失。
## 适用条件
正式环境且活动预算达到策略阈值。
## 不适用条件
不产生真实消耗的沙箱活动。
## 详细说明
复核人必须检查预算、时间、受众和素材状态并留下审批记录。
## 验证方式
抽查发布记录并确认创建人与复核人不同。
## 来源
运营流程 AD-OPS-2026-03。
## 参与角色
活动创建者、运营复核人和发布系统。
## 前置条件
活动配置完整且通过自动校验。
## 流程步骤
创建者提交、复核人检查、系统记录审批并执行发布。
## 状态转换
草稿进入待复核，通过后进入已发布，拒绝后返回草稿。
## 异常分支
复核超时或配置变化时撤销原审批并重新提交。
## 权威确认人
广告运营负责人。
