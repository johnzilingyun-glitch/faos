# Financial Agent Operating System (FAOS)

Version: V5.0

Status: Architecture Frozen

---

# Architecture Freeze

本文档定义 Financial Agent Operating System（FAOS）的最终架构。

本架构自 V5 起正式冻结（Architecture Freeze）。

后续版本：

- 不再调整核心分层
- 不再修改模块关系
- 不再改变系统数据流

后续所有文档仅扩展：

- Module Responsibilities
- Interface Specification
- Workflow
- Configuration
- Extension SDK
- Best Practices

不修改 Architecture。

---

# Design Philosophy

FAOS 不是传统意义上的 AI Agent。

它不是：

```
LLM

↓

Tool

↓

LLM
```

而是：

```
Task

↓

Planning

↓

Execution

↓

Reasoning

↓

Decision
```

LLM 是系统中的推理组件。

不是系统本身。

整个系统由 Task Runtime 驱动。

---

# Core Principles

整个系统遵循以下原则：

## 1. Task First

Task 是整个系统唯一的一等公民（First Class Citizen）。

所有请求最终都会转换为 Task。

例如：

- Analyze Stock
- Analyze Portfolio
- Analyze Macro
- Generate Report
- Screen Stocks
- Monitor Market
- Backtesting
- Trading Decision

Task 是整个系统生命周期的载体。

---

## 2. Runtime Driven

系统只有一个 Runtime。

即：

Task Runtime。

Runtime：

负责：

- 生命周期
- 调度
- Context
- Event
- Scheduling

其它模块均属于 Runtime 调用的 Service。

---

## 3. Service Oriented

整个系统采用 Service-Oriented Architecture。

包括：

- Domain Service
- Capability Service
- Workflow Service
- Skill Service
- Provider Service
- Knowledge Service
- Reasoning Service
- Decision Service
- Report Service

Runtime 不实现业务。

Service 不负责调度。

---

## 4. Capability Driven

Planner 永远规划 Capability。

而不是：

Skill。

Skill 是 Capability 的一种实现方式。

Planner 不关心 Skill。

---

## 5. Provider Isolation

Skill 不允许直接访问：

第三方数据源。

所有数据统一来自：

Provider Service。

Provider 可以随时替换。

Skill 不需要修改。

---

## 6. LLM Independent

LLM 仅负责推理。

LLM：

不知道：

Provider。

不知道：

Workflow。

不知道：

Skill。

LLM：

只接收：

Context。

返回：

Reasoning。

---

## 7. Event Driven

所有模块通过 Event 解耦。

禁止：

模块直接调用模块。

统一：

发布：

事件。

例如：

TaskStarted

ProviderCompleted

ReasoningFinished

DecisionGenerated

ReportGenerated

---

## 8. Data First

所有 Provider：

统一输出：

标准化数据。

LLM 永远处理：

Structured Data。

禁止：

Provider 返回 Prompt。

---

## 9. Observable

整个 Runtime：

必须：

可观察。

包括：

Trace

Metrics

Latency

Cost

Token

Provider

Workflow

Skill

Decision

---

## 10. Plugin Architecture

所有 Service：

均可插件化。

包括：

Capability

Workflow

Skill

Provider

Knowledge

Reasoning

Decision

无需修改 Runtime。

---

# Frozen Architecture

整个系统采用固定分层。

以后禁止修改。

```
                   User
                     │
                     ▼
             Request Dispatcher
                     │
                     ▼
                Task Runtime
                     │
                     ▼
             Planner Pipeline
                     │
                     ▼
             Execution Context
                     │
                     ▼
             Execution Engine
                     │
────────────────────────────────────────────

                Domain Service

────────────────────────────────────────────

             Capability Service

────────────────────────────────────────────

              Workflow Service

────────────────────────────────────────────

                Skill Service

────────────────────────────────────────────

              Provider Service

────────────────────────────────────────────

                 Data Route

────────────────────────────────────────────

             Knowledge Service

────────────────────────────────────────────

             Reasoning Service

────────────────────────────────────────────

             Discussion Service

────────────────────────────────────────────

             Reflection Service

────────────────────────────────────────────

          Decision & Strategy Service

────────────────────────────────────────────

               Report Service
```

---

# Layer Responsibilities

## Task Runtime

整个系统唯一 Runtime。

负责：

- Task Lifecycle
- Task Queue
- Session
- Scheduler
- Event Dispatch
- Execution Context
- Metrics
- Trace

Task Runtime 不实现业务逻辑。

---

## Planner Pipeline

负责：

将 Task 转换为：

Execution Plan。

包括：

- Intent Analysis
- Entity Extraction
- Domain Selection
- Capability Planning
- Dependency Analysis
- Execution Plan Generation

Planner 永远不执行业务。

---

## Execution Context

Execution Context 是整个 Task 的共享上下文。

包括：

- Variables
- Results
- Memory References
- Provider Outputs
- Trace
- Decisions
- Events

所有 Service 共享同一 Context。

---

## Execution Engine

Execution Engine：

解释：

Execution Plan。

负责：

- DAG Scheduling
- Parallel Execution
- Retry
- Timeout
- Dependency Resolution
- Error Recovery

Execution Engine 不关心业务。

---

## Domain Service

负责：

业务领域。

例如：

- Stock
- ETF
- Fund
- Bond
- Macro
- Crypto
- Futures

Domain：

决定：

Capability。

---

## Capability Service

Capability：

定义：

系统能力。

例如：

Realtime Quote

Financial Analysis

News Analysis

Risk Analysis

Portfolio Analysis

Capability：

由：

Workflow 组成。

---

## Workflow Service

Workflow：

组合：

多个 Capability。

例如：

Analyze Stock：

包含：

Quote

Financial

News

Macro

Valuation

Risk

Workflow：

不直接获取数据。

---

## Skill Service

Skill：

实现：

具体业务。

例如：

AShareSkill

HKStockSkill

MacroSkill

NewsSkill

Skill：

不知道：

LLM。

不知道：

Provider。

---

## Provider Service

负责：

获取：

外部数据。

例如：

AkShare

EastMoney

Yahoo

Polygon

MCP

REST API

Provider：

统一输出：

标准模型。

---

## Data Route

负责：

Provider 路由。

包括：

- Priority
- Fallback
- Merge
- Cache
- Validation
- Normalization

---

## Knowledge Service

负责：

静态知识。

包括：

- Industry Knowledge
- Financial Indicators
- Prompt Templates
- Strategy Templates
- RAG Documents
- Embedding Index

Knowledge：

不是：

Memory。

---

## Reasoning Service

负责：

LLM 推理。

包括：

- Prompt Builder
- Context Builder
- Token Budget
- Compression
- Model Router

支持：

- GPT
- Claude
- Gemini
- DeepSeek
- Qwen
- OpenRouter

---

## Discussion Service

负责：

多 Agent 协作。

例如：

Fundamental Agent

Technical Agent

Macro Agent

Risk Agent

News Agent

最终：

形成：

Consensus。

---

## Reflection Service

负责：

第二轮审查。

包括：

- Consistency Check
- Hallucination Check
- Fact Verification
- Self Review

Reflection：

输出：

最终可信结果。

---

## Decision & Strategy Service

负责：

投资决策。

包括：

- Signal
- Score
- Risk
- Position
- Allocation
- Portfolio
- Strategy

LLM 可以参与。

但不是必须。

---

## Report Service

负责：

最终输出。

包括：

Markdown

JSON

HTML

PDF

Dashboard

---

# System Object Model

整个系统只有一个核心对象：

Task。

Task：

包含：

- Intent
- Entity
- Execution Plan
- Execution Context
- Workflow
- Results
- Memory
- Trace
- Decision
- Report

所有 Service：

围绕：

Task 工作。

---

# Architecture Freeze Statement

自 V5 起：

整个系统架构正式冻结。

允许扩展：

- 新 Domain
- 新 Capability
- 新 Workflow
- 新 Skill
- 新 Provider
- 新 Knowledge
- 新 Reasoning Model
- 新 Report Format

禁止修改：

- 核心分层
- 数据流方向
- Runtime 定义
- Task 生命周期
- Service 边界

任何新增能力必须遵循本架构规范。

---

End of Architecture Freeze

架构约束（Architecture Constraints），作为所有后续开发必须遵守的规则：

Task Runtime 是唯一 Runtime，其它均为 Service。
Service 之间禁止直接依赖，统一通过 Execution Context 和 Event 交互。
Planner 不调用 Skill，只生成 Execution Plan。
LLM 不直接访问 Provider，所有外部数据必须先经过 Provider Service 和 Data Route 标准化。
Decision & Strategy Service 是唯一允许产生投资结论的模块，Reasoning Service 只负责推理，不直接输出最终决策。


# Chapter 01 - System Overview

> Financial Agent Operating System (FAOS)
>
> Version: V5.0
>
> Status: Architecture Frozen

---

# 1. Overview

## 1.1 Purpose

Financial Agent Operating System（FAOS）是一个面向金融分析场景设计的智能分析平台。

它不是传统意义上的 AI Agent，也不是简单的 Tool Calling Framework，而是一套以 **Task Runtime** 为核心的金融智能操作系统。

FAOS 的目标是建立统一的任务执行框架，将数据获取、知识检索、多模型推理、策略决策和报告生成整合到同一个运行时中，实现复杂金融分析任务的自动化执行。

系统采用：

- Task-Oriented Architecture
- Service-Oriented Architecture
- Event-Driven Architecture
- Capability-Driven Execution
- Multi-LLM Collaboration

共同构成完整的 Financial AI Runtime。

---

# 1.2 Vision

FAOS 的长期目标不是构建一个聊天机器人，而是构建一个能够持续演进的金融智能分析平台。

平台应能够支持：

- 股票分析
- ETF 分析
- 基金分析
- 行业研究
- 宏观经济分析
- 新闻事件分析
- 财务分析
- 风险分析
- 投资组合分析
- 自动日报
- 自动监控
- 自动预警
- 策略研究
- 回测
- 自动交易（未来）

平台最终形成统一的金融智能底座。

---

# 1.3 Objectives

系统设计目标包括：

## Unified Runtime

所有任务统一进入 Task Runtime。

Runtime 是整个系统唯一调度中心。

---

## Unified Context

所有模块共享 Execution Context。

避免重复查询。

避免重复推理。

避免重复构建 Prompt。

---

## Unified Capability

所有分析能力统一抽象为 Capability。

Planner 不关心具体实现。

---

## Unified Provider

所有数据统一通过 Provider Service 获取。

禁止直接调用第三方 API。

---

## Unified Knowledge

所有静态知识统一通过 Knowledge Service 管理。

包括：

- 行业知识
- 财务知识
- 指标定义
- Prompt 模板
- 分析模板

---

## Unified Reasoning

支持多个模型统一推理。

例如：

- GPT
- Claude
- Gemini
- DeepSeek
- Qwen
- OpenRouter

模型可以自由替换。

---

## Unified Decision

所有分析最终进入 Decision & Strategy Service。

统一输出：

- 风险评分
- 投资评分
- 建议仓位
- 组合建议

---

# 1.4 Architecture Style

FAOS 采用混合架构。

包括：

## Task-Oriented

所有工作围绕 Task。

Task 是系统唯一执行对象。

---

## Service-Oriented

所有能力均以 Service 提供。

Service 可独立扩展。

---

## Event-Driven

所有模块通过 Event 通信。

避免模块直接依赖。

---

## Plugin-Oriented

Capability

Workflow

Skill

Provider

Reasoning

均支持插件化。

---

## Context-Oriented

Execution Context 是所有模块共享的数据中心。

Context 生命周期贯穿整个 Task。

---

# 1.5 Typical Workflow

一个完整分析流程如下：

```
User Request

↓

Task Runtime

↓

Planner Pipeline

↓

Execution Engine

↓

Capability Service

↓

Workflow Service

↓

Skill Service

↓

Provider Service

↓

Knowledge Service

↓

Reasoning Service

↓

Discussion Service

↓

Reflection Service

↓

Decision Service

↓

Report Service
```

整个生命周期均由 Task Runtime 管理。

---

# 1.6 Key Concepts

系统定义以下核心对象：

## Task

系统唯一执行对象。

代表一次完整分析任务。

---

## Execution Plan

Planner 输出。

描述任务执行流程。

---

## Execution Context

Task 生命周期共享上下文。

保存所有执行状态。

---

## Domain

业务领域。

例如：

- Stock
- ETF
- Fund
- Macro
- Crypto

---

## Capability

系统能力定义。

例如：

News Search

Financial Analysis

Valuation

---

## Workflow

Capability 组合。

例如：

Analyze Stock Workflow。

---

## Skill

具体业务实现。

例如：

AShare Skill。

---

## Provider

数据提供者。

例如：

AkShare。

---

## Knowledge

静态知识。

例如：

Prompt 模板。

行业分类。

---

## Reasoning

LLM 推理。

支持多个模型。

---

## Decision

投资决策。

生成最终分析结果。

---

# 1.7 Supported Scenarios

平台支持以下典型任务：

### 股票分析

分析上市公司。

输出完整报告。

---

### 投资组合分析

分析整个持仓。

识别风险。

---

### 行业研究

研究产业链。

分析行业景气度。

---

### 新闻分析

分析重大新闻。

识别影响。

---

### 宏观分析

分析：

- 利率
- CPI
- PMI
- GDP

---

### 自动监控

后台持续运行。

自动发现异常。

---

### 自动日报

定时生成：

市场日报。

行业日报。

组合日报。

---

### 自动预警

价格异常。

资金异常。

公告异常。

自动通知。

---

# 1.8 Non-Goals

系统当前不负责：

- 高频交易
- Tick Engine
- 行情推送
- Broker Gateway
- Order Matching

这些属于交易系统。

FAOS 负责：

分析。

决策。

建议。

---

# 1.9 Summary

FAOS 是一个围绕 Task Runtime 构建的金融智能分析平台。

Runtime 统一调度整个任务生命周期。

各 Service 提供独立能力。

LLM 不再是系统中心，而是作为推理服务参与整个分析流程。

通过 Task、Capability、Workflow、Skill、Provider、Knowledge、Reasoning、Decision 等模块协同工作，实现复杂金融分析任务的自动化执行。

本章定义了系统的总体定位、目标、核心对象和适用范围。

后续章节将在冻结架构基础上，对各模块的职责、交互和扩展规范进行详细说明。

---


# Chapter 02 - Task Runtime

> Financial Agent Operating System (FAOS)
>
> Version: V5.0
>
> Status: Architecture Frozen

---

# 2. Task Runtime

## 2.1 Purpose

Task Runtime 是整个 Financial Agent Operating System 的唯一 Runtime，也是整个系统的核心。

所有用户请求、后台任务、定时任务、自动监控任务均必须进入 Task Runtime。

Task Runtime 负责管理任务生命周期、执行上下文、事件调度和执行状态。

整个系统只有一个 Runtime：

```
Task Runtime
```

其它所有模块均属于 Runtime 调度的 Service。

---

# 2.2 Responsibilities

Task Runtime 负责：

- Task 生命周期管理
- Execution Context 管理
- Planner Pipeline 调用
- Execution Engine 调度
- Event Dispatch
- Service 调用
- Trace 管理
- Metrics 收集
- Token 统计
- Cost 统计
- Result 聚合

Task Runtime 不负责：

- 获取数据
- 推理
- Prompt
- Skill
- Workflow
- Provider
- 决策
- 报告生成

这些全部交给对应 Service。

---

# 2.3 Runtime Position

整个系统中只有一个 Runtime。

```
                  User
                    │
                    ▼
          Request Dispatcher
                    │
                    ▼
              Task Runtime
                    │
                    ▼
           Planner Pipeline
                    │
                    ▼
          Execution Engine
                    │
─────────────────────────────────────
       Service Layer
─────────────────────────────────────
```

Task Runtime 永远作为唯一入口。

---

# 2.4 Task Lifecycle

Task 生命周期定义如下：

```
Created

↓

Initialized

↓

Planning

↓

Scheduled

↓

Running

↓

Reasoning

↓

Decision

↓

Reporting

↓

Completed
```

异常情况：

```
Running

↓

Retrying

↓

Running
```

或者：

```
Running

↓

Failed
```

或者：

```
Running

↓

Cancelled
```

---

# 2.5 Task State

Task 支持以下状态：

| State | Description |
|---------|------------|
| CREATED | 创建完成 |
| INITIALIZED | 初始化完成 |
| PLANNING | Planner 正在生成 Execution Plan |
| SCHEDULED | 等待执行 |
| RUNNING | Execution Engine 正在执行 |
| WAITING | 等待依赖 |
| PAUSED | 暂停 |
| RETRYING | 自动重试 |
| COMPLETED | 完成 |
| FAILED | 执行失败 |
| CANCELLED | 用户取消 |

Task Runtime 管理状态转换。

Service 不允许修改 Task 状态。

---

# 2.6 Task Object

Task 是整个系统唯一核心对象。

包含：

```yaml
Task

id

type

status

priority

request

intent

entities

domain

execution_plan

execution_context

workflow

results

decision

report

memory_reference

trace

metrics

events

created_at

finished_at
```

所有模块均围绕 Task 工作。

---

# 2.7 Task Context

Execution Context 是 Task 生命周期中的共享上下文。

包括：

```yaml
Context

Variables

Provider Outputs

Knowledge

Memory

Intermediate Results

Reasoning Result

Decision Result

Report Result
```

所有 Service：

共享：

Execution Context。

禁止：

Service 自己维护状态。

---

# 2.8 Task Scheduling

Task Runtime 负责调度。

包括：

```
Priority Queue

↓

Scheduler

↓

Execution Engine
```

支持：

- FIFO
- Priority
- Delayed Task
- Scheduled Task
- Background Task

未来：

支持：

Distributed Queue。

---

# 2.9 Event Management

Task Runtime 是唯一 Event Dispatcher。

事件包括：

```
TaskCreated

TaskStarted

PlanningStarted

PlanningCompleted

ExecutionStarted

ExecutionCompleted

ReasoningStarted

ReasoningCompleted

DecisionCompleted

ReportCompleted

TaskCompleted
```

任何 Service：

均可：

监听事件。

---

# 2.10 Runtime Context

Task Runtime 保存：

```
Current Task

↓

Execution Context

↓

Metrics

↓

Trace

↓

Logs
```

Runtime：

本身：

保持：

Stateless。

所有状态：

全部：

保存在：

Task。

---

# 2.11 Task Types

系统支持：

## Interactive Task

用户实时分析。

例如：

```
分析贵州茅台
```

---

## Background Task

后台执行。

例如：

```
每天18:00

生成市场日报
```

---

## Scheduled Task

Cron。

例如：

```
每5分钟：

扫描股票
```

---

## Monitoring Task

持续监控。

例如：

```
股价跌破：

MA60

通知
```

---

## Batch Task

批量。

例如：

```
分析：

3000只股票
```

---

# 2.12 Task Priority

系统定义：

| Priority | Description |
|------------|-------------|
| Critical | 实时用户请求 |
| High | 风险预警 |
| Normal | 普通分析 |
| Low | 后台分析 |
| Idle | 回测 |

Scheduler：

根据：

Priority：

排序。

---

# 2.13 Execution Context Lifecycle

Execution Context：

生命周期：

```
Create

↓

Attach

↓

Update

↓

Read

↓

Persist

↓

Destroy
```

Task 完成后：

Context：

可：

持久化。

---

# 2.14 Runtime Metrics

Task Runtime：

负责：

统计：

```
Execution Time

LLM Cost

Token

Provider Latency

Workflow Time

Skill Time

Retry Count

Memory Usage
```

Metrics：

统一：

保存。

---

# 2.15 Runtime Trace

每个 Task：

