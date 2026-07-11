---
schema_version: 1
id: TK-GDL-001
title: 消息消费者必须保证业务幂等
type: guideline
scope: tech
domain: messaging
maturity: verified
status: active
risk_level: medium
owner: middleware-team
maintainers: [backend-team]
created_at: 2026-01-10
updated_at: 2026-06-18
applicable_phases: [ARCHITECT, IMPLEMENT, BUILD_VERIFY]
applicable_conditions: [消费端可能收到重复消息, 消费操作会改变业务状态]
not_applicable_conditions: [消费操作天然无副作用]
tags: [message-queue, idempotency]
source_references: [{type: pull_request, ref: order-service#182}]
supersedes: []
superseded_by: null
polarity: recommend
---
# 消息消费者必须保证业务幂等
## 结论
会改变业务状态的消息消费者必须使用业务幂等键防止重复执行。
## 背景与问题
消息系统通常只保证至少投递一次，重复消息可能造成重复扣款或状态推进。
## 适用条件
消息可能重复投递且处理存在副作用。
## 不适用条件
只读操作或底层已经提供可证明的严格去重保证。
## 详细说明
幂等判断必须与业务写入处于同一事务边界，不能只依赖进程内缓存。
## 验证方式
重复投递相同业务键并确认业务状态只变化一次。
## 来源
order-service#182。
## 具体行为
为每个业务操作定义稳定幂等键并持久化处理结果。
## 预期收益
避免重复投递造成重复业务副作用。
## 例外情况
天然无副作用的消费者可以不增加持久化幂等记录。
