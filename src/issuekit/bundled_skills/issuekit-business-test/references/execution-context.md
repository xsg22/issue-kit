# 测试执行上下文

## 环境与代码来源

测试用例可以环境无关，但执行记录必须明确：

```yaml
test_target:
  environment: local | pre | prod
  code_source:
    type: branch | commit | deployed_version
    repository: ""
    branch: ""
    commit_sha: ""
    deployed_version: ""
  service:
    base_url: ""
  database:
    profile: ""
    schema: ""
  logs:
    source: ""
  actor:
    uid: ""
    client: ""
    app_version: ""
```

环境、服务地址和代码来源不得由 Agent 自行推断。缺失时停止真实执行，设计模式仍可继续生成用例。

工作区分支不能代表远程服务部署版本。执行报告必须分别记录：

- `workspace_branch`：本地查看的代码分支；
- `workspace_commit`：本地代码 commit；
- `deployed_version`：远程环境实际部署版本；
- `deployed_commit`：远程部署对应 commit；
- `actual_base_url`：本次请求真正访问的地址。

请求环境和实际环境不一致时，结果为 `ENVIRONMENT_MISMATCH`，不得继续汇总为目标环境的通过。

## 能力状态

```yaml
capabilities:
  api_read: AVAILABLE
  api_write: AVAILABLE
  database_read: PARTIAL
  database_write: UNAVAILABLE
  log_read: UNKNOWN
  async_status_read: AVAILABLE
```

能力不足时先生成限制，不要直接把所有用例标记为阻塞。只有无法构造或执行核心动作时才是 `BLOCKED`。

能力检查至少覆盖：

| 能力 | 影响 |
|---|---|
| API 读取 | 能否查询当前业务状态 |
| API 写入 | 能否执行真实业务动作 |
| 数据库读取 | 能否验证业务实体、可变资源、任务和审计记录变化 |
| 数据库写入 | 能否初始化临界余额或状态 |
| 日志读取 | 能否验证异步链路和失败原因 |
| 异步状态读取 | 能否判断最终收口 |
| 真实用户认证 | 能否使用真实 UID 操作 |
| 本地服务控制 | 能否测试指定工作区代码 |

非核心能力缺失时允许执行并降级结果；核心动作缺失时才阻断。

## 测试运行记录

每轮执行使用唯一 `test_run_id`，关联环境、代码版本、账号、请求、响应、业务 ID、快照、日志和最终结果。

推荐记录：

```yaml
test_run_id: "20260921-CASE-001-001"
case_id: "CASE-001"
requested_environment: "pre"
actual_environment: "pre"
actor_uid: ""
request_ids: []
trace_ids: []
business_ids: []
database_snapshots: []
log_queries: []
async_waits: []
result: "PASS_WITH_WARNINGS"
limitations: []
```