生成：

完整：

Trace。

包括：

```
Planner

↓

Workflow

↓

Skill

↓

Provider

↓

Reasoning

↓

Decision

↓

Report
```

方便：

调试。

Replay。

审计。

---

# 2.16 Runtime Constraints

Task Runtime：

禁止：

直接：

调用：

Provider。

禁止：

构建：

Prompt。

禁止：

实现：

业务。

禁止：

调用：

LLM。

Runtime：

仅：

负责：

调度。

---

# 2.17 Runtime Extension

未来：

允许：

增加：

- Distributed Runtime
- Cloud Runtime
- Local Runtime
- Multi-Tenant Runtime
- HA Runtime

无需：

修改：

Service。

---

# 2.18 Summary

Task Runtime 是整个 FAOS 的唯一 Runtime。

所有任务均围绕 Task 生命周期运行。

Task Runtime 不实现业务，而是负责：

- 生命周期管理
- 调度
- 上下文管理
- 事件分发
- Trace
- Metrics

其它所有能力均通过 Service 提供。

Task Runtime 与 Service 解耦，是整个系统稳定演进的基础。

---

# Chapter 03 - Planner Pipeline

> Financial Agent Operating System (FAOS)
>
> Version: V5.0
>
> Status: Architecture Frozen

---

# 3. Planner Pipeline

## 3.1 Purpose

Planner Pipeline 是 FAOS 的智能规划中心。

它负责将用户请求转换为系统可以执行的 Execution Plan。

Planner 不负责执行任何业务逻辑。

Planner 不负责调用 Provider。

Planner 不负责调用 Skill。

Planner 不负责调用 LLM Tool。

Planner 唯一职责是：

> **把一个 Task 规划成可执行的 Execution Plan。**

---

# 3.2 Position

Planner 位于 Task Runtime 与 Execution Engine 之间。

```
User Request
      │
      ▼
Task Runtime
      │
      ▼
Planner Pipeline
      │
      ▼
Execution Plan
      │
      ▼
Execution Engine
```

Planner 输出的是"计划（Plan）"，而不是"结果（Result）"。

Execution Engine 才负责执行。

---

# 3.3 Responsibilities

Planner Pipeline 负责：

- Intent Recognition（意图识别）
- Entity Extraction（实体提取）
- Task Classification（任务分类）
- Domain Resolution（领域识别）
- Capability Planning（能力规划）
- Workflow Selection（工作流选择）
- Dependency Analysis（依赖分析）
- Parallelism Analysis（并行分析）
- Execution Plan Generation（执行计划生成）
- Cost Estimation（资源评估）

Planner 不负责：

- 获取数据
- 推理
- 访问 Provider
- 调用 Skill
- 调用 Workflow
- 生成报告

---

# 3.4 Planning Pipeline

整个规划流程如下：

```
User Request
      │
      ▼
Intent Recognition
      │
      ▼
Entity Extraction
      │
      ▼
Task Classification
      │
      ▼
Domain Resolution
      │
      ▼
Capability Planning
      │
      ▼
Workflow Selection
      │
      ▼
Dependency Analysis
      │
      ▼
Execution Plan
```

Planner 只产生 Plan。

---

# 3.5 Intent Recognition

第一步识别用户真正想完成的任务。

例如：

```
分析贵州茅台
```

Intent：

```
Analyze Stock
```

例如：

```
生成今天市场日报
```

Intent：

```
Generate Daily Report
```

Intent 不包含任何业务执行。

仅描述目标。

---

# 3.6 Entity Extraction

提取任务涉及的业务实体。

例如：

```
分析贵州茅台
```

得到：

```yaml
Entities

Stock:
  code: 600519
  market: CN

Date:
  latest

Language:
  zh-CN
```

Planner 不查询数据。

只识别对象。

---

# 3.7 Task Classification

Planner 根据 Intent 创建 Task。

例如：

```yaml
Task

type: ANALYZE_STOCK

priority: HIGH

interactive: true

requires_reasoning: true

requires_report: true
```

Task 是 Runtime 管理的核心对象。

---

# 3.8 Domain Resolution

确定属于哪个业务领域。

例如：

```
Analyze Stock
```

↓

```
Stock Domain
```

例如：

```
Analyze ETF
```

↓

```
ETF Domain
```

Domain 决定后续可用的 Capability。

---

# 3.9 Capability Planning

根据 Domain 选择所需 Capability。

例如：

```
Stock Domain
```

需要：

```
Realtime Quote

Financial Analysis

News Analysis

Valuation

Technical Analysis

Risk Analysis
```

Planner 只选择 Capability。

不知道 Skill。

---

# 3.10 Workflow Selection

Capability 可以由 Workflow 实现。

例如：

```
Analyze Stock Workflow
```

Workflow：

```
Quote

↓

Financial

↓

News

↓

Macro

↓

Valuation

↓

Risk

↓

Summary
```

Workflow 属于 Capability Service 管理。

---

# 3.11 Dependency Analysis

分析 Capability 之间的依赖关系。

例如：

```
Financial

↓

Valuation
```

必须先获得财务数据，再计算估值。

又例如：

```
Quote

News

Macro
```

三者互不依赖，可并行执行。

Planner 输出 DAG（有向无环图）供 Execution Engine 调度。

---

# 3.12 Parallel Planning

Planner 应识别可并行执行的节点，以提升整体效率。

例如：

```
             Analyze Stock
                    │
      ┌─────────────┼─────────────┐
      ▼             ▼             ▼
Realtime Quote   News Search   Macro Analysis
      │             │             │
      └──────┬──────┴──────┬──────┘
             ▼             ▼
       Financial Analysis
             │
             ▼
      Valuation Analysis
             │
             ▼
      Decision Generation
```

Execution Engine 根据 DAG 自动并行执行。

---

# 3.13 Execution Plan

Planner 最终输出 Execution Plan。

例如：

```yaml
Task:
  ANALYZE_STOCK

Domain:
  STOCK

Capabilities:

  - quote
  - financial
  - news
  - macro
  - valuation
  - risk

Workflow:

  AnalyzeStockWorkflow

Execution:

  parallel:
    - quote
    - news
    - macro

  sequential:
    - financial
    - valuation
    - risk

Report:
  markdown
```

Execution Plan 是 Planner 唯一输出。

---

# 3.14 Dynamic Planning

Planner 支持动态规划。

例如：

用户要求：

```
分析贵州茅台
```

Execution 过程中：

发现：

```
存在重大公告
```

Execution Engine 可请求 Planner：

重新规划。

新增：

```
Announcement Analysis

Policy Analysis
```

无需终止整个 Task。

---

# 3.15 Cost Estimation

Planner 在执行前预估资源消耗。

包括：

- Provider 数量
- LLM 调用次数
- Token 预算
- 并发数量
- 预计执行时间
- 成本估算

Execution Engine 可根据预算调整执行策略。

---

# 3.16 Failure Strategy

Planner 失败时：

Task Runtime：

可执行：

```
Retry Planner

↓

Fallback Planner

↓

Manual Rule Planner

↓

Task Failed
```

Planner 本身不执行恢复逻辑。

---

# 3.17 Design Principles

Planner 必须遵循：

- 无状态（Stateless）
- 不访问外部数据
- 不执行业务
- 不依赖 Provider
- 不依赖 Skill
- 不生成 Prompt
- 不直接调用 LLM Tool
- 输出确定性的 Execution Plan

Planner 是整个系统的"大脑"，但不是"执行者"。

---

# 3.18 Summary

Planner Pipeline 是 FAOS 的规划核心。

它负责把用户请求转换为标准化的 Execution Plan，并明确：

- Task 类型
- Domain
- Capability
- Workflow
- DAG
- 并行关系
- 执行顺序
- 资源预算

Execution Engine 根据该计划执行，Planner 不参与具体业务逻辑。

这一设计实现了"规划与执行分离"，是 FAOS 相较传统 LLM→Tool 架构的重要优势。

---

# Chapter 04 - Execution Engine

> Financial Agent Operating System (FAOS)
>
> Version: V5.0
>
> Status: Architecture Frozen

---

# 4. Execution Engine

## 4.1 Purpose

Execution Engine 是 FAOS 的执行中心。

Planner Pipeline 负责规划。

Execution Engine 负责执行。

Execution Engine 根据 Planner 输出的 Execution Plan，对整个 Task 进行调度、编排、重试、异常恢复和结果汇总。

Execution Engine 不负责：

- 业务逻辑
- 数据获取
- Prompt 构建
- LLM 推理
- 投资决策

Execution Engine 只负责：

> **按照 Execution Plan 正确、高效、可靠地执行整个任务。**

---

# 4.2 Position

Execution Engine 位于 Planner Pipeline 与各 Service 之间。

```
                  Task Runtime
                       │
                       ▼
               Planner Pipeline
                       │
                Execution Plan
                       │
                       ▼
               Execution Engine
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
Capability      Workflow      Event Dispatcher
        │
        ▼
Service Layer
```

Execution Engine 是所有 Service 的统一入口。

---

# 4.3 Responsibilities

Execution Engine 负责：

- Execution Plan 解析
- DAG 调度
- Dependency Resolution
- Parallel Scheduling
- Service Invocation
- Retry
- Timeout
- Circuit Breaker
- Event Publishing
- Result Collection
- Context Update
- Error Recovery

Execution Engine 不负责业务逻辑。

---

# 4.4 Execution Flow

执行流程如下：

```
Execution Plan
       │
       ▼
Plan Parser
       │
       ▼
Dependency Graph
       │
       ▼
Scheduler
       │
       ▼
Worker Pool
       │
       ▼
Service Invocation
       │
       ▼
Context Update
       │
       ▼
Next Node
```

直到整个 DAG 执行完成。

---

# 4.5 Plan Parsing

Execution Engine 首先解析 Execution Plan。

例如：

```yaml
Workflow:

AnalyzeStockWorkflow

Capabilities:

- quote
- news
- macro
- financial
- valuation
- decision
```

解析后构建执行图。

---

# 4.6 Dependency Graph

Execution Plan 被转换成 DAG。

例如：

```
                Analyze Stock
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
Realtime Quote     News        Macro
        │              │              │
        └──────┬───────┴──────┬───────┘
               ▼              ▼
          Financial Analysis
               │
               ▼
          Valuation
               │
               ▼
      Decision Strategy
               │
               ▼
           Report
```

Execution Engine 永远执行 DAG。

---

# 4.7 Scheduler

Scheduler 负责寻找：

所有 Ready Node。

例如：

```
Quote

News

Macro
```

没有依赖。

可以立即执行。

Financial：

必须等待：

Quote 完成。

Scheduler 自动处理。

---

# 4.8 Parallel Execution

Execution Engine 默认采用并行执行。

例如：

```
Quote

News

Macro
```

同时运行。

完成后：

Financial。

Execution Engine 自动决定并发。

无需 Workflow 编写者关心。

---

# 4.9 Service Invocation

Execution Engine 调用 Service。

例如：

```
Capability

↓

Workflow

↓

Skill

↓

Provider
```

Execution Engine 不关心：

Service 如何实现。

只关心：

输入。

输出。

状态。

---

# 4.10 Execution Context Update

每个节点完成后：

更新：

Execution Context。

例如：

Quote：

```
context.quote
```

News：

```
context.news
```

Financial：

```
context.financial
```

所有 Service：

共享：

Execution Context。

---

# 4.11 Event Publishing

Execution Engine：

自动发布事件。

例如：

```
NodeStarted

NodeCompleted

NodeFailed

NodeRetry

TaskProgress

TaskCompleted
```

任何 Service：

可以监听。

---

# 4.12 Retry Strategy

支持自动重试。

例如：

```
Retry Count

3
```

策略：

```
Fixed

Linear

Exponential

Custom
```

Provider：

超时。

自动重试。

---

# 4.13 Timeout

每个节点：

支持：

Timeout。

例如：

```
Quote

5s
```

超过：

Timeout。

Execution Engine：

自动：

取消。

Retry。

Fallback。

---

# 4.14 Failure Recovery

失败：

不意味着：

整个 Task 失败。

例如：

```
Yahoo

×

↓

EastMoney

↓

AkShare
```

Provider：

自动切换。

Workflow：

继续。

---

# 4.15 Circuit Breaker

Execution Engine：

维护：

Service Health。

例如：

```
AkShare

连续失败

10次
```

自动：

熔断。

短时间：

不再：

调用。

等待：

恢复。

---

# 4.16 Result Aggregation

Execution Engine：

统一：

聚合：

所有结果。

例如：

```
Quote

Financial

Macro

News

↓

Execution Context
```

Reasoning：

统一：

读取。

---

# 4.17 Execution Metrics

Execution Engine：

统计：

```
Execution Time

Success Rate

Retry

Provider Time

Skill Time

Workflow Time

Queue Time
```

全部：

写入：

Trace。

---

# 4.18 Design Principles

Execution Engine：

必须：

Stateless。

Execution Context：

保存：

全部状态。

Execution Engine：

只负责：

执行。

不负责：

业务。

---

# 4.19 Summary

Execution Engine 是整个 FAOS 的执行核心。

Planner 决定：

做什么。

Execution Engine 决定：

什么时候做。

如何做。

是否重试。

是否并发。

是否恢复。

Execution Engine 将 Execution Plan 转换为真正可执行的任务流，并保证整个 Task 稳定、高效地完成。

---

# Chapter 05 - Execution Context

> Financial Agent Operating System (FAOS)
>
> Version: V5.0
>
> Status: Architecture Frozen

---

# 5. Execution Context

## 5.1 Purpose

Execution Context 是整个 FAOS 的共享数据中心（Shared Runtime State）。

它贯穿 Task 的整个生命周期。

所有 Service：

- 不保存业务状态
- 不共享内部对象
- 不直接调用彼此

所有数据交换均通过 Execution Context 完成。

Execution Context 是整个系统唯一的数据共享对象。

---

# 5.2 Position

Execution Context 位于整个 Runtime 中心。

```
                    Task Runtime
                         │
                         ▼
                 Execution Context
                         │
    ┌──────────┬─────────┼──────────┬──────────┐
    ▼          ▼         ▼          ▼          ▼
Capability  Workflow  Provider  Knowledge  Reasoning
    │          │         │          │          │
    └──────────┴─────────┼──────────┴──────────┘
                         ▼
                Decision Service
                         │
                         ▼
                  Report Service
```

Execution Context 是所有 Service 的唯一共享对象。

---

# 5.3 Responsibilities

Execution Context 负责：

- 保存任务状态
- 保存 Provider 数据
- 保存 Workflow 输出
- 保存 Skill 输出
- 保存 LLM 推理结果
- 保存 Decision
- 保存 Report
- 保存 Trace
- 保存 Metrics
- 保存 Event

Execution Context 不负责：

- 数据获取
- 推理
- 调度
- 生命周期管理

这些由对应 Service 完成。

---

# 5.4 Design Principles

Execution Context 必须遵循以下原则：

## Single Source of Truth

整个 Task 期间：

所有共享数据只有一份。

禁止：

```
Skill A

保存一份 Quote
```

同时：

```
Skill B

再保存一份 Quote
```

所有数据：

统一保存：

Context。

---

## Immutable Result

已经完成的结果：

默认不可修改。

例如：

```
Quote

Financial

News
```

除非：

Execution Engine：

重新执行。

否则：

不能覆盖。

---

## Structured Data

Context：

禁止：

保存 Prompt。

禁止：

保存自然语言。

全部采用：

结构化数据。

例如：

```yaml
quote:

    symbol:

    price:

    volume:
```

而不是：

```
当前股价为……
```

---

## Context Sharing

所有 Service：

读取：

同一个 Context。

避免：

重复请求。

重复 Provider。

重复推理。

---

# 5.5 Context Structure

Execution Context 推荐结构如下：

```yaml
task:

request:

intent:

entities:

domain:

execution:

plan:

graph:

current_node:

completed_nodes:

failed_nodes:

variables:

provider:

knowledge:

workflow:

reasoning:

discussion:

reflection:

decision:

report:

events:

metrics:

trace:

cache:
```

Context 是整个 Runtime 的共享状态树。

---

# 5.6 Context Sections

Execution Context 可划分为多个逻辑区域。

```
Execution Context

├── Task
├── Request
├── Variables
├── Provider Data
├── Knowledge
├── Workflow State
├── Reasoning
├── Discussion
├── Reflection
├── Decision
├── Report
├── Metrics
├── Trace
└── Cache
```

每个 Service 只负责维护自己的区域。

---

# 5.7 Variables

Variables 保存执行过程中产生的变量。

例如：

```yaml
variables:

market:

CN

currency:

CNY

language:

zh-CN

analysis_date:

2026-07-15
```

Variables 可以被所有 Service 使用。

---

# 5.8 Provider Data

所有 Provider 输出：

统一保存：

```yaml
provider:

quote:

financial:

macro:

news:

industry:

announcement:
```

Provider Service 不允许直接返回给 LLM。

必须先进入 Context。

---

# 5.9 Knowledge

Knowledge Service：

写入：

```yaml
knowledge:

industry_profile:

indicator_definition:

valuation_method:

prompt_template:

analysis_template:
```

Knowledge：

属于静态知识。

不是：

Memory。

---

# 5.10 Workflow State

Workflow：

执行状态。

例如：

```yaml
workflow:

current:

completed:

failed:

pending:
```

Execution Engine：

根据：

Workflow State：

继续执行。

---

# 5.11 Reasoning Result

LLM：

输出：

统一保存：

```yaml
reasoning:

summary:

risks:

opportunities:

confidence:

references:
```

多个模型：

分别：

保存。

例如：

```yaml
reasoning:

deepseek:

claude:

gemini:
```

避免：

覆盖。

---

# 5.12 Discussion

Discussion Service：

保存：

多 Expert。

例如：

```yaml
discussion:

fundamental:

technical:

macro:

risk:

consensus:
```

所有观点：

全部保留。

方便：

Trace。

---

# 5.13 Reflection

Reflection：

保存：

第二轮。

例如：

```yaml
reflection:

issues:

verified:

hallucination:

revision:
```

Reflection：

不修改：

Reasoning。

生成：

新的：

Review。

---

# 5.14 Decision

Decision Service：

保存：

最终：

```yaml
decision:

score:

risk:

signal:

allocation:

position:

confidence:
```

Decision：

整个 Task：

只有：

一个。

---

# 5.15 Report

Report：

保存：

输出。

例如：

```yaml
report:

markdown:

json:

html:

pdf:
```

Report Service：

负责：

生成。

Context：

负责：

保存。

---

# 5.16 Metrics

统一：

统计：

```yaml
metrics:

execution_time:

provider_time:

llm_time:

reasoning_time:

workflow_time:

retry:

token:

cost:
```

方便：

Dashboard。

---

# 5.17 Trace

Trace：

完整记录：

```yaml
trace:

planner:

execution:

provider:

workflow:

reasoning:

decision:

report:
```

用于：

Replay。

Debug。

Audit。

---

# 5.18 Cache

Execution Context：

允许：

短生命周期缓存。

例如：

```
Quote

Financial

Embedding

Prompt
```

Task 完成：

Cache：

自动：

释放。

长期缓存：

由 Knowledge Service 或 Provider Service 管理。

---

# 5.19 Lifecycle

Execution Context 生命周期：

```
Create

↓

Initialize

↓

Update

↓

Share

↓

Persist

↓

Archive

↓

Destroy
```

Task Runtime：

负责：

生命周期。

Execution Context：

不自行管理。

---

# 5.20 Design Constraints

Execution Context 必须遵循：

- 唯一共享状态
- 结构化数据
- 不保存业务逻辑
- 不保存 Service 实例
- 不保存数据库连接
- 不保存 Provider Client
- 不保存 LLM Client
- 不保存临时对象引用

