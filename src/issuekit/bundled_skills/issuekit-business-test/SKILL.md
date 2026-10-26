---
name: issuekit-business-test
description: 将验收目标落成可执行业务 Case、测试数据准备和真实验证证据；支持独立设计用例、准备、执行及回归。用户要求详细业务测试或真实接口、数据库、日志与异步结果验收时使用。
---

# IssueKit 真实业务测试

帮助开发者将业务预期落成确定性 Case，判断当前环境能验证到什么程度，并取得可追溯的实际结果。可以独立调用；不要求先运行其他 Skill 或存在完整技术方案。`issuekit-test` 负责风险策略与覆盖，本工具维护详细 Case、Fixture、Readiness 和逐轮运行证据，策略只引用同一份 Case。

业务规则与领域知识来自项目及有效需求；通用发行内容不内置项目账号、密钥、接口和 SQL。需求决定应该怎样，真实代码与运行事实说明怎样调用、准备和观测，不能以当前实现降低验收标准。

## 按任务加载

未指定模式时采用 `design`，不自行准备数据或执行有副作用的业务动作。可以直接进入已具备充分事实的模式，不要求重做已完成工作。

| 模式 | 责任与按需资料 |
| --- | --- |
| `design` | 生成详细 Case、精确预期与覆盖。阅读 [Case 设计](references/case-design.md)、[Case 维护](references/case-maintenance.md)；需结构协议时阅读 [Case Schema](references/testcase-schema.md) 与 [状态模型](references/test-model.md)。 |
| `prepare` | 绑定真实环境与版本，准备并回读 Fixture。阅读 [执行上下文与准备门禁](references/execution-readiness.md)、[Case 维护](references/case-maintenance.md)；数据操作细节见 [准备协议](references/preparation-protocol.md)、[隔离规则](references/data-isolation.md) 和 [数据库证据](references/database-evidence.md)。 |
| `execute` | 执行已冻结 Case，保留每条实际结果与证据。阅读 [执行上下文与准备门禁](references/execution-readiness.md)、[Case 维护](references/case-maintenance.md) 和 [执行与结果收口](references/execution-loop.md)。 |
| `regression` | 关联修复版本，重新验证失败项与受影响范围并保留历轮证据。阅读 [执行上下文与准备门禁](references/execution-readiness.md)、[Case 维护](references/case-maintenance.md) 和 [执行与结果收口](references/execution-loop.md)。 |

出现契约冲突时阅读 [漂移处理](references/contract-drift.md)；需失败归因或自动运行细节时阅读 [失败分析](references/failure-analysis.md) 与 [自动化循环](references/automation-loop.md)。只加载当前任务相关资料。

## 共用原则与门禁

- **事实充分**：复用有效需求、项目约定、测试知识、真实代码和已有 Case；缺少特定文档不阻断，缺少会改变业务预期的关键规则才阻断相关 Case。明确区分需求事实、实现事实、假设与冲突；其余可独立工作继续。
- **唯一预期**：每个 Case 有独立 ID、修订、精确前置状态、操作、可观察断言及明确通过条件。覆盖用户结果、系统状态和必要副作用，明确禁止变化的不变量。代码不符合明确需求应判实现缺口，不能把断言改成当前代码能通过的结果。
- **功能保全**：同时考虑新行为与受影响的既有有效能力。需求废止、替代或 Case 退休要有依据，不静默删掉失败边界；Case、索引、Fixture 与固定执行脚本保持一致。
- **定义与运行分离**：规范定义只写预期；每轮报告用新的 `test_run_id` 记录 `case_id + revision + commit + fixture_id`、实际值、差异及证据。变更预期不回写历史结果，历史报告仅追加勘误。
- **执行身份明确**：执行前明确目标环境、实际被测版本、服务/数据源、测试主体、凭据来源与写入范围，核实真实身份；不从当前分支、默认连接或历史信息猜测环境。无环境也能设计 Case，不能伪装完成真实验收。
- **授权与隔离**：业务请求、数据准备、清理和修复分别遵守本次授权。写入前明确旧值、新值、条件、影响及恢复/保留策略；Fixture 回读不符不得继续。使用可归属的测试数据，不并行共享可变主体或资源，不通过临时账号、SQL 或手工步骤绕过前置门禁。
- **确定性执行**：可重复验收使用项目维护的固定 Case 脚本和共享驱动；缺脚本或核心请求/主体/前置能力时，报告具体阻塞。脚本语法、单测和 Mock 只证明工具质量，不能代替真实业务证据。
- **证据真实**：运行结论绑定实际版本、环境和范围。证据不足按协议降级，接口成功不能单独证明数据库、异步或最终资源成功；保留矛盾证据，不选择性报告。敏感凭据不得进入报告。
- **范围完整**：冻结本轮 Case 清单，每条都有结果或未执行原因；安全条件允许时继续互不影响的 Case，不因一条失败省略剩余项。部分选取必须披露遗漏的 ACTIVE Case 并标 `INCOMPLETE_EXECUTION`，不能称为全量验收。出现授权、隔离或前置状态失效时停止受影响动作。
- **尽力与兜底**：先调查和完成独立可验证部分。区分实现、数据、配置、环境与证据问题；在授权范围内修复并回归，不默认扩大为代码实施或线上变更。仍无法裁决时提供证据、候选判断与具体人工决策点。

## 交付

按项目约定输出 Case、覆盖索引、Fixture、Readiness 或逐轮报告，不强制每次产生所有产物。存在时复用 `.issuekit/templates/business-test-case.md`、`test-readiness-report.md`、`test-execution-report.md`，写入当前 Issue 或 `.issuekit/testing/generated/`；不存在时也可交付，但要标明项目测试知识缺口。

可用 `scripts/validate_testcase_document.py <path> --kind definition` 检查规范定义，`--kind report` 检查独立运行报告；默认只检查定义。输入结构与迁移要求见 [Case Schema](references/testcase-schema.md)，结构通过不证明业务正确。

报告明确本次完成了设计、准备还是实际执行，列出通过/失败/阻塞范围、版本与环境、证据及限制；未执行不写 PASS，修复建议不写成已修复结果。输出格式与确定性脚本的输入协议保持一致。
