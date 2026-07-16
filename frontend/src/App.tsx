import React, { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
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

const getNodeName = (nodeId: string) => {
  const map: Record<string, string> = {
    'node1': 'Fetch Market Data (Quote)',
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
  gemini: ['gemini-3.5-flash', 'gemini-3.5-pro', 'gemini-2.0-flash'],
  deepseek: ['deepseek-v4-flash', 'deepseek-v4-pro', 'deepseek-chat', 'deepseek-reasoner'],
  openrouter: [
    'tencent/hy3:free',
    'openai/gpt-4o',
    'anthropic/claude-3.5-sonnet',
    'meta-llama/llama-3.3-70b-instruct',
    'google/gemini-3.5-pro'
  ]
};


function App() {
  const [intent, setIntent] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showConfig, setShowConfig] = useState(false);
  const [llmProvider, setLlmProvider] = useState(() => localStorage.getItem('faos_provider') || 'mock');
  const [llmModel, setLlmModel] = useState(() => localStorage.getItem('faos_model') || 'gemini-2.0-flash');
  const [llmApiKey, setLlmApiKey] = useState(() => localStorage.getItem('faos_api_key') || '');
  const [events, setEvents] = useState<FAOSEvent[]>([]);
  const [taskStatus, setTaskStatus] = useState<'idle' | 'running' | 'completed' | 'failed'>('idle');
  
  // Pipeline Data State
  const [analysisReports, setAnalysisReports] = useState<Record<string, AnalysisReport> | null>(null);
  const [discussion, setDiscussion] = useState<Record<string, any> | null>(null);
  const [decision, setDecision] = useState<{trader?: TraderStrategy, pm?: PMDecision} | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const eventsEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    eventsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [events]);

  const [wsConnected, setWsConnected] = useState(false);

  useEffect(() => {
    let ws: WebSocket | null = null;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    let reconnectDelay = 1000;
    let unmounted = false;

    function connect() {
      if (unmounted) return;
      ws = new WebSocket('ws://localhost:8001/ws/events');

      ws.onopen = () => {
        console.log('Connected to FAOS EventBus');
        setWsConnected(true);
        reconnectDelay = 1000; // reset backoff on success
      };

      ws.onmessage = (event) => {
        try {
          const faosEvent: FAOSEvent = JSON.parse(event.data);
          setEvents(prev => [...prev, faosEvent]);

          if (faosEvent.type === 'TaskSubmitted') setTaskStatus('running');
          if (faosEvent.type === 'TaskCompleted') setTaskStatus('completed');
          if (faosEvent.type === 'TaskFailed') setTaskStatus('failed');

          // Extract Node Completed data
          if (faosEvent.type === 'NodeCompleted' && faosEvent.payload?.results) {
            const results = faosEvent.payload.results;
            // Analyze Node
            if (faosEvent.payload.node_id === 'node3' && results.analysis_reports) {
              setAnalysisReports(results.analysis_reports);
            }
            // Discuss Node
            if (faosEvent.payload.node_id === 'node_discuss' && results.discussion) {
              setDiscussion(results.discussion);
            }
            // Decision Node
            if (faosEvent.payload.node_id === 'node_decision' && results.decision) {
              setDecision({
                trader: results.decision['Trader Strategy'],
                pm: results.decision['Portfolio Manager Decision']
              });
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

      wsRef.current = ws;
    }

    connect();

    return () => {
      unmounted = true;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      ws?.close();
    };
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!intent.trim()) return;
    
    setIsSubmitting(true);
    setEvents([]);
    setAnalysisReports(null);
    setDiscussion(null);
    setDecision(null);
    setTaskStatus('idle');
    
    // Save config
    localStorage.setItem('faos_provider', llmProvider);
    localStorage.setItem('faos_model', llmModel);
    localStorage.setItem('faos_api_key', llmApiKey);

    try {
      const response = await fetch('http://localhost:8001/api/tasks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          intent, 
          context: {
            llm_config: {
              provider: llmProvider,
              model: llmModel,
              api_key: llmApiKey
            }
          } 
        }),
      });
      if (!response.ok) throw new Error('Network response was not ok');
    } catch (error) {
      console.error('Error submitting task:', error);
      alert('Failed to submit task. Is the FAOS API running on port 8001?');
    } finally {
      setIsSubmitting(false);
      setIntent('');
    }
  };

  return (
    <div className="app-container">
      {/* Main Canvas Area */}
      <div className="main-canvas">
        <div className="topbar" style={{ position: 'relative', background: 'transparent', border: 'none', padding: '0 0 2rem 0' }}>
          <div className="topbar-brand">
            <h1>FAOS TradingAgents</h1>
          </div>
          <form className="topbar-controls" onSubmit={handleSubmit}>
            <input 
              type="text" 
              value={intent}
              onChange={(e) => setIntent(e.target.value)}
              placeholder="e.g. Analyze AAPL for swing trading..." 
              disabled={isSubmitting || taskStatus === 'running'}
            />
            <button type="submit" className="btn-primary" disabled={isSubmitting || !intent.trim() || taskStatus === 'running'}>
              {isSubmitting ? 'Submitting...' : 'Analyze'}
            </button>
            <button type="button" className="btn-secondary" onClick={() => setShowConfig(!showConfig)}>
              ⚙️
            </button>
            <div className={`status-indicator status-${taskStatus}`}>
              {taskStatus.toUpperCase()}
            </div>
          </form>
          {showConfig && (
            <div className="config-panel impeccable-card">
              <div className="config-row">
                <label>Provider:</label>
                <select value={llmProvider} onChange={(e) => {
                  const val = e.target.value;
                  setLlmProvider(val);
                  setLlmModel(MODEL_OPTIONS[val]?.[0] || '');
                }}>
                  <option value="mock">Mock</option>
                  <option value="gemini">Gemini</option>
                  <option value="deepseek">DeepSeek</option>
                  <option value="openrouter">OpenRouter</option>
                </select>
              </div>
              <div className="config-row">
                <label>Model:</label>
                <select value={llmModel} onChange={(e) => setLlmModel(e.target.value)}>
                  {(MODEL_OPTIONS[llmProvider] || []).map((model) => (
                    <option key={model} value={model}>{model}</option>
                  ))}
                  {/* Allow custom models for openrouter if needed, but official list is requested */}
                </select>
              </div>
              <div className="config-row">
                <label>API Key:</label>
                <input 
                  type="password" 
                  value={llmApiKey} 
                  onChange={(e) => setLlmApiKey(e.target.value)} 
                  placeholder="Leave empty to use backend default" 
                />
              </div>
            </div>
          )}
        </div>

        {/* Stage 1: Analyze */}
        {analysisReports && (
          <div className="stage-section delay-1">
            <h2 className="stage-title">
              <span className="badge">Stage 1</span>
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
                      <ReactMarkdown>{report}</ReactMarkdown>
                    ) : (
                      <>
                        <strong>Conclusion:</strong> {report.conclusion}
                        <hr style={{opacity: 0.1, margin: '0.75rem 0'}}/>
                        <ReactMarkdown>{report.reasoning}</ReactMarkdown>
                      </>
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
            <h2 className="stage-title">
              <span className="badge">Stage 2</span>
              Agent Debates
            </h2>
            
            {discussion['Investment Debate'] && (
              <div className="grid-2x2" style={{marginBottom: '1.5rem'}}>
                <div className="impeccable-card card-bull">
                  <div className="card-header">
                    <div className="card-title">Bull Case</div>
                  </div>
                  <div className="card-body small markdown-body"><ReactMarkdown>{discussion['Investment Debate']['Bull']}</ReactMarkdown></div>
                </div>
                <div className="impeccable-card card-bear">
                  <div className="card-header">
                    <div className="card-title">Bear Case</div>
                  </div>
                  <div className="card-body small markdown-body"><ReactMarkdown>{discussion['Investment Debate']['Bear']}</ReactMarkdown></div>
                </div>
              </div>
            )}

            {discussion['Investment Plan'] && (
              <div className="impeccable-card card-manager" style={{marginBottom: '3rem'}}>
                <div className="card-header">
                  <div className="card-title">Investment Thesis</div>
                </div>
                <div className="card-body markdown-body"><ReactMarkdown>{discussion['Investment Plan']}</ReactMarkdown></div>
              </div>
            )}

            {discussion['Risk Debate'] && (
              <div className="grid-3" style={{marginBottom: '1.5rem'}}>
                {Object.entries(discussion['Risk Debate']).map(([role, text]) => (
                  <div key={role} className="impeccable-card">
                    <div className="card-header">
                      <div className="card-title">{role} Risk Assessment</div>
                    </div>
                    <div className="card-body small markdown-body"><ReactMarkdown>{text as string}</ReactMarkdown></div>
                  </div>
                ))}
              </div>
            )}

            {discussion['Risk Plan'] && (
              <div className="impeccable-card card-manager">
                <div className="card-header">
                  <div className="card-title">Risk Management Plan</div>
                </div>
                <div className="card-body markdown-body"><ReactMarkdown>{discussion['Risk Plan']}</ReactMarkdown></div>
              </div>
            )}
          </div>
        )}

        {/* Stage 3: Decision */}
        {decision && decision.pm && (
          <div className="stage-section delay-3">
            <h2 className="stage-title">
              <span className="badge">Stage 3</span>
              Final Verdict
            </h2>
            
            <div className="verdict-card">
              <div className={`verdict-action verdict-${decision.pm.decision}`}>
                {decision.pm.decision}
              </div>
              <div style={{color: 'var(--text-secondary)'}}>
                Confidence: {decision.pm.confidence}
              </div>
              
              <div className="grid-2x2" style={{width: '100%', gap: '1.5rem', marginTop: '1rem'}}>
                <div className="verdict-details" style={{background: 'rgba(255,255,255,0.03)'}}>
                  <h4>Trader Strategy</h4>
                  {decision.trader ? (
                    <>
                      <p><strong>Type:</strong> {decision.trader.trade_type}</p>
                      <p><strong>Entry:</strong> {decision.trader.entry_target}</p>
                      <p><strong>Stop Loss:</strong> {decision.trader.stop_loss}</p>
                      <p><strong>Position:</strong> {decision.trader.position_sizing}</p>
                    </>
                  ) : <p>No strategy provided.</p>}
                </div>
                <div className="verdict-details" style={{background: 'rgba(255,255,255,0.03)'}}>
                  <h4>Portfolio Manager Reasoning</h4>
                  <div className="markdown-body"><ReactMarkdown>{decision.pm.reasoning}</ReactMarkdown></div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Sidebar (Event Trace) */}
      <div className="sidebar">
        <div className="sidebar-header" style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
          <span>System Event Trace</span>
          <span style={{
            fontSize: '0.7rem',
            padding: '2px 8px',
            borderRadius: '9999px',
            background: wsConnected ? 'rgba(16,185,129,0.2)' : 'rgba(239,68,68,0.2)',
            color: wsConnected ? '#34d399' : '#f87171'
          }}>
            {wsConnected ? '● Connected' : '○ Reconnecting...'}
          </span>
        </div>
        <div className="event-log">
          {events.length === 0 ? (
            <div style={{ color: 'var(--text-secondary)', textAlign: 'center', marginTop: '2rem' }}>
              {wsConnected ? 'Connected. Waiting for task...' : 'Connecting to backend...'}
            </div>
          ) : (
            events.map((evt) => (
              <div key={evt.id} className={`event-item ${evt.type === 'NodeCompleted' ? 'important' : ''}`}>
                {evt.type === 'NodeStarted' ? (
                  <>
                    <div><span style={{color: '#fbbf24'}}>▶ Starting</span></div>
                    <div style={{marginTop: '0.25rem', color: '#e2e8f0'}}>{getNodeName(evt.payload?.node_id)}</div>
                  </>
                ) : evt.type === 'NodeCompleted' ? (
                  <>
                    <div><span style={{color: '#34d399'}}>✓ Completed</span></div>
                    <div style={{marginTop: '0.25rem', color: '#e2e8f0'}}>{getNodeName(evt.payload?.node_id)}</div>
                  </>
                ) : (
                  <div><span style={{color: '#60a5fa'}}>[{evt.type}]</span> {evt.source}</div>
                )}
              </div>
            ))
          )}
          <div ref={eventsEndRef} />
        </div>
      </div>
    </div>
  );
}

export default App;