Context 仅保存：

**数据（Data）**。

---

# 5.21 Best Practices

推荐：

✅ 所有 Service：

只读：

Context。

通过：

Execution Engine：

统一：

提交更新。

避免：

多个 Service：

同时修改：

Context。

推荐：

```
Service

↓

Context Patch

↓

Execution Engine

↓

Merge

↓

Context
```

而不是：

```
Service

↓

Context

（直接修改）
```

这样：

Execution Engine：

可以：

统一：

控制：

- 冲突
- 回滚
- Trace
- Event

---

# 5.22 Summary

Execution Context 是 FAOS 最核心的数据对象。

整个系统：

只有一个共享状态。

所有 Service：

围绕：

Execution Context 工作。

Execution Context：

保证：

- 数据一致性
- 生命周期一致性
- Service 解耦
- Trace 可追踪
- Replay 可实现

它是整个 Task Runtime 的"共享内存"，也是连接 Planner、Execution Engine 与各 Service 的核心纽带。

---


# Chapter 06 - Domain Service

> Financial Agent Operating System (FAOS)
>
> Version: V5.0
>
> Status: Architecture Frozen

---

# 6. Domain Service

## 6.1 Purpose

Domain Service 是 FAOS 的业务领域中心（Business Domain Center）。

它负责定义系统支持的业务领域，并为每个领域提供统一的业务模型、能力注册、规则配置和扩展机制。

Domain 不实现具体业务。

Domain 不获取数据。

Domain 不调用 LLM。

Domain 的职责只有一个：

> **定义业务世界（Business World）。**

---

# 6.2 Position

Domain Service 位于 Capability Service 之上。

```
Task Runtime
      │
      ▼
Planner Pipeline
      │
      ▼
Execution Engine
      │
      ▼
Domain Service
      │
      ▼
Capability Service
      │
      ▼
Workflow Service
```

Planner 根据 Task 选择 Domain。

Execution Engine 根据 Domain 加载对应 Capability。

---

# 6.3 Responsibilities

Domain Service 负责：

- Domain 注册
- Domain 生命周期
- Domain Metadata
- Entity Definition
- Capability Mapping
- Domain Rule
- Domain Validation
- Domain Extension

Domain Service 不负责：

- Workflow
- Skill
- Provider
- Prompt
- Reasoning
- Decision

---

# 6.4 Why Domain Exists

金融系统天然存在多个不同领域。

例如：

```
股票

ETF

基金

债券

期货

期权

外汇

数字货币

宏观经济

行业研究
```

不同领域：

拥有：

不同：

- 数据源
- 指标
- Workflow
- Skill
- Knowledge
- Decision Rule

因此必须抽象 Domain。

---

# 6.5 Built-in Domains

FAOS 默认支持：

```
Stock

ETF

Fund

Bond

Future

Option

Crypto

Macro

Industry

Portfolio

Market

News
```

后续：

允许：

插件扩展。

---

# 6.6 Domain Object

每个 Domain 包含：

```yaml
Domain

id

name

version

description

supported_entities

capabilities

knowledge

workflow

decision_rule

metadata
```

Domain 是整个业务世界的入口。

---

# 6.7 Entity Definition

每个 Domain 定义自己的业务实体。

例如：

Stock Domain：

```yaml
Entity

Stock

code

market

exchange

industry

currency
```

ETF Domain：

```yaml
Entity

ETF

code

issuer

tracking_index

expense_ratio
```

Macro Domain：

```yaml
Entity

EconomicIndicator

country

indicator

period
```

---

# 6.8 Capability Mapping

Domain 决定：

允许使用哪些 Capability。

例如：

Stock：

```
Realtime Quote

Financial Analysis

News Analysis

Valuation

Risk

Technical
```

Macro：

```
Economic Calendar

GDP

PMI

CPI

Interest Rate
```

Planner：

通过：

Domain：

自动选择 Capability。

---

# 6.9 Workflow Mapping

Domain：

决定：

默认 Workflow。

例如：

Stock：

```
Analyze Stock Workflow
```

Portfolio：

```
Portfolio Workflow
```

Macro：

```
Macro Workflow
```

Workflow：

可以：

覆盖。

---

# 6.10 Knowledge Mapping

每个 Domain：

绑定：

自己的 Knowledge。

例如：

Stock：

```
财务指标

估值方法

行业分类

上市规则
```

Macro：

```
经济指标

央行政策

货币理论
```

Knowledge Service：

根据：

Domain：

自动加载。

---

# 6.11 Decision Rule

每个 Domain：

拥有：

自己的 Decision Rule。

例如：

Stock：

```
Buy

Hold

Sell
```

Portfolio：

```
Increase

Reduce

Rebalance
```

Macro：

```
Bull

Neutral

Bear
```

Decision Service：

读取：

Domain Rule。

---

# 6.12 Domain Metadata

每个 Domain：

包含：

```yaml
metadata

icon

color

risk_level

market

language

timezone
```

方便：

UI。

API。

Report。

---

# 6.13 Domain Registry

Domain Service：

维护：

Registry。

例如：

```
Stock

↓

StockDomain
```

```
ETF

↓

ETFDomain
```

Planner：

只访问：

Registry。

不直接创建 Domain。

---

# 6.14 Domain Extension

新增 Domain：

无需修改 Runtime。

例如：

```
Commodity

REIT

Carbon

AI Industry

ESG
```

实现：

Domain Plugin：

即可。

---

# 6.15 Validation

Domain：

负责：

校验：

Entity。

例如：

```
600519
```

合法：

Stock。

```
BTCUSDT
```

合法：

Crypto。

```
GDP
```

合法：

Macro。

非法 Entity：

直接返回 Planner。

---

# 6.16 Domain Isolation

不同 Domain：

完全隔离。

例如：

Stock：

不会：

调用：

Crypto Workflow。

ETF：

不会：

加载：

Bond Knowledge。

降低：

耦合。

---

# 6.17 Multi-Domain Task

一个 Task：

允许：

多个 Domain。

例如：

```
分析黄金上涨

对紫金矿业影响
```

Planner：

得到：

```
Macro

+

Commodity

+

Stock
```

Execution Engine：

自动：

协调：

多个 Domain。

---

# 6.18 Plugin Architecture

Domain：

采用：

插件机制。

例如：

```
domains/

stock/

macro/

crypto/

portfolio/
```

Runtime：

自动发现。

自动注册。

无需修改核心代码。

---

# 6.19 Design Principles

Domain 必须遵循：

- 不访问 Provider
- 不调用 Skill
- 不调用 Workflow
- 不保存状态
- 不依赖 LLM
- 不实现分析逻辑

Domain：

只定义：

业务边界。

---

# 6.20 Summary

Domain Service 是 FAOS 的业务领域中心。

它定义：

- 业务实体
- 能力范围
- 默认 Workflow
- 知识体系
- 决策规则

Planner 根据 Domain 完成规划。

Execution Engine 根据 Domain 加载能力。

整个系统通过 Domain 实现不同金融领域之间的统一管理与隔离。

增加一个 Domain Profile 概念，但不要新增 Service。

也就是每个 Domain 不只是一个配置，而是一份完整的 Profile

StockDomain:

supported_entities:

supported_capabilities:

default_workflow:

provider_priority:

knowledge_pack:

reasoning_strategy:

decision_policy:

report_template:

Planner 不需要写死规则；
Capability 不需要写 if-else；
新增一个 Domain 只需增加一个 Profile 即可。


# Chapter 07 - Capability Service

> Financial Agent Operating System (FAOS)
>
> Version: V5.0
>
> Status: Architecture Frozen

---

# 7. Capability Service

## 7.1 Purpose

Capability Service 是 FAOS 的能力中心（Capability Center）。

它负责定义系统能够提供的所有分析能力，并建立 Domain、Workflow、Skill 之间的桥梁。

Capability 是整个系统最重要的业务抽象。

Planner 永远规划 Capability。

Execution Engine 永远执行 Capability。

Workflow 永远组合 Capability。

Skill 永远实现 Capability。

因此：

> **Capability 是整个系统的标准能力接口。**

---

# 7.2 Position

Capability Service 位于 Domain Service 与 Workflow Service 之间。

```
                Domain Service
                       │
                       ▼
              Capability Service
                       │
                       ▼
               Workflow Service
                       │
                       ▼
                  Skill Service
```

Capability 是 Domain 与 Workflow 之间的桥梁。

---

# 7.3 Responsibilities

Capability Service 负责：

- Capability Registry
- Capability Discovery
- Capability Metadata
- Capability Validation
- Capability Dependency
- Capability Version
- Capability Policy
- Capability Permission

Capability Service 不负责：

- 数据获取
- Workflow 编排
- Skill 执行
- LLM 推理
- Provider 调用

---

# 7.4 Why Capability

Capability 是系统能力，而不是业务实现。

例如：

```
获取实时行情
```

属于：

```
Realtime Quote
```

Capability。

而不是：

```
AkShare

EastMoney

Yahoo
```

Provider。

Planner 永远不知道：

Provider。

Planner 只知道：

Capability。

---

# 7.5 Capability Hierarchy

Capability 可以划分多个层级。

```
Financial Analysis

├── Income Statement
├── Balance Sheet
├── Cash Flow
└── Financial Ratio
```

```
News Analysis

├── Search
├── Summarize
├── Sentiment
└── Impact
```

Planner 可以规划：

父 Capability。

Execution Engine：

自动展开。

---

# 7.6 Capability Object

Capability 定义如下：

```yaml
Capability

id

name

version

description

domain

input_schema

output_schema

dependencies

workflow

metadata
```

Capability 是一个标准接口。

---

# 7.7 Capability Categories

FAOS 内置以下能力分类。

## Market Capability

例如：

- Realtime Quote
- Historical Quote
- Tick Data
- Capital Flow

---

## Financial Capability

例如：

- Financial Statement
- Financial Ratio
- Cash Flow
- ROE
- ROIC

---

## Valuation Capability

例如：

- PE
- PB
- EV/EBITDA
- DCF
- PEG

---

## Technical Capability

例如：

- MA
- MACD
- RSI
- KDJ
- Bollinger Band

---

## News Capability

例如：

- News Search
- Announcement
- Sentiment
- Hot Topic

---

## Macro Capability

例如：

- GDP
- CPI
- PMI
- Interest Rate
- Exchange Rate

---

## Portfolio Capability

例如：

- Position Analysis
- Correlation
- Diversification
- Risk Exposure

---

## Strategy Capability

例如：

- Signal Generation
- Backtesting
- Screening
- Portfolio Optimization

---

## Report Capability

例如：

- Markdown
- PDF
- HTML
- Dashboard

---

# 7.8 Capability Registry

所有 Capability：

统一注册。

例如：

```yaml
RealtimeQuote

↓

QuoteCapability

FinancialRatio

↓

FinancialCapability

NewsSearch

↓

NewsCapability
```

Planner：

统一查询 Registry。

---

# 7.9 Capability Metadata

Capability 保存：

```yaml
metadata

category

version

owner

timeout

cost

parallel

cacheable

requires_reasoning

requires_provider
```

Execution Engine：

根据 Metadata：

决定执行策略。

---

# 7.10 Capability Dependency

Capability 可以依赖其它 Capability。

例如：

```
Valuation

↓

Financial Statement
```

必须先执行：

Financial。

Planner：

自动生成 DAG。

---

# 7.11 Capability Input

Capability 定义统一输入。

例如：

```yaml
Input

Entity

Context

Parameters

Knowledge

Variables
```

Execution Engine：

负责：

构造输入。

Workflow：

无需关心。

---

# 7.12 Capability Output

Capability 输出统一结构。

```yaml
Output

status

data

metrics

trace

artifacts

events
```

Execution Engine：

统一写入：

Execution Context。

---

# 7.13 Capability Policy

每个 Capability：

可以定义：

执行策略。

例如：

```yaml
Policy

timeout

retry

fallback

parallel

priority

cache

budget
```

Execution Policy：

自动读取。

---

# 7.14 Capability Discovery

Planner：

根据：

Task。

自动发现：

Capability。

例如：

```
Analyze Stock
```

得到：

```
Quote

Financial

News

Risk

Valuation
```

Planner：

无需：

知道 Workflow。

---

# 7.15 Capability Version

Capability：

支持版本。

例如：

```
Financial Capability

v1

v2

v3
```

Workflow：

可绑定：

固定版本。

方便：

升级。

---

# 7.16 Capability Permission

Capability：

支持权限。

例如：

```
Realtime Quote

↓

Everyone
```

```
Trading Signal

↓

Premium
```

```
Order Execution

↓

Admin
```

方便：

SaaS。

---

# 7.17 Capability Extension

新增 Capability：

无需修改 Runtime。

例如：

新增：

```
ESG Analysis
```

只需要：

```
Register

↓

Workflow

↓

Skill
```

Planner：

自动：

发现。

---

# 7.18 Capability Lifecycle

Capability 生命周期：

```
Register

↓

Enable

↓

Discover

↓

Execute

↓

Deprecate

↓

Remove
```

Capability：

始终：

保持：

Stateless。

---

# 7.19 Design Principles

Capability 必须遵循：

- 与 Provider 解耦
- 与 Skill 解耦
- 与 LLM 解耦
- 与 Workflow 解耦
- 可组合
- 可发现
- 可扩展
- 可版本化

Capability 描述的是：

"系统能做什么"。

而不是：

"系统怎么做"。

---

# 7.20 Relationship with Other Services

Capability 与其它模块关系如下：

```
Task
 │
 ▼
Planner
 │
 ▼
Capability
 │
 ▼
Workflow
 │
 ▼
Skill
 │
 ▼
Provider
```

Planner：

只关心：

Capability。

Skill：

只负责：

实现。

---

# 7.21 Best Practices

推荐：

一个 Capability：

只完成：

一个明确目标。

例如：

推荐：

```
Realtime Quote
```

而不是：

```
Quote + Financial + News
```

保持：

Capability：

原子化（Atomic）。

Workflow：

负责：

组合。

---

在 Capability Service 内部增加一个 Capability Manifest 规范（不是新增 Service）。

每个 Capability 都携带一份 Manifest，例如：
id: realtime_quote

name: Realtime Quote

domain:
  - stock
  - etf

inputs:
  - entity

outputs:
  - quote

requires:
  - market_open

workflow:
  QuoteWorkflow

policies:
  timeout: 5s
  retry: 2
  cache: 10s

reasoning: false

provider:
  preferred:
    - eastmoney
    - akshare

这样 Planner、Execution Engine 和 Workflow 都可以依赖 Manifest 自动工作，而不是写大量硬编码逻辑

# 7.22 Summary

Capability Service 是 FAOS 的能力中心。

它定义系统"能够做什么"，并作为 Planner、Workflow 与 Skill 之间的标准接口。

通过统一的 Capability 抽象，系统可以在不修改 Planner 和 Runtime 的前提下，持续扩展新的业务能力，实现真正的插件化架构。

---



# Chapter 08 - Workflow Service

> Financial Agent Operating System (FAOS)
>
> Version: V5.0
>
> Status: Architecture Frozen

---

# 8. Workflow Service

## 8.1 Purpose

Workflow Service 是 FAOS 的业务编排中心（Business Orchestration Center）。

Workflow 的职责不是实现业务。

Workflow 的职责也不是获取数据。

Workflow 的职责更不是调用 LLM。

Workflow 的唯一职责是：

> **按照业务目标，将多个 Capability 组织成完整的业务流程。**

Workflow 是业务流程。

Capability 是业务能力。

Skill 是能力实现。

Provider 是数据来源。

四者职责完全不同。

---

# 8.2 Position

Workflow Service 位于 Capability Service 与 Skill Service 之间。

```
Task Runtime
      │
      ▼
Planner Pipeline
      │
      ▼
Execution Engine
      │
      ▼
Capability Service
      │
      ▼
Workflow Service
      │
      ▼
Skill Service
```

Workflow 是业务编排层。

Skill 是执行层。

---

# 8.3 Responsibilities

Workflow Service 负责：

- Workflow Registry
- Workflow Discovery
- Workflow Composition
- Capability Orchestration
- Execution Sequence
- Workflow Version
- Workflow Policy
- Workflow Validation

Workflow 不负责：

- Provider
- Prompt
- LLM
- 数据获取
- 推理
- 决策

Workflow 只负责：

业务流程。

---

# 8.4 Why Workflow

Capability 是原子能力。

Workflow 是业务流程。

例如：

```
股票分析
```

不是一个 Capability。

而是：

```
Realtime Quote

↓

Financial Analysis

↓

News Analysis

↓

Valuation

↓

Risk Analysis

↓

Investment Decision

↓

Report
```

Workflow 就是：

多个 Capability 的组合。

---

# 8.5 Workflow Object

Workflow 定义如下：

```yaml
Workflow

id

name

version

description

domain

supported_tasks

capabilities

entry

exit

policy

metadata
```

Workflow 描述：

业务流程。

---

# 8.6 Workflow Registry

所有 Workflow：

统一注册。

例如：

```
AnalyzeStockWorkflow

PortfolioWorkflow

MacroWorkflow

DailyReportWorkflow

MarketMonitorWorkflow

BacktestWorkflow
```

Planner：

根据：

Capability：

选择：

Workflow。

---

# 8.7 Workflow Composition

Workflow：

由多个 Capability 构成。

例如：

```
Analyze Stock

├── Quote
├── Financial
├── News
├── Macro
├── Valuation
├── Technical
├── Risk
└── Decision
```

Workflow：

不关心：

Skill。

---

# 8.8 Workflow Structure

Workflow 推荐采用 DAG 描述。

例如：

```
                  Analyze Stock

                         │

      ┌──────────────────┼──────────────────┐

      ▼                  ▼                  ▼

Realtime Quote       News Search      Macro Analysis

      │                  │                  │

      └──────────────┬───┴──────────────────┘

                     ▼

            Financial Analysis

                     │

                     ▼

            Valuation Analysis

                     │

                     ▼

               Risk Analysis

                     │

                     ▼

         Decision & Strategy

                     │

                     ▼

                 Report
```

Execution Engine：

自动执行。

---

# 8.9 Workflow Lifecycle

Workflow 生命周期：

```
Register

↓

Load

↓

Validate

↓

Execute

↓

Complete

↓

Archive
```

Workflow：

始终保持：

Stateless。

---

# 8.10 Workflow Metadata

每个 Workflow：

包含：

```yaml
metadata

domain

priority

estimated_cost

estimated_time

parallel

retry

timeout

version

owner
```

Execution Engine：

自动读取。

---

# 8.11 Workflow Policy

Workflow 可以定义：

执行策略。

例如：

```yaml
Policy

retry

parallel

timeout

provider_strategy

reasoning_strategy

decision_strategy
```

Execution Engine：

负责：

执行。

---

# 8.12 Workflow Inputs

Workflow 输入：

统一采用：

```yaml
Input

Task

Execution Context

Capability List

Parameters
```

Workflow：

不直接解析：

Request。

---

# 8.13 Workflow Outputs

Workflow 输出：

统一：

```yaml
Output

Artifacts

Execution Result

Metrics

Trace

Events
```

Execution Engine：

写入：

Execution Context。

---

# 8.14 Workflow Templates

FAOS 提供标准 Workflow。

例如：

```
AnalyzeStockWorkflow

AnalyzeETFWorkflow

AnalyzePortfolioWorkflow

AnalyzeMacroWorkflow

GenerateReportWorkflow

ScreenStockWorkflow

MonitorWorkflow

BacktestWorkflow
```

开发者：

可以：

继承。

扩展。

---

# 8.15 Conditional Workflow

Workflow 支持条件分支。

例如：

```
IF

Market == CN

↓

Use AShare Workflow

ELSE

↓

Use US Workflow
```

