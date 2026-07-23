import React, { useState, useEffect } from 'react';
import { Target, X, RefreshCw, Award, Brain, Zap } from 'lucide-react';

interface AnalystRanking {
  analyst: string;
  accuracy: number;
  total_evaluations: number;
}

interface DecisionStat {
  decision: string;
  total: number;
  win: number;
  win_rate: number;
}

interface ExperienceRule {
  id: string;
  category: string;
  rule: string;
  trigger_count: number;
  success_improvement: string;
  created_at: string;
}

interface AccuracyData {
  total_predictions: number;
  winning_trades: number;
  losing_trades: number;
  pending_count?: number;
  unresolved_count?: number;
  win_rate: number;
  avg_return_pct: number;
  avg_win_pct?: number;
  avg_loss_pct?: number;
  profit_loss_ratio: string;
  analyst_rankings: AnalystRanking[];
  decision_stats?: DecisionStat[];
  hold_window_days?: number;
  data_source?: string;
}

interface AccuracyDashboardModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const AccuracyDashboardModal: React.FC<AccuracyDashboardModalProps> = ({
  isOpen,
  onClose,
}) => {
  const [loading, setLoading] = useState(false);
  const [accuracyData, setAccuracyData] = useState<AccuracyData | null>(null);
  const [experiences, setExperiences] = useState<ExperienceRule[]>([]);

  const fetchBacktestData = async (force = false) => {
    setLoading(true);
    try {
      const [accRes, expRes] = await Promise.all([
        fetch(`/api/backtest/accuracy${force ? '?force=true' : ''}`),
        fetch('/api/experience')
      ]);

      if (accRes.ok) {
        const accJson = await accRes.json();
        setAccuracyData(accJson);
      }
      if (expRes.ok) {
        const expJson = await expRes.json();
        setExperiences(expJson);
      }
    } catch (err) {
      console.error('Failed to load backtest data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchBacktestData();
    }
  }, [isOpen]);

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
          maxWidth: '850px',
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
            <Target size={24} color="var(--accent-color)" />
            <div>
              <h2 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary, #0f172a)' }}>
                AI 预测准确率回测与自我闭环进化看板
              </h2>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary, #475569)' }}>
                对比历史决策与行情变化，反思经验法则并实现闭环自我修正
              </span>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <button
              type="button"
              onClick={() => fetchBacktestData(true)}
              disabled={loading}
              className="btn-secondary"
              style={{ fontSize: '0.85rem', padding: '0.4rem 0.85rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}
            >
              <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
              <span>重新评估</span>
            </button>
            <button type="button" onClick={onClose} style={{ background: 'transparent', border: 'none', color: 'var(--text-secondary, #475569)', cursor: 'pointer', padding: '0.4rem' }}>
              <X size={20} />
            </button>
          </div>
        </div>

        {/* Modal Scroll Content */}
        <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '1.5rem', paddingRight: '0.25rem' }}>
          
          {/* Key Stat Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem' }}>
            <div style={{ background: 'rgba(59, 130, 246, 0.06)', border: '1px solid rgba(59, 130, 246, 0.2)', borderRadius: '14px', padding: '1rem', textAlign: 'center' }}>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>预测胜率 (Win Rate)</div>
              <div style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--accent-color)' }}>
                {accuracyData ? `${accuracyData.win_rate}%` : '--'}
              </div>
            </div>

            <div style={{ background: 'rgba(16, 185, 129, 0.06)', border: '1px solid rgba(16, 185, 129, 0.2)', borderRadius: '14px', padding: '1rem', textAlign: 'center' }}>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>盈亏比 (P/L Ratio)</div>
              <div style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--success-color)' }}>
                {accuracyData ? accuracyData.profit_loss_ratio : '--'}
              </div>
            </div>

            <div style={{ background: 'rgba(245, 158, 11, 0.06)', border: '1px solid rgba(245, 158, 11, 0.2)', borderRadius: '14px', padding: '1rem', textAlign: 'center' }}>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>评估决策样本数</div>
              <div style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--warning-color)' }}>
                {accuracyData ? accuracyData.total_predictions : '--'} 次
              </div>
            </div>

            <div style={{ background: 'rgba(168, 85, 247, 0.06)', border: '1px solid rgba(168, 85, 247, 0.2)', borderRadius: '14px', padding: '1rem', textAlign: 'center' }}>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>平均策略收益率</div>
              <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#a855f7' }}>
                {accuracyData ? `${accuracyData.avg_return_pct > 0 ? '+' : ''}${accuracyData.avg_return_pct}%` : '--'}
              </div>
            </div>
          </div>

          {/* Data source & pending banner */}
          {accuracyData && (
            <div style={{
              display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.5rem',
              background: 'rgba(59, 130, 246, 0.05)', border: '1px solid rgba(59, 130, 246, 0.18)',
              borderRadius: '12px', padding: '0.65rem 1rem', fontSize: '0.8rem', color: 'var(--text-secondary)'
            }}>
              <span>
                数据来源: <strong>{accuracyData.data_source || 'Yahoo Finance'}</strong>
                {typeof accuracyData.hold_window_days === 'number' && <> · 持有窗口 T+{accuracyData.hold_window_days} 交易日</>}
              </span>
              <span style={{ display: 'flex', gap: '0.85rem' }}>
                {typeof accuracyData.avg_win_pct === 'number' && (
                  <span style={{ color: 'var(--success-color)' }}>均盈 +{accuracyData.avg_win_pct}%</span>
                )}
                {typeof accuracyData.avg_loss_pct === 'number' && (
                  <span style={{ color: 'var(--danger-color)' }}>均亏 {accuracyData.avg_loss_pct}%</span>
                )}
                {typeof accuracyData.pending_count === 'number' && accuracyData.pending_count > 0 && (
                  <span style={{ color: 'var(--warning-color)' }}>待结算 {accuracyData.pending_count} 条 (前向窗口未到)</span>
                )}
                {typeof accuracyData.unresolved_count === 'number' && accuracyData.unresolved_count > 0 && (
                  <span style={{ color: 'var(--text-muted)' }}>无法解析 {accuracyData.unresolved_count} 条</span>
                )}
              </span>
            </div>
          )}

          {/* Empty-state hint when nothing is evaluable yet */}
          {accuracyData && accuracyData.total_predictions === 0 && (
            <div style={{
              background: 'rgba(245, 158, 11, 0.06)', border: '1px solid rgba(245, 158, 11, 0.25)',
              borderRadius: '12px', padding: '1rem', fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.6
            }}>
              暂无可结算的历史决策：所有决策的 T+{accuracyData.hold_window_days ?? 5} 前向行情窗口尚未走完（例如决策发生在最近交易日）。
              随着时间推移，真实前向收益到位后本看板将自动计算实际胜率、盈亏比与分析师命中率。
            </div>
          )}

          {/* Decision-type breakdown (real) */}
          {accuracyData?.decision_stats && accuracyData.decision_stats.length > 0 && (
            <div style={{ background: 'rgba(255, 255, 255, 0.8)', border: '1px solid var(--surface-border)', borderRadius: '16px', padding: '1.25rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
                <Target size={18} color="var(--accent-color)" />
                <h3 style={{ margin: 0, fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                  决策类型实测胜率 (BUY / SELL / HOLD)
                </h3>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: `repeat(${accuracyData.decision_stats.length}, 1fr)`, gap: '1rem' }}>
                {accuracyData.decision_stats.map((d) => (
                  <div key={d.decision} style={{ background: 'rgba(241, 245, 249, 0.6)', border: '1px solid var(--surface-border)', borderRadius: '12px', padding: '0.85rem 1rem', textAlign: 'center' }}>
                    <div style={{ fontSize: '0.85rem', fontWeight: 700, marginBottom: '0.3rem' }}>{d.decision}</div>
                    <div style={{ fontSize: '1.3rem', fontWeight: 800, color: 'var(--accent-color)' }}>{d.win_rate}%</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{d.win}/{d.total} 命中</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Section 1: Analyst Accuracy Scoreboard */}
          <div style={{ background: 'rgba(255, 255, 255, 0.8)', border: '1px solid var(--surface-border)', borderRadius: '16px', padding: '1.25rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
              <Award size={18} color="var(--accent-color)" />
              <h3 style={{ margin: 0, fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                分析师方向命中率分布 (实测归因)
              </h3>
            </div>

            {accuracyData?.analyst_rankings && accuracyData.analyst_rankings.length > 0 ? (
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                {accuracyData.analyst_rankings.map((item, idx) => (
                  <div key={idx} style={{ background: 'rgba(241, 245, 249, 0.6)', border: '1px solid var(--surface-border)', borderRadius: '12px', padding: '0.85rem 1rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.4rem', fontSize: '0.9rem', fontWeight: 600 }}>
                      <span>{item.analyst} · {item.total_evaluations} 次</span>
                      <span style={{ color: 'var(--accent-color)' }}>{item.accuracy}%</span>
                    </div>
                    <div style={{ width: '100%', height: '8px', background: 'rgba(226, 232, 240, 0.8)', borderRadius: '9999px', overflow: 'hidden' }}>
                      <div style={{ width: `${item.accuracy}%`, height: '100%', background: 'linear-gradient(90deg, #3b82f6, #10b981)', borderRadius: '9999px', transition: 'width 0.4s ease' }} />
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>尚无已结算样本，分析师命中率待前向行情到位后生成。</div>
            )}
          </div>

          {/* Section 2: Self-Optimization Experience Memory Log */}
          <div style={{ background: 'rgba(255, 255, 255, 0.8)', border: '1px solid var(--surface-border)', borderRadius: '16px', padding: '1.25rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Brain size={18} color="#10b981" />
                <h3 style={{ margin: 0, fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                  AI 自我进化与经验反思记忆库 (Self-Optimization Memory)
                </h3>
              </div>
              <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                盘后检讨智能体萃取的规则已注入 Prompt
              </span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
              {experiences.length === 0 && (
                <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                  经验规则由真实回测结果自动萃取；当前尚无已结算样本，待前向行情到位后将自动生成数据驱动的规则。
                </div>
              )}
              {experiences.map((exp) => (
                <div key={exp.id} style={{ background: 'rgba(241, 245, 249, 0.7)', border: '1px solid var(--surface-border)', borderRadius: '12px', padding: '0.9rem 1.1rem', display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <span style={{ fontSize: '0.75rem', fontWeight: 700, padding: '2px 8px', borderRadius: '9999px', background: 'rgba(59,130,246,0.1)', color: 'var(--accent-color)', border: '1px solid rgba(59,130,246,0.2)' }}>
                        {exp.category}
                      </span>
                      <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{exp.created_at}</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', fontSize: '0.8rem', fontWeight: 700, color: 'var(--success-color)' }}>
                      <Zap size={14} />
                      <span>规则触发提升胜率: {exp.success_improvement}</span>
                    </div>
                  </div>
                  <div style={{ fontSize: '0.9rem', color: 'var(--text-primary)', lineHeight: 1.5, fontWeight: 500 }}>
                    💡 {exp.rule}
                  </div>
                </div>
              ))}
            </div>
          </div>

        </div>
      </div>
    </div>
  );
};
