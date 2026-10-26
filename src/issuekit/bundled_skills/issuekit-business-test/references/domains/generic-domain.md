# 通用业务领域示例

本文件只展示抽象结构，不包含任何项目的真实业务名称、字段、状态、金额、额度或接口路径。

```yaml
domain: example_domain
entities:
  - actor
  - business_entity
  - mutable_resource
  - task
rules:
  - id: resource-threshold
    when: resource_a.available < requested_amount
    expect: reject_without_side_effect
```

项目的真实业务规则、字段、状态和接口应放在项目自己的 `.issuekit/testing/business-domains/` 目录，由项目知识和有效需求来源（任务、已确认讨论或文档）提供。