或者：

```
IF

重大公告存在

↓

Announcement Workflow

ELSE

↓

Skip
```

Execution Engine：

负责：

条件判断。

---

# 8.16 Dynamic Workflow

Workflow 可以动态扩展。

例如：

分析过程中：

发现：

```
重大资产重组
```

Execution Engine：

请求：

Planner。

新增：

```
Announcement Analysis

Corporate Governance Analysis
```

无需：

终止 Task。

---

# 8.17 Nested Workflow

Workflow 支持嵌套。

例如：

```
Portfolio Workflow

├── Analyze Stock Workflow
├── Analyze ETF Workflow
├── Risk Workflow
└── Allocation Workflow
```

Execution Engine：

自动展开。

---

# 8.18 Workflow Reuse

Workflow 应尽可能复用。

例如：

```
Realtime Quote Workflow
```

可以用于：

- 股票分析
- ETF 分析
- 行业分析
- 回测
- 风险分析

避免：

重复开发。

---

# 8.19 Workflow Validation

Workflow 加载时：

自动校验：

- Capability 是否存在
- Capability 是否兼容
- Domain 是否支持
- Version 是否正确
- Policy 是否合法

非法 Workflow：

禁止执行。

---

# 8.20 Workflow Version

Workflow 支持版本管理。

例如：

```
AnalyzeStockWorkflow

v1

v2

v3
```

Task 可以绑定：

指定版本。

方便：

灰度升级。

---

# 8.21 Workflow Extension

新增 Workflow：

无需修改 Runtime。

例如：

```
Dividend Workflow

ESG Workflow

Carbon Workflow

IPO Workflow
```

注册即可。

Planner：

自动发现。

---

# 8.22 Relationship with Other Services

Workflow 与其它模块关系如下：

```
Domain

↓

Capability

↓

Workflow

↓

Skill

↓

Provider
```

Workflow：

负责：

组织。

Skill：

负责：

实现。

---

# 8.23 Best Practices

建议：

一个 Workflow：

只负责：

一个业务目标。

例如：

推荐：

```
Analyze Stock Workflow
```

而不是：

```
Analyze Stock

+

Portfolio

+

Macro

+

Trading
```

Workflow：

应该保持：

高内聚。

低耦合。

---

# 8.24 Workflow vs Capability vs Skill

三者职责必须严格区分。

| Module | Responsibility |
|----------|---------------|
| Capability | 系统能做什么 |
| Workflow | 如何组织这些能力 |
| Skill | 如何具体实现能力 |

例如：

```
Capability

↓

Financial Analysis

Workflow

↓

Analyze Stock Workflow

Skill

↓

AShare Financial Skill
```

Planner：

永远规划：

Capability。

Workflow：

永远组织：

Capability。

Skill：

永远实现：

Capability。

---

# 8.25 Declarative Workflow

FAOS 推荐：

Workflow 全部采用声明式定义。

例如：

```yaml
workflow:

AnalyzeStock

steps:

- capability: realtime_quote

- capability: financial_analysis

- capability: news_analysis

- capability: valuation

- capability: decision

parallel:

- realtime_quote

- news_analysis

dependencies:

financial_analysis:

- realtime_quote

valuation:

- financial_analysis
```

Execution Engine：

负责解释。

Workflow：

不包含业务代码。

---

增加一个 Workflow Manifest（仍属于 Workflow Service 内部，不新增核心分层）。

因为你的 Workflow 将来会越来越复杂（股票、ETF、基金、行业、投资组合、多 Agent），如果全部写 Python，会越来越难维护。

建议每个 Workflow 都有一个 workflow.yaml

id: analyze_stock

version: 1.0

domain: stock

entry:
  capability: realtime_quote

steps:
  - capability: financial_analysis
  - capability: news_analysis
  - capability: valuation

decision:
  capability: investment_decision

report:
  capability: markdown_report

Execution Engine 负责解释 YAML 并执行，这样新增一个 Workflow 基本只需要新增配置，无需修改 Runtime

# 8.26 Summary

Workflow Service 是 FAOS 的业务编排中心。

它负责将多个 Capability 组合成完整的业务流程。

Workflow 不实现业务。

Skill 不组织流程。

Provider 不关心业务。

Planner 不关心实现。

通过 Workflow，系统能够以声明式方式构建复杂分析流程，实现业务逻辑与执行逻辑彻底分离，为复杂金融分析、多 Agent 协作和未来插件扩展提供统一编排能力。

---



# Chapter 09 - Skill Service

> Financial Agent Operating System (FAOS)
>
> Version: V5.0
>
> Status: Architecture Frozen

---

# 9. Skill Service

## 9.1 Purpose

Skill Service 是 FAOS 的业务实现中心（Business Implementation Center）。

Skill 是 Capability 的具体实现。

Workflow 定义业务流程。

Capability 定义系统能力。

Skill 则真正完成能力的执行。

Skill 是整个系统中唯一允许实现业务逻辑的模块。

> **Workflow 决定做什么。**
>
> **Skill 决定怎么做。**

---

# 9.2 Position

Skill Service 位于 Workflow Service 与 Provider Service 之间。

```
Planner Pipeline
        │
        ▼
Capability Service
        │
        ▼
Workflow Service
        │
        ▼
Skill Service
        │
        ▼
Provider Service
```

Skill 是业务逻辑的实现层。

---

# 9.3 Responsibilities

Skill Service 负责：

- Skill Registry
- Skill Discovery
- Skill Loading
- Skill Execution
- Skill Version
- Skill Validation
- Skill Sandbox
- Skill Plugin

Skill Service 不负责：

- Task 调度
- Workflow 编排
- Provider 路由
- LLM 管理
- Report 输出

---

# 9.4 What is a Skill

Skill 是一个可复用、可测试、可独立部署的业务模块。

例如：

```
AShare Quote Skill

US Quote Skill

Financial Statement Skill

Dividend Skill

Industry Analysis Skill

Macro Indicator Skill

News Summarizer Skill
```

Skill 完成一个明确业务目标。

---

# 9.5 Skill Object

Skill 定义如下：

```yaml
Skill

id

name

version

description

domain

capability

inputs

outputs

policies

metadata
```

Skill 是 Capability 的具体实现。

---

# 9.6 Skill Registry

所有 Skill：

统一注册。

例如：

```
stock.quote

↓

AShareQuoteSkill

stock.financial

↓

FinancialStatementSkill

macro.gdp

↓

GDPAnalysisSkill
```

Execution Engine：

通过 Registry：

加载 Skill。

---

# 9.7 Skill Lifecycle

Skill 生命周期：

```
Register

↓

Load

↓

Initialize

↓

Execute

↓

Complete

↓

Unload
```

Skill 默认保持无状态（Stateless）。

---

# 9.8 Skill Categories

FAOS 推荐将 Skill 分类管理。

例如：

## Market Skills

- AShare Quote
- HK Quote
- US Quote
- Futures Quote

---

## Financial Skills

- Income Statement
- Balance Sheet
- Cash Flow
- Financial Ratio

---

## News Skills

- News Search
- Announcement Parser
- Sentiment Analysis

---

## Macro Skills

- GDP
- CPI
- PMI
- Interest Rate

---

## Strategy Skills

- Screening
- Backtesting
- Signal Generation

---

## Report Skills

- Markdown Report
- PDF Report
- Dashboard Report

---

# 9.9 Skill Manifest

每个 Skill 必须提供 Manifest。

例如：

```yaml
id: financial_statement

version: 1.0

domain:
  - stock

capability:
  financial_analysis

inputs:
  - entity
  - context

outputs:
  - financial

provider:
  - eastmoney
  - akshare

reasoning:
  false

cache:
  1d

timeout:
  10s
```

Manifest 是 Skill 的标准描述。

---

# 9.10 Skill Inputs

Skill 输入统一来自 Execution Context。

例如：

```yaml
Input

Entity

Context

Knowledge

Parameters

Variables
```

Skill 不直接解析用户请求。

---

# 9.11 Skill Outputs

Skill 输出统一结构。

```yaml
Output

status

data

artifacts

metrics

events

trace
```

Execution Engine：

负责写入 Context。

---

# 9.12 Skill Implementation

Skill 可以采用不同实现方式。

例如：

### Native

```text
Python

Go

Rust
```

---

### Script

```text
Python Script

Shell

Node.js
```

---

### MCP

```text
Filesystem MCP

GitHub MCP

Browser MCP

Database MCP
```

---

### External Service

```text
REST API

gRPC

HTTP Service
```

FAOS 不限制实现语言。

只要求遵循 Skill 接口规范。

---

# 9.13 Skill Sandbox

Skill 必须运行在隔离环境。

例如：

```
Docker

Virtual Environment

Container

Remote Worker
```

Skill 不允许影响 Runtime。

---

# 9.14 Skill Policies

每个 Skill 可以定义：

```yaml
timeout

retry

cache

parallel

priority

fallback

budget
```

Execution Policy 自动读取。

---

# 9.15 Skill Dependency

Skill 可以依赖其它 Skill。

例如：

```
Valuation Skill

↓

Financial Statement Skill
```

但推荐依赖 Capability，而不是直接依赖具体 Skill。

Execution Engine 根据 Capability 解析最终 Skill。

---

# 9.16 Skill Discovery

Execution Engine：

根据：

Capability：

自动发现 Skill。

例如：

```
Capability

↓

Financial Analysis

↓

Financial Statement Skill
```

Skill 可动态替换。

---

# 9.17 Skill Version

Skill 支持版本。

例如：

```
Financial Skill

v1

v2

v3
```

Workflow 可指定版本。

支持灰度发布。

---

# 9.18 Skill Plugin

Skill 支持插件化。

目录建议：

```
skills/

stock/

macro/

portfolio/

report/
```

Runtime 自动发现。

无需修改核心代码。

---

# 9.19 Skill Isolation

Skill 之间禁止直接调用。

例如：

禁止：

```
News Skill

↓

Financial Skill
```

正确方式：

```
News Skill

↓

Execution Context

↓

Execution Engine

↓

Financial Skill
```

通过 Context 共享数据。

避免强耦合。

---

# 9.20 Skill vs Provider

Skill：

负责业务。

例如：

```
计算 ROE

分析财报

识别风险
```

Provider：

负责数据。

例如：

```
EastMoney

AkShare

Yahoo Finance
```

Skill 不负责数据来源。

---

# 9.21 Skill vs LLM

LLM 不是 Skill。

LLM 是 Reasoning Service 的资源。

Skill 可以：

请求：

Reasoning Service。

例如：

```
News Summary Skill

↓

Reasoning Service

↓

LLM
```

Skill 不直接调用具体模型。

---

# 9.22 Skill Development Principles

所有 Skill 必须遵循：

- 单一职责
- 无状态
- 可测试
- 可复用
- 可版本化
- 可插件化
- 与 Provider 解耦
- 与 Workflow 解耦
- 与 LLM 解耦

---

# 9.23 Example

股票分析：

```
Workflow

↓

Financial Capability

↓

Financial Statement Skill

↓

Provider

↓

EastMoney

↓

Execution Context

↓

Reasoning Service

↓

Decision
```

Skill 永远只是其中一个执行节点。

---

# 9.24 Best Practices

推荐：

一个 Skill：

只完成：

一个业务目标。

例如：

推荐：

```
Financial Statement Skill
```

不要：

```
Financial

+

News

+

Macro

+

Report
```

保持：

高内聚。

低耦合。

---

Skill Service 内部增加一个 Skill Descriptor（技能描述） 规范。

每个 Skill 不仅有 Manifest，还要有一份供 Planner 和 Reasoning Service 理解的描述，例如

Skill Service 内部增加一个 Skill Descriptor（技能描述） 规范。

每个 Skill 不仅有 Manifest，还要有一份供 Planner 和 Reasoning Service 理解的描述，例如
Planner 可以根据描述自动匹配 Skill。
Reasoning Service 可以构建 Skill Catalog，作为模型上下文的一部分。
将来支持 LLM 自动选择 Skill 时，不需要硬编码路由，而是根据 Skill Descriptor + Capability Manifest 自动规划


# 9.25 Summary

Skill Service 是 FAOS 的业务实现中心。

它实现 Capability 定义的业务能力，并通过统一接口与 Workflow、Provider、Reasoning Service 协作。

Skill 是整个系统唯一实现业务逻辑的模块，但不负责调度、不负责数据源管理、不直接依赖 LLM。

通过 Skill 插件化，FAOS 可以持续扩展新的金融分析能力，而无需修改 Task Runtime 或 Execution Engine。

---

# Chapter 10 - Provider Service

> Financial Agent Operating System (FAOS)
>
> Version: V5.0
>
> Status: Architecture Frozen

---

# 10. Provider Service

## 10.1 Purpose

Provider Service 是 FAOS 的统一数据访问中心（Unified Data Access Layer）。

Provider 的唯一职责：

> **负责从外部系统获取数据，并转换成 FAOS 标准数据模型。**

Provider 不负责：

- 业务分析
- Workflow
- Skill
- Prompt
- LLM
- Decision

Provider 只负责：

> 获取数据。

---

# 10.2 Position

Provider Service 位于 Skill Service 与 Data Route 之间。

```
Workflow

↓

Skill

↓

Provider Service

↓

Data Route

↓

External Providers
```

Provider 是系统访问外部世界的唯一入口。

---

# 10.3 Design Goals

Provider Service 的设计目标：

- 数据统一
- 数据标准化
- Provider 解耦
- 自动 Failover
- 自动 Cache
- 自动 Retry
- 自动 Validation
- 自动 Metrics
- 自动 Monitoring

---

# 10.4 Responsibilities

Provider Service 负责：

- Provider Registry
- Provider Discovery
- Provider Loading
- Provider Lifecycle
- Provider Health Check
- Provider Authentication
- Provider Normalization
- Provider Metrics
- Provider Validation

Provider 不负责：

- Provider 路由
- Provider 优先级
- Provider Failover
- Provider Cache

这些交由 Data Route。

---

# 10.5 Why Provider

FAOS 不允许 Skill 直接访问：

```
AkShare

EastMoney

Yahoo

Polygon

Wind

Tushare

REST API

MCP
```

否则：

Skill 将与数据源强耦合。

例如：

```
Financial Skill

↓

AkShare
```

未来：

切换：

EastMoney。

整个 Skill：

必须修改。

这是禁止的。

---

# 10.6 Provider Object

Provider 定义：

```yaml
Provider

id

name

version

description

category

supported_entities

supported_markets

supported_capabilities

authentication

rate_limit

metadata
```

---

# 10.7 Provider Categories

Provider 可划分：

## Market Provider

例如：

- EastMoney
- Yahoo Finance
- Polygon
- Alpaca

---

## Financial Provider

例如：

- AkShare
- EastMoney
- Alpha Vantage

---

## News Provider

例如：

- Google News
- NewsAPI
- GDELT
- RSS

---

## Macro Provider

例如：

- FRED
- World Bank
- IMF

---

## Knowledge Provider

例如：

- RAG
- Vector DB
- Knowledge Base

---

## MCP Provider

例如：

Filesystem

GitHub

Browser

Database

Search

---

## Custom Provider

企业内部：

REST API

Database

RPC

---

# 10.8 Provider Registry

所有 Provider：

统一注册。

例如：

```
eastmoney

↓

EastMoneyProvider

akshare

↓

AkShareProvider

fred

↓

FREDProvider
```

Execution Engine：

永远访问 Registry。

---

# 10.9 Provider Manifest

每个 Provider：

提供：

Manifest。

例如：

```yaml
id: eastmoney

category: market

market:

CN

capabilities:

- realtime_quote
- financial
- announcement

priority:

100

timeout:

5s

retry:

2

cache:

10s
```

Planner：

不会读取。

Data Route：

会读取。

---

# 10.10 Standard Data Model

所有 Provider：

必须返回：

统一模型。

例如：

Quote：

```yaml
Quote

symbol

market

price

change

volume

timestamp

source
```

禁止：

不同 Provider：

返回：

不同字段。

---

# 10.11 Provider Adapter

每个 Provider：

负责：

Adapter。

例如：

```
EastMoney JSON

↓

Provider Adapter

↓

Standard Quote
```

Skill 永远读取：

Standard Model。

---

# 10.12 Authentication

Provider：

统一认证。

例如：

```
API Key

OAuth

JWT

Cookie

Anonymous
```

Skill：

不知道：

认证方式。

---

# 10.13 Health Check

Provider：

持续：

健康检查。

例如：

```
Latency

Availability

Success Rate

Error Rate
```

Data Route：

自动：

调整：

优先级。

---

# 10.14 Provider Lifecycle

生命周期：

```
Register

↓

Initialize

↓

Authenticate

↓

Ready

↓

Serving

↓

Degraded

↓

Offline

↓

Removed
```

---

# 10.15 Validation

所有 Provider：

输出：

统一校验。

例如：

```
Required Fields

Schema

Type

Range

Timestamp
```

非法数据：

禁止：

进入：

Execution Context。

---

# 10.16 Metrics

Provider：

自动统计：

```
Latency

Availability

Request Count

Error Count

Success Rate

Cost

Bandwidth
```

Metrics：

进入：

Trace。

---

# 10.17 Retry

Provider：

失败：

Execution Engine：

按照：

Execution Policy：

自动：

Retry。

Provider：

无需：

实现：

Retry。

---

# 10.18 Security

Provider：

必须：

遵循：

- API Key 加密
- Secret 隔离
- HTTPS
- TLS
- Rate Limit
- Audit Log

禁止：

Skill：

保存：

Secret。

---

# 10.19 Plugin

新增 Provider：

无需修改 Runtime。

例如：

```
providers/

eastmoney/

akshare/

polygon/

fred/

newsapi/
```

自动注册。

---

# 10.20 Provider Isolation

不同 Provider：

互相独立。

例如：

```
Yahoo

×

不会影响

EastMoney
```

每个 Provider：

独立部署。

独立升级。

---

# 10.21 Provider Version

支持：

```
v1

v2

v3
```

Skill：

无需升级。

Data Route：

自动适配。

---

# 10.22 Best Practices

推荐：

一个 Provider：

只负责：

一个系统。

例如：

```
EastMoney Provider
```

不要：

```
EastMoney

+

Yahoo

+

Polygon
```

Provider：

保持：

单一职责。

---

Provider 不直接代表数据源，而代表一种数据能力（Data Connector）

例如：

EastMoney

不是一个 Provider。

而是：EastMoney Connector

真正的 Provider 应该是：

Market Quote Provider

↓

EastMoney Connector

AkShare Connector

Yahoo Connector

也就是说：
Skill
      │
      ▼
Market Quote Provider
      │
      ▼
Data Route
      │
 ┌────┼────────────┐
 ▼    ▼            ▼
EastMoney   AkShare   Yahoo

这样做的好处：

一个 Provider 可以聚合多个 Connector。
Data Route 不再直接路由到第三方，而是路由到 Connector。
后续增加 MCP、WebSearch、SQL、Kafka 等，都可以统一看作 Connector。

# 10.23 Summary

Provider Service 是 FAOS 的统一数据访问中心。

它屏蔽所有外部数据源差异，为 Skill 提供统一的数据模型。

通过标准化接口、统一认证、统一校验和插件化机制，Provider Service 实现了数据获取与业务逻辑的彻底解耦。

---

# Chapter 11 - Data Route Service

> Financial Agent Operating System (FAOS)
>
> Version: V5.0
>
> Status: Architecture Frozen

---

# 11. Data Route Service

> **Data Route 是 FAOS 的智能数据路由中心（Intelligent Data Routing Layer）。**

它位于 Provider Service 与 Connector 之间。

整个系统所有数据请求，都必须经过 Data Route。

---

