# FAOS (Financial Agent Operating System) 开发指南

## 1. 架构总览与核心原则

FAOS 不是传统的“大模型调用工具”，而是一个**Task Runtime 驱动的事件响应式操作系统**。
LLM 在其中仅作为推理组件（Reasoning Service），整个系统的运转由 Task（任务）和 Event（事件）驱动。

开发 FAOS 时，必须严格遵守以下核心原则（摘自 V5 冻结架构）：
1. **Task First**: 一切皆 Task。用户的请求必须解析并转换为 Task，它是系统内的一等公民。
2. **Runtime Driven**: 系统有且只有一个 Runtime (`Task Runtime`)，负责生命周期和调度，不涉及具体业务。
3. **Service Oriented**: 所有能力皆服务。包括 Domain, Capability, Workflow, Skill, Provider, Reasoning 等。
4. **Event Driven**: 模块之间**禁止直接相互调用**。必须通过向事件总线（Event Bus）发布事件来解耦。
5. **Data First**: 数据在各个 Provider 之间流动必须是结构化（Standard Model）的，LLM 只处理结构化数据，禁止 Provider 直接返回 Prompt 文本。

## 2. 目录结构规范

推荐的 Python 目录结构如下，所有核心模块和 Service 都通过插件化方式注册：

```
faos/
├── core/                   # 核心基础层
│   ├── runtime.py          # Task Runtime 实现
│   ├── event_bus.py        # 内存/分布式事件总线
│   ├── context.py          # Execution Context，存储变量和共享状态
│   └── models.py           # 核心领域模型（Task, Event等基础定义）
├── execution/              # 调度与执行层
│   ├── engine.py           # Execution Engine (DAG 解析与执行)
│   └── planner.py          # Planner Pipeline (Task 转 Plan)
├── services/               # 插件化服务层 (所有的业务实现放在这里)
│   ├── provider/           # 数据源接口 (e.g. YahooFinanceProvider)
│   ├── skill/              # 业务技能 (e.g. StockAnalyzeSkill)
│   ├── workflow/           # 流程组合服务
│   ├── reasoning/          # LLM 推理接口包装
│   ├── domain/             # 领域知识服务
│   └── ...                 
├── api/                    # 对外暴露的接口层 (REST API, WebSockets)
├── tests/                  # 测试用例
├── main.py                 # 系统启动入口点
└── requirements.txt        # 依赖清单
```

## 3. 开发范式 - 如何编写一个新的 Service

1. **实现接口**: 所有 Service 必须继承自相应的基类（如 `BaseSkill`, `BaseProvider`）。
2. **事件驱动交互**:
   - 不要写 `result = some_service.do_something()`
   - 应该写 `self.event_bus.publish(Event(type="ProviderRequested", payload={...}))`
   - 然后监听对应的完成事件：`@event_bus.subscribe("ProviderCompleted")`
3. **隔离性原则**:
   - Skill **绝对不能**直接发 HTTP 请求访问第三方数据。
   - 数据获取必须交由 **Provider** 负责。Skill 只监听 Provider 发出的数据事件，然后进行业务处理。

## 4. 技术栈选型

- **语言**: Python 3.10+
- **并发与异步**: `asyncio`，由于事件驱动特性，所有核心组件均应异步化。
- **数据校验**: `Pydantic` V2，用于定义结构化事件 Payload、Provider 统一输出模型等。
- **事件总线**: MVP 阶段使用 `asyncio.Queue` 实现内存 Pub/Sub 模式。
