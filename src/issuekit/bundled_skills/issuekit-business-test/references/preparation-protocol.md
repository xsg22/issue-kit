# 测试数据初始化协议

## 执行顺序

```text
生成 test_run_id
  -> 确认需求基线
  -> 确认实现基线
  -> 确认环境/版本/权限
  -> 生成 Fixture 计划
  -> 校验主体没有被其他 run 占用
  -> 保存 before 快照
  -> 执行初始化动作
  -> 按目标值回读验证
  -> 标记 Fixture VERIFIED
  -> 冻结状态并执行 Case
```

## Fixture 计划结构

```yaml
fixture_batch:
  batch_id: ""
  test_run_id: ""
  requirement_source:
    document: ""
    version: ""
    commit_sha: ""
  technical_design_source:
    status: "AVAILABLE | INCOMPLETE | NOT_AVAILABLE"
    document: ""
    version: ""
    commit_sha: ""
  implementation_source:
    repository: ""
    type: "branch | commit | deployed_version"
    branch: ""
    commit_sha: ""
    deployed_version: ""
  environment: "local | pre | prod"
  code_source: "branch/commit/deployed_version"
  database_profile: ""
  write_authorization: ""
  status: "PLANNED | VERIFIED | APPLIED | FAILED"
  fixtures:
    - fixture_id: ""
      case_ids: []
      actor:
        id: ""
        tenant_id: ""
        lease_id: ""
      target_state: {}
      setup:
        mode: "business_api | controlled_database_write | none"
        operations: []
        expected_affected_rows: 0
      verification:
        query: ""
        expected: {}
      reset:
        required: true
        strategy: ""
      cleanup:
        allowed: false
        strategy: ""
      parallel_safe: false
```

## 状态要求

- `PLANNED`：计划已生成，但未执行写入；
- `VERIFIED`：目标状态已回读确认，可以执行 Case；
- `APPLIED`：初始化动作已执行，但仍需回读验证；
- `FAILED`：影响行数、字段值、主体占用或回滚不符合预期，停止该 Fixture 及其关联 Case。

只有 `VERIFIED` 才能进入业务执行。

## 需求和实现基线

初始化至少要同时记录两类基线：

| 基线 | 必须确认的内容 |
|---|---|
| 需求基线 | 需求文档路径、版本/commit、验收标准、测试 Case 来源 |
| 技术方案材料 | 存在时用于理解设计意图；缺失或不完整时记录缺口，不阻塞初始化 |
| 实现基线 | 仓库、分支或 commit、部署版本、实际服务地址 |

本地测试时，代码分支/commit必须和启动服务的代码一致；Pre/Prod 测试时，部署 commit 必须能和实际服务版本对应。需求基线必须完整；技术方案可以缺失，但必须由真实代码、配置、数据库模型和运行行为补齐。只有需求和实现基线都确认，才能初始化数据。

## 主体租用

执行前必须确认测试主体没有被其他测试批次使用。能实现时写入短期 `lease_id` 或等价占用标识，并设置过期时间；不能实现时至少用独立主体和唯一测试前缀隔离，并在报告中记录并发风险。

## 多 Case 复用

共享 Fixture 只能共享初始化定义，不能共享已被消费的运行态。若 Case 会改变目标状态，必须在下一个 Case 前复位，或者分配独立主体。复位后必须重新回读目标值，不能只执行更新动作而不验证。

## 失败处理

出现以下任一情况立即停止后续业务操作：

- 环境或代码版本未确认；
- 需求文档或验收标准未确认；
- 实现分支、commit 或部署版本未确认；
- 需求基线和实现基线不匹配；
- 没有当前写入授权；
- 主体已被占用；
- before 快照失败；
- 影响行数不符合预期；
- 初始化后回读值不等于目标值；
- 无法确认是否污染了其他测试数据。

这些情况标记为 `DATA_PREPARATION_BLOCKED` 或 `DATA_PREPARATION_FAILED`，不能归因于被测业务。
