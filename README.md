# IssueKit

面向开发者的工程工具包，在开发周期的关键节点，帮助 AI 编程助手理解约束、做出工程判断并交付可验证的结果。

## IssueKit 是什么？

IssueKit 提供可独立使用、也可组合的 Skills。开发者可以直接开始需求澄清、设计、编码、验证、审核或合并，无需先走完整周期或补齐一套文档。Agent 自主选择方法，工具包提供判断原则、必要门禁与人工兜底边界。

| 当前需要 | Skill | 主要结果 |
| --- | --- | --- |
| 理解项目或模块 | `$issuekit-knowledge` | 可追溯的上下文与约束 |
| 澄清目标和验收条件 | `$issuekit-require` | 需求范围、验收标准与关键歧义 |
| 比较技术方案 | `$issuekit-design` | 取舍、边界、契约与演进考虑 |
| 完成实现或修复 | `$issuekit-coding` | 最小完整代码和验证证据 |
| 规划风险覆盖 | `$issuekit-test` | 验证策略、关键预期与覆盖关系 |
| 落地真实业务验收 | `$issuekit-business-test` | 详细 Case、准备状态、运行证据与判定 |
| 审核明确的改动范围 | `$issuekit-review` | 有依据、可行动的问题与风险 |
| 集成代码并保全功能 | `$issuekit-merge` | 各方有效能力的保全与集成证据 |
| 清理分支与 worktree、查询历史清理 | `$issuekit-cleanup` | 基线判断、执行前清单与可查询的清理记录，默认仅本地 |
| 判断和准备交付 | `$issuekit-release` | 交付条件、恢复说明及已授权动作 |
| 管理目标或决策变化 | `$issuekit-change` | 影响分析、材料更新和需重验范围 |

既有需求、任务说明、代码、讨论和项目文档均可作为材料。只有会影响正确性且无法自行查明的关键歧义才需要人工裁决；缺少模板文件不等于任务不能继续。准备、代码修改、提交、推送和线上操作遵守本次实际授权。

架构定位、各工具职责与实施进展见 [开发者工具包架构](docs/developer-toolkit-architecture.md)。

## 安装

```bash
pip install issuekit
```

## 快速上手

### 第 1 步：初始化

在你的项目根目录运行：

```bash
cd your-project
issuekit init --ai cursor     # Cursor
issuekit init --ai codex      # Codex
issuekit init --ai claude     # Claude Code
```

这会创建 `.issuekit/` 目录（模板 + 知识库配置），并将 Skills 安装到对应目录。

默认 Issue 文档存放在项目根目录的 `issues/` 文件夹下。你也可以自定义目录：

```bash
issuekit init --ai cursor --issues-dir doc/issues
```

### 按当前任务选用工具

可选地使用 `$issuekit-knowledge` 建立当前任务相关的项目理解；已有上下文足够时直接进入需要的节点。

```text
$issuekit-require    # 目标不明确时澄清范围与验收
$issuekit-design     # 需要工程取舍时设计方案
$issuekit-coding     # 目标清楚时完成实现
$issuekit-test       # 规划覆盖与验证层级
$issuekit-business-test  # 需要真实业务证据时落地验收
$issuekit-review     # 审核明确的代码范围，不要求先创建 PR
$issuekit-merge      # 合并选定代码，保护已有和新增有效能力
$issuekit-cleanup    # 先列清单和理由，再按授权清理本地分支/worktree并留存结果
$issuekit-release    # 准备交付，按实际授权执行相关动作
$issuekit-change     # 目标变化时追踪影响与兑现状态
```

文档按任务规模裁剪，复用项目已有材料。需要持续维护的 Issue 可使用 `requirement.md`、`technical-design.md`、`test-plan.md` 等模板；小任务不要求为调用 Skill 创建全套文件。详细业务 Case 保留单一规范定义，实际结果写入独立运行记录；测试计划不能作为已通过的证据。

## `init` 做了什么

1. 创建 `.issuekit/` 目录：
  - `config.yaml` — 项目配置（Issue 文档目录等）
  - `templates/` — 各阶段文档模板（需求、技术方案、测试、发布、审核）
  - `knowledge/` — 项目上下文知识摘要
