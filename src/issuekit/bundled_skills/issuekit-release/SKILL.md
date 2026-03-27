---
name: issuekit-release
description: 准备发布文档并创建 Pull Request。分析代码变更，对比技术方案，生成部署指南。当用户提到准备发布、创建 PR 时使用。
---

## 用户输入

用户可以指定 issue ID，也可以从当前 git 分支自动推断。

## 概述

本 skill 生成发布文档并创建 Pull Request。分析特性分支上的所有代码变更，对比技术方案，生成部署指南。

## 前置条件

- 开发和测试已完成
- 代码已提交到特性分支
- issue 目录中存在 `technical-design.md` 和 `test-plan.md`

## 工作流程

### 第 0 步：先读取知识约定并规划任务

在开始发布规划前，优先执行：

1. 阅读 `.issuekit/knowledge/conventions.md`（如有）
2. 阅读 `.issuekit/knowledge/` 下与本次发布内容相关的已有知识摘要（如有），若存在 `.issuekit/knowledge/modules/` 对应模块文件则优先阅读
3. 基于上述约定与已有知识，再开始后续发布步骤

### 第 1 步：定位 Issue 并分析变更

1. 读取 `.issuekit/config.yaml` 中的 `issues_dir` 配置项，获取 Issue 文档存放目录（默认为 `issues`）
2. 定位 issue 目录（从用户输入或当前分支）
3. 运行 `git diff master...HEAD` 收集所有代码变更
4. 运行 `git log master..HEAD --oneline` 列出所有提交

### 第 2 步：阅读上下文

1. 阅读 `technical-design.md` 获取设计方案
2. 阅读 `test-plan.md` 获取测试覆盖和结果
3. 阅读 `requirement.md` 获取原始需求

### 第 3 步：对比方案与实际实现

将技术方案与实际代码变更对比：
- 识别已实现的项目
- 标记偏离设计的地方
- 记录计划外的变更

### 第 4 步：生成发布文档

加载模板 `.issuekit/templates/release-note.md` 并填充所有章节：

- 变更概述
- 需求变更汇总：合并 `requirement.md`、`technical-design.md` 末尾「变更记录」（排除仅初稿条目），并补充本分支 `git log` 中体现的需求或方案变更，去重后填入
- 详细变更清单（功能、接口、数据库、配置）
- 影响范围
- 部署步骤（有序检查清单）
- 回滚方案
- 监控与告警
- 发布后验证

### 第 5 步：创建 Pull Request

```bash
git push -u origin HEAD
gh pr create --title "{Issue ID}: {摘要}" --body "$(cat <<'EOF'
## 概述
{发布文档中的关键变更}

## 变更清单
{变更列表}

## 测试情况
{测试覆盖摘要}

## 部署说明
{部署步骤（如有）}

## 相关文档
- 需求文档：{issues_dir}/{issue-id}/requirement.md
- 技术方案：{issues_dir}/{issue-id}/technical-design.md
- 测试方案：{issues_dir}/{issue-id}/test-plan.md
- 发布文档：{issues_dir}/{issue-id}/release-note.md

EOF
)"
```

### 第 6 步：写入文件并报告

1. 将 `release-note.md` 写入 issue 目录
2. 报告 PR 链接并建议下一步：`$issuekit-review`
