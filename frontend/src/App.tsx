import React, { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { CheckCircle2, XCircle, BrainCircuit, MessageSquare, TrendingUp, FileText, ChevronRight, Activity, LineChart, Send, Zap, User, Bot, Sparkles, RefreshCw, History, Download, X, Target, LayoutGrid } from 'lucide-react';
import { MarketChart } from './components/MarketChart';
import { AgentDebateMap } from './components/AgentDebateMap';
import { ScoreRadar } from './components/ScoreRadar';
import { SettingsPopover } from './components/SettingsPopover';
import { HistoryModal, type HistoryRecord } from './components/HistoryModal';
import { AccuracyDashboardModal } from './components/AccuracyDashboardModal';
import { WatchlistDashboardModal } from './components/WatchlistDashboardModal';
import './index.css';

interface FAOSEvent {
  id: string;
  type: string;
  source: string;
  timestamp: string;
  payload: Record<string, any>;
}

interface AnalysisReport {
  analyst_type: string;
  market_context?: string;
  reasoning: string;
  conclusion: string;
}

interface TraderStrategy {
  trade_type?: string;
  entry_target?: string;
  stop_loss?: string;
  position_sizing?: string;
  justification?: string;
}

interface PMDecision {
  decision: string;
  confidence: string;
  reasoning: string;
}

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

const getNodeName = (nodeId: string, capability?: string) => {
  if (capability) {
    const capMap: Record<string, string> = {
      'FetchData': 'Fetch Market Data (Quote)',
      'FetchNews': 'Fetch News Data',
      'Analyze': 'Multi-Dimensional Analysis',
      'Discussion': 'Multi-Agent Debate & Consensus',
      'Decision': 'Trader Strategy & Verdict',
      'Reflection': 'Risk Reflection & Verification',
      'GenerateReport': 'Compile Final Report',
      'InitBacktest': 'Initialize Backtest Engine',
      'RunBacktestLoop': 'Run Backtest Simulation'
    };
    if (capMap[capability]) return capMap[capability];
  }
  const map: Record<string, string> = {
    'node1': 'Fetch Data',
    'node2': 'Fetch News Data',
    'node3': 'Multi-Dimensional Analysis',
    'node_discuss': 'Multi-Agent Debate & Consensus',
    'node_decision': 'Trader Strategy & Final Verdict',
    'node4': 'Compile Final Report'
  };
  return map[nodeId] || nodeId;
};

const MODEL_OPTIONS: Record<string, string[]> = {
  mock: ['mock-model'],
  gemini: ['gemini-3.5-flash', 'gemini-3.1-flash-lite', 'gemini-3.1-pro-preview'],
  deepseek: ['deepseek-v4-flash', 'deepseek-v4-pro'],
  openrouter: [
    'tencent/hy3:free',
    'openai/gpt-4o',
    'anthropic/claude-3.5-sonnet',
    'meta-llama/llama-3.3-70b-instruct',
    'google/gemini-pro-1.5'
  ]
};


function App() {
  // Phase: 'chat' = conversational planner phase, 'analysis' = running pipeline
  const [phase, setPhase] = useState<'chat' | 'analysis'>('chat');
  const [chatInput, setChatInput] = useState('');
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [isChatLoading, setIsChatLoading] = useState(false);

  const [showConfig, setShowConfig] = useState(false);
  const [llmProvider, setLlmProvider] = useState(() => localStorage.getItem('faos_provider') || 'mock');
  const [llmModel, setLlmModel] = useState(() => localStorage.getItem('faos_model') || 'gemini-3.5-flash');
  const [llmApiKey, setLlmApiKey] = useState(() => localStorage.getItem('faos_api_key') || '');
  const [llmLanguage, setLmLanguage] = useState(() => localStorage.getItem('faos_language') || 'zh');
  const [events, setEvents] = useState<FAOSEvent[]>([]);
  const [taskStatus, setTaskStatus] = useState<'idle' | 'running' | 'completed' | 'failed'>('idle');

  // Pipeline Data State
  const [marketData, setMarketData] = useState<{ time: string, value: number }[] | null>(null);
  const [analysisReports, setAnalysisReports] = useState<Record<string, AnalysisReport> | null>(null);
  const [discussion, setDiscussion] = useState<Record<string, any> | null>(null);
  const [decision, setDecision] = useState<{ trader?: TraderStrategy, pm?: PMDecision } | null>(null);
  const [reportContent, setReportContent] = useState<string | null>(null);
  const [currentSymbol, setCurrentSymbol] = useState('');

  // Post-Report Follow-up Chat State
  const [followUpInput, setFollowUpInput] = useState('');
  const [followUpHistory, setFollowUpHistory] = useState<ChatMessage[]>([]);
  const [isFollowUpLoading, setIsFollowUpLoading] = useState(false);
  const [showFollowUpThread, setShowFollowUpThread] = useState(true);

  // History Records State
  const [historyRecords, setHistoryRecords] = useState<HistoryRecord[]>(() => {
    try {
      const saved = localStorage.getItem('faos_history_records');
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });
  const [showHistoryModal, setShowHistoryModal] = useState(false);
  const [showAccuracyModal, setShowAccuracyModal] = useState(false);
  const [showWatchlistModal, setShowWatchlistModal] = useState(false);

  const sessionRef = useRef<{
    symbol: string;
    marketData: any;
    analysisReports: any;
    discussion: any;
    decision: any;
    reportContent: any;
  }>({
    symbol: '',
    marketData: null,
    analysisReports: null,
    discussion: null,
    decision: null,
    reportContent: null
  });

  const chatEndRef = useRef<HTMLDivElement>(null);
  const eventsEndRef = useRef<HTMLDivElement>(null);
  const followUpEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory]);

  useEffect(() => {
    eventsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [events]);

  useEffect(() => {
    followUpEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [followUpHistory]);

  // Sync history from SQLite backend on initial mount
  useEffect(() => {
    fetch('/api/history')
      .then(res => res.ok ? res.json() : null)
      .then(data => {
        if (Array.isArray(data) && data.length > 0) {
          setHistoryRecords(data);
          localStorage.setItem('faos_history_records', JSON.stringify(data));
        }
      })
      .catch(err => console.warn('SQLite history sync warning:', err));
  }, []);

  // Helper: Save current analysis session to history (SQLite + LocalStorage)
  const saveCurrentToHistory = (overrideReport?: string | null) => {
    const s = sessionRef.current;
    const targetSymbol = currentSymbol || s.symbol || 'Asset';
    const targetReport = overrideReport !== undefined ? overrideReport : (reportContent || s.reportContent);

    if (!targetSymbol && !targetReport && chatHistory.length === 0) return;

    const newRecord: HistoryRecord = {
      id: Date.now().toString(),
      timestamp: new Date().toLocaleString(),
      symbol: targetSymbol,
      chatHistory: [...chatHistory],
      followUpHistory: [...followUpHistory],
      reportContent: targetReport,
      decision: decision || s.decision,
      analysisReports: analysisReports || s.analysisReports,
      discussion: discussion || s.discussion,
      marketData: marketData || s.marketData
    };

    setHistoryRecords(prev => {
      const updated = [newRecord, ...prev.filter(r => r.id !== newRecord.id)].slice(0, 50);
      localStorage.setItem('faos_history_records', JSON.stringify(updated));
      return updated;
    });

    // Async sync to SQLite backend database
    fetch('/api/history', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newRecord)
    }).catch(err => console.error('Failed to save history to SQLite', err));
  };

  const handleSelectHistoryRecord = (record: HistoryRecord) => {
    setCurrentSymbol(record.symbol);
    setChatHistory(record.chatHistory || []);
    setFollowUpHistory(record.followUpHistory || []);
    setReportContent(record.reportContent);
    setDecision(record.decision);
    setAnalysisReports(record.analysisReports);
    setDiscussion(record.discussion);
    setMarketData(record.marketData);

    sessionRef.current = {
      symbol: record.symbol,
      marketData: record.marketData,
      analysisReports: record.analysisReports,
      discussion: record.discussion,
      decision: record.decision,
      reportContent: record.reportContent
    };

    setPhase('analysis');
    setShowHistoryModal(false);
  };

  const handleDeleteHistoryRecord = (id: string) => {
    setHistoryRecords(prev => {
      const updated = prev.filter(r => r.id !== id);
      localStorage.setItem('faos_history_records', JSON.stringify(updated));
      return updated;
    });

    fetch(`/api/history/${id}`, { method: 'DELETE' }).catch(err => console.error('Failed to delete history from SQLite', err));
  };

  const handleClearHistory = () => {
    setHistoryRecords([]);
    localStorage.removeItem('faos_history_records');

    fetch('/api/history', { method: 'DELETE' }).catch(err => console.error('Failed to clear history in SQLite', err));
  };

  // Helper: Export and Download HTML Report & Conversation Transcript
  const downloadHtmlReport = () => {
    const symbol = currentSymbol || 'Asset';
    const dateStr = new Date().toLocaleString();

    const reportHtml = `<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <title>FAOS 投研研报档案 - ${symbol}</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f172a; color: #e2e8f0; margin: 0; padding: 40px; line-height: 1.7; }
    .container { max-width: 920px; margin: 0 auto; background: #1e293b; padding: 40px; border-radius: 16px; border: 1px solid #334155; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5); }
    h1 { color: #818cf8; border-bottom: 2px solid #334155; padding-bottom: 15px; margin-top: 0; font-size: 26px; }
    h2 { color: #60a5fa; margin-top: 30px; border-bottom: 1px solid #334155; padding-bottom: 8px; font-size: 20px; }
    h3 { color: #fbbf24; font-size: 16px; margin-top: 20px; }
    .meta-bar { font-size: 14px; color: #94a3b8; margin-bottom: 30px; background: rgba(255,255,255,0.04); padding: 14px 20px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.08); }
    .card { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 22px; margin-bottom: 25px; }
    .badge { display: inline-block; padding: 6px 16px; border-radius: 9999px; font-weight: bold; font-size: 16px; text-transform: uppercase; margin-bottom: 12px; }
    .badge-BUY { background: rgba(16,185,129,0.2); color: #34d399; border: 1px solid #10b981; }
    .badge-SELL { background: rgba(239,68,68,0.2); color: #f87171; border: 1px solid #ef4444; }
    .badge-HOLD { background: rgba(245,158,11,0.2); color: #fbbf24; border: 1px solid #f59e0b; }
    .badge-REVIEW { background: rgba(168,85,247,0.2); color: #c084fc; border: 1px solid #a855f7; }
    .chat-bubble { background: rgba(255,255,255,0.04); padding: 14px 18px; border-radius: 12px; margin-bottom: 12px; border-left: 4px solid #6366f1; }
    .chat-bubble.follow-up { border-left-color: #3b82f6; background: rgba(59, 130, 246, 0.08); }
    .footer { text-align: center; margin-top: 40px; font-size: 13px; color: #64748b; border-top: 1px solid #334155; padding-top: 20px; }
    pre { white-space: pre-wrap; word-break: break-word; font-family: inherit; }
  </style>
</head>
<body>
  <div class="container">
    <h1>FAOS 智能投研研报与分析档案</h1>
    <div class="meta-bar">
      <strong>分析标的:</strong> ${symbol} &nbsp;|&nbsp; 
      <strong>生成时间:</strong> ${dateStr} &nbsp;|&nbsp; 
      <strong>系统:</strong> FAOS Multi-Agent Trading Engine
    </div>

    <!-- Stage 3 Verdict -->
    ${decision?.pm ? `
    <div class="card">
      <h2>Stage 3: 最终投资裁决与策略建议</h2>
      <div class="badge badge-${decision.pm.decision || 'HOLD'}">${decision.pm.decision || 'HOLD'}</div>
      <p><strong>置信度评分:</strong> ${decision.pm.confidence}</p>
      <h3>基金经理决策理由</h3>
      <pre>${typeof decision.pm.reasoning === 'string' ? decision.pm.reasoning : JSON.stringify(decision.pm.reasoning, null, 2)}</pre>
    </div>
    ` : ''}

    <!-- Final Consolidated Executive Report -->
    ${reportContent ? `
    <div class="card">
      <h2>综合金融分析报告 (Consolidated Executive Report)</h2>
      <pre>${typeof reportContent === 'string' ? reportContent : JSON.stringify(reportContent, null, 2)}</pre>
    </div>
    ` : ''}

    <!-- Chat History & Follow-up Transcripts -->
    ${(chatHistory.length > 0 || followUpHistory.length > 0) ? `
    <div class="card">
      <h2>对话与追问记录 (Conversational Transcript & Follow-up Q&A)</h2>
      ${chatHistory.map(m => `
        <div class="chat-bubble">
          <strong>${m.role === 'user' ? '👤 用户' : '🤖 FAOS 投研助手'}:</strong>
          <div style="margin-top: 6px;"><pre>${m.content}</pre></div>
        </div>
      `).join('')}
      ${followUpHistory.map(m => `
        <div class="chat-bubble follow-up">
          <strong>${m.role === 'user' ? '💬 研报深度追问' : '💡 FAOS 追问解答'}:</strong>
          <div style="margin-top: 6px;"><pre>${m.content}</pre></div>
        </div>
      `).join('')}
    </div>
    ` : ''}

    <div class="footer">
      Generated by FAOS (Financial Agent Operating System) — Confidential Investment Research
    </div>
  </div>
</body>
</html>`;

    const blob = new Blob([reportHtml], { type: 'text/html;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `FAOS_Report_${symbol}_${new Date().toISOString().slice(0, 10)}.html`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const [wsConnected, setWsConnected] = useState(false);

  useEffect(() => {
    let ws: WebSocket | null = null;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    let reconnectDelay = 1000;
    let unmounted = false;

    function connect() {
      if (unmounted) return;
      const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      ws = new WebSocket(`${wsProtocol}//${window.location.host}/ws/events`);

      ws.onopen = () => {
        console.log('Connected to FAOS EventBus');
        setWsConnected(true);
        reconnectDelay = 1000;
      };

      ws.onmessage = (event) => {
        try {
          const faosEvent: FAOSEvent = JSON.parse(event.data);
          setEvents(prev => [...prev, faosEvent]);

          if (faosEvent.type === 'TaskSubmitted') setTaskStatus('running');
          if (faosEvent.type === 'TaskCompleted') {
            setTaskStatus('completed');
            saveCurrentToHistory();
          }
          if (faosEvent.type === 'TaskFailed') setTaskStatus('failed');

          // Extract Node Completed data
          if (faosEvent.type === 'NodeCompleted' && faosEvent.payload?.results) {
            const results = faosEvent.payload.results;
            
            if (results.history) {
              sessionRef.current.marketData = results.history;
              setMarketData(results.history);
            }
            if (results.analysis_reports) {
              sessionRef.current.analysisReports = results.analysis_reports;
              setAnalysisReports(results.analysis_reports);
            }
            if (results.discussion) {
              sessionRef.current.discussion = results.discussion;
              setDiscussion(results.discussion);
            }
            if (results.decision) {
              const d = results.decision;
              let traderData = d['Trader Strategy'] || d.trader || d.strategy;
              let pmData = d['Portfolio Manager Decision'] || d.pm;
              if (!pmData) {
                pmData = {
                  decision: d.action || 'HOLD',
                  confidence: d.confidence !== undefined ? (typeof d.confidence === 'number' ? (d.confidence <= 1 ? `${(d.confidence * 100).toFixed(0)}%` : `${d.confidence}%`) : String(d.confidence)) : 'High',
                  reasoning: d.reason || d.justification || ''
                };
              }
              const decObj = { trader: traderData, pm: pmData };
              sessionRef.current.decision = decObj;
              setDecision(decObj);
            }
            if (results.report) {
              sessionRef.current.reportContent = results.report;
              setReportContent(results.report);
              saveCurrentToHistory(results.report);
            }
          }
        } catch (err) {
          console.error('Failed to parse event', err);
        }
      };

      ws.onclose = () => {
        console.log('Disconnected from FAOS EventBus, reconnecting...');
        setWsConnected(false);
        if (!unmounted) {
          reconnectTimer = setTimeout(() => {
            reconnectDelay = Math.min(reconnectDelay * 2, 10000);
            connect();
          }, reconnectDelay);
        }
      };

      ws.onerror = () => {
        ws?.close();
      };
    }

    connect();

    return () => {
      unmounted = true;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      ws?.close();
    };
  }, []);

  const getLlmConfig = () => {
    localStorage.setItem('faos_provider', llmProvider);
    localStorage.setItem('faos_model', llmModel);
    localStorage.setItem('faos_api_key', llmApiKey);
    localStorage.setItem('faos_language', llmLanguage);
    return { provider: llmProvider, model: llmModel, api_key: llmApiKey, language: llmLanguage };
  };

  const transitionToAnalysis = (symbol?: string) => {
    setPhase('analysis');
    setEvents([]);
    setMarketData(null);
    setAnalysisReports(null);
    setDiscussion(null);
    setDecision(null);
    setReportContent(null);
    setFollowUpHistory([]);
    setFollowUpInput('');
    if (symbol) setCurrentSymbol(symbol);
    setTaskStatus('running');

    sessionRef.current = {
      symbol: symbol || '',
      marketData: null,
      analysisReports: null,
      discussion: null,
      decision: null,
      reportContent: null
    };
  };

  const handleChatSend = async (forceExecute = false) => {
    const text = chatInput.trim();
    if (!text && !forceExecute) return;
    if (isChatLoading) return;

    // Append user message
    if (text) {
      const userMsg: ChatMessage = { role: 'user', content: text, timestamp: new Date() };
      setChatHistory(prev => [...prev, userMsg]);
      setChatInput('');
    }

    setIsChatLoading(true);

    try {
      // Build messages payload from history + current message
      const allMessages = [...chatHistory];
      if (text) {
        allMessages.push({ role: 'user', content: text, timestamp: new Date() });
      }

      const messagesPayload = allMessages.map(m => ({ role: m.role, content: m.content }));

      const response = await fetch('/api/plan/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: messagesPayload,
          force_execute: forceExecute,
          llm_config: getLlmConfig()
        }),
      });

      if (!response.ok) throw new Error('Network response was not ok');
      
      const data = await response.json();

      if (data.status === 'clarify') {
        // Planner is asking for more info
        const assistantMsg: ChatMessage = {
          role: 'assistant',
          content: data.message || "Could you provide more details?",
          timestamp: new Date()
        };
        setChatHistory(prev => [...prev, assistantMsg]);
      } else if (data.status === 'ready') {
        // Planner is satisfied, transition to analysis dashboard
        const summary = data.message || `Starting analysis with workflow: ${data.workflow_id}`;
        const assistantMsg: ChatMessage = {
          role: 'assistant',
          content: `✅ ${summary}`,
          timestamp: new Date()
        };
        setChatHistory(prev => [...prev, assistantMsg]);

        // Short delay for the user to see the confirmation
        setTimeout(() => {
          transitionToAnalysis(data.parameters?.symbol);
        }, 800);
      }
    } catch (error) {
      console.error('Error in planner chat:', error);
      const errMsg: ChatMessage = {
        role: 'assistant',
        content: '⚠️ Failed to connect to the Planner. Is the FAOS API running on port 8088?',
        timestamp: new Date()
      };
      setChatHistory(prev => [...prev, errMsg]);
    } finally {
      setIsChatLoading(false);
    }
  };

  const handleFollowUpSend = async () => {
    const text = followUpInput.trim();
    if (!text || isFollowUpLoading) return;

    const userMsg: ChatMessage = { role: 'user', content: text, timestamp: new Date() };
    setFollowUpHistory(prev => [...prev, userMsg]);
    setFollowUpInput('');
    setIsFollowUpLoading(true);

    try {
      const messagesPayload: { role: string, content: string }[] = [];
      
      // Inject Report Context into conversation history for Planner LLM
      if (reportContent) {
        messagesPayload.push({
          role: 'assistant',
          content: `[Current Analysis Report for ${currentSymbol || 'Asset'}]\n${typeof reportContent === 'string' ? reportContent.slice(0, 3000) : ''}`
        });
      }
      
      followUpHistory.forEach(m => {
        messagesPayload.push({ role: m.role, content: m.content });
      });
      messagesPayload.push({ role: 'user', content: text });

      const response = await fetch('/api/plan/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: messagesPayload,
          force_execute: false,
          llm_config: getLlmConfig()
        }),
      });

      if (!response.ok) throw new Error('Network response was not ok');

      const data = await response.json();

      const assistantMsg: ChatMessage = {
        role: 'assistant',
        content: data.message || "I have analyzed your follow-up request.",
        timestamp: new Date()
      };

      setFollowUpHistory(prev => [...prev, assistantMsg]);

      if (data.status === 'ready') {
        setTimeout(() => {
          transitionToAnalysis(data.parameters?.symbol || currentSymbol);
        }, 1000);
      }
    } catch (error) {
      console.error('Error in follow-up chat:', error);
      const errMsg: ChatMessage = {
        role: 'assistant',
        content: '⚠️ 追问回答生成失败，请检查后端服务连接。',
        timestamp: new Date()
      };
      setFollowUpHistory(prev => [...prev, errMsg]);
    } finally {
      setIsFollowUpLoading(false);
    }
  };

  const handleNewAnalysis = () => {
    setPhase('chat');
    setChatHistory([]);
    setChatInput('');
    setCurrentSymbol('');
    setFollowUpHistory([]);
    setFollowUpInput('');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleChatSend(false);
    }
  };

  // ── Chat Phase UI ────────────────────────────────────────
  if (phase === 'chat') {
    return (
      <div className="app-container" style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
        {/* Header */}
        <div className="topbar" style={{ position: 'relative', flexShrink: 0 }}>
          <div className="topbar-brand">
            <h1>FAOS TradingAgents</h1>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <span style={{
              fontSize: '0.7rem',
              padding: '2px 8px',
              borderRadius: '9999px',
              background: wsConnected ? 'rgba(5,150,105,0.1)' : 'rgba(220,38,38,0.1)',
              color: wsConnected ? 'var(--success-color)' : 'var(--danger-color)'
            }}>
              {wsConnected ? '● Connected' : '○ Reconnecting...'}
            </span>
            <button
              type="button"
              onClick={() => setShowHistoryModal(true)}
              className="btn-secondary"
              style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem' }}
            >
              <History size={15} color="var(--accent-color)" />
              <span>历史记录</span>
            </button>
            <button
              type="button"
              onClick={() => setShowAccuracyModal(true)}
              className="btn-secondary"
              style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem' }}
            >
              <Target size={15} color="var(--success-color)" />
              <span>回测与进化</span>
            </button>
            <button
              type="button"
              onClick={() => setShowWatchlistModal(true)}
              className="btn-secondary"
              style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem' }}
            >
              <LayoutGrid size={15} color="#a855f7" />
              <span>资产看板</span>
            </button>
            <SettingsPopover
              isOpen={showConfig}
              onToggle={() => setShowConfig(!showConfig)}
              onClose={() => setShowConfig(false)}
              llmProvider={llmProvider}
              setLlmProvider={setLlmProvider}
              llmModel={llmModel}
              setLlmModel={setLlmModel}
              llmApiKey={llmApiKey}
              setLlmApiKey={setLlmApiKey}
              llmLanguage={llmLanguage}
              setLmLanguage={setLmLanguage}
              modelOptions={MODEL_OPTIONS}
            />
          </div>
        </div>

        {/* Chat Area */}
        <div style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          maxWidth: '800px',
          width: '100%',
          margin: '0 auto',
          padding: '2rem 1.5rem 0',
          overflow: 'hidden'
        }}>
          {/* Welcome / Empty State */}
          {chatHistory.length === 0 && (
            <div style={{
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '1.5rem',
              textAlign: 'center',
              opacity: 0.9
            }}>
              <div style={{
                width: 72, height: 72, borderRadius: '50%',
                background: 'linear-gradient(135deg, var(--accent-color), #8b5cf6)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                boxShadow: '0 8px 32px var(--accent-glow)'
              }}>
                <BrainCircuit size={36} color="white" />
              </div>
              <h2 style={{ margin: 0, fontSize: 'var(--text-2xl)', fontWeight: 700, color: 'var(--text-primary)' }}>
                FAOS AI Planner
              </h2>
              <p style={{ margin: 0, color: 'var(--text-secondary)', maxWidth: 480, lineHeight: 1.6 }}>
                Tell me what you'd like to analyze. I'll ask clarifying questions if needed, 
                or jump straight into the analysis when I have enough information.
              </p>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', justifyContent: 'center', marginTop: '0.5rem' }}>
                {['分析宝丰能源，中文输出', 'Analyze AAPL for swing trading', '帮我分析下特斯拉', 'What about MSFT?'].map(suggestion => (
                  <button
                    key={suggestion}
                    onClick={() => { setChatInput(suggestion); }}
                    style={{
                      padding: '0.5rem 1rem',
                      background: 'var(--surface-bg)',
                      border: '1px solid var(--surface-border)',
                      borderRadius: '20px',
                      color: 'var(--text-secondary)',
                      fontSize: 'var(--text-xs)',
                      cursor: 'pointer',
                      transition: 'all 0.2s ease',
                      fontFamily: 'var(--font-main)',
                    }}
                    onMouseEnter={e => {
                      e.currentTarget.style.borderColor = 'var(--accent-color)';
                      e.currentTarget.style.color = 'var(--accent-color)';
                    }}
                    onMouseLeave={e => {
                      e.currentTarget.style.borderColor = 'var(--surface-border)';
                      e.currentTarget.style.color = 'var(--text-secondary)';
                    }}
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Chat Messages */}
          {chatHistory.length > 0 && (
            <div style={{
              flex: 1,
              overflowY: 'auto',
              display: 'flex',
              flexDirection: 'column',
              gap: '1rem',
              paddingBottom: '1rem'
            }}>
              {chatHistory.map((msg, i) => (
                <div key={i} style={{
                  display: 'flex',
                  justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
                  gap: '0.75rem',
                  alignItems: 'flex-start',
                  animation: 'fadeSlideUp 0.3s ease-out'
                }}>
                  {msg.role === 'assistant' && (
                    <div style={{
                      width: 36, height: 36, borderRadius: '50%', flexShrink: 0,
                      background: 'linear-gradient(135deg, var(--accent-color), #8b5cf6)',
                      display: 'flex', alignItems: 'center', justifyContent: 'center'
                    }}>
                      <Bot size={18} color="white" />
                    </div>
                  )}
                  <div style={{
                    maxWidth: '75%',
                    padding: '0.875rem 1.125rem',
                    borderRadius: msg.role === 'user' ? '18px 18px 4px 18px' : '18px 18px 18px 4px',
                    background: msg.role === 'user'
                      ? 'linear-gradient(135deg, var(--accent-color), #2563eb)'
                      : 'var(--surface-bg)',
                    color: msg.role === 'user' ? '#ffffff' : 'var(--text-primary)',
                    border: msg.role === 'user' ? 'none' : '1px solid var(--surface-border)',
                    fontSize: 'var(--text-sm)',
                    lineHeight: 1.6,
                    boxShadow: msg.role === 'user'
                      ? '0 4px 12px var(--accent-glow)'
                      : '0 2px 8px rgba(0,0,0,0.04)',
                    backdropFilter: msg.role === 'assistant' ? 'blur(8px)' : undefined,
                  }}>
                    {msg.content}
                  </div>
                  {msg.role === 'user' && (
                    <div style={{
                      width: 36, height: 36, borderRadius: '50%', flexShrink: 0,
                      background: 'linear-gradient(135deg, #10b981, #059669)',
                      display: 'flex', alignItems: 'center', justifyContent: 'center'
                    }}>
                      <User size={18} color="white" />
                    </div>
                  )}
                </div>
              ))}

              {isChatLoading && (
                <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-start' }}>
                  <div style={{
                    width: 36, height: 36, borderRadius: '50%', flexShrink: 0,
                    background: 'linear-gradient(135deg, var(--accent-color), #8b5cf6)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center'
                  }}>
                    <Bot size={18} color="white" />
                  </div>
                  <div style={{
                    padding: '0.875rem 1.125rem',
                    borderRadius: '18px 18px 18px 4px',
                    background: 'var(--surface-bg)',
                    border: '1px solid var(--surface-border)',
                    fontSize: 'var(--text-sm)',
                    color: 'var(--text-muted)'
                  }}>
                    <span className="typing-dots">Planner is thinking</span>
                  </div>
                </div>
              )}

              <div ref={chatEndRef} />
            </div>
          )}

          {/* Chat Input Area */}
          <div style={{
            padding: '1rem 0 2rem',
            display: 'flex',
            gap: '0.75rem',
            alignItems: 'flex-end',
            flexShrink: 0,
          }}>
            <div style={{
              flex: 1,
              display: 'flex',
              alignItems: 'center',
              background: '#ffffff',
              border: '1px solid var(--surface-border)',
              borderRadius: '16px',
              padding: '0.5rem 0.75rem',
              transition: 'all 0.3s ease',
              boxShadow: '0 2px 12px rgba(0,0,0,0.04)',
            }}>
              <input
                type="text"
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Describe what you'd like to analyze..."
                disabled={isChatLoading}
                style={{
                  flex: 1, border: 'none', outline: 'none', background: 'transparent',
                  color: 'var(--text-primary)', fontSize: 'var(--text-sm)',
                  fontFamily: 'var(--font-main)', padding: '0.5rem',
                }}
              />
              <button
                onClick={() => handleChatSend(false)}
                disabled={isChatLoading || !chatInput.trim()}
                style={{
                  width: 38, height: 38, borderRadius: '12px', border: 'none',
                  background: chatInput.trim() ? 'var(--accent-color)' : '#e2e8f0',
                  color: chatInput.trim() ? '#fff' : '#94a3b8',
                  cursor: chatInput.trim() ? 'pointer' : 'default',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  transition: 'all 0.2s ease', flexShrink: 0
                }}
              >
                <Send size={16} />
              </button>
            </div>

            {/* Force Execute Button — only show after at least one exchange */}
            {chatHistory.length > 0 && (
              <button
                onClick={() => handleChatSend(true)}
                disabled={isChatLoading}
                title="Force the Planner to auto-fill missing info and start analysis immediately"
                style={{
                  display: 'flex', alignItems: 'center', gap: '0.5rem', flexShrink: 0,
                  padding: '0.75rem 1.25rem',
                  background: 'linear-gradient(135deg, #ef4444, #dc2626)',
                  color: '#ffffff', border: 'none', borderRadius: '12px',
                  fontFamily: 'var(--font-main)', fontWeight: 600,
                  fontSize: 'var(--text-xs)', cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  boxShadow: '0 4px 12px rgba(239,68,68,0.3)',
                  opacity: isChatLoading ? 0.5 : 1,
                }}
                onMouseEnter={e => { if (!isChatLoading) e.currentTarget.style.transform = 'translateY(-1px)'; }}
                onMouseLeave={e => { e.currentTarget.style.transform = 'translateY(0)'; }}
              >
                <Zap size={16} />
                Force Execute
              </button>
            )}
          </div>
        </div>

        {/* History Records Modal */}
        <HistoryModal
          isOpen={showHistoryModal}
          onClose={() => setShowHistoryModal(false)}
          historyRecords={historyRecords}
          onSelectRecord={handleSelectHistoryRecord}
          onClearHistory={handleClearHistory}
          onDeleteRecord={handleDeleteHistoryRecord}
        />

        {/* AI Accuracy & Self-Optimization Modal */}
        <AccuracyDashboardModal
          isOpen={showAccuracyModal}
          onClose={() => setShowAccuracyModal(false)}
        />

        {/* User Watchlist & Analytics Dashboard Modal */}
        <WatchlistDashboardModal
          isOpen={showWatchlistModal}
          onClose={() => setShowWatchlistModal(false)}
          onStartAnalysis={(symbol) => {
            setShowWatchlistModal(false);
            setCurrentSymbol(symbol);
            transitionToAnalysis(symbol);
            // Directly submit analysis task to the pipeline
            fetch('/api/tasks', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                intent: `分析${symbol}，输出中文报告`,
                context: { llm_config: getLlmConfig(), planner_params: { symbol } }
              })
            }).catch(err => console.error('Failed to submit analysis task:', err));
          }}
        />
      </div>
    );
  }

  // ── Analysis Phase UI ────────────────────────────────────
  return (
    <div className="app-container">
      {/* Main Canvas Area */}
      <div className="main-canvas">
        <div className="topbar" style={{ position: 'relative', background: 'transparent', border: 'none', padding: '0 0 2rem 0' }}>
          <div className="topbar-brand">
            <h1>FAOS TradingAgents</h1>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
            <button
              type="button"
              onClick={handleNewAnalysis}
              className="btn-secondary"
              style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}
            >
              <MessageSquare size={16} />
              <span>新分析</span>
            </button>
            <button
              type="button"
              onClick={() => setShowHistoryModal(true)}
              className="btn-secondary"
              style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}
            >
              <History size={16} color="var(--accent-color)" />
              <span>历史记录</span>
            </button>
            <button
              type="button"
              onClick={() => setShowAccuracyModal(true)}
              className="btn-secondary"
              style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}
            >
              <Target size={16} color="var(--success-color)" />
              <span>回测与进化</span>
            </button>
            <button
              type="button"
              onClick={() => setShowWatchlistModal(true)}
              className="btn-secondary"
              style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}
            >
              <LayoutGrid size={16} color="#a855f7" />
              <span>资产看板</span>
            </button>
            <button
              type="button"
              onClick={downloadHtmlReport}
              className="btn-primary"
              style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', background: 'linear-gradient(135deg, #10b981, #059669)', border: 'none' }}
              title="下载完整 HTML 研报与对话档案"
            >
              <Download size={16} />
              <span>下载 HTML 研报</span>
            </button>
            <SettingsPopover
              isOpen={showConfig}
              onToggle={() => setShowConfig(!showConfig)}
              onClose={() => setShowConfig(false)}
              llmProvider={llmProvider}
              setLlmProvider={setLlmProvider}
              llmModel={llmModel}
              setLlmModel={setLlmModel}
              llmApiKey={llmApiKey}
              setLlmApiKey={setLlmApiKey}
              llmLanguage={llmLanguage}
              setLmLanguage={setLmLanguage}
              modelOptions={MODEL_OPTIONS}
            />
            <div className={`status-indicator status-${taskStatus}`}>
              {taskStatus === 'running' && <Activity size={14} className="animate-spin" />}
              {taskStatus.toUpperCase()}
              {currentSymbol && ` — ${currentSymbol}`}
            </div>
          </div>
        </div>

        {/* Market Data Chart */}
        {marketData && (
          <div className="stage-section delay-1" style={{ marginBottom: '2rem' }}>
            <h2 className="stage-title">
              <span className="badge">Data</span>
              <LineChart size={24} color="#818cf8" />
              Market Overview
            </h2>
            <MarketChart data={marketData} symbol={currentSymbol || 'Asset'} />
          </div>
        )}

        {/* Stage 1: Analyze */}
        {analysisReports && (
          <div className="stage-section delay-1">
            <h2 className="stage-title" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span className="badge">Stage 1</span>
              <BrainCircuit size={24} color="#60a5fa" />
              Multi-Dimensional Analysis
            </h2>
            <div className="grid-2x2">
              {Object.entries(analysisReports).map(([name, report]) => (
                <div key={name} className="impeccable-card">
                  <div className="card-header">
                    <div className="card-title">{name}</div>
                  </div>
                  <div className="card-body small markdown-body">
                    {typeof report === 'string' ? (
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>{report}</ReactMarkdown>
                    ) : typeof report === 'object' && report !== null ? (
                      <>
                        {report.conclusion && <div><strong>Conclusion:</strong> {String(report.conclusion)}</div>}
                        <hr style={{ opacity: 0.1, margin: '0.75rem 0' }} />
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>{typeof report.reasoning === 'string' ? report.reasoning : JSON.stringify(report.reasoning || report, null, 2)}</ReactMarkdown>
                      </>
                    ) : (
                      <p>{String(report || '')}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Stage 2: Discuss */}
        {discussion && (
          <div className="stage-section delay-2">
            <h2 className="stage-title" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span className="badge">Stage 2</span>
              <MessageSquare size={24} color="#fbbf24" />
              Agent Debates & Consensus
            </h2>

            {discussion['Investment Debate'] && discussion['Investment Plan'] && discussion['Risk Plan'] ? (
              <>
                <AgentDebateMap
                  bull={typeof discussion['Investment Debate'] === 'string' ? discussion['Investment Debate'] : (discussion['Investment Debate']['Bull'] || discussion['Investment Debate']['Bull Analyst'] || discussion['Investment Debate']['Bull Researcher'] || Object.values(discussion['Investment Debate'])[0] || '') as string}
                  bear={typeof discussion['Investment Debate'] === 'string' ? '' : (discussion['Investment Debate']['Bear'] || discussion['Investment Debate']['Bear Analyst'] || discussion['Investment Debate']['Bear Researcher'] || Object.values(discussion['Investment Debate'])[1] || '') as string}
                  manager={typeof discussion['Investment Plan'] === 'string' ? discussion['Investment Plan'] : JSON.stringify(discussion['Investment Plan'] || '')}
                  risk={typeof discussion['Risk Plan'] === 'string' ? discussion['Risk Plan'] : JSON.stringify(discussion['Risk Plan'] || '')}
                />

                {discussion['Risk Debate'] && (
                  <div className="grid-3" style={{ marginTop: '1.5rem' }}>
                    {Object.entries(discussion['Risk Debate']).map(([role, text]) => (
                      <div key={role} className="impeccable-card">
                        <div className="card-header">
                          <div className="card-title">{role} Risk Assessment</div>
                        </div>
                        <div className="card-body small markdown-body overflow-x-auto">
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>{typeof text === 'string' ? text : JSON.stringify(text || '')}</ReactMarkdown>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </>
            ) : (
              /* Fallback: render every discussion entry as its own full-width card */
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                {Object.entries(discussion).map(([key, value]) => (
                  <div key={key} className="impeccable-card">
                    <div className="card-header">
                      <div className="card-title">{key}</div>
                    </div>
                    <div className="card-body small markdown-body" style={{ overflowX: 'auto' }}>
                      {typeof value === 'string' ? (
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>{value}</ReactMarkdown>
                      ) : typeof value === 'object' && value !== null ? (
                        Object.entries(value as Record<string, any>).map(([subKey, subVal]) => (
                          <div key={subKey} style={{ marginBottom: '1rem' }}>
                            <strong style={{ color: 'var(--accent-color)' }}>{subKey}:</strong>
                            <div style={{ marginTop: '0.25rem' }}>
                              <ReactMarkdown remarkPlugins={[remarkGfm]}>{typeof subVal === 'string' ? subVal : JSON.stringify(subVal, null, 2)}</ReactMarkdown>
                            </div>
                          </div>
                        ))
                      ) : (
                        <p>{String(value)}</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Stage 3: Decision */}
        {decision && decision.pm && (
          <div className="stage-section delay-3">
            <h2 className="stage-title" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span className="badge">Stage 3</span>
              <TrendingUp size={24} color="#34d399" />
              Final Verdict & Strategy
            </h2>

            <div className="verdict-card">
              <div className={`verdict-action verdict-${String(decision.pm.decision || 'HOLD')}`}>
                {String(decision.pm.decision || 'HOLD')}
              </div>
              <div style={{ color: 'var(--text-secondary)' }}>
                Confidence: {String(decision.pm.confidence || 'High')}
              </div>

              <div className="grid-2x2" style={{ width: '100%', gap: '1.5rem', marginTop: '1rem' }}>
                <div className="verdict-details" style={{ background: 'rgba(255,255,255,0.03)' }}>
                  <h4>Trader Strategy</h4>
                  {decision.trader ? (
                    typeof decision.trader === 'string' ? (
                      <div className="markdown-body"><ReactMarkdown remarkPlugins={[remarkGfm]}>{decision.trader}</ReactMarkdown></div>
                    ) : (
                      <>
                        {decision.trader.trade_type && <p><strong>Type:</strong> {decision.trader.trade_type}</p>}
                        {decision.trader.entry_target && <p><strong>Entry:</strong> {decision.trader.entry_target}</p>}
                        {decision.trader.stop_loss && <p><strong>Stop Loss:</strong> {decision.trader.stop_loss}</p>}
                        {decision.trader.position_sizing && <p><strong>Position:</strong> {decision.trader.position_sizing}</p>}
                        {decision.trader.justification && (
                          <div className="markdown-body" style={{ marginTop: '0.5rem' }}>
                            <ReactMarkdown remarkPlugins={[remarkGfm]}>{typeof decision.trader.justification === 'string' ? decision.trader.justification : JSON.stringify(decision.trader.justification)}</ReactMarkdown>
                          </div>
                        )}
                        {!decision.trader.trade_type && !decision.trader.entry_target && !decision.trader.justification && (
                          <div className="markdown-body"><ReactMarkdown remarkPlugins={[remarkGfm]}>{JSON.stringify(decision.trader, null, 2)}</ReactMarkdown></div>
                        )}
                      </>
                    )
                  ) : <p>No strategy provided.</p>}
                </div>
                <div className="verdict-details" style={{ background: 'rgba(255,255,255,0.03)' }}>
                  <h4>Portfolio Manager Reasoning</h4>
                  <div className="markdown-body">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {typeof decision.pm.reasoning === 'string' ? decision.pm.reasoning : JSON.stringify(decision.pm.reasoning || decision.pm || '', null, 2)}
                    </ReactMarkdown>
                  </div>
                </div>
              </div>

              <div style={{ marginTop: '2rem' }}>
                <ScoreRadar 
                  scores={{
                    fundamental: 85,
                    technical: 60,
                    sentiment: 75,
                    macro: 50,
                    risk: decision.pm.confidence === 'High' ? 20 : 80
                  }}
                />
              </div>
            </div>
          </div>
        )}

        {/* Final Executive / News Summary Report */}
        {reportContent && (
          <div className="stage-section delay-3" style={{ marginTop: '2rem', marginBottom: '6rem' }}>
            <h2 className="stage-title" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span className="badge">Report</span>
              <FileText size={24} color="#a855f7" />
              Analysis & Summary Report
            </h2>
            <div className="impeccable-card" style={{ padding: '2rem' }}>
              <div className="markdown-body" style={{ overflowX: 'auto', lineHeight: 1.7 }}>
                {typeof reportContent === 'string' ? (
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{reportContent}</ReactMarkdown>
                ) : (
                  <pre>{JSON.stringify(reportContent, null, 2)}</pre>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Bottom spacer so scrollable content clears the fixed input bar */}
        {phase === 'analysis' && <div style={{ height: '6rem' }} />}

        {/* Floating Post-Report Follow-up Chat Bar */}
        {phase === 'analysis' && (
          <div className="floating-followup-container" style={{
            position: 'fixed',
            bottom: '1.5rem',
            left: 'calc((100vw - 320px) / 2)',
            transform: 'translateX(-50%)',
            width: 'min(1400px, calc(100vw - 320px))',
            padding: '0 4rem',
            boxSizing: 'border-box',
            zIndex: 100,
            display: 'flex',
            flexDirection: 'column',
            gap: '0.75rem'
          }}>
          {/* Expandable Conversation Thread Popup */}
          {followUpHistory.length > 0 && showFollowUpThread && (
            <div className="impeccable-card" style={{
              background: 'var(--surface-bg, rgba(255, 255, 255, 0.95))',
              backdropFilter: 'blur(16px)',
              border: '1px solid var(--surface-border, #e2e8f0)',
              borderRadius: '16px',
              padding: '1.25rem',
              boxShadow: '0 15px 35px rgba(0, 0, 0, 0.12)',
              maxHeight: '320px',
              overflowY: 'auto'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem', borderBottom: '1px solid var(--surface-border)', paddingBottom: '0.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem', fontWeight: 600, color: 'var(--accent-color)' }}>
                  <Sparkles size={16} />
                  <span>研报追问对话记录 ({followUpHistory.length})</span>
                </div>
                <button type="button" onClick={() => setShowFollowUpThread(false)} style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
                  <X size={16} />
                </button>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {followUpHistory.map((msg, idx) => (
                  <div key={idx} style={{ display: 'flex', gap: '0.6rem', alignItems: 'flex-start', justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start' }}>
                    {msg.role === 'assistant' && (
                      <div style={{ background: 'var(--accent-color)', width: 28, height: 28, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, color: '#fff' }}>
                        <Bot size={14} />
                      </div>
                    )}
                    <div style={{
                      background: msg.role === 'user' ? 'rgba(59, 130, 246, 0.12)' : 'rgba(241, 245, 249, 0.9)',
                      padding: '0.65rem 0.9rem',
                      borderRadius: '12px',
                      border: '1px solid var(--surface-border)',
                      maxWidth: '88%',
                      color: 'var(--text-primary)'
                    }}>
                      <div className="markdown-body" style={{ fontSize: '0.88rem', lineHeight: '1.5' }}>
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
                      </div>
                    </div>
                    {msg.role === 'user' && (
                      <div style={{ background: '#3b82f6', width: 28, height: 28, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, color: '#fff' }}>
                        <User size={14} />
                      </div>
                    )}
                  </div>
                ))}
                <div ref={followUpEndRef} />
              </div>
            </div>
          )}

          {/* Compact Floating Input Bar */}
          <div className="impeccable-card" style={{
            background: 'var(--surface-bg, rgba(255, 255, 255, 0.95))',
            backdropFilter: 'blur(16px)',
            border: '1px solid var(--surface-border, #e2e8f0)',
            borderRadius: '16px',
            padding: '0.65rem 1rem',
            boxShadow: '0 12px 30px rgba(0, 0, 0, 0.12)',
            display: 'flex',
            alignItems: 'center',
            gap: '0.75rem'
          }}>
            <Sparkles size={18} color="var(--accent-color)" style={{ flexShrink: 0 }} />

            {followUpHistory.length > 0 && (
              <button
                type="button"
                onClick={() => setShowFollowUpThread(!showFollowUpThread)}
                style={{
                  fontSize: '0.78rem',
                  fontWeight: 600,
                  color: 'var(--accent-color)',
                  background: 'rgba(59, 130, 246, 0.08)',
                  border: '1px solid rgba(59, 130, 246, 0.2)',
                  borderRadius: '8px',
                  padding: '0.35rem 0.65rem',
                  cursor: 'pointer',
                  flexShrink: 0,
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.3rem'
                }}
              >
                <MessageSquare size={13} />
                <span>对话 ({followUpHistory.length})</span>
              </button>
            )}

            <input
              type="text"
              value={followUpInput}
              onChange={(e) => setFollowUpInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleFollowUpSend();
                }
              }}
              placeholder="针对研报向 AI 提问 (例如: 解释支撑位/止损策略/建议理由)..."
              disabled={isFollowUpLoading}
              style={{
                flex: 1,
                padding: '0.5rem 0.75rem',
                borderRadius: '10px',
                background: 'rgba(241, 245, 249, 0.7)',
                border: '1px solid var(--surface-border, #e2e8f0)',
                color: 'var(--text-primary)',
                fontSize: '0.9rem',
                outline: 'none'
              }}
            />

            <button
              type="button"
              onClick={handleFollowUpSend}
              disabled={isFollowUpLoading || !followUpInput.trim()}
              className="btn-primary"
              style={{
                padding: '0.55rem 1.1rem',
                borderRadius: '10px',
                display: 'flex',
                alignItems: 'center',
                gap: '0.4rem',
                fontSize: '0.88rem',
                fontWeight: 600,
                flexShrink: 0
              }}
            >
              {isFollowUpLoading ? <RefreshCw className="spin" size={15} /> : <Send size={15} />}
              <span>发送</span>
            </button>
          </div>
        </div>
      )}
      </div>

      {/* Sidebar (Event Trace) */}
      <div className="sidebar">
        <div className="sidebar-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>System Event Trace</span>
          <span style={{
            fontSize: '0.7rem',
            padding: '2px 8px',
            borderRadius: '9999px',
            background: wsConnected ? 'rgba(5,150,105,0.1)' : 'rgba(220,38,38,0.1)',
            color: wsConnected ? 'var(--success-color)' : 'var(--danger-color)'
          }}>
            {wsConnected ? '● Connected' : '○ Reconnecting...'}
          </span>
        </div>
        <div className="event-log">
          {events.length === 0 ? (
            <div style={{ color: 'var(--text-secondary)', textAlign: 'center', marginTop: '2rem' }}>
              {wsConnected ? 'Connected. Waiting for pipeline...' : 'Connecting to backend...'}
            </div>
          ) : (
            events.map((evt) => (
              <div key={evt.id} className={`event-item ${evt.type === 'NodeCompleted' ? 'important' : ''}`}>
                {evt.type === 'NodeStarted' ? (
                  <>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}><Activity size={16} color="#d97706" /><span style={{ color: 'var(--warning-color)' }}>Starting</span></div>
                    <div style={{ marginTop: '0.25rem', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '0.25rem' }}><ChevronRight size={14} /> {getNodeName(evt.payload?.node_id, evt.payload?.capability)}</div>
                  </>
                ) : evt.type === 'NodeCompleted' ? (
                  <>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}><CheckCircle2 size={16} color="#059669" /><span style={{ color: 'var(--success-color)' }}>Completed</span></div>
                    <div style={{ marginTop: '0.25rem', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '0.25rem' }}><ChevronRight size={14} /> {getNodeName(evt.payload?.node_id, evt.payload?.capability)}</div>
                  </>
                ) : evt.type === 'TaskFailed' ? (
                  <>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}><XCircle size={16} color="#dc2626" /><span style={{ color: 'var(--danger-color)' }}>Failed</span></div>
                    <div style={{ marginTop: '0.25rem', color: 'var(--danger-color)' }}>{evt.source}</div>
                  </>
                ) : (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}><FileText size={14} color="var(--accent-color)" /><span style={{ color: 'var(--accent-color)' }}>[{evt.type}]</span> {evt.source}</div>
                )}
              </div>
            ))
          )}
        </div>
      </div>

      {/* History Records Modal */}
      <HistoryModal
        isOpen={showHistoryModal}
        onClose={() => setShowHistoryModal(false)}
        historyRecords={historyRecords}
        onSelectRecord={handleSelectHistoryRecord}
        onClearHistory={handleClearHistory}
        onDeleteRecord={handleDeleteHistoryRecord}
      />

      {/* AI Accuracy & Self-Optimization Modal */}
      <AccuracyDashboardModal
        isOpen={showAccuracyModal}
        onClose={() => setShowAccuracyModal(false)}
      />

      {/* User Watchlist & Analytics Dashboard Modal */}
      <WatchlistDashboardModal
        isOpen={showWatchlistModal}
        onClose={() => setShowWatchlistModal(false)}
        onStartAnalysis={(symbol) => {
          setShowWatchlistModal(false);
          setCurrentSymbol(symbol);
          transitionToAnalysis(symbol);
          // Directly submit analysis task to the pipeline
          fetch('/api/tasks', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              intent: `分析${symbol}，输出中文报告`,
              context: { llm_config: getLlmConfig(), planner_params: { symbol } }
            })
          }).catch(err => console.error('Failed to submit analysis task:', err));
        }}
      />
    </div>
  );
}

export default App;