2. 安装 Skills 到对应目录：
  - Cursor → `.cursor/skills/`
  - Claude Code → `.claude/skills/`
  - Codex → `.agents/skills/`
  - GitHub Copilot → `.github/skills/`

每个 Skill 包含 `SKILL.md`（指令），并按需携带 `references/`、`scripts/` 和 `assets/`；Codex 还会安装 `agents/openai.yaml` 元数据。

## 更新模板与 Skills（已 init 的项目）

文档模板与 Skills 都来自 **已安装的 `issuekit` PyPI 包**。要拿到新版内容，先升级包，再同步到项目：

```bash
pip install -U issuekit
issuekit upgrade --ai cursor    # 与 init 时选的助手一致：cursor / claude / codex / copilot
```

`upgrade` 会：

- **覆盖** `.issuekit/templates/` 下与内置同名的 `.md`（若你改过模板，请先备份或自行合并）；
- **保护 Skill 本地修改**：依据宿主 Skills 目录中的安装清单更新未修改的文件；本地与新版内容相同可收敛，内容不同或没有旧基线时保留并报告冲突，命令非零退出。
- **受管理的移除资源**：只清理有基线且未修改的旧资源，项目自有文件不受影响。

旧项目首次升级如果没有安装清单，先审阅差异并备份本地定制；只有将冲突文件明确对齐到期望发行内容后，再重试建立基线。不要为了消除冲突直接删除 Skill 目录。Skill 冲突预检不通过时，不先写入文档模板。

**不会** 修改 `.issuekit/config.yaml`、`.issuekit/knowledge/config.yaml`，也不会删除 `.issuekit/knowledge/` 里已生成的知识摘要文件。

若你曾用 `issuekit init --issues-dir` 自定义过 Issue 目录，无需再改；`upgrade` 不涉及该配置。

> **不建议** 用 `issuekit init --force` 仅为了更新：`--force` 会**整目录删除** `.issuekit/` 并重建，可能丢失知识库配置与 `.issuekit/knowledge/` 下已生成的摘要。

## 开发与验证

```bash
pip install -e ".[test]"
python -m pytest
```

测试覆盖资源安装和引用完整性，并包含隔离 merge 评测工具的自检。行为评测夹具的准备、独立验收和限制见 [merge 评测试点](evals/merge/README.md)；工具自检通过不代表 Agent 已通过评测。

## 支持的 AI 助手


| AI 助手          | 参数             | Skills 目录         |
| -------------- | -------------- | ----------------- |
| Cursor         | `--ai cursor`  | `.cursor/skills/` |
| Claude Code    | `--ai claude`  | `.claude/skills/` |
| Codex          | `--ai codex`   | `.agents/skills/` |
| GitHub Copilot | `--ai copilot` | `.github/skills/` |


## 目录结构

```
.issuekit/
├── config.yaml               # 项目配置（issues_dir 等）
├── templates/                # 文档模板
│   ├── requirement.md        # 需求文档模板
│   ├── technical-design.md   # 技术方案模板
│   ├── test-plan.md          # 测试方案模板
│   ├── release-note.md       # 发布文档模板
│   └── code-review.md        # 代码审核模板
└── knowledge/                # 项目上下文知识摘要
    ├── config.yaml           # 知识库配置
    ├── project-overview.md   # 项目概览
    ├── architecture.md       # 架构分析
    ├── api-surface.md        # API 接口摘要
    ├── data-model.md         # 数据模型摘要
    ├── integrations.md       # 外部集成摘要
    └── conventions.md        # 编码约定摘要

.cursor/skills/               # Cursor Skills（示例）
├── issuekit-require/
│   └── SKILL.md
├── issuekit-design/
│   └── SKILL.md
└── ...

issues/                       # Issue 文档（默认目录，可通过 --issues-dir 自定义）
└── FEAT-20260228-xxx/
    ├── requirement.md
    ├── technical-design.md
    ├── test-plan.md
    ├── release-note.md
    └── code-review.md
```

## 许可证

MIT