# 11.1 Purpose

Provider 定义：

> 我能提供什么数据。

Connector 定义：

> 我如何获取数据。

Data Route 定义：

> **本次请求应该由谁去获取数据。**

Data Route 不获取数据。

Data Route 不解析业务。

Data Route 不调用 LLM。

它唯一负责：

**智能选择最佳的数据来源。**

---

# 11.2 Position

```
Workflow
      │
      ▼
Skill
      │
      ▼
Provider Service
      │
      ▼
Data Route Service
      │
      ▼
Connector
      │
      ▼
External Systems
```

Data Route 是整个系统唯一的数据调度中心。

---

# 11.3 Responsibilities

Data Route 负责：

- Connector Discovery
- Connector Selection
- Priority Routing
- Failover
- Load Balance
- Health Awareness
- Cost Awareness
- Latency Awareness
- Cache Lookup
- Request Merge
- Result Merge

Data Route 不负责：

- HTTP 请求
- SQL 查询
- MCP 调用
- API Key 管理

这些全部属于 Connector。

---

# 11.4 Why Data Route

如果没有 Data Route：

```
Financial Skill

↓

AkShare

×

失败

↓

EastMoney

↓

Yahoo
```

Skill 会越来越复杂。

如果增加：

Polygon

Wind

TuShare

整个 Skill：

必须修改。

这是禁止的。

Data Route 负责解决这个问题。

---

# 11.5 Request Flow

数据请求流程：

```
Skill

↓

Provider

↓

Data Route

↓

Connector Selection

↓

Connector Execution

↓

Normalization

↓

Provider

↓

Skill
```

Skill 永远不知道：

最终用了哪个 Connector。

---

# 11.6 Connector Registry

所有 Connector：

统一注册。

例如：

```
EastMoney Connector

AkShare Connector

Yahoo Connector

Polygon Connector

Wind Connector

REST Connector

MCP Connector
```

Data Route：

统一管理。

---

# 11.7 Connector Manifest

每个 Connector：

提供：

```yaml
id: eastmoney

category: market

market:

CN

supports:

- realtime_quote

- financial

priority:

100

cost:

0

latency:

80ms

reliability:

0.98
```

Data Route：

读取 Manifest。

自动评分。

---

# 11.8 Routing Strategy

默认：

综合评分。

例如：

```
Score

=

Priority

+

Health

+

Latency

+

Success Rate

+

Cost

+

Freshness
```

得分最高：

优先执行。

---

# 11.9 Priority Routing

例如：

国内股票：

```
EastMoney

↓

AkShare

↓

Yahoo
```

美股：

```
Polygon

↓

Yahoo

↓

Alpaca
```

Planner：

无需配置。

Data Route：

自动选择。

---

# 11.10 Health Routing

Connector：

实时维护：

```
Healthy

Warning

Degraded

Offline
```

如果：

EastMoney：

Offline。

自动：

切换：

AkShare。

---

# 11.11 Failover

例如：

```
Connector A

↓

Timeout

↓

Connector B

↓

Success
```

Skill：

完全无感知。

---

# 11.12 Parallel Routing

部分数据：

允许：

多个 Connector：

同时请求。

例如：

```
Yahoo

EastMoney

↓

Merge
```

提高：

稳定性。

---

# 11.13 Result Merge

多个 Connector：

返回：

```
Price

Volume

Timestamp
```

Data Route：

统一：

Merge。

例如：

最新时间。

最高可信度。

多数一致。

---

# 11.14 Cache

Data Route：

统一缓存。

例如：

```
Quote

10 秒

Financial

1 天

Macro

1 小时

News

5 分钟
```

Skill：

不关心 Cache。

---

# 11.15 Request Deduplication

如果：

多个 Skill：

同时请求：

```
600519 Quote
```

Data Route：

只请求：

一次。

多个 Skill：

共享结果。

避免重复访问。

---

# 11.16 Batch Optimization

例如：

```
600519

000858

300750
```

自动：

Batch。

Connector：

一次请求。

提高效率。

---

# 11.17 Cost Optimization

不同 Connector：

成本不同。

例如：

```
Yahoo

Free
```

```
Polygon

Paid
```

Data Route：

根据：

Budget：

自动选择。

---

# 11.18 Latency Optimization

例如：

要求：

```
Realtime
```

优先：

```
EastMoney
```

而不是：

```
Yahoo
```

Data Route：

自动：

调整。

---

# 11.19 Freshness Optimization

不同 Connector：

更新时间不同。

例如：

```
Yahoo

15min Delay
```

```
EastMoney

Realtime
```

Data Route：

自动：

选择：

最新数据。

---

# 11.20 Metrics

Data Route：

持续统计：

```
Latency

Availability

Hit Rate

Failover Count

Retry Count

Cost

Freshness

Connector Score
```

所有指标：

进入：

Trace。

---

# 11.21 Policies

支持：

```yaml
routing:

prefer:

realtime

fallback:

cache

timeout:

5s

retry:

2

budget:

low
```

Execution Engine：

自动：

读取。

---

# 11.22 Plugin Architecture

Connector：

插件化。

例如：

```
connectors/

eastmoney/

akshare/

polygon/

fred/

github/

filesystem/

mcp/
```

自动发现。

自动注册。

---

# 11.23 Relationship

Data Route：

连接：

```
Provider

↓

Connector

↓

External Systems
```

Skill：

不知道：

Connector。

Provider：

不知道：

第三方。

真正实现：

彻底解耦。

---

# 11.24 Best Practices

推荐：

所有外部访问：

全部经过：

Data Route。

禁止：

Skill：

直接：

HTTP。

禁止：

Provider：

直接：

SQL。

禁止：

Workflow：

直接：

API。

统一：

进入：

Data Route。

---

将 Data Route 从简单的"路由器"升级为 Data Access Gateway（数据访问网关）。
它不仅负责路由，还统一承担：
Request
   │
   ▼
Authentication
   │
Rate Limit
   │
Cache
   │
Request Merge
   │
Connector Selection
   │
Failover
   │
Result Validation
   │
Normalization
   │
Metrics
   │
Trace

也就是说，所有 Connector 都变成非常轻量的 Adapter，而复杂逻辑全部集中在 Data Route。

这样未来无论接入：

AkShare
EastMoney
MCP
REST API
GraphQL
Kafka
SQL
DuckDB
Milvus
Firecrawl
SearXNG

都不需要修改 Skill 和 Provider。

# 11.25 Summary

Data Route Service 是 FAOS 的智能数据路由中心。

它负责：

- Connector 选择
- Failover
- Cache
- Batch
- Merge
- Health
- Cost
- Freshness

Provider 描述能力。

Connector 实现访问。

Data Route 负责决策。

三者共同构成 FAOS 高可靠、高扩展的数据访问体系。

---


# Chapter 12 - Knowledge Service

> Financial Agent Operating System (FAOS)
>
> Version: V5.0
>
> Status: Architecture Frozen

---

# 12. Knowledge Service

> **Knowledge Service 是 FAOS 的知识中心（Knowledge Center）。**

Knowledge Service 负责整个系统的静态知识管理。

它不是数据库。

不是 RAG。

不是 Prompt。

不是 Memory。

而是：

> **整个金融分析系统的知识层。**

---

# 12.1 Purpose

Knowledge Service 的职责：

统一管理：

- 金融知识
- 行业知识
- 分析方法
- 指标定义
- Prompt 模板
- Workflow 模板
- Strategy 模板
- Rule
- Ontology

Knowledge 不负责：

- Provider
- Workflow
- Skill
- Decision
- LLM

Knowledge 提供：

知识。

---

# 12.2 Position

```
Task Runtime
      │
      ▼
Planner
      │
      ▼
Knowledge Service
      │
      ▼
Reasoning Service
```

Knowledge 是 Planner 与 Reasoning 的知识来源。

---

# 12.3 Responsibilities

Knowledge Service 负责：

- Knowledge Registry
- Knowledge Discovery
- Knowledge Loading
- Knowledge Version
- Knowledge Retrieval
- Knowledge Validation
- Knowledge Packaging
- Knowledge Distribution

Knowledge 不负责：

- 向量搜索
- Embedding
- LLM
- Prompt 拼接

这些由其它模块完成。

---

# 12.4 Knowledge Categories

Knowledge 可以划分：

## Domain Knowledge

例如：

```
股票

ETF

基金

债券

期货

期权
```

---

## Industry Knowledge

例如：

```
新能源

半导体

银行

保险

消费

医药
```

---

## Financial Knowledge

例如：

```
ROE

ROIC

PEG

DCF

PB

EV/EBITDA
```

---

## Macro Knowledge

例如：

```
GDP

PMI

CPI

利率

汇率
```

---

## Strategy Knowledge

例如：

```
价值投资

成长投资

量化

趋势

事件驱动
```

---

## Prompt Knowledge

例如：

```
分析模板

Prompt 模板

Few Shot

System Prompt
```

---

## Report Knowledge

例如：

```
Markdown

HTML

PDF

JSON
```

---

# 12.5 Knowledge Object

Knowledge 定义：

```yaml
Knowledge

id

name

category

domain

version

description

content

metadata
```

Knowledge 是一个独立资源。

---

# 12.6 Knowledge Package

Knowledge 推荐采用 Package。

例如：

```
stock-basic

industry-semiconductor

macro-cn

valuation

financial-analysis
```

Planner：

按需加载。

避免一次性全部注入。

---

# 12.7 Knowledge Registry

所有 Knowledge：

统一注册。

例如：

```
valuation

↓

Valuation Pack

roe

↓

Financial Indicator Pack

macro-cn

↓

Macro Pack
```

---

# 12.8 Knowledge Manifest

每个 Package：

提供：

```yaml
id: valuation

version: 1.0

domain:

- stock

includes:

- pe

- pb

- dcf

- peg

language:

zh-CN
```

Planner：

自动选择。

---

# 12.9 Knowledge Loading

Planner：

根据：

Task。

动态加载。

例如：

```
分析银行股
```

加载：

```
Bank Pack

Financial Pack

Valuation Pack
```

不会加载：

```
Crypto Pack
```

---

# 12.10 Knowledge Injection

Knowledge：

不会直接提供给 LLM。

流程：

```
Knowledge

↓

Reasoning Service

↓

Prompt Builder

↓

LLM
```

Reasoning Service：

决定：

注入哪些知识。

---

# 12.11 Knowledge Version

支持：

```
v1

v2

v3
```

Workflow：

可以固定版本。

方便：

升级。

---

# 12.12 Knowledge Metadata

Knowledge：

包含：

```yaml
metadata

author

owner

created

updated

language

domain

tags

priority
```

方便管理。

---

# 12.13 Knowledge Validation

Knowledge：

支持：

校验。

例如：

```
Schema

Reference

Markdown

JSON

YAML
```

非法内容：

禁止发布。

---

# 12.14 Knowledge Dependency

Knowledge：

允许：

依赖。

例如：

```
Semiconductor Pack

↓

Financial Pack

↓

Valuation Pack
```

Planner：

自动加载。

---

# 12.15 Knowledge Lifecycle

生命周期：

```
Create

↓

Review

↓

Publish

↓

Version

↓

Deprecate

↓

Archive
```

Knowledge：

支持长期维护。

---

# 12.16 Knowledge Source

Knowledge 来源：

```
Manual

Internal Docs

Markdown

Database

Wiki

RAG

LLM Generated

Research
```

统一管理。

---

# 12.17 Knowledge Cache

Knowledge：

支持：

Cache。

例如：

```
Memory Cache

Disk Cache

Redis

Object Storage
```

避免重复加载。

---

# 12.18 Knowledge Plugins

推荐目录：

```
knowledge/

stock/

macro/

industry/

valuation/

prompt/

report/
```

自动注册。

---

# 12.19 Knowledge vs Memory

Knowledge：

是：

长期静态知识。

例如：

```
PE 的定义

DCF 方法

银行估值模型
```

Memory：

是：

运行时经验。

例如：

```
上次分析结果

用户偏好

历史执行记录
```

两者：

完全不同。

---

# 12.20 Knowledge vs Provider

Knowledge：

回答：

```
什么是 ROE？
```

Provider：

回答：

```
贵州茅台 ROE 是多少？
```

Knowledge：

解释方法。

Provider：

提供数据。

---

# 12.21 Knowledge vs Prompt

Knowledge：

保存知识。

Prompt：

只是表达方式。

例如：

Knowledge：

```
DCF 定义
```

Prompt：

```
请根据 DCF 方法分析……
```

Prompt：

来自：

Prompt Builder。

不是：

Knowledge。

---

# 12.22 Best Practices

推荐：

Knowledge：

颗粒度保持中等。

例如：

推荐：

```
Financial Indicator Pack
```

不要：

```
一本金融教材
```

也不要：

```
PE 一句话
```

保证：

可组合。

可复用。

---

结合你之前关于 Skill 自动发现、LLM 自动选择 Skill、动态规划 的讨论，在 Knowledge Service 中增加一个新的知识类型：

Capability Knowledge

它不是业务知识，而是系统能力知识。

例如：

id: capability.financial_analysis

description: |
  Retrieve financial statements, calculate financial indicators,
  analyze profitability, solvency and growth.

input:
  entity

output:
  financial_metrics

related_skills:

- financial_statement

- roe_analysis

- balance_sheet

再例如：
id: capability.news_analysis

description: |
  Collect market news, summarize key events,
  evaluate sentiment and estimate market impact.

related_skills:

- news_search

- announcement

- sentiment

这是实现你一直希望达到的目标——

"LLM 不需要知道每一个 Tool，而是知道系统有哪些 Capability，需要时自动规划并调用对应 Skill。"

Reasoning Service 不需要注入几十上百个 Tool，只需要读取 Capability Knowledge Catalog。

Planner 根据这些能力知识生成执行计划，Execution Engine 再解析 Capability → Workflow → Skill → Provider。

这样整个系统将真正实现：

LLM 面向 Capability 思考
Runtime 面向 Skill 执行
Data Route 面向 Connector 获取数据

# 12.23 Summary

Knowledge Service 是 FAOS 的统一知识中心。

它管理整个系统的金融知识、行业知识、分析方法和 Prompt 模板。

Knowledge 不参与执行。

不参与推理。

它为 Planner、Reasoning 和 Report 提供统一、版本化、可组合的知识资源，是整个金融 Agent 系统的重要基础设施。

---





# Chapter 13 - Reasoning Service

> Financial Agent Operating System (FAOS)
>
> Version: V5.0
>
> Status: Architecture Frozen

---

# 13. Reasoning Service

> **Reasoning Service 是 FAOS 的 AI 推理中心（AI Reasoning Center）。**

Reasoning Service 是整个系统唯一负责 AI 推理、LLM 协作和智能分析的模块。

它不负责获取数据。

不负责业务流程。

不负责执行任务。

不负责投资决策。

它只负责：

> **将数据转换为认知（Insight）。**

---

# 13.1 Purpose

Reasoning Service 的目标：

让系统能够利用一个或多个 LLM，对已有的数据进行：

- 理解（Understand）
- 分析（Analyze）
- 推理（Reason）
- 验证（Verify）
- 反思（Reflect）
- 讨论（Debate）
- 总结（Summarize）

最终形成：

可信、可解释、可追踪的分析结果。

---

# 13.2 Position

```
Knowledge Service
        │
        ▼
Execution Context
        │
        ▼
Reasoning Service
        │
        ▼
Decision Service
```

Reasoning Service 永远建立在：

已有数据之上。

不会主动获取数据。

---

# 13.3 Responsibilities

Reasoning Service 负责：

- Prompt Builder
- Context Builder
- Multi-LLM Orchestration
- Expert Discussion
- Reflection
- Critic
- Verification
- Consensus
- Citation
- Context Compression
- Token Budget
- Output Standardization

Reasoning Service 不负责：

- Skill
- Provider
- Workflow
- Decision
- Report

---

# 13.4 Core Principle

Reasoning Service 的输入永远来自：

```
Execution Context
```

而不是：

```
Provider

HTTP

数据库

MCP
```

LLM 永远不能直接访问外部世界。

所有事实必须来自：

Execution Context。

---

# 13.5 Input

Reasoning 输入：

```yaml
Task

Execution Context

Knowledge Package

Capability Catalog

Variables

Prompt Template
```

所有输入均为结构化数据。

---

# 13.6 Output

Reasoning 输出：

```yaml
summary

insights

risks

opportunities

confidence

evidence

citations

trace
```

统一写入：

Execution Context。

---

# 13.7 Prompt Builder

Prompt Builder：

负责生成 Prompt。

它根据：

- Task
- Context
- Knowledge
- Capability
- Domain

自动构建 Prompt。

Reasoning Service 永远不直接拼接 Prompt。

---

# 13.8 Context Builder

Context Builder：

负责：

选择需要进入 Context Window 的数据。

例如：

```
Financial

News

Macro

Announcement

Knowledge
```

不是全部 Context。

而是：

最相关部分。

---

# 13.9 Context Compression

如果：

Context 超过：

Token Budget。

Context Builder 自动压缩。

例如：

```
最近一次 Quote

最近三条 News

Financial Summary

Macro Summary
```

而不是：

全部数据。

---

# 13.10 Token Budget

Reasoning Service：

统一管理：

```
Planner

10%

Discussion

45%

Reflection

20%

Decision

15%

Reserve

10%
```

避免：

单 Agent 消耗全部 Token。

---

# 13.11 Prompt Template

Prompt 不写死。

统一来自：

Knowledge。

例如：

```
Financial Analysis Prompt

Macro Prompt

Risk Prompt

Decision Prompt
```

Reasoning Service：

自动选择。

---

# 13.12 Capability Catalog

Reasoning Service：

不会直接看到：

Skill。

而是看到：

```
Capability Catalog
```

例如：

```
Financial Analysis

News Analysis

Valuation

Macro

Risk
```

LLM 思考的是：

能力。

不是：

实现。

---

# 13.13 Skill Catalog（Runtime）

Execution Engine：

根据 Planner：

生成：

当前 Task 可用 Skill Catalog。

例如：

```
Financial Skill

News Skill

Macro Skill
```

Reasoning：

如果需要更多数据。

请求：

Capability。

Execution Engine：

负责：

执行。

---

# 13.14 Tool Calling Principle

LLM：

不会直接调用：

Provider。

不会直接调用：

HTTP。

不会直接调用：

数据库。

LLM：

只能请求：

```
Capability
```

Execution Engine：

解析：

```
Capability

↓

Workflow

↓

Skill

↓

Provider
```

这是整个 FAOS 的核心原则。

---

# 13.15 Multi-LLM

Reasoning Service：

支持：

多个模型。

例如：

```
DeepSeek

Claude

GPT

Gemini

Qwen

Kimi
```

每个模型：

负责不同角色。

---

# 13.16 Expert Roles

例如：

```
Fundamental Expert

Technical Expert

Macro Expert

Risk Expert

Value Expert

Growth Expert
```

Expert：

只是：

Prompt。

不是：

新的 Runtime。

---

# 13.17 Discussion

多个 Expert：

共享：

Execution Context。

例如：

```
Financial

↓

Fundamental

News

↓

Sentiment

Macro

↓

Macro Expert
```

Discussion：

统一：

保存。

---

# 13.18 Reflection

Discussion 完成后：

Reflection：

重新检查：

```
逻辑

证据

引用

数据

风险
```

Reflection：

不会获取新数据。

---

# 13.19 Critic

Critic：

负责：

寻找：

```
矛盾

证据不足

幻觉

推理错误

引用错误
```

输出：

Review。

---

# 13.20 Verification

Verification：

检查：

```
Evidence

Citation

Data Consistency

Context Consistency
```

发现问题：

重新请求：

Capability。

而不是：

LLM 猜测。

