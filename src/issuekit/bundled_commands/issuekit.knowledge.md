---
description: 分析当前项目，生成结构化的上下文知识摘要到 .issuekit/knowledge/，供其他 issuekit 命令使用。
---

## 概述

本命令分析当前项目的代码、配置和结构，生成一系列知识摘要文件。这些摘要让 AI Agent 在执行需求分析、技术方案设计等任务时，能快速理解项目上下文，而无需每次从零扫描。

**输出目录**: `.issuekit/knowledge/`

## 工作流程

### 第 1 步：检测项目类型

自动识别项目的技术栈和构建系统：

1. 扫描项目根目录的构建/配置文件：
   - `pom.xml` / `build.gradle` → Java/Kotlin
   - `package.json` → JavaScript/TypeScript
   - `go.mod` → Go
   - `requirements.txt` / `pyproject.toml` / `setup.py` → Python
   - `Cargo.toml` → Rust
   - `*.csproj` / `*.sln` → C#/.NET
   - 其他构建文件 → 按实际情况处理
2. 读取依赖配置，提取所有依赖及版本
3. 读取应用配置文件（如 application.yml, .env, config/ 等）识别中间件和外部服务

### 第 2 步：项目概览

生成 `.issuekit/knowledge/project-overview.md`：

- 项目名称和简要描述（从 README 或配置推断）
- 目录结构树（关键目录 + 一句话说明）
- 技术栈表格（类别 | 技术 | 版本 | 用途）
- 代码规模统计（按语言/模块的文件数和行数）
- Git 活跃度（近 6 个月的提交频率、主要贡献者）

### 第 3 步：架构分析

生成 `.issuekit/knowledge/architecture.md`：

- 分层架构（识别项目的层级划分，如 Controller/Service/DAO 或其他模式）
- 每层的职责描述
- 模块间依赖关系（Mermaid 图）
- 设计模式识别（策略、工厂、适配器等，标注使用位置）
- 横切关注点（缓存、事务、异常处理、配置管理、安全/认证）

### 第 4 步：API 接口摘要

生成 `.issuekit/knowledge/api-surface.md`：

- 扫描所有 API 端点（HTTP 路由、gRPC 服务、GraphQL schema 等）
- 按业务模块分组
- 每个端点：方法、路径、简要说明
- 请求/响应的通用约定（统一返回体、错误码规范、参数校验方式）
- API 数量统计（按模块分布饼图）

### 第 5 步：数据模型摘要

生成 `.issuekit/knowledge/data-model.md`：

- 扫描 ORM 实体/模型定义
- 如果有 MCP 数据库连接可用：
  1. 先验证该数据库连接与当前项目相关（检查 MCP 的数据库连接字符串中的数据库名称、主机等信息，与项目配置文件中的数据库配置做比对）
  2. 如果确认相关，查询实际表结构
  3. 如果无法确认相关性或明确不相关，跳过数据库查询并在文档中注明"未使用 MCP 数据库查询：无法确认数据库连接与当前项目相关"，避免不相关的数据库信息误导后续分析
- 按业务域分组列出表/实体
- 核心表的关系图（Mermaid erDiagram）
- 标注实体类在代码中的位置

### 第 6 步：外部集成摘要

生成 `.issuekit/knowledge/integrations.md`：

- 识别所有外部服务集成（SDK、REST API、gRPC、消息队列、缓存等）
- 每个集成：服务名、集成方式、适配类/客户端位置、配置项
- 外部依赖拓扑图（Mermaid flowchart）

### 第 7 步：编码约定摘要

生成 `.issuekit/knowledge/conventions.md`：

- 从现有代码推断编码风格和约定
- 命名约定（类名、方法名、变量名、数据库表/列）
- 日志使用方式
- 错误处理模式
- 如果项目已有规范文件（如 .cursor/rules/, .editorconfig, linter 配置），整合其内容

### 第 8 步：报告完成

```
知识库更新完成 ✓
━━━━━━━━━━━━━━━━━━━━
生成文件：
- .issuekit/knowledge/project-overview.md
- .issuekit/knowledge/architecture.md
- .issuekit/knowledge/api-surface.md
- .issuekit/knowledge/data-model.md
- .issuekit/knowledge/integrations.md
- .issuekit/knowledge/conventions.md

后续命令（如 /issuekit.require、/issuekit.design）将自动读取这些知识摘要。
```

## AI 执行指南

### 通用化原则

- 不假设任何特定的语言或框架，根据实际项目自适应
- 如果某个步骤不适用（如项目无数据库），跳过并注明
- 优先使用 Mermaid 图表，文字作为补充
- 所有关键入口使用可点击的相对路径链接

### 增量更新

- 如果知识文件已存在，对比后仅更新有变化的部分
- 在每个文件末尾记录最后更新时间
