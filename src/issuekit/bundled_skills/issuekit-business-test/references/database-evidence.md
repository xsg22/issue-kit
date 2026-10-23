# 数据库准备与证据

## 四阶段快照

对有数据变化的 Case 至少保存：

1. `before`：执行前真实状态；
2. `prepared`：数据初始化后的状态；
3. `after_response`：接口返回后的同步状态；
4. `after_async`：异步任务最终收口状态。

## 数据准备记录

```yaml
preparation:
  operation_id: ""
  test_run_id: ""
  case_id: ""
  environment: ""
  actor_uid: ""
  data_profile: "isolated-default"
  preparation_mode: "business_api | controlled_database_write"
  plan_status: "PLANNED | APPLIED | VERIFIED | FAILED"
  changes:
    - table: ""
      where: ""
      before: {}
      after: {}
      affected_rows: 0
      verify_query: ""
      verify_result: {}
  rollback:
    available: false
    description: ""
  retained: false
```

优先使用业务接口准备数据。必须通过数据库写入时，先保存旧值，执行后回读并校验影响行数；不能对未知表或未知字段猜测写入。

## 准备阶段判定

```text
未绑定环境/账号/数据库
  -> DATA_PREPARATION_BLOCKED
已执行但未回读确认
  -> DATA_PREPARATION_UNVERIFIED
回读值与 Case 前置状态一致
  -> DATA_PREPARATION_VERIFIED
字段或影响行数不一致
  -> DATA_PREPARATION_FAILED
```

只有 `DATA_PREPARATION_VERIFIED` 才能进入真实业务操作。

## 断言

每项断言需包含查询条件、字段、旧值、预期新值和允许的最终一致性等待时间。没有数据库读权限时，不能声称业务实体、可变资源或审计记录已正确变化。
