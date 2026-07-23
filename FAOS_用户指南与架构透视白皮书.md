# FAOS TradingAgents - 用户使用指南与架构透视白皮书

欢迎使用 **FAOS (Financial Analysis Operating System) TradingAgents**。本项目是一个基于大语言模型（LLM）驱动的**多智能体金融量化分析与模拟交易操作系统**。

本指南将为您详细解析系统架构、数据流转、核心工作流以及各 AI 智能体的透视说明，帮助您快速上手并深入理解系统底层运行逻辑。

---

## 目录
1. [快速上手指南](#1-快速上手指南)
2. [项目顶层架构 (V5 Frozen)](#2-项目顶层架构)
3. [标准分析与数据工作流](#3-标准分析与数据工作流)
4. [AI 智能体 (Agent) 深度透视](#4-ai-智能体-agent-深度透视)
5. [回测引擎运行机制](#5-回测引擎运行机制)

---

## 1. 快速上手指南

### 1.1 系统启动与配置
- **一键启动**：在项目根目录下双击或在 PowerShell 中运行 `.\start.ps1`，将自动在后台启动 FastAPI 后端服务器（`8001` 端口）与 React 前端 Web 服务（`5173` 端口）。
- **一键退出**：运行 `.\stop.ps1` 可以安全地关闭所有关联进程。
- **配置大模型 (LLM)**：打开浏览器进入 `http://localhost:5173`，点击右上角的 **设置 (⚙️) 按钮**：
  - **Provider (平台)**：支持 `mock`（本地调试假数据）、`gemini`、`deepseek`、`openrouter`。
  - **Model (模型)**：根据平台选择对应的高级推理模型（如 `gpt-4o`, `claude-3.5-sonnet`, `gemini-pro-1.5`）。
  - **API Key**：填入您的认证秘钥（若留空则尝试读取系统默认环境变量）。

### 1.2 发起分析与回测任务
在顶部输入框中，输入自然语言指令（Intent），例如：
- **“分析 AAPL 的财报与技术面走势”**：触发标准分析流（AnalyzeStockWorkflow）。
- **“Backtest TSLA”**：触发历史回测模拟工作流（BacktestWorkflow）。

系统将以非阻塞的异步事件流形式，在左侧舞台分阶段实时展示 AI 的思考过程、市场图表、智能体辩论图谱以及最终决策雷达图，同时右侧记录实时的系统级事件轨迹 (Event Trace)。

---

## 2. 项目顶层架构

FAOS 严格遵循“核心底座与业务逻辑分离”的架构原则，整体分为三大层级：

### 2.1 任务执行引擎层 (Core Runtime & EventBus)
系统的“心脏”。所有组件通过轻量级的基于 `asyncio` 的 **EventBus (事件总线)** 进行松耦合通信。
- **TaskRuntime**：负责任务生命周期管理。当用户提交请求时，初始化 `ExecutionContext`（执行上下文）。
- **Planner (规划器)**：接收自然语言意图，映射到注册好的 `Workflow`（有向无环图 DAG），解析依赖顺序。
- **Execution Engine (执行引擎)**：按照依赖关系（如数据必须在分析前获取），并行或串行地分发能力 (Capability) 请求给对应的 Skill。

### 2.2 微服务与技能抽象层 (Services & Skills)
系统的“四肢”。每一个具体的动作被封装为 `Skill`，这些技能调用底层的微服务。
- **ProviderService**：数据适配器。目前对接了 `yfinance` 等外部 API，负责抓取股票行情、财务预期、新闻和计算情感得分。
- **ReasoningService**：大语言模型推理底座，管理统一的 Prompt 封装与 API 调用。
- **DecisionService & DiscussionService**：上层金融分析与量化逻辑的载体（下文 Agent 透视将详细介绍）。

### 2.3 前端可视化层 (Frontend UI)
React 单页应用，通过 WebSocket 连接后端。使用 `recharts` 渲染市场 K 线、雷达评分图，利用分层卡片展示多智能体辩论树 (`AgentDebateMap`)。

---

## 3. 标准分析与数据工作流

当触发 `AnalyzeStockWorkflow` 时，数据的生命周期与流转链路如下：

1. **节点 1 & 2：数据源抓取 (Fetch Data & News)**
   - **数据流出**：调用 `yfinance`。获取价格历史（用于画图）、EPS 预测值、营业收入预测值等前瞻性指标；同时抓取相关新闻，并通过轻量级算法进行情感极性评分（Sentiment 0~1）。
   - **状态存储**：原始数据被写入当前任务的 `ExecutionContext` 中。

2. **节点 3：多维独立分析 (Analyze Node)**
   - 唤醒 4 个虚拟分析师。将步骤 1 的数据注入 Prompt，分别生成四个视角的结构化报告：
     - **基本面分析**：基于 EPS 和营收预测进行估值模型推导。
     - **技术面分析**：量价趋势评估。
     - **情绪与新闻分析**：舆情热度计算。
     - **宏观环境分析**：行业与系统性风险。

3. **节点 4：多智能体辩论 (Discussion Node)**
   - 这是**信息流的高潮**。数据进入“对冲辩论”阶段（详细见下方Agent透视）。

4. **节点 5：最终决策 (Decision Node)**
   - 提取辩论共识，并由投资组合经理（PM）生成买卖指令。系统内置 `PolicyEngine`（策略引擎）会在此处将定性文本转化为 0-100 的定量打分，并在前端生成多维**雷达图**。

---

## 4. AI 智能体 (Agent) 深度透视

FAOS 系统最核心的亮点是防止 AI 出现“幻觉”和“附和倾向”的**对抗性多智能体机制**。它们被严格划分为三个梯队：

### 📈 梯队一：独立研究员 (The Researchers)
- **Bull Researcher (多头研究员)**：
  - **角色约束**：只能寻找和放大看涨信号（利好财报、技术突破）。
  - **核心任务**：构建最乐观的投资论点。
- **Bear Researcher (空头研究员)**：
  - **角色约束**：必须充当“魔鬼代言人”。被严格要求挖掘数据缺失、过度估值以及潜在的暴雷风险（例如：提示由于缺乏散户另类数据而导致的羊群效应盲区）。
  - **核心任务**：无情地攻击多头逻辑。

### ⚖️ 梯队二：研究主管与风控 (The Managers)
- **Research Manager (研究主管)**：
  - **核心任务**：不再抓取原始数据，而是**只阅读**多空双方的辩论记录。负责调和矛盾，产出不偏不倚的《投资共识计划 (Investment Plan)》。
- **Chief Risk Officer (首席风控官 CRO)**：
  - **特殊约束**：在 Prompt 中被注入了极其严格的“量化对冲纪律”。
  - **核心任务**：对主管的投资计划进行压力测试，强制要求给出止损线（Stop Loss）、仓位限制（Position Sizing）以及黑天鹅对冲方案。

### 💰 梯队三：交易执行 (The Executioners)
- **Portfolio Manager (PM) & Trader**：
  - 接收经过风控过滤的共识计划，根据系统风险偏好下达最终的指令（Action: BUY / SELL / HOLD），并计算确定性置信度（Confidence）。

---

## 5. 回测引擎运行机制 (Backtesting Engine)

系统内置了历史模拟回测工作流 (`BacktestWorkflow`)：

1. **时间旅行沙盒 (`BacktestInitSkill`)**：
   - 初始化一个虚拟的 `PortfolioTracker`（默认初始资金 $100,000）。
   - 切分历史时间序列（如按周切片）。
2. **状态迭代 (`BacktestLoopSkill`)**：
   - 系统穿越到历史特定时间点，仅仅将**该时间点之前**的数据提供给智能体（严格杜绝未来函数）。
   - LLM 基于历史截面给出 BUY/HOLD/SELL 决策与置信度。
   - `PortfolioTracker` 根据决策执行模拟建仓/平仓，并更新现金流与持仓市值。
3. **回测指标输出**：
   - 循环结束后，系统将统计出**总收益率 (Total Return)**、**最大回撤 (Max Drawdown)** 以及交易胜率，为优化 Agent Prompt 提供闭环数据支撑。

---
*FAOS TradingAgents 致力于将华尔街顶级的多军/空军/风控对冲委员会机制，浓缩在一个开源、自动化、强可视化的 LLM 引擎中。祝您探索愉快！*
