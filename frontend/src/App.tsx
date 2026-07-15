import React, { useState, useEffect, useRef } from 'react';

// Define the shape of our events coming from FAOS EventBus
interface FAOSEvent {
  id: string;
  type: string;
  source: string;
  timestamp: string;
  payload: Record<string, any>;
}

function App() {
  const [intent, setIntent] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [events, setEvents] = useState<FAOSEvent[]>([]);
  const [currentTaskId, setCurrentTaskId] = useState<string | null>(null);
  const [taskStatus, setTaskStatus] = useState<string>('idle');
  
  const wsRef = useRef<WebSocket | null>(null);
  const eventsEndRef = useRef<HTMLDivElement>(null);

  // Auto scroll to bottom of event log
  useEffect(() => {
    eventsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [events]);

  useEffect(() => {
    // Connect to FAOS API WebSocket
    const ws = new WebSocket('ws://localhost:8001/ws/events');
    
    ws.onopen = () => {
      console.log('Connected to FAOS EventBus');
    };
    
    ws.onmessage = (event) => {
      try {
        const faosEvent: FAOSEvent = JSON.parse(event.data);
        setEvents(prev => [...prev, faosEvent]);
        
        // Update task status based on events
        if (faosEvent.type === 'TaskSubmitted') {
          setCurrentTaskId(faosEvent.payload.task_id);
          setTaskStatus('running');
        } else if (faosEvent.type === 'TaskCompleted') {
          setTaskStatus('completed');
        } else if (faosEvent.type === 'TaskFailed') {
          setTaskStatus('failed');
        }
      } catch (err) {
        console.error('Failed to parse event', err);
      }
    };
    
    ws.onclose = () => {
      console.log('Disconnected from FAOS EventBus');
    };
    
    wsRef.current = ws;
    
    return () => {
      ws.close();
    };
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!intent.trim()) return;
    
    setIsSubmitting(true);
    setEvents([]); // Clear previous run
    setCurrentTaskId(null);
    setTaskStatus('idle');
    
    try {
      const response = await fetch('http://localhost:8001/api/tasks', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          intent: intent,
          context: {}
        }),
      });
      
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      
      const data = await response.json();
      console.log('Task submitted:', data);
      
    } catch (error) {
      console.error('Error submitting task:', error);
      alert('Failed to submit task. Is the FAOS API running on port 8001?');
    } finally {
      setIsSubmitting(false);
      setIntent('');
    }
  };

  return (
    <>
      <div className="header">
        <h1>FAOS Runtime</h1>
        <p>Financial Agent Operating System v5.0</p>
      </div>

      <div className="container">
        {/* Left Column: Input and Status */}
        <div className="glass-panel">
          <h2 className="panel-title">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
            </svg>
            Task Submission
          </h2>
          
          <form onSubmit={handleSubmit} className="input-group">
            <input 
              type="text" 
              value={intent}
              onChange={(e) => setIntent(e.target.value)}
              placeholder="e.g. Analyze AAPL stock fundamentals..." 
              disabled={isSubmitting || taskStatus === 'running'}
              required
            />
            <button 
              type="submit" 
              disabled={isSubmitting || !intent.trim() || taskStatus === 'running'}
            >
              {isSubmitting ? 'Submitting...' : 'Execute Task'}
            </button>
          </form>

          {currentTaskId && (
            <div style={{ marginTop: '2rem', paddingTop: '2rem', borderTop: '1px solid var(--surface-border)' }}>
              <h3 style={{ fontSize: '1.2rem', marginBottom: '1rem', color: 'var(--text-secondary)' }}>Current Task</h3>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>{currentTaskId.split('-')[0]}...</span>
                <span className={`status-badge status-${taskStatus}`}>
                  {taskStatus.toUpperCase()}
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Event Log */}
        <div className="glass-panel">
          <h2 className="panel-title">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
            </svg>
            Event Trace
          </h2>
          
          <div className="event-log">
            {events.length === 0 ? (
              <div style={{ color: 'var(--text-secondary)', textAlign: 'center', marginTop: '2rem' }}>
                Waiting for system events...
              </div>
            ) : (
              events.map((evt) => (
                <div key={evt.id} className={`event-item ${evt.type === 'TaskCompleted' ? 'completed' : ''}`}>
                  <div className="event-time">
                    {new Date(evt.timestamp).toLocaleTimeString()}
                  </div>
                  <div>
                    <span className="event-type">[{evt.type}]</span>{' '}
                    <span className="event-source">from {evt.source}</span>
                  </div>
                  {evt.payload && (
                    <div className="event-payload">
                      {JSON.stringify(evt.payload, null, 2)}
                    </div>
                  )}
                </div>
              ))
            )}
            <div ref={eventsEndRef} />
          </div>
        </div>
      </div>
    </>
  );
}

export default App;
