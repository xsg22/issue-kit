# 清理记录与查询

## 稳定位置

优先采用项目已有的清理历史位置；没有时使用规范项目/工作区根目录下的 `.issuekit/cleanup/`。多仓工作区可统一在该位置记录，但逐项标注所属仓库。无须创建 Issue 才能清理，也不把 Git 运维日志混作需求文档。

定位记录目录后在对话明确展示绝对路径。记录必须位于所有待清理目录之外，不放在临时 worktree、skill 包目录或 `/tmp`。规范根目录也在候选内时，改用用户指定的外部持久目录或同级清理记录目录。

```text
.issuekit/cleanup/
  index.md
  20261026T103000+0800-a1b2c3/
    plan.json
    events.jsonl
    result.md
```

- `run_id`：带时区的创建时间加随机后缀，避免同日覆盖；在进程重试时复用原 run，新的计划建立新 run。
- `plan.json`：执行前写入，含完整候选、保留项和判断证据。实际目标或动作变化时保留原计划，再新增修订与授权依据；不能静默替换已展示的清单。
- `events.jsonl`：逐动作追加，开始执行前写入 `started`，回读后写入最终状态。包括成功、失败、跳过及恢复信息，便于异常退出后重建已知状态。
- `result.md`：运行开始即建立 `running` 摘要；收尾记录 `completed`、`partial`、`failed` 或 `interrupted`、计数、逐项结果、剩余项与限制。重新查询发现最后一个事件只有 started 时，实际状态标记为未知，先回读再决定，不擅自重放动作。
- `index.md`：新增一条含 run ID、时区时间、仓库、状态、本地/远端范围、数量和结果链接的索引；开始时建立入口，结束后更新本条状态，不覆盖其他历史。并发写入需防止丢记录；索引缺失时以各 run 记录为准。

不要求引入数据库。小规模使用 Markdown 索引与 JSON/JSONL 即可，按文件内容用 `rg` 检索。记录仅保存必要元数据，不复制 token、远端 URL 中的认证信息、ignored 文件中的密钥或业务原文。备份敏感文件时保留其访问限制，报告只给位置。

## 执行前计划

以下为字段约定，值必须来自本次事实；示例字段不是预填通过结论。

```json
{
  "run_id": "20261026T103000+0800-a1b2c3",
  "created_at": "2026-10-26T10:30:00+08:00",
  "scope": "local",
  "authorization": "用户本次明确要求及已有保护约定的摘要",
  "repositories": [{
    "path": "/absolute/project/repo",
    "common_git_dir": "/absolute/project/repo/.git",
    "primary_branch": "<已核实主分支>",
    "targets": [{"ref": "refs/remotes/origin/<目标>", "sha": "<目标 SHA>", "reason": "<依据>"}],
    "protected": ["<保护分支、工作区及原因>"],
    "before": {"worktree_registrations": 0, "existing_worktree_directories": 0, "local_branches": 0}
  }],
  "items": [{
    "id": "item-001",
    "repository": "/absolute/project/repo",
    "worktree": "/absolute/task-worktree",
    "branch": "refs/heads/<任务>",
    "head_sha": "<实际 SHA>",
    "purpose": "<任务用途与来源>",
    "last_commit_at": "<带时区的提交时间>",
    "activity_evidence": "<活跃或结束依据及无法确认的部分>",
    "target_ref": "refs/remotes/origin/<目标>",
    "target_sha": "<实际 SHA>",
    "integration_evidence": "<已集成、未交付或证据不足>",
    "worktree_state": "<暂存、未暂存、未跟踪、重要 ignored、中间态>",
    "decision": "keep",
    "actions": [],
    "reason": "<具体判断，不只写旧或没用>",
    "recovery": {"location": null, "ref": null, "sha": null, "verified": false, "depends_on": []}
  }]
}
```

没有 worktree 的分支，其 worktree 为 null；detached HEAD 的 branch 为 null。`decision` 可用 `remove`、`archive`、`keep`、`review`。actions 分别列出移除目录、归档、回收登记、删除本地引用等，不把它们合并成一个含糊的“删”。明确授权远端删除时，scope 为 `local_and_remote`，对应 item 增加远端名称、服务器仓库标识、完整 ref、预期 SHA 和本次授权依据。

## 事件与结果

每项动作记录：`timestamp`、`item_id`、`action`、`status`、对象及仓库、预期/实际旧 SHA、回读结果；涉及备份时保存路径、恢复 ref、恢复验证方式及依赖。状态至少区分 `started`、`succeeded`、`failed`、`skipped`；执行失败与核验未知不能写成功。

结果汇总明确：

- 主分支与目标基线、授权范围、执行起止时间、运行状态。
- 每个对象为何处理、实际执行什么、是否仅移出或已经物理删除、是否涉及服务器。
- 前后 worktree 登记、实际目录、本地分支数量；远端只统计本次准确列举的对象，不用本地 remote-tracking 数量代替。
- 原工作区与保护对象核验结果；并发造成的数量变化单列，不能把它记成本次清理成果。
- 归档位置、恢复条件与验证结果；区分文件已保存、提交可达、独立备份可还原及尚未演练。
- 失败、跳过、未知或需人工决定的事项，以及剩余对象、用途和最后提交时间。

## 查询方式

先定位规范根目录，再读取索引；按原路径、分支或 run ID 检索计划与事件，例如：

```bash
rg -n --fixed-strings '<branch-or-path-or-run-id>' /absolute/workspace/.issuekit/cleanup
```

回答给出本次匹配的仓库、时间、原因、实际结果和可点击记录位置。有必要时只读回验恢复文件与引用是否仍存在；历史上存在不能写成现在仍可恢复。不要因为索引写了 completed 就忽略逐项失败或仅开始未结束的事件。

没有历史记录时明确证据缺失。用户要求补录时，可根据实际日志、归档 manifest 和恢复引用重建，并标记为事后补录、来源及未知项，不虚构当时的授权、基线判断或执行成功。