---

# 13.21 Evidence-based Reasoning

所有结论：

必须：

绑定：

Evidence。

例如：

```
ROE

↓

Financial Statement
```

```
行业增长

↓

Research Report
```

禁止：

无证据结论。

---

# 13.22 Citation

所有引用：

必须来自：

Execution Context。

例如：

```
News

Financial

Announcement

Knowledge
```

LLM：

不得：

编造引用。

---

# 13.23 Consensus

多个 Expert：

最终形成：

Consensus。

例如：

```
Bullish

75%

Neutral

20%

Bearish

5%
```

Decision：

读取：

Consensus。

---

# 13.24 Hallucination Guard

Reasoning Service：

自动检查：

```
Unknown Fact

Unsupported Claim

Missing Evidence

Fake Citation
```

发现：

拒绝输出。

---

# 13.25 Reasoning Trace

保存：

```
Prompt

Context

LLM

Discussion

Reflection

Critic

Consensus
```

方便：

Replay。

---

# 13.26 LLM Independence

Reasoning Service：

不依赖：

具体模型。

例如：

```
Claude

GPT

DeepSeek

Gemini
```

均可替换。

Reasoning：

保持统一接口。

---

# 13.27 Design Principles

Reasoning Service 必须遵循：

- Data First
- Evidence First
- Capability First
- Stateless
- Explainable
- Traceable
- Verifiable
- Model Independent

---

# 13.28 Relationship

```
Knowledge
      │
      ▼
Reasoning
      │
      ▼
Decision
      │
      ▼
Report
```

Reasoning：

负责：

思考。

Decision：

负责：

决策。

---

# 13.29 Best Practices

推荐：

Reasoning：

只分析。

不要：

获取数据。

不要：

调用 Provider。

不要：

决定买卖。

所有分析：

必须：

基于：

Execution Context。

---

在 Reasoning Service 内部增加三个核心子组件
Reasoning Service
│
├── Prompt Builder
├── Context Builder
├── Capability Planner
├── Tool Planner
├── Discussion Engine
├── Reflection Engine
├── Critic Engine
├── Consensus Engine
└── Citation Engine

其中最重要的是：

Capability Planner

LLM 看到的是：

"系统有哪些能力（Capability）"

而不是：

"系统有哪些 Tool"

例如：
Financial Analysis
News Analysis
Valuation
Industry Analysis
Risk Analysis

LLM 判断：

"我需要 Financial Analysis"

Execution Engine 再自动解析：

Financial Analysis
        ↓
Financial Workflow
        ↓
Financial Skill
        ↓
Provider
        ↓
Connector

这样 LLM 永远不需要知道 Skill、Provider、HTTP API 或 MCP，整个 Runtime 负责把能力映射到具体实现。


# 13.30 Summary

Reasoning Service 是 FAOS 的 AI 大脑。

它负责利用一个或多个 LLM，对 Execution Context 中的数据进行理解、推理、验证、讨论与总结。

Reasoning 不获取数据。

不调用 Skill。

不直接访问 Tool。

它始终围绕 **Capability、Evidence、Knowledge、Execution Context** 展开推理，并通过统一的 Prompt Builder、Context Builder 和 Multi-LLM Orchestrator，实现可解释、可验证、可追踪的智能分析。

---




# Chapter 14 - Decision Service

> Financial Agent Operating System (FAOS)
>
> Version: V5.0
>
> Status: Architecture Frozen

---

# Chapter 14 - Decision Service

> **Decision Service 是 FAOS 的决策中心（Decision Center）。**

Decision Service 是整个系统唯一负责生成最终业务决策的模块。

它负责：

> **将 Reasoning Service 产生的 Insight 转换为可执行的业务决策。**

Decision 不负责：

- 获取数据
- 调用 Skill
- Provider
- Workflow
- Prompt
- LLM 推理

Decision 只负责：

> **Decision。**

---

# 14.1 Purpose

Decision Service 的目标：

根据：

- Execution Context
- Reasoning Result
- Discussion
- Reflection
- Knowledge
- Policy

生成：

最终决策。

例如：

```
Buy

Hold

Sell
```

或者：

```
Increase Position

Reduce Position

Rebalance
```

---

# 14.2 Position

```
Knowledge
      │
      ▼
Reasoning Service
      │
      ▼
Decision Service
      │
      ▼
Report Service
```

Decision 永远位于：

Reasoning 之后。

Report 之前。

---

# 14.3 Responsibilities

Decision Service 负责：

- Decision Policy
- Decision Engine
- Risk Evaluation
- Confidence Evaluation
- Consensus Evaluation
- Arbitration
- Position Recommendation
- Portfolio Recommendation
- Strategy Selection
- Decision Trace

Decision 不负责：

- Provider
- Workflow
- Prompt
- Skill
- Report

---

# 14.4 Core Principle

Reasoning：

负责：

分析。

Decision：

负责：

决定。

例如：

Reasoning：

```
公司盈利增长

行业景气

估值偏低
```

Decision：

```
Buy
```

职责必须分离。

---

# 14.5 Input

Decision 输入：

```yaml
Execution Context

Reasoning

Consensus

Evidence

Knowledge

Policy
```

禁止：

直接读取：

Provider。

---

# 14.6 Output

Decision 输出：

```yaml
decision

confidence

risk

allocation

strategy

reason

evidence
```

统一写入：

Execution Context。

---

# 14.7 Decision Object

Decision：

定义：

```yaml
Decision

id

type

score

confidence

risk

strategy

allocation

reason

evidence
```

Decision 是标准对象。

---

# 14.8 Decision Policy

Decision 永远基于：

Policy。

例如：

```
Conservative

Balanced

Aggressive
```

不同 Policy：

得到不同结果。

---

# 14.9 Decision Strategy

支持：

多个 Strategy。

例如：

```
Value Investing

Growth Investing

Dividend

Momentum

Trend

Quality

Low Volatility
```

Decision：

自动选择。

---

# 14.10 Confidence

Decision：

必须：

计算：

Confidence。

例如：

```
92%

Strong Buy
```

Confidence 来源：

- Evidence
- Consensus
- Risk
- Data Quality

而不是：

LLM 自评。

---

# 14.11 Risk Evaluation

Risk：

统一计算。

例如：

```
Financial Risk

Macro Risk

Policy Risk

Liquidity Risk

Valuation Risk
```

Risk：

影响：

Decision。

---

# 14.12 Evidence Requirement

所有 Decision：

必须：

绑定：

Evidence。

例如：

```
ROE

Financial

News

Announcement

Macro
```

没有 Evidence。

禁止：

输出。

---

# 14.13 Consensus

多个 Expert：

产生：

Consensus。

例如：

```
Bull

80%

Neutral

15%

Bear

5%
```

Decision：

读取：

Consensus。

---

# 14.14 Arbitration

如果：

多个模型：

冲突。

例如：

```
Claude

Buy
```

```
DeepSeek

Sell
```

Decision：

启动：

Arbitration。

例如：

```
Majority

Weighted

Policy

Evidence
```

---

# 14.15 Scoring

Decision：

统一评分。

例如：

```
Financial

30

Macro

20

Valuation

25

Risk

15

Technical

10
```

最终：

```
Score

85
```

---

# 14.16 Allocation

如果：

Portfolio。

Decision：

输出：

```yaml
allocation

stock:

20%

gold:

10%

cash:

30%
```

---

# 14.17 Position

Decision：

建议：

```
Open

Close

Increase

Reduce

Hold
```

统一接口。

---

# 14.18 Portfolio Decision

Portfolio：

输出：

```
Diversification

Correlation

Sector Weight

Risk Exposure
```

不是：

单只股票。

---

# 14.19 Multi-Asset Decision

支持：

```
Stock

ETF

Fund

Bond

Commodity

Crypto
```

统一 Decision。

---

# 14.20 Rule Engine

Decision：

支持：

Rule。

例如：

```
Risk >

80

↓

Reject
```

```
Confidence <

50

↓

Review
```

无需：

LLM。

---

# 14.21 Decision Version

支持：

```
v1

v2

v3
```

方便：

策略升级。

---

# 14.22 Decision Trace

记录：

```
Evidence

Reasoning

Consensus

Score

Policy

Strategy
```

方便：

Audit。

---

# 14.23 Explainability

Decision：

必须：

解释。

例如：

```
为什么 Buy？

为什么 Sell？

为什么 Hold？
```

Explanation：

必须引用：

Evidence。

---

# 14.24 Policy Engine

Decision：

读取：

Policy。

例如：

```
Long Only

No Margin

Max Position

Sector Limit
```

统一：

控制。

---

# 14.25 Guardrail

Decision：

最后：

通过：

Guardrail。

例如：

```
Evidence Missing

↓

Reject
```

```
Risk Too High

↓

Reject
```

```
Data Expired

↓

Reject
```

Guardrail：

优先级最高。

---

# 14.26 Human Override

支持：

人工：

Override。

例如：

```
Decision

↓

Manual Review

↓

Approved
```

企业部署：

必须支持。

---

# 14.27 Best Practices

Decision：

禁止：

直接：

调用：

LLM。

禁止：

重新获取数据。

禁止：

修改：

Reasoning。

Decision：

只消费：

已有结果。

---

# 14.28 Relationship

```
Reasoning

↓

Decision

↓

Report
```

Reasoning：

负责：

分析。

Decision：

负责：

选择。

Report：

负责：

展示。

---

# 14.29 Design Principles

Decision 必须：

- Evidence First
- Policy First
- Explainable
- Traceable
- Stateless
- Versioned
- Deterministic（尽可能）

---

增加一个 Decision Policy Engine（作为 Decision Service 的内部组件，而不是新增顶层 Service）

内部结构如下：
Decision Service
│
├── Policy Engine
├── Scoring Engine
├── Risk Engine
├── Confidence Engine
├── Consensus Engine
├── Arbitration Engine
├── Guardrail Engine
├── Allocation Engine
└── Explainability Engine

其中最重要的是 Policy Engine。

它负责统一管理：

投资风格（价值、成长、红利、趋势等）
风险偏好（保守、平衡、激进）
市场规则（A 股、港股、美股等）
用户约束（仓位上限、行业限制、禁买名单等）
合规规则（企业版、机构版）

这样，Reasoning Service 专注于"分析"，Decision Service 专注于"裁决"，两者职责完全分离

# 14.30 Summary

Decision Service 是 FAOS 的统一决策中心。

它基于 Reasoning、Evidence、Consensus 和 Policy，生成最终业务决策，并输出风险、置信度、仓位建议和策略建议。

Decision Service 不参与数据获取，不参与推理，不依赖具体 LLM，而是作为整个金融 Agent 的最终业务裁决层，为 Report 和下游业务提供统一、可解释、可审计的决策结果。

---


# Chapter 15 - Report Service

> Financial Agent Operating System (FAOS)
>
> Version: V5.0
>
> Status: Architecture Frozen

---

# Chapter 15 - Report Service

> **Report Service 是 FAOS 的统一结果输出中心（Unified Reporting Center）。**

Report Service 是整个系统唯一负责生成分析报告、结构化结果和可视化输出的模块。

它的职责不是分析。

不是推理。

不是决策。

而是：

> **将整个系统的执行结果，以人类可理解的方式呈现出来。**

---

# 15.1 Purpose

Report Service 的目标：

将：

- Execution Context
- Reasoning Result
- Decision
- Evidence
- Trace

组织成：

最终输出。

例如：

```
Markdown Report

HTML Report

JSON

PDF

Dashboard
```

---

# 15.2 Position

```
Execution Context
        │
        ▼
Reasoning Service
        │
        ▼
Decision Service
        │
        ▼
Report Service
```

Report 永远位于流程最后。

---

# 15.3 Responsibilities

Report Service 负责：

- Report Builder
- Report Template
- Visualization
- Markdown
- HTML
- PDF
- JSON
- Dashboard
- Citation
- Export
- Report Version

Report 不负责：

- Workflow
- Skill
- Provider
- Decision
- LLM 推理

---

# 15.4 Core Principle

Report：

只消费数据。

绝不修改数据。

例如：

```
Execution Context

↓

Report

↓

Markdown
```

Report 不允许：

重新推理。

重新决策。

重新调用 Skill。

---

# 15.5 Input

Report 输入：

```yaml
Execution Context

Reasoning Result

Decision

Evidence

Trace
```

统一来自：

Execution Context。

---

# 15.6 Output

支持：

```
Markdown

HTML

PDF

DOCX

JSON

Dashboard

API Response
```

所有格式：

共享同一个：

Report Model。

---

# 15.7 Report Object

统一模型：

```yaml
Report

title

summary

sections

charts

tables

citations

appendix

metadata
```

所有 Renderer：

读取：

统一对象。

---

# 15.8 Report Builder

Builder：

负责：

组织内容。

例如：

```
Summary

↓

Financial

↓

News

↓

Macro

↓

Risk

↓

Decision

↓

Evidence
```

Builder：

不负责：

渲染。

---

# 15.9 Renderer

不同 Renderer：

输出：

```
Markdown Renderer

HTML Renderer

PDF Renderer

Dashboard Renderer

JSON Renderer
```

Builder 与 Renderer：

完全解耦。

---

# 15.10 Report Template

支持：

模板。

例如：

```
Investment Report

Research Report

Daily Report

Portfolio Report

Risk Report
```

Builder：

自动：

选择模板。

---

# 15.11 Sections

Report：

由多个 Section 组成。

例如：

```
Executive Summary

Financial Analysis

Industry Analysis

Macro Analysis

Risk Analysis

Decision

Evidence
```

Section：

支持：

插件化。

---

# 15.12 Evidence

每个结论：

必须关联：

Evidence。

例如：

```
ROE

↓

Financial Statement
```

```
新闻观点

↓

News
```

禁止：

无来源结论。

---

# 15.13 Citation

统一引用。

例如：

```
EastMoney

Yahoo

AkShare

NewsAPI

Knowledge Pack
```

Report：

自动：

生成：

引用。

---

# 15.14 Explainability

每个结论：

必须：

解释：

```
为什么？

依据是什么？

风险是什么？
```

Explainability：

来自：

Decision。

---

# 15.15 Charts

支持：

```
Line

Bar

Pie

Radar

Candlestick

Heatmap

TreeMap
```

图表：

统一接口。

---

# 15.16 Tables

支持：

```
Financial Table

Portfolio Table

Comparison Table

Valuation Table
```

统一：

Table Model。

---

# 15.17 Dashboard

Dashboard：

实时读取：

Report Model。

例如：

```
Web

React

Mobile

Desktop
```

无需：

重新分析。

---

# 15.18 JSON API

所有 Report：

支持：

JSON。

例如：

```json
{
  "summary": "...",
  "decision": "...",
  "risk": "...",
  "confidence": 0.91
}
```

方便：

API。

---

# 15.19 PDF

PDF：

通过：

PDF Renderer。

支持：

```
目录

页码

图表

引用

附录
```

---

# 15.20 Markdown

Markdown：

作为：

默认输出。

原因：

- 易读
- 易存储
- 易版本管理
- 易二次加工

---

# 15.21 HTML

HTML：

支持：

```
交互图表

折叠

搜索

链接

导航
```

适合：

Web。

---

# 15.22 Metadata

每份 Report：

包含：

```yaml
title

author

created

task_id

workflow_id

reasoning_version

decision_version

report_version
```

方便：

追踪。

---

# 15.23 Report Version

支持：

```
v1

v2

v3
```

模板升级：

不会影响：

历史报告。

---

# 15.24 Report Lifecycle

生命周期：

```
Build

↓

Render

↓

Review

↓

Export

↓

Archive
```

支持：

长期管理。

---

# 15.25 Report Plugin

支持：

插件。

例如：

```
reports/

markdown/

html/

pdf/

dashboard/

json/
```

新增 Renderer：

无需修改：

核心代码。

---

# 15.26 Report Trace

每份 Report：

保留：

```
Task

Workflow

Reasoning

Decision

Evidence

Trace
```

支持：

Replay。

---

# 15.27 Best Practices

推荐：

Report：

只负责：

展示。

不要：

计算。

不要：

推理。

不要：

调用 LLM。

不要：

访问 Provider。

---

# 15.28 Relationship

```
Reasoning

↓

Decision

↓

Report

↓

User
```

Report：

是整个系统唯一面向用户的输出层。

---

# 15.29 Design Principles

Report 必须：

- Read Only
- Explainable
- Evidence First
- Traceable
- Template Driven
- Renderer Independent
- Versioned
- Plugin Based

---

架构
Report Service
│
├── Report Builder
├── Template Engine
├── Visualization Engine
├── Renderer Manager
├── Citation Engine
├── Explainability Engine
├── Export Engine
└── Artifact Manager


Artifact Manager

这一层负责统一管理所有分析产物（Artifacts），例如：

Markdown 报告
PDF
HTML
JSON
图表（PNG、SVG）
数据表（CSV、Excel）
Trace 文件
Prompt 快照
Execution Context 快照
Decision 快照

每个分析任务最终形成一个完整的 Artifact Bundle，例如
task_20260715/
├── report.md
├── report.pdf
├── report.html
├── report.json
├── charts/
├── tables/
├── trace.json
├── context.json
└── metadata.yaml

这样 Report Service 不仅输出展示内容，还能够作为整个分析任务的归档中心，方便：

回放（Replay）
审计（Audit）
分享（Share）
二次分析（Re-analysis）
持续学习（Future Learning）

这一设计与前面的 Execution Trace、Decision Trace、Reasoning Trace 可以形成完整闭环

# 15.30 Summary

Report Service 是 FAOS 的统一输出中心。

它负责将 Execution Context、Reasoning、Decision 和 Evidence 组织成统一的 Report Model，并通过 Markdown、HTML、PDF、Dashboard、JSON 等不同 Renderer 输出最终结果。

Report 不参与分析，不参与推理，不参与决策，它是整个系统唯一面向用户的展示层，实现分析结果的可解释、可追踪和可复用。

---

# Chapter 16 - Plugin Architecture

> Financial Agent Operating System (FAOS)
>
> Version: V5.0
>
> Status: Architecture Frozen

---

# Chapter 16 - Plugin Architecture

> **Plugin Architecture 是 FAOS 的统一扩展机制（Unified Extension Framework）。**

Plugin Architecture 的目标：

> **任何新能力都不应该修改核心系统，而应该以插件（Plugin）的方式接入。**

FAOS 的所有核心层均支持插件化，包括：

- Domain
- Capability
- Workflow
- Skill
- Provider
- Connector
- Knowledge
- Reasoning
- Decision
- Report

通过统一的插件机制，系统能够持续扩展，而无需修改 Runtime 或 Execution Engine。

---

# 16.1 Purpose

Plugin Architecture 的目标：

- 解耦核心框架
- 支持第三方扩展
- 支持企业定制
- 支持动态加载
- 支持热更新
- 支持版本管理
- 支持权限控制
- 支持依赖管理

Plugin 是整个系统可扩展性的基础。

---

# 16.2 Position

```
                 Task Runtime
                      │
     ┌────────────────┼────────────────┐
     ▼                ▼                ▼
 Domain Plugin   Skill Plugin   Report Plugin
     ▼                ▼                ▼
           Plugin Runtime
                │
         Plugin Registry
                │
        Plugin Lifecycle
```

Plugin Runtime 为所有插件提供统一运行环境。

---

# 16.3 Core Principle

FAOS 核心代码：

永远不直接依赖：

```
AkShare

DeepSeek

EastMoney

Wind

Firecrawl

MCP

Claude
```

所有外部能力：

全部通过 Plugin。

---

# 16.4 Responsibilities

Plugin Architecture 负责：

- Plugin Registry
- Plugin Loader
- Plugin Lifecycle
- Plugin Dependency
- Plugin Manifest
- Plugin Sandbox
- Plugin Security
- Plugin Version
- Plugin Discovery

