import React, { useState, useEffect } from 'react';
import { LayoutGrid, X, Plus, Trash2, Play, RefreshCw, TrendingUp, TrendingDown, Eye, Activity } from 'lucide-react';

interface WatchlistItem {
  symbol: string;
  current_price: number;
  change_pct: number;
  latest_verdict: string;
  analysis_count: number;
  last_analyzed: string;
}

interface UserAnalytics {
  total_analyses: number;
  total_watchlist: number;
  bull_count: number;
  bear_count: number;
  hold_count: number;
  bullish_ratio: number;
  most_analyzed_symbol: string;
  most_analyzed_count: number;
}

interface WatchlistDashboardModalProps {
  isOpen: boolean;
  onClose: () => void;
  onStartAnalysis: (symbol: string) => void;
}

export const WatchlistDashboardModal: React.FC<WatchlistDashboardModalProps> = ({
  isOpen,
  onClose,
  onStartAnalysis,
}) => {
  const [loading, setLoading] = useState(false);
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([]);
  const [analytics, setAnalytics] = useState<UserAnalytics | null>(null);
  const [newSymbolInput, setNewSymbolInput] = useState('');

  const loadData = async () => {
    setLoading(true);
    try {
      const [wlRes, anaRes] = await Promise.all([
        fetch('/api/watchlist'),
        fetch('/api/user/analytics')
      ]);

      if (wlRes.ok) {
        const wlJson = await wlRes.json();
        setWatchlist(wlJson);
      }
      if (anaRes.ok) {
        const anaJson = await anaRes.json();
        setAnalytics(anaJson);
      }
    } catch (err) {
      console.error('Failed to load watchlist data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      loadData();
      // Auto-refresh every 10 minutes while modal is open
      const interval = setInterval(loadData, 10 * 60 * 1000);
      return () => clearInterval(interval);
    }
  }, [isOpen]);

  const handleAddSymbol = async () => {
    const sym = newSymbolInput.trim();
    if (!sym) return;

    try {
      const res = await fetch('/api/watchlist', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symbol: sym })
      });
      if (res.ok) {
        setNewSymbolInput('');
        loadData();
      }
    } catch (err) {
      console.error('Failed to add symbol:', err);
    }
  };

  const handleRemoveSymbol = async (sym: string) => {
    try {
      const res = await fetch(`/api/watchlist/${encodeURIComponent(sym)}`, {
        method: 'DELETE'
      });
      if (res.ok) {
        loadData();
      }
    } catch (err) {
      console.error('Failed to remove symbol:', err);
    }
  };

  if (!isOpen) return null;

  return (
    <div
      className="modal-backdrop"
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: 'rgba(15, 23, 42, 0.4)',
        backdropFilter: 'blur(12px)',
        zIndex: 999,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '2rem'
      }}
      onClick={onClose}
    >
      <div
        className="impeccable-card"
        style={{
          width: '100%',
          maxWidth: '920px',
          maxHeight: '88vh',
          display: 'flex',
          flexDirection: 'column',
          background: 'var(--surface-bg, rgba(255, 255, 255, 0.95))',
          border: '1px solid var(--surface-border, #e2e8f0)',
          borderRadius: '20px',
          padding: '1.75rem',
          boxShadow: '0 20px 40px rgba(0, 0, 0, 0.15)',
          color: 'var(--text-primary, #0f172a)'
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem', borderBottom: '1px solid var(--surface-border, #e2e8f0)', paddingBottom: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <LayoutGrid size={24} color="var(--accent-color)" />
            <div>
              <h2 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary, #0f172a)' }}>
                用户分析概览与自选标的监控看板
              </h2>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary, #475569)' }}>
                实时监控关注资产的价格变动、AI 历史评级与投研分析频次
              </span>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <button
              type="button"
              onClick={loadData}
              disabled={loading}
              className="btn-secondary"
              style={{ fontSize: '0.85rem', padding: '0.4rem 0.85rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}
            >
              <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
              <span>刷新行情</span>
            </button>
            <button type="button" onClick={onClose} style={{ background: 'transparent', border: 'none', color: 'var(--text-secondary, #475569)', cursor: 'pointer', padding: '0.4rem' }}>
              <X size={20} />
            </button>
          </div>
        </div>

        {/* Analytics Top Cards */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem', marginBottom: '1.25rem' }}>
          <div style={{ background: 'rgba(59, 130, 246, 0.06)', border: '1px solid rgba(59, 130, 246, 0.2)', borderRadius: '14px', padding: '1rem', textAlign: 'center' }}>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.25rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.3rem' }}>
              <Eye size={14} color="var(--accent-color)" />
              <span>自选监控标的</span>
            </div>
            <div style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--accent-color)' }}>
              {analytics ? analytics.total_watchlist : '--'} 只
            </div>
          </div>

          <div style={{ background: 'rgba(16, 185, 129, 0.06)', border: '1px solid rgba(16, 185, 129, 0.2)', borderRadius: '14px', padding: '1rem', textAlign: 'center' }}>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.25rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.3rem' }}>
              <TrendingUp size={14} color="var(--success-color)" />
              <span>看多标的比例</span>
            </div>
            <div style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--success-color)' }}>
              {analytics ? `${analytics.bullish_ratio}%` : '--'}
            </div>
          </div>

          <div style={{ background: 'rgba(245, 158, 11, 0.06)', border: '1px solid rgba(245, 158, 11, 0.2)', borderRadius: '14px', padding: '1rem', textAlign: 'center' }}>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.25rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.3rem' }}>
              <Activity size={14} color="var(--warning-color)" />
              <span>累计投研研报数</span>
            </div>
            <div style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--warning-color)' }}>
              {analytics ? analytics.total_analyses : '--'} 份
            </div>
          </div>

          <div style={{ background: 'rgba(168, 85, 247, 0.06)', border: '1px solid rgba(168, 85, 247, 0.2)', borderRadius: '14px', padding: '1rem', textAlign: 'center' }}>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>最常分析标的</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#a855f7' }}>
              {analytics ? `${analytics.most_analyzed_symbol}` : '--'}
            </div>
          </div>
        </div>

        {/* Add Ticker Input Bar */}
        <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1.25rem' }}>
          <input
            type="text"
            value={newSymbolInput}
            onChange={(e) => setNewSymbolInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter') handleAddSymbol(); }}
            placeholder="添加新关注股票 (例如: TSLA, AAPL, NVDA, 600989)..."
            style={{
              flex: 1,
              padding: '0.65rem 1rem',
              borderRadius: '12px',
              background: 'rgba(241, 245, 249, 0.8)',
              border: '1px solid var(--surface-border, #e2e8f0)',
              color: 'var(--text-primary)',
              fontSize: '0.9rem',
              outline: 'none',
              boxSizing: 'border-box'
            }}
          />
          <button
            type="button"
            onClick={handleAddSymbol}
            disabled={!newSymbolInput.trim()}
            className="btn-primary"
            style={{ padding: '0.65rem 1.25rem', borderRadius: '12px', display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.88rem', fontWeight: 600 }}
          >
            <Plus size={16} />
            <span>添加自选</span>
          </button>
        </div>

        {/* Watchlist Table */}
        <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', paddingRight: '0.25rem' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.9rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--surface-border)', color: 'var(--text-secondary)', fontSize: '0.82rem' }}>
                <th style={{ padding: '0.65rem 1rem' }}>标的代码 (Symbol)</th>
                <th style={{ padding: '0.65rem 1rem' }}>最新价格</th>
                <th style={{ padding: '0.65rem 1rem' }}>24h 涨跌幅</th>
                <th style={{ padding: '0.65rem 1rem' }}>AI 最新裁决</th>
                <th style={{ padding: '0.65rem 1rem' }}>分析频次</th>
                <th style={{ padding: '0.65rem 1rem' }}>最近分析时间</th>
                <th style={{ padding: '0.65rem 1rem', textAlign: 'right' }}>操作</th>
              </tr>
            </thead>
            <tbody>
              {watchlist.map((item) => {
                const isPositive = item.change_pct >= 0;
                return (
                  <tr key={item.symbol} style={{ borderBottom: '1px solid var(--surface-border)', transition: 'background 0.2s ease' }}>
                    <td style={{ padding: '0.85rem 1rem', fontWeight: 700, color: 'var(--accent-color)' }}>
                      {item.symbol}
                    </td>
                    <td style={{ padding: '0.85rem 1rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                      ${item.current_price}
                    </td>
                    <td style={{ padding: '0.85rem 1rem', fontWeight: 600, color: isPositive ? 'var(--success-color)' : 'var(--danger-color)' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.2rem' }}>
                        {isPositive ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
                        <span>{isPositive ? '+' : ''}{item.change_pct}%</span>
                      </div>
                    </td>
                    <td style={{ padding: '0.85rem 1rem' }}>
                      <span style={{
                        fontSize: '0.75rem',
                        fontWeight: 700,
                        padding: '2px 8px',
                        borderRadius: '9999px',
                        background: item.latest_verdict === 'BUY' ? 'rgba(5,150,105,0.1)' : item.latest_verdict === 'SELL' ? 'rgba(220,38,38,0.1)' : 'rgba(217,119,6,0.1)',
                        color: item.latest_verdict === 'BUY' ? 'var(--success-color)' : item.latest_verdict === 'SELL' ? 'var(--danger-color)' : 'var(--warning-color)',
                        border: `1px solid ${item.latest_verdict === 'BUY' ? 'rgba(5,150,105,0.3)' : item.latest_verdict === 'SELL' ? 'rgba(220,38,38,0.3)' : 'rgba(217,119,6,0.3)'}`
                      }}>
                        {item.latest_verdict}
                      </span>
                    </td>
                    <td style={{ padding: '0.85rem 1rem', color: 'var(--text-secondary)' }}>
                      {item.analysis_count} 次
                    </td>
                    <td style={{ padding: '0.85rem 1rem', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                      {item.last_analyzed}
                    </td>
                    <td style={{ padding: '0.85rem 1rem', textAlign: 'right' }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '0.5rem' }}>
                        <button
                          type="button"
                          onClick={() => {
                            onClose();
                            onStartAnalysis(item.symbol);
                          }}
                          className="btn-secondary"
                          style={{ fontSize: '0.78rem', padding: '0.35rem 0.7rem', display: 'flex', alignItems: 'center', gap: '0.3rem', color: 'var(--accent-color)' }}
                        >
                          <Play size={13} />
                          <span>一键分析</span>
                        </button>
                        <button
                          type="button"
                          onClick={() => handleRemoveSymbol(item.symbol)}
                          style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', padding: '0.35rem' }}
                          title="移除自选"
                        >
                          <Trash2 size={15} />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
