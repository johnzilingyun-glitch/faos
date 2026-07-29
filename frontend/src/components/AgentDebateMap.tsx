import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { ShieldAlert, Users } from 'lucide-react';

export interface AgentDebateMapProps {
  bull: string;
  bear: string;
  manager: string;
  risk: string;
  bullStructured?: any;
  bearStructured?: any;
  managerStructured?: any;
  riskStructured?: any;
}

export function AgentDebateMap({
  bull,
  bear,
  manager,
  risk,
  bullStructured,
  bearStructured,
  managerStructured,
  riskStructured,
}: AgentDebateMapProps) {
  const safeBull = typeof bull === 'string' ? bull : JSON.stringify(bull || '');
  const safeBear = typeof bear === 'string' ? bear : JSON.stringify(bear || '');
  const safeManager = typeof manager === 'string' ? manager : JSON.stringify(manager || '');
  const safeRisk = typeof risk === 'string' ? risk : JSON.stringify(risk || '');

  const bullClaims = Array.isArray(bullStructured?.claims) ? bullStructured.claims : [];
  const bearRebuttals = Array.isArray(bearStructured?.rebuttals) ? bearStructured.rebuttals : [];
  const managerVerdicts = Array.isArray(managerStructured?.verdicts) ? managerStructured.verdicts : [];
  const riskHedges = Array.isArray(riskStructured?.hedges) ? riskStructured.hedges : [];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Debate Phase: Bull vs Bear */}
      <div className="grid-2x2">
        <div className="impeccable-card card-bull">
          <div className="card-header" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <TrendingUpIcon />
            <div className="card-title" style={{ color: 'var(--success-color)' }}>Bull Analyst</div>
          </div>
          <div className="card-body small markdown-body overflow-x-auto">
            {bullClaims.length > 0 && (
              <div style={{ marginBottom: '0.8rem' }}>
                <div style={{ fontWeight: 700, marginBottom: '0.35rem' }}>Claims</div>
                {bullClaims.slice(0, 8).map((c: any) => (
                  <div key={c.id || c.statement} style={{ marginBottom: '0.35rem' }}>
                    <strong>{c.id || 'C?'}</strong> {c.statement}
                  </div>
                ))}
                <hr style={{ opacity: 0.15, margin: '0.6rem 0' }} />
              </div>
            )}
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{safeBull}</ReactMarkdown>
          </div>
        </div>

        <div className="impeccable-card card-bear">
          <div className="card-header" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <TrendingDownIcon />
            <div className="card-title" style={{ color: 'var(--danger-color)' }}>Bear Analyst</div>
          </div>
          <div className="card-body small markdown-body overflow-x-auto">
            {bearRebuttals.length > 0 && (
              <div style={{ marginBottom: '0.8rem' }}>
                <div style={{ fontWeight: 700, marginBottom: '0.35rem' }}>Point-by-Point Rebuttals</div>
                {bearRebuttals.slice(0, 8).map((r: any, idx: number) => (
                  <div key={`${r.target_claim_id}-${idx}`} style={{ marginBottom: '0.35rem' }}>
                    <strong>[vs {r.target_claim_id || 'C?'}]</strong> {r.counter}
                  </div>
                ))}
                <hr style={{ opacity: 0.15, margin: '0.6rem 0' }} />
              </div>
            )}
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{safeBear}</ReactMarkdown>
          </div>
        </div>
      </div>

      {/* Consensus Phase */}
      <div className="impeccable-card card-manager">
        <div className="card-header" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Users size={18} color="var(--accent-color)" />
          <div className="card-title" style={{ color: 'var(--accent-color)' }}>Portfolio Manager (Consensus)</div>
        </div>
        <div className="card-body small markdown-body overflow-x-auto">
          {managerVerdicts.length > 0 && (
            <div style={{ marginBottom: '0.8rem' }}>
              <div style={{ fontWeight: 700, marginBottom: '0.35rem' }}>Per-Claim Verdicts</div>
              {managerVerdicts.slice(0, 8).map((v: any, idx: number) => (
                <div key={`${v.claim_id}-${idx}`} style={{ marginBottom: '0.35rem' }}>
                  <strong>{v.claim_id || 'C?'}</strong> winner={String(v.winner || 'tie')}
                </div>
              ))}
              <hr style={{ opacity: 0.15, margin: '0.6rem 0' }} />
            </div>
          )}
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{safeManager}</ReactMarkdown>
        </div>
      </div>

      {/* Risk Phase */}
      <div className="impeccable-card card-risk">
        <div className="card-header" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <ShieldAlert size={18} color="var(--warning-color)" />
          <div className="card-title" style={{ color: 'var(--warning-color)' }}>Chief Risk Officer (Guardrails)</div>
        </div>
        <div className="card-body small markdown-body overflow-x-auto">
          {(riskStructured?.stop_loss || riskStructured?.position_sizing || riskHedges.length > 0) && (
            <div style={{ marginBottom: '0.8rem' }}>
              <div style={{ fontWeight: 700, marginBottom: '0.35rem' }}>Structured Guardrails</div>
              {riskStructured?.stop_loss && <div><strong>Stop Loss:</strong> {riskStructured.stop_loss}</div>}
              {riskStructured?.position_sizing && <div><strong>Position:</strong> {riskStructured.position_sizing}</div>}
              {riskHedges.length > 0 && (
                <div>
                  <strong>Hedges:</strong>
                  {riskHedges.slice(0, 5).map((h: string, idx: number) => (
                    <div key={idx}>- {h}</div>
                  ))}
                </div>
              )}
              <hr style={{ opacity: 0.15, margin: '0.6rem 0' }} />
            </div>
          )}
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{safeRisk}</ReactMarkdown>
        </div>
      </div>
    </div>
  );
}

// Simple icons for Bull and Bear since lucide-react might not be fully imported in this file context
function TrendingUpIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--success-color)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"></polyline><polyline points="16 7 22 7 22 13"></polyline></svg>
  );
}
function TrendingDownIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--danger-color)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="22 17 13.5 8.5 8.5 13.5 2 7"></polyline><polyline points="16 17 22 17 22 11"></polyline></svg>
  );
}