---

# 16.5 Plugin Categories

支持：

## Domain Plugin

例如：

```
Stock

Fund

Bond

Crypto
```

---

## Capability Plugin

例如：

```
Valuation

Risk Analysis

Macro Analysis
```

---

## Workflow Plugin

例如：

```
Stock Workflow

Portfolio Workflow
```

---

## Skill Plugin

例如：

```
Financial Skill

News Skill
```

---

## Provider Plugin

例如：

```
EastMoney

AkShare

Polygon
```

---

## Connector Plugin

例如：

```
REST

GraphQL

SQL

MCP

Filesystem
```

---

## Knowledge Plugin

例如：

```
Industry Pack

Prompt Pack

Valuation Pack
```

---

## Reasoning Plugin

例如：

```
Reflection

Critic

Consensus

Debate
```

---

## Decision Plugin

例如：

```
Value Policy

Growth Policy

Risk Policy
```

---

## Report Plugin

例如：

```
Markdown

PDF

Dashboard
```

---

# 16.6 Plugin Manifest

所有 Plugin：

必须提供 Manifest。

例如：

```yaml
id: financial_skill

name: Financial Skill

version: 1.0

type: skill

author: FAOS

dependencies:

- provider.financial

- capability.financial

permissions:

- financial.read

entry:

financial_skill.py
```

Manifest 是插件唯一入口。

---

# 16.7 Plugin Registry

Plugin Registry：

统一维护：

```
Plugin ID

Type

Version

Status

Dependencies

Permissions
```

Execution Engine：

通过 Registry：

发现插件。

---

# 16.8 Plugin Discovery

系统启动时：

自动扫描：

```
plugins/

domain/

skill/

provider/

knowledge/

report/
```

注册到：

Plugin Registry。

无需手工配置。

---

# 16.9 Plugin Lifecycle

生命周期：

```
Discover

↓

Load

↓

Validate

↓

Initialize

↓

Activate

↓

Serving

↓

Upgrade

↓

Unload
```

统一管理。

---

# 16.10 Dependency Management

Plugin：

可以依赖：

其它 Plugin。

例如：

```
Financial Skill

↓

Financial Provider

↓

REST Connector
```

Execution Engine：

自动解析依赖。

---

# 16.11 Versioning

支持：

```
v1

v2

v3
```

多个版本：

可同时存在。

Workflow：

可以指定版本。

---

# 16.12 Compatibility

Plugin：

声明兼容版本。

例如：

```yaml
compatible:

runtime:

>=5.0
```

避免：

升级破坏。

---

# 16.13 Sandbox

所有 Plugin：

运行于：

Sandbox。

例如：

```
Python venv

Docker

Remote Worker
```

防止：

影响 Runtime。

---

# 16.14 Permissions

Plugin：

必须声明：

权限。

例如：

```yaml
permissions:

market.read

financial.read

filesystem.read

mcp.invoke
```

Execution Engine：

统一授权。

---

# 16.15 Resource Limits

支持：

限制：

```
CPU

Memory

Timeout

Token Budget

Cost Budget
```

避免：

插件失控。

---

# 16.16 Plugin Communication

Plugin：

禁止：

互相调用。

必须：

通过：

```
Execution Context

Event Bus

Capability
```

进行协作。

避免：

强耦合。

---

# 16.17 Plugin Isolation

不同 Plugin：

互不影响。

例如：

```
Financial Plugin

×

News Plugin
```

一个插件异常：

不会影响：

其它插件。

---

# 16.18 Plugin Update

支持：

```
Hot Reload

Rolling Upgrade

Blue/Green

Canary
```

无需：

停止 Runtime。

---

# 16.19 Plugin Packaging

推荐：

```
plugin/

manifest.yaml

README.md

src/

tests/

resources/
```

统一结构。

---

# 16.20 Plugin Repository

企业版：

支持：

```
Internal Plugin Store
```

社区版：

支持：

```
Git Repository

Package Registry
```

统一安装。

---

# 16.21 Plugin Testing

每个 Plugin：

必须：

提供：

```
Unit Test

Integration Test

Contract Test
```

保证：

质量。

---

# 16.22 Plugin Metrics

记录：

```
Latency

Error Rate

Success Rate

Invocation Count

Cost
```

统一进入：

Metrics。

---

# 16.23 Plugin Trace

记录：

```
Load

Invoke

Result

Error

Version
```

方便：

Replay。

---

# 16.24 Plugin Security

Plugin：

禁止：

- 任意访问 Secret
- 任意访问文件
- 任意访问数据库

所有资源：

统一授权。

---

# 16.25 Best Practices

推荐：

Plugin：

保持：

- 单一职责
- 无状态
- 可测试
- 可升级
- 可替换
- 可回滚

不要：

多个业务：

写入：

一个 Plugin。

---

# 16.26 Relationship

```
Plugin

↓

Registry

↓

Runtime

↓

Execution Engine

↓

Execution Context
```

Plugin：

始终运行于：

统一 Runtime。

---

# 16.27 Design Principles

Plugin 必须：

- Plugin First
- Manifest Driven
- Versioned
- Isolated
- Permission Based
- Discoverable
- Hot Swappable
- Observable

---
将 Plugin 与 MCP（Model Context Protocol） 完全统一，而不是并列存在。

即新增一个抽象：

Plugin
│
├── Native Plugin
├── Python Plugin
├── REST Plugin
├── MCP Plugin
├── Docker Plugin
├── Remote Plugin
└── AI Plugin

这样对于 Runtime 来说，所有能力都是 Plugin，区别仅在于执行方式：

Plugin 类型	执行方式
Native Plugin	本地 Python/Go/Rust
REST Plugin	HTTP API
MCP Plugin	MCP Server
Docker Plugin	Docker 容器
Remote Plugin	RPC/gRPC
AI Plugin	调用外部 AI 服务

这样可以带来几个好处：

统一生命周期管理（安装、升级、卸载）。
统一权限控制（所有插件共享 Permission 模型）。
统一监控与审计（所有插件共享 Trace 和 Metrics）。
统一发现机制（Registry 中不区分 MCP、REST、Python）。

这样 MCP 不再是一个特殊能力，而只是 Plugin Runtime 支持的一种执行协议

# 16.28 Summary

Plugin Architecture 是 FAOS 的统一扩展框架。

它为 Domain、Capability、Workflow、Skill、Provider、Knowledge、Reasoning、Decision、Report 等所有模块提供一致的插件化机制，使系统具备长期演进能力，而无需修改核心 Runtime。

Plugin 通过 Manifest、Registry、Lifecycle、Sandbox 和 Permission 统一管理，实现企业级 AI Agent 平台所需的高扩展性、高稳定性和高可维护性。

---


# Chapter 17 - Event Bus & Observability

> Financial Agent Operating System (FAOS)
>
> Version: V5.0
>
> Status: Architecture Frozen

---

# Chapter 17 - Event Bus & Observability

> **Event Bus & Observability 是 FAOS 的运行时神经系统（Runtime Nervous System）。**

它负责：

> **让系统中的所有模块能够解耦协作，并让整个运行过程可观测、可追踪、可回放。**

Event Bus 是消息通道。

Observability 是运行时可见性。

两者共同组成整个 Runtime 的基础设施。

---

# 17.1 Purpose

本模块负责：

- Event Bus
- Event Routing
- Event Store
- Metrics
- Trace
- Logging
- Audit
- Replay
- Monitoring
- Telemetry

它不负责：

- Workflow
- Skill
- Provider
- LLM
- Decision

---

# 17.2 Position

```
                 Task Runtime
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
 Workflow       Reasoning      Decision
        │             │             │
        └─────────────┼─────────────┘
                      ▼
           Event Bus & Observability
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
      Trace        Metrics        Audit
```

所有模块都通过 Event Bus 进行事件通知。

所有运行数据都进入 Observability。

---

# 17.3 Core Principle

所有模块：

禁止：

直接监听彼此。

例如：

```
Workflow

×

直接通知 Report
```

正确方式：

```
Workflow

↓

Event Bus

↓

Report
```

实现：

松耦合。

---

# 17.4 Responsibilities

Event Bus：

负责：

- Publish
- Subscribe
- Broadcast
- Queue
- Retry
- Ordering

Observability：

负责：

- Trace
- Metrics
- Log
- Audit
- Replay

---

# 17.5 Event Model

统一 Event：

```yaml
Event

id

type

source

target

timestamp

payload

metadata

trace_id
```

所有模块：

统一事件模型。

---

# 17.6 Event Types

例如：

```
TaskCreated

WorkflowStarted

SkillStarted

SkillCompleted

ProviderFailed

ReasoningCompleted

DecisionCompleted

ReportGenerated
```

所有状态变化：

均通过 Event。

---

# 17.7 Publish

任何模块：

可以：

Publish。

例如：

```
Reasoning Completed
```

↓

```
Decision Service
```

收到通知。

---

# 17.8 Subscribe

模块：

订阅：

自己关心事件。

例如：

```
Report

↓

Decision Completed
```

自动生成报告。

---

# 17.9 Event Routing

支持：

```
Broadcast

Point-to-Point

Topic

Priority Queue
```

统一：

消息路由。

---

# 17.10 Event Store

重要 Event：

永久保存。

例如：

```
Task Started

Decision Completed

Provider Failed
```

方便：

Replay。

---

# 17.11 Trace

整个 Task：

只有：

一个：

Trace。

例如：

```
Task

↓

Workflow

↓

Skill

↓

Provider

↓

Reasoning

↓

Decision

↓

Report
```

全部：

共享：

同一个：

Trace ID。

---

# 17.12 Trace Object

统一：

```yaml
Trace

trace_id

task_id

span_id

parent_span

start

end

duration
```

支持：

OpenTelemetry。

---

# 17.13 Span

每个步骤：

一个 Span。

例如：

```
Reasoning

Span

↓

Discussion

Span

↓

Reflection

Span
```

最终形成：

Trace Tree。

---

# 17.14 Metrics

统一采集：

```
Latency

Success Rate

Failure Rate

Retry

Token

Cost

CPU

Memory
```

统一：

Metrics。

---

# 17.15 Logging

统一日志。

例如：

```
INFO

WARN

ERROR

DEBUG

TRACE
```

所有模块：

统一格式。

---

# 17.16 Audit

企业版：

必须支持：

Audit。

例如：

```
谁执行

什么时候

调用什么 Skill

输出什么 Decision
```

全部记录。

---

# 17.17 Replay

Replay：

重新播放：

整个 Task。

例如：

```
Workflow

↓

Reasoning

↓

Decision
```

无需：

重新获取数据。

方便：

Debug。

---

# 17.18 Monitoring

支持：

```
Grafana

Prometheus

OpenTelemetry

CloudWatch

Datadog
```

统一接入。

---

# 17.19 Alert

支持：

```
Provider Down

Skill Timeout

LLM Timeout

Budget Exceeded

Error Rate
```

自动：

告警。

---

# 17.20 Cost Metrics

统计：

```
LLM Cost

Provider Cost

Connector Cost

Total Cost
```

方便：

成本控制。

---

# 17.21 Token Metrics

记录：

```
Prompt Token

Completion Token

Cache Hit

Compression Ratio
```

帮助：

优化 Prompt。

---

# 17.22 Health Dashboard

统一：

Dashboard。

例如：

```
Workflow

Provider

Connector

LLM

Plugin

Runtime
```

实时：

健康状态。

---

# 17.23 Event Replay

支持：

按：

```
Task

Workflow

Trace

Time
```

重新执行。

方便：

问题定位。

---

# 17.24 Event Version

支持：

```
v1

v2

v3
```

保证：

兼容。

---

# 17.25 Plugin Events

Plugin：

统一：

事件。

例如：

```
Plugin Loaded

Plugin Failed

Plugin Upgraded
```

方便：

运维。

---

# 17.26 Best Practices

推荐：

所有模块：

只：

Publish。

不要：

直接调用：

其它模块。

真正实现：

Event Driven。

---

# 17.27 Relationship

```
Execution Engine

↓

Event Bus

↓

Observability

↓

Monitoring
```

整个 Runtime：

保持：

可观测。

---

# 17.28 Design Principles

Event Bus：

必须：

- Async First
- Event Driven
- Traceable
- Replayable
- Versioned
- Ordered
- Observable

---

架构

Observability
│
├── Event Bus
├── Trace Center
├── Metrics Center
├── Log Center
├── Audit Center
├── Replay Center
└── Runtime Timeline   ⭐

Runtime Timeline

Timeline 按时间顺序记录整个 Task 的生命周期，例如
10:00:00  Task Created
10:00:01  Workflow Selected
10:00:01  Financial Skill Started
10:00:02  EastMoney Connector Invoked
10:00:02  Data Returned
10:00:03  Reasoning Started
10:00:08  Expert Discussion Finished
10:00:10  Decision Generated
10:00:11  Report Exported
这比单纯查看日志或 Trace 更容易理解整个分析过程。

对于你的多 LLM 金融分析系统来说，Timeline 可以直接展示：

每个 Expert 的开始和结束时间
每轮 Discussion 的耗时
每次 Skill 调用
每次 Provider 路由
每次 LLM Token 消耗
每次 Decision 更新

最终形成一条完整的分析时间轴，非常适合调试、性能分析和向用户展示 AI 的工作过程

# 17.29 Summary

Event Bus & Observability 是 FAOS 的运行时基础设施。

Event Bus 实现模块之间的事件驱动协作。

Observability 提供统一的 Trace、Metrics、Logging、Audit 和 Replay 能力。

两者共同保证整个系统可监控、可调试、可审计、可回放，为企业级 AI Agent 提供稳定可靠的运行保障。

---



# Chapter 18 - Security & Governance

> Financial Agent Operating System (FAOS)
>
> Version: V5.0
>
> Status: Architecture Frozen

---

# Chapter 18 - Security & Governance

> **Security & Governance 是 FAOS 的统一安全与治理中心（Security & Governance Center）。**

Security 负责：

> **保证系统安全。**

Governance 负责：

> **保证系统可控。**

本模块为整个 Runtime 提供统一的权限、安全、预算、审计和治理能力。

---

# 18.1 Purpose

Security & Governance 负责：

- Identity
- Authentication
- Authorization
- Secret Management
- Permission
- Budget
- Quota
- Policy
- Compliance
- Audit
- Governance

不负责：

- Workflow
- Skill
- Provider
- Decision
- Report

---

# 18.2 Position

```
                Task Runtime
                     │
      ┌──────────────┼──────────────┐
      ▼              ▼              ▼
 Workflow      Reasoning      Provider
      │              │              │
      └──────────────┼──────────────┘
                     ▼
        Security & Governance
```

所有模块均受统一治理。

---

# 18.3 Core Principle

任何资源访问：

都必须经过：

```
Identity

↓

Authentication

↓

Authorization

↓

Execution
```

禁止：

绕过权限控制。

---

# 18.4 Responsibilities

Security：

负责：

- Login
- API Key
- Secret
- Permission
- Encryption

Governance：

负责：

- Budget
- Quota
- Policy
- Audit
- Compliance

---

# 18.5 Identity

统一身份：

例如：

```
User

Agent

Plugin

Service

API Client
```

所有操作：

都有身份。

---

# 18.6 Authentication

支持：

```
Password

OAuth

JWT

API Key

SSO

OIDC
```

统一认证。

---

# 18.7 Authorization

采用：

RBAC（Role-Based Access Control）。

例如：

```
Admin

Researcher

Trader

Viewer
```

不同角色：

权限不同。

---

# 18.8 Permission

统一权限模型：

例如：

```yaml
market.read

financial.read

provider.invoke

reasoning.execute

report.export
```

所有模块共享。

---

# 18.9 Secret Management

统一管理：

```
API Key

Access Token

OAuth Secret

Database Password

Private Key
```

禁止：

硬编码。

建议：

统一接入：

```
Vault

AWS Secrets Manager

Azure Key Vault

Environment Variables
```

---

# 18.10 Encryption

支持：

```
TLS

HTTPS

AES

RSA
```

敏感数据：

默认加密。

---

# 18.11 Budget

统一预算：

例如：

```
Daily Budget

Monthly Budget

LLM Budget

Provider Budget
```

Runtime：

实时控制。

---

# 18.12 Quota

支持：

```
Daily Request

Token Limit

API Call Limit

Concurrent Task
```

统一限制。

---

# 18.13 Policy

统一策略：

例如：

```
禁止调用某模型

禁止联网

禁止导出

禁止调用高成本 Provider
```

无需修改代码。

---

# 18.14 Compliance

支持：

```
GDPR

ISO27001

SOC2

企业内部规范
```

统一管理。

---

# 18.15 Audit

记录：

```
谁

什么时候

执行什么

访问什么

生成什么
```

支持：

长期保存。

---

# 18.16 Data Classification

数据分级：

例如：

```
Public

Internal

Confidential

Restricted
```

不同等级：

不同权限。

---

# 18.17 Resource Governance

统一限制：

```
CPU

Memory

GPU

Disk

Network
```

避免：

资源争抢。

---

# 18.18 Cost Governance

统一控制：

```
LLM

Provider

Plugin

Storage

Network
```

自动统计。

自动限制。

---

# 18.19 Multi-Tenant

支持：

```
Tenant A

Tenant B

Tenant C
```

数据：

完全隔离。

---

# 18.20 Workspace

支持：

```
Research

Production

Development
```

不同 Workspace：

独立配置。

---

# 18.21 Plugin Security

所有 Plugin：

必须声明：

```
Permission

Capability

Network Access

Filesystem Access
```

统一审核。

---

# 18.22 Provider Security

Provider：

禁止：

直接暴露：

```
API Key

Cookie

Secret
```

全部：

统一托管。

---

# 18.23 Reasoning Governance

限制：

```
最大 Token

最大轮数

最大 Expert 数

最大成本
```

避免：

无限推理。

---

# 18.24 Report Governance

支持：

```
Watermark

Signature

Export Permission

Confidential Label
```

企业版：

推荐启用。

---

# 18.25 Event Governance

所有：

Audit Event：

永久保存。

例如：

```
Delete Report

Export PDF

Policy Changed
```

方便：

审计。

---

# 18.26 Best Practices

推荐：

统一：

- Secret Manager
- RBAC
- Budget
- Audit
- Policy Engine

不要：

各模块：

自行管理权限。

---

# 18.27 Relationship

```
Runtime

↓

Security

↓

Governance

↓

Audit
```

整个系统：

统一治理。

---

# 18.28 Design Principles

Security 必须：

- Zero Trust
- Least Privilege
- Encryption by Default
- Audit Everything

Governance 必须：

- Policy First
- Budget First
- Compliance Ready
- Observable

---

架构
不要把 Policy 分散到多个模块，而是建立一个统一的 Policy Engine（作为 Security & Governance 的内部组件）
Security & Governance
│
├── Identity Manager
├── Authentication
├── Authorization (RBAC)
├── Secret Manager
├── Policy Engine        ⭐
├── Budget Manager
├── Quota Manager
├── Compliance Center
├── Audit Center
└── Governance Center

Policy Engine 的职责

整个系统所有策略统一由它管理，例如：

Runtime Policy
最大并发 Task
最大 Workflow 深度
最大 Token 数
Reasoning Policy
最大 Discussion 轮数
是否允许 Reflection
是否启用 Critic
Provider Policy
是否允许访问外网
是否允许付费 API
数据源优先级
Plugin Policy
哪些插件允许加载
哪些插件只能管理员启用
Report Policy
是否允许导出 PDF
是否允许生成外部分享链接

这样，所有策略配置集中在一个 Policy Engine，而不是分散在 Runtime、Reasoning、Decision、Provider 等模块中，整个 FAOS 的治理体系会更加统一、可维护，也更适合企业级部署

