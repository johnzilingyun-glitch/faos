import React, { useState } from 'react';
import { History, X, Search, Trash2, Clock, ChevronRight } from 'lucide-react';

export interface HistoryRecord {
  id: string;
  timestamp: string;
  symbol: string;
  chatHistory: any[];
  followUpHistory: any[];
  reportContent: string | null;
  decision: any;
  analysisReports: any;
  discussion: any;
  marketData: any;
}

interface HistoryModalProps {
  isOpen: boolean;
  onClose: () => void;
  historyRecords: HistoryRecord[];
  onSelectRecord: (record: HistoryRecord) => void;
  onClearHistory: () => void;
  onDeleteRecord: (id: string) => void;
}

export const HistoryModal: React.FC<HistoryModalProps> = ({
  isOpen,
  onClose,
  historyRecords,
  onSelectRecord,
  onClearHistory,
  onDeleteRecord,
}) => {
  const [searchTerm, setSearchTerm] = useState('');

  if (!isOpen) return null;

  const filteredRecords = historyRecords.filter(rec =>
    rec.symbol.toLowerCase().includes(searchTerm.toLowerCase()) ||
    rec.timestamp.includes(searchTerm) ||
    (rec.reportContent && rec.reportContent.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  return (
    <div
      className="modal-backdrop"
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: 'rgba(15, 23, 42, 0.35)',
        backdropFilter: 'blur(10px)',
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
          maxWidth: '720px',
          maxHeight: '85vh',
          display: 'flex',
          flexDirection: 'column',
          background: 'var(--surface-bg, rgba(255, 255, 255, 0.95))',
          border: '1px solid var(--surface-border, #e2e8f0)',
          borderRadius: '20px',
          padding: '1.75rem',
          boxShadow: '0 20px 40px rgba(0, 0, 0, 0.12)',
          color: 'var(--text-primary, #0f172a)'
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem', borderBottom: '1px solid var(--surface-border, #e2e8f0)', paddingBottom: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <History size={22} color="var(--accent-color)" />
            <h2 style={{ margin: 0, fontSize: '1.2rem', fontWeight: 600, color: 'var(--text-primary, #0f172a)' }}>
              历史分析与对话档案
            </h2>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            {historyRecords.length > 0 && (
              <button
                type="button"
                onClick={onClearHistory}
                className="btn-secondary"
                style={{ fontSize: '0.8rem', padding: '0.4rem 0.8rem', color: 'var(--danger-color, #dc2626)', borderColor: 'rgba(220,38,38,0.2)', display: 'flex', alignItems: 'center', gap: '0.3rem', background: 'rgba(220,38,38,0.05)' }}
              >
                <Trash2 size={14} /> 清空全部记录
              </button>
            )}
            <button type="button" onClick={onClose} style={{ background: 'transparent', border: 'none', color: 'var(--text-secondary, #475569)', cursor: 'pointer', padding: '0.4rem' }}>
              <X size={20} />
            </button>
          </div>
        </div>

        {/* Search Bar */}
        <div style={{ position: 'relative', marginBottom: '1.25rem', width: '100%', boxSizing: 'border-box' }}>
          <Search size={18} color="var(--text-muted, #94a3b8)" style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)' }} />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="搜索股票代码、生成时间或研报关键词..."
            style={{
              width: '100%',
              boxSizing: 'border-box',
              padding: '0.75rem 1rem 0.75rem 2.75rem',
              borderRadius: '12px',
              background: 'rgba(241, 245, 249, 0.8)',
              border: '1px solid var(--surface-border, #e2e8f0)',
              color: 'var(--text-primary, #0f172a)',
              fontSize: '0.9rem',
              outline: 'none'
            }}
          />
        </div>

        {/* Record List */}
        <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '0.85rem', paddingRight: '0.25rem' }}>
          {filteredRecords.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '3rem 1rem', color: 'var(--text-secondary, #475569)' }}>
              <Clock size={40} style={{ margin: '0 auto 1rem auto', opacity: 0.4 }} />
              <p style={{ margin: 0, fontSize: '0.95rem' }}>
                {historyRecords.length === 0 ? '暂无历史分析记录。完成一次投研分析后将自动存入此档案库。' : '未找到匹配的历史研报记录。'}
              </p>
            </div>
          ) : (
            filteredRecords.map((rec) => (
              <div
                key={rec.id}
                style={{
                  background: 'rgba(255, 255, 255, 0.8)',
                  border: '1px solid var(--surface-border, #e2e8f0)',
                  borderRadius: '14px',
                  padding: '1rem 1.25rem',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  boxShadow: '0 2px 6px rgba(0, 0, 0, 0.02)'
                }}
                onClick={() => onSelectRecord(rec)}
              >
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem', flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <span style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--accent-color, #3b82f6)' }}>
                      {rec.symbol}
                    </span>
                    {rec.decision?.pm?.decision && (
                      <span style={{
                        fontSize: '0.75rem',
                        fontWeight: 700,
                        padding: '2px 8px',
                        borderRadius: '9999px',
                        background: rec.decision.pm.decision === 'BUY' ? 'rgba(5,150,105,0.1)' : rec.decision.pm.decision === 'SELL' ? 'rgba(220,38,38,0.1)' : 'rgba(217,119,6,0.1)',
                        color: rec.decision.pm.decision === 'BUY' ? 'var(--success-color, #059669)' : rec.decision.pm.decision === 'SELL' ? 'var(--danger-color, #dc2626)' : 'var(--warning-color, #d97706)',
                        border: `1px solid ${rec.decision.pm.decision === 'BUY' ? 'rgba(5,150,105,0.3)' : rec.decision.pm.decision === 'SELL' ? 'rgba(220,38,38,0.3)' : 'rgba(217,119,6,0.3)'}`
                      }}>
                        {rec.decision.pm.decision}
                      </span>
                    )}
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-muted, #94a3b8)' }}>
                      {rec.timestamp}
                    </span>
                  </div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary, #475569)', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                    {rec.reportContent ? rec.reportContent.slice(0, 140) + '...' : '已完成分析对话记录'}
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginLeft: '1rem' }} onClick={(e) => e.stopPropagation()}>
                  <button
                    type="button"
                    onClick={() => onDeleteRecord(rec.id)}
                    style={{ background: 'transparent', border: 'none', color: 'var(--text-muted, #94a3b8)', cursor: 'pointer', padding: '0.4rem' }}
                    title="删除此记录"
                  >
                    <Trash2 size={16} />
                  </button>
                  <ChevronRight size={18} color="var(--accent-color, #3b82f6)" />
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
