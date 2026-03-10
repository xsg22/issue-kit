# IssueKit

AI 辅助开发的 Issue 全生命周期工具。从需求分析到代码审核，由你的 AI 编程助手驱动。

## IssueKit 是什么？

IssueKit 为 AI 辅助开发提供结构化的工作流。它提供一组 Skills，引导你的 AI 编程助手（Cursor、Claude Code、Codex 等）完成一个 Issue 的完整生命周期：

| 阶段 | Skill | 说明 |
|------|-------|------|
| 1. 需求分析 | `$issuekit-require` | 分析需求，生成面向产品经理的需求文档 |
| 2. 技术方案 | `$issuekit-design` | 架构设计、接口设计、组件设计、开发步骤 |
| 3. 编码实现 | `$issuekit-coding` | 按技术方案编码，交叉校验代码与文档一致性 |
| 4. 测试方案 | `$issuekit-test` | 黑盒业务测试 + 白盒单测/接口测试用例 |
| 5. 发布准备 | `$issuekit-release` | 生成发布文档，创建 Pull Request |
| 6. 代码审核 | `$issuekit-review` | 多维度交叉验证（需求、方案、质量） |

还有一个 `$issuekit-knowledge` skill，用于生成项目上下文摘要，让 AI 助手快速理解项目。

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

### 第 2 步：构建项目知识（可选但推荐）

在 AI 助手中运行：

```
$issuekit-knowledge
```

AI 助手会分析你的项目，生成结构化的知识摘要到 `.issuekit/knowledge/`。后续的需求分析和技术方案设计会自动读取这些摘要。

### 第 3 步：创建第一个 Issue

假设产品经理给了一个需求："用户个人资料页面增加修改头像功能，支持裁剪和压缩"。

在 AI 助手中调用 `$issuekit-require`，AI 助手会：
1. 深入分析代码，理解现有用户模块的实现
2. 生成 Issue ID（如 `FEAT-20260228-avatar-upload`）
3. 创建 `issues/FEAT-20260228-avatar-upload/requirement.md`
4. 从 master 拉出特性分支 `feature/FEAT-20260228-avatar-upload`

需求文档包含：用户故事（Mermaid 流程图）、边界场景、验收标准、AI 需求评审、待确认问题。

### 第 4 步：设计技术方案

需求确认后，调用 `$issuekit-design`。

生成 `technical-design.md`，涵盖技术调研、架构设计、核心流程、组件设计、接口设计、开发步骤。

### 第 5 步：编码实现

调用 `$issuekit-coding`。

AI 助手按技术文档的开发步骤逐步实现，完成后自动交叉校验代码与技术文档、需求文档的一致性。

### 第 6 步：后续流程

```
$issuekit-test      # 生成测试方案
$issuekit-release   # 生成发布文档 + 创建 PR
$issuekit-review    # 多维度代码审核
```

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

每个 Skill 包含 `SKILL.md`（指令）和 `agents/openai.yaml`（元数据）。

## 支持的 AI 助手

| AI 助手 | 参数 | Skills 目录 |
|---------|------|------------|
| Cursor | `--ai cursor` | `.cursor/skills/` |
| Claude Code | `--ai claude` | `.claude/skills/` |
| Codex | `--ai codex` | `.agents/skills/` |
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
│   ├── SKILL.md
│   └── agents/openai.yaml
├── issuekit-design/
│   ├── SKILL.md
│   └── agents/openai.yaml
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