# 18.29 Summary

Security & Governance 为 FAOS 提供统一的安全与治理能力。

它覆盖身份认证、权限控制、Secret 管理、预算限制、策略治理、审计追踪、多租户隔离和合规管理，确保整个 AI Agent 平台安全、可控、可审计，并满足企业级部署要求。

---


# Chapter 19 - Deployment Architecture

> Financial Agent Operating System (FAOS)
>
> Version: V5.0
>
> Status: Architecture Frozen

---

# Chapter 19 - Deployment Architecture

> **Deployment Architecture 定义 FAOS 的运行方式。**

本章节描述：

- 系统如何部署
- 服务如何拆分
- Worker 如何运行
- AI 如何扩容
- 数据如何流动
- 多机如何协同

Deployment 不属于业务架构。

而属于：

> **运行架构（Runtime Architecture）。**

---

# 19.1 Purpose

Deployment Architecture 定义：

整个 FAOS 如何从：

```
单机 Demo
```

演进到：

```
企业级 AI Agent Platform
```

保证：

- 高可用
- 高扩展
- 高性能
- 高稳定
- 易维护

---

# 19.2 Deployment Principles

FAOS 采用：

```
Cloud Native

Plugin First

Stateless

Horizontal Scaling

Event Driven
```

所有核心 Service：

默认：

无状态。

---

# 19.3 Deployment Layers

整个部署：

建议：

```
Client Layer

↓

Gateway Layer

↓

Task Runtime Layer

↓

Business Service Layer

↓

Infrastructure Layer

↓

External Systems
```

---

# 19.4 Client Layer

支持：

```
Web

Desktop

Mobile

REST API

MCP Client

CLI

SDK
```

统一：

访问：

Gateway。

---

# 19.5 Gateway Layer

Gateway：

负责：

```
Authentication

Routing

Rate Limit

Load Balance

Logging

API Version
```

Gateway：

不执行业务。

---

# 19.6 Runtime Layer

Runtime：

负责：

```
Task Runtime

Execution Engine

Execution Context

Scheduler
```

这是：

整个系统入口。

---

# 19.7 Business Layer

Business Layer：

包括：

```
Domain

Capability

Workflow

Skill

Provider

Knowledge

Reasoning

Decision

Report
```

全部：

插件化。

---

# 19.8 Infrastructure Layer

包括：

```
Connector

Database

Object Storage

Vector DB

Cache

Message Queue

Monitoring
```

整个 Runtime：

依赖：

Infrastructure。

---

# 19.9 Storage

建议：

统一：

```
SQLite

DuckDB

PostgreSQL

Object Storage
```

根据：

部署规模：

选择。

---

# 19.10 Cache

支持：

```
Memory

Redis

Disk Cache
```

统一：

Cache Layer。

---

# 19.11 Queue

支持：

```
RabbitMQ

Kafka

Redis Stream

NATS

SQS
```

Event Bus：

可以：

接入。

---

# 19.12 Scheduler

Scheduler：

负责：

```
Periodic Task

Cron

Retry

Timeout

Delayed Task
```

统一调度。

---

# 19.13 Worker

支持：

多个 Worker。

例如：

```
Reasoning Worker

Provider Worker

Report Worker

Plugin Worker
```

独立扩容。

---

# 19.14 AI Worker

建议：

Reasoning：

独立部署。

例如：

```
DeepSeek Worker

Claude Worker

GPT Worker
```

避免：

互相影响。

---

# 19.15 Connector Worker

Provider：

调用：

Connector。

例如：

```
AkShare Worker

REST Worker

MCP Worker

SQL Worker
```

统一管理。

---

# 19.16 Scaling

所有 Worker：

支持：

```
Horizontal Scaling
```

例如：

```
Reasoning x10

Provider x5

Report x2
```

Runtime：

自动调度。

---

# 19.17 High Availability

支持：

```
Multiple Runtime

Multiple Queue

Multiple Cache

Multiple Database
```

避免：

单点故障。

---

# 19.18 Multi Region

支持：

```
CN

Singapore

US

EU
```

Runtime：

就近部署。

---

# 19.19 Container

推荐：

```
Docker
```

作为：

默认运行方式。

企业版：

支持：

```
Kubernetes
```

---

# 19.20 Kubernetes

建议：

拆分：

```
Runtime Pod

Reasoning Pod

Provider Pod

Report Pod

Gateway Pod
```

支持：

自动扩缩容。

---

# 19.21 MCP Deployment

MCP：

作为：

独立 Runtime。

例如：

```
Filesystem MCP

GitHub MCP

Browser MCP
```

Runtime：

统一访问。

---

# 19.22 Object Storage

统一保存：

```
Artifacts

Report

Chart

Trace

Prompt Snapshot
```

推荐：

```
S3

MinIO

OSS
```

---

# 19.23 Database

建议：

职责划分：

```
Configuration

↓

SQLite/PostgreSQL

Trace

↓

ClickHouse

Knowledge

↓

Vector DB

Artifacts

↓

Object Storage
```

避免：

单数据库。

---

# 19.24 Monitoring

统一：

```
Prometheus

Grafana

OpenTelemetry
```

企业部署：

默认启用。

---

# 19.25 Disaster Recovery

支持：

```
Backup

Snapshot

Replay

Restore
```

保证：

业务连续性。

---

# 19.26 CI/CD

推荐：

```
GitHub Actions

GitLab CI

Jenkins

ArgoCD
```

统一部署。

---

# 19.27 Environment

支持：

```
Development

Testing

Staging

Production
```

配置：

隔离。

---

# 19.28 Best Practices

推荐：

所有 Service：

无状态。

所有状态：

放入：

```
Database

Object Storage

Cache
```

方便：

水平扩展。

---

# 19.29 Relationship

```
Gateway

↓

Runtime

↓

Business Service

↓

Infrastructure

↓

External Systems
```

整个系统：

层次清晰。

职责明确。

---

架构建议
                Client
                   │
                   ▼
          API Gateway / MCP Gateway
                   │
                   ▼
        Task Runtime Cluster
                   │
      ┌────────────┼────────────┐
      ▼            ▼            ▼
Business      AI Workers    Data Workers
 Services                     (Connector)
      │            │            │
      └────────────┼────────────┘
                   ▼
          Infrastructure Layer
		  

其中：

Business Services：Domain、Capability、Workflow、Skill、Decision、Report 等业务服务。
AI Workers：Reasoning、Planner、Discussion、Reflection、Critic 等 AI 推理能力，可根据模型负载独立扩容。
Data Workers：Provider、Connector、MCP、Web Search、数据库访问等数据获取能力，可根据数据访问压力独立扩容
		  

# 19.30 Summary

Deployment Architecture 定义了 FAOS 从单机到企业级平台的部署模型。

通过 Gateway、Task Runtime、Business Service、Infrastructure、Worker、Queue、Object Storage 和 Kubernetes，FAOS 能够实现高可用、高扩展、高性能的运行架构，并支持多模型、多数据源、多租户和企业级生产部署。

---


# Chapter 20 - FAOS Architecture Principles

> Financial Agent Operating System (FAOS)
>
> Version: V5.0 (Frozen Architecture)
>
> Status: Final Architecture Principles

---

# Chapter 20 - FAOS Architecture Principles

> **本章定义 FAOS 的最高设计原则（Architecture Constitution）。**

前面的章节介绍了：

- Runtime
- Domain
- Capability
- Workflow
- Skill
- Provider
- Knowledge
- Reasoning
- Decision
- Report

本章定义：

> **为什么这样设计。**

也就是：

整个 FAOS 永远遵守的架构原则。

这是所有开发者都必须遵循的最高规范。

---

# 20.1 Design Philosophy

FAOS 的目标不是：

> 构建一个聊天机器人（ChatBot）。

也不是：

> 构建一个 Prompt 工程。

而是：

> **构建一个可持续演进的 AI Operating System。**

因此：

所有设计必须满足：

- 可扩展
- 可维护
- 可组合
- 可替换
- 可测试
- 可观察

---

# 20.2 Separation of Concerns

系统最大的原则：

> **一个模块只负责一件事情。**

例如：

Task Runtime

负责：

任务生命周期。

Reasoning

负责：

分析。

Decision

负责：

决策。

Provider

负责：

获取数据。

Report

负责：

展示。

任何模块：

不要跨职责。

---

# 20.3 Capability First

FAOS 永远围绕：

```
Capability
```

组织。

而不是：

```
Tool
```

也不是：

```
Provider
```

例如：

用户需要：

```
Financial Analysis
```

Runtime：

自动找到：

```
Workflow

↓

Skill

↓

Provider
```

LLM 永远不知道：

Provider。

---

# 20.4 Data First

LLM：

不是：

数据来源。

数据：

必须来自：

```
Provider

Knowledge

Execution Context
```

LLM：

负责：

理解。

不是：

生成事实。

---

# 20.5 Evidence First

任何分析：

必须：

绑定：

Evidence。

例如：

```
ROE

↓

Financial Statement
```

```
利润增长

↓

Income Statement
```

禁止：

没有证据的结论。

---

# 20.6 Context First

所有模块：

共享：

```
Execution Context
```

而不是：

互相调用。

Context：

成为：

整个 Runtime 的唯一事实来源（Single Source of Truth）。

---

# 20.7 Runtime Driven

整个系统：

由：

Task Runtime

驱动。

不是：

Workflow。

不是：

LLM。

不是：

Skill。

Runtime：

负责：

统一协调。

---

# 20.8 Plugin First

所有扩展：

必须：

Plugin。

例如：

新增：

```
Bloomberg

↓

Provider Plugin
```

新增：

```
Crypto

↓

Domain Plugin
```

新增：

```
Research Report

↓

Knowledge Plugin
```

禁止：

修改：

Runtime。

---

# 20.9 Event Driven

模块之间：

禁止：

直接调用。

例如：

```
Workflow

×

Report
```

必须：

```
Workflow

↓

Event

↓

Report
```

实现：

解耦。

---

# 20.10 Stateless

所有 Service：

默认：

无状态。

状态：

统一：

进入：

Execution Context。

方便：

扩容。

---

# 20.11 Explainable AI

所有 AI：

必须：

解释：

```
为什么？

依据是什么？

风险是什么？
```

Explainability：

不是：

可选功能。

而是：

默认能力。

---

# 20.12 Model Independent

系统：

不能依赖：

任何模型。

例如：

```
Claude

GPT

DeepSeek

Gemini

Qwen

Kimi
```

全部：

可以替换。

Reasoning：

保持统一接口。

---

# 20.13 Provider Independent

系统：

不能依赖：

任何数据源。

例如：

```
AkShare

Yahoo

Polygon

Wind

TuShare
```

全部：

通过：

Provider。

---

# 20.14 Connector Independent

系统：

不能依赖：

任何协议。

例如：

```
REST

MCP

GraphQL

SQL

Filesystem
```

统一：

Connector。

---

# 20.15 Workflow Independent

Workflow：

只是：

业务流程。

不是：

系统核心。

新增 Workflow：

不修改：

Runtime。

---

# 20.16 Domain Independent

新增：

```
Crypto
```

不影响：

```
Stock
```

新增：

```
Medical
```

不影响：

```
Finance
```

Domain：

完全独立。

---

# 20.17 Configuration Driven

所有行为：

尽可能：

配置驱动。

例如：

```
Prompt

Policy

Provider

Workflow

Capability

Budget
```

避免：

写死。

---

# 20.18 Convention over Configuration

系统：

提供：

默认规范。

例如：

```
plugins/

skills/

providers/
```

开发者：

遵循约定。

无需：

大量配置。

---

# 20.19 Observable by Default

任何执行：

默认：

生成：

```
Trace

Metrics

Event

Log
```

不是：

调试时：

才开启。

---

# 20.20 Secure by Default

默认：

启用：

```
Permission

Secret

Policy

Audit

Encryption
```

不是：

企业版：

才有。

---

# 20.21 Testable by Design

所有模块：

支持：

```
Unit Test

Integration Test

Replay Test

Simulation Test
```

避免：

黑盒。

---

# 20.22 Version Everything

统一版本：

```
Workflow

Skill

Prompt

Knowledge

Decision

Report

Policy
```

支持：

长期演进。

---

# 20.23 Backward Compatibility

升级：

不能：

破坏：

已有 Workflow。

已有：

Plugin。

已有：

Report。

保持：

兼容。

---

# 20.24 Anti-Patterns

禁止：

```
LLM

↓

HTTP
```

禁止：

```
LLM

↓

SQL
```

禁止：

```
LLM

↓

AkShare
```

禁止：

```
Workflow

↓

Provider
```

禁止：

跨层调用。

---

# 20.25 Golden Flow

整个系统：

统一流程：

```
Task

↓

Runtime

↓

Workflow

↓

Capability

↓

Skill

↓

Provider

↓

Execution Context

↓

Knowledge

↓

Reasoning

↓

Decision

↓

Report
```

这是：

唯一推荐流程。

---

# 20.26 Future Evolution

未来：

可以新增：

```
Planning Service

Learning Service

Memory Service

Simulation Service

Optimization Service
```

但：

不修改：

当前核心分层。

---

# 20.27 Architecture Stability

冻结：

以下核心层：

```
Task Runtime

Domain

Capability

Workflow

Skill

Provider

Knowledge

Reasoning

Decision

Report
```

以后：

只扩展。

不重构。

---

# 20.28 FAOS Mission

FAOS 的使命：

> 建立一个统一、开放、可解释、可扩展、面向 AI Agent 的金融智能操作系统。

---

# 20.29 Summary

FAOS 的全部设计围绕四个核心理念展开：

- Runtime 统一调度
- Capability 抽象能力
- Context 统一事实
- Plugin 持续扩展

所有模块职责单一，所有能力可替换，所有流程可追踪，所有结果可解释。

这构成了 FAOS 的长期演进基础，也是整个系统的最高架构规范。

---

# 20.30 Frozen Architecture

最终冻结架构如下：

```
                         Client
                            │
                            ▼
                    API / Gateway Layer
                            │
                            ▼
                     Task Runtime Layer
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
     Domain            Capability          Workflow
        │                   │                   │
        └───────────────────┼───────────────────┘
                            ▼
                         Skill Layer
                            │
                            ▼
                       Provider Layer
                            │
                            ▼
                    Execution Context
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
     Knowledge          Reasoning          Decision
                            │
                            ▼
                        Report Layer
                            │
                            ▼
                  Event Bus & Observability
                            │
                            ▼
               Security & Governance Layer
                            │
                            ▼
                Plugin & Deployment Platform
```

> **自本版本起，以上分层作为 FAOS Frozen Architecture（冻结架构），后续版本仅允许扩展模块能力、接口和插件，不再调整核心分层结构。**

---


补充章节：
# Chapter 21 - Prompt & Context Engineering

> Financial Agent Operating System (FAOS)
>
> Version: V5.0
>
> Status: Architecture Specification

---

# 21. Prompt & Context Engineering

Prompt Engineering 并不是 Prompt 编写。

在 FAOS 中：

Prompt Engineering = Runtime 如何构建 Context。

Prompt 只是最终产物。

真正重要的是：

```
Knowledge

+

Capability

+

Execution Context

+

Task

+

Policy

↓

Prompt Builder

↓

LLM
```

---

# 21.1 Goal

Prompt Builder：

负责：

自动生成 Prompt。

而不是：

开发人员手写 Prompt。

---

# 21.2 Prompt Pipeline

统一流程：

```
Task

↓

Execution Context

↓

Capability Catalog

↓

Knowledge Pack

↓

Policy

↓

Prompt Builder

↓

Prompt
```

---

# 21.3 Prompt Components

Prompt：

由：

```
System

Role

Capability

Knowledge

Evidence

Context

Constraints

Output Schema
```

组成。

---

# 21.4 Context First

Prompt：

不是：

输入。

Execution Context：

才是真正输入。

Prompt：

只是：

Context 的表达方式。

---

# 21.5 Capability Catalog

LLM：

只知道：

```
Financial Analysis

News Analysis

Risk Analysis

Valuation
```

不知道：

Skill。

不知道：

Provider。

---

# 21.6 Skill Catalog

Skill Catalog：

Runtime 内部使用。

例如：

```
financial_skill

news_skill

macro_skill
```

Prompt：

默认：

不暴露。

---

# 21.7 Dynamic Prompt

Prompt：

运行时生成。

例如：

根据：

```
Task

Domain

Capability

Policy
```

自动变化。

---

# 21.8 Prompt Template

所有 Prompt：

模板化。

例如：

```
Financial Analysis

Macro Analysis

Risk Analysis
```

统一维护。

---

# 21.9 Context Compression

Context 超长：

自动：

摘要。

保留：

Evidence。

删除：

重复内容。

---

# 21.10 Evidence Injection

所有 Prompt：

自动：

注入：

Evidence。

禁止：

LLM 自行假设。

---

# 21.11 Knowledge Injection

Knowledge：

不是：

全部加载。

Runtime：

自动：

选择。

---

# 21.12 Output Schema

所有 Prompt：

定义：

JSON Schema。

保证：

输出稳定。

---

# 21.13 Prompt Version

Prompt：

支持：

```
v1

v2

v3
```

统一升级。

---

# 21.14 Design Principles

Prompt：

必须：

- Dynamic
- Structured
- Capability Driven
- Context Driven
- Evidence First

---

# 21.15 Summary

Prompt 不是开发者写出来的。

Prompt 是 Runtime 根据：

Execution Context、

Knowledge、

Capability、

Policy

动态生成的。

Prompt Builder 是整个 Runtime 的核心组件。


# Chapter 22 - AI Collaboration Protocol

> Financial Agent Operating System (FAOS)

---

# 22. AI Collaboration Protocol

本章节定义：

多个 AI 如何协同工作。

不是：

多个 Prompt。

而是：

多个智能体。

---

# 22.1 Goal

统一：

Agent 通信协议。

避免：

Prompt 拼接。

---

# 22.2 Agent Roles

例如：

```
Planner

Financial Expert

Macro Expert

Risk Expert

Reviewer

Critic

Decision Arbiter
```

---

# 22.3 Agent Lifecycle

```
Create

↓

Assign Role

↓

Reasoning

↓

Discussion

↓

Reflection

↓

Consensus

↓

Finish
```

---

# 22.4 Planner

Planner：

负责：

拆解任务。

选择：

Capability。

不是：

调用 Tool。

---

# 22.5 Expert

Expert：

只负责：

自己的领域。

例如：

Financial。

---

# 22.6 Reviewer

负责：

检查：

Expert 输出。

---

# 22.7 Critic

寻找：

逻辑漏洞。

证据不足。

引用错误。

---

# 22.8 Arbiter

多个 Expert：

意见冲突。

Arbiter：

最终裁决。

---

# 22.9 Consensus

输出：

统一观点。

不是：

多个答案。

---

# 22.10 Communication

Agent：

共享：

Execution Context。

禁止：

互相拼 Prompt。

---

# 22.11 Message Schema

统一：

```
Role

Task

Evidence

Reasoning

Confidence

Citation
```

---

# 22.12 Reflection

每轮：

自动：

Reflection。

---

# 22.13 Memory

共享：

Execution Context。

不是：

共享 Prompt。

---

# 22.14 Trace

记录：

全部 Discussion。

Replay。

---

# 22.15 Design Principles

AI Collaboration：

必须：

- Role Based
- Capability Driven
- Evidence First
- Shared Context
- Structured Message

---

# 22.16 Summary

多个 AI：

不是：

多个 Chat。

而是：

多个 Role。

共享：

Execution Context。

通过统一协议协作。

Runtime：

负责协调。

LLM：

负责推理。
