# FAOS TradingAgents

FAOS TradingAgents is an advanced, multi-agent financial analysis and trading simulation platform driven by Large Language Models (LLMs). Built on a robust, asynchronous EventBus architecture, it coordinates expert AI personas to fetch market data, analyze fundamentals and technicals, conduct rigorous bull/bear debates, and execute simulated trades with risk guardrails.

## Key Features

1. **Multi-Agent Debate Protocol (Discussion Service)**
   - **Bull & Bear Researchers**: Generate competing investment hypotheses.
   - **Research Manager**: Synthesizes debates into a unified consensus.
   - **Chief Risk Officer (CRO)**: Enforces strict hedging constraints and risk guardrails.
   - **Portfolio Manager (PM)**: Translates consensus and risk profiles into actionable trading signals (Buy/Sell/Hold).

2. **Extensible Plugin & Capability Architecture**
   - Built on a "Frozen Architecture" (V5). Core runtime is decoupled from business logic.
   - Expand capabilities simply by registering new Skills and Workflows.
   - Native integration with `yfinance` for live quotes, earnings estimates, and market news.

3. **Backtesting Engine**
   - Time-series loop simulation (`BacktestWorkflow`).
   - Evaluates LLM trading strategies against historical data.
   - `PortfolioTracker` tracks PnL, cash reserves, and maximum drawdowns without look-ahead bias.

4. **Rich Visualizations (Frontend)**
   - **Agent Debate Map**: See the explicit tree of how information flows from researchers to the final PM decision.
   - **Alpha Score Radar**: Multi-dimensional visual evaluation across Fundamentals, Technicals, Sentiment, Macro, and Risk metrics.
   - **Market Charts**: Integrated `recharts` for charting asset price history.

## Architecture

- **Backend**: Python 3.13+, FastAPI, Uvicorn, asyncio EventBus.
- **Frontend**: React, TypeScript, Vite, Recharts, Tailwind CSS.

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- npm

### Installation

1. **Install Backend Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
2. **Install Frontend Dependencies:**
   ```bash
   cd frontend
   npm install
   ```

### Running the System

You can easily start and stop the system using the provided PowerShell scripts:

- **Start Services**: Run `.\start.ps1` to launch both the FastAPI backend and the Vite frontend.
- **Stop Services**: Run `.\stop.ps1` to cleanly terminate both background processes.

Alternatively, manually start them:
- **Backend**: `uvicorn faos.api.server:app --port 8001`
- **Frontend**: `cd frontend && npm run dev`

### Configuration

The frontend UI provides a Settings panel where you can configure the LLM backend:
- Support for Mock models (local testing), Gemini, DeepSeek, and OpenRouter (GPT-4, Claude 3.5).
- Input your API keys dynamically through the UI.

## Project Structure

- `faos/core/`: EventBus, Task Runtime, Execution Engine.
- `faos/services/`: Modular service layers (Skill, Workflow, Provider, Reasoning, Discussion, Decision).
- `faos/api/`: FastAPI server endpoints.
- `frontend/`: React single-page application.
