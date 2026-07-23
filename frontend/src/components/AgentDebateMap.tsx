import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { ShieldAlert, Users } from 'lucide-react';

export interface AgentDebateMapProps {
  bull: string;
  bear: string;
  manager: string;
  risk: string;
}

export function AgentDebateMap({ bull, bear, manager, risk }: AgentDebateMapProps) {
  const safeBull = typeof bull === 'string' ? bull : JSON.stringify(bull || '');
  const safeBear = typeof bear === 'string' ? bear : JSON.stringify(bear || '');
  const safeManager = typeof manager === 'string' ? manager : JSON.stringify(manager || '');
  const safeRisk = typeof risk === 'string' ? risk : JSON.stringify(risk || '');

  return (
    <div className="w-full bg-[#1e293b] rounded-xl p-8 border border-[#334155] shadow-2xl flex flex-col gap-6">
      
      {/* Debate Phase */}
      <div className="flex flex-col gap-6 w-full">
        {/* Bull Agent */}
        <div className="flex-1 bg-[#064e3b]/40 border border-[#10b981]/30 rounded-xl overflow-hidden flex flex-col">
          <div className="bg-[#10b981]/20 p-3 px-5 border-b border-[#10b981]/30 flex items-center gap-3">
            <div className="bg-[#10b981] p-1.5 rounded-full"><TrendingUpIcon /></div>
            <h4 className="text-[#34d399] font-bold text-lg m-0">Bull Analyst</h4>
          </div>
          <div className="p-5 text-[#cbd5e1] text-sm markdown-body prose-invert flex-1 overflow-x-auto">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{safeBull}</ReactMarkdown>
          </div>
        </div>

        {/* Bear Agent */}
        <div className="flex-1 bg-[#7f1d1d]/40 border border-[#ef4444]/30 rounded-xl overflow-hidden flex flex-col">
          <div className="bg-[#ef4444]/20 p-3 px-5 border-b border-[#ef4444]/30 flex items-center gap-3">
            <div className="bg-[#ef4444] p-1.5 rounded-full"><TrendingDownIcon /></div>
            <h4 className="text-[#f87171] font-bold text-lg m-0">Bear Analyst</h4>
          </div>
          <div className="p-5 text-[#cbd5e1] text-sm markdown-body prose-invert flex-1 overflow-x-auto">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{safeBear}</ReactMarkdown>
          </div>
        </div>
      </div>

      {/* Consensus Phase */}
      <div className="w-full bg-[#1e3a8a]/40 border border-[#3b82f6]/30 rounded-xl overflow-hidden flex flex-col mt-4">
        <div className="bg-[#3b82f6]/20 p-3 px-5 border-b border-[#3b82f6]/30 flex items-center gap-3">
          <div className="bg-[#3b82f6] p-1.5 rounded-full"><Users size={16} color="white" /></div>
          <h4 className="text-[#60a5fa] font-bold text-lg m-0">Portfolio Manager (Consensus)</h4>
        </div>
        <div className="p-5 text-[#cbd5e1] text-sm markdown-body prose-invert overflow-x-auto">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{safeManager}</ReactMarkdown>
        </div>
      </div>

      {/* Risk Phase */}
      <div className="w-full bg-[#7c2d12]/40 border border-[#f97316]/30 rounded-xl overflow-hidden flex flex-col mt-4">
        <div className="bg-[#f97316]/20 p-3 px-5 border-b border-[#f97316]/30 flex items-center gap-3">
          <div className="bg-[#f97316] p-1.5 rounded-full"><ShieldAlert size={16} color="white" /></div>
          <h4 className="text-[#fdba74] font-bold text-lg m-0">Chief Risk Officer (Guardrails)</h4>
        </div>
        <div className="p-5 text-[#cbd5e1] text-sm markdown-body prose-invert overflow-x-auto">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{safeRisk}</ReactMarkdown>
        </div>
      </div>

    </div>
  );
}

// Simple icons for Bull and Bear since lucide-react might not be fully imported in this file context
function TrendingUpIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"></polyline><polyline points="16 7 22 7 22 13"></polyline></svg>
  );
}
function TrendingDownIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="22 17 13.5 8.5 8.5 13.5 2 7"></polyline><polyline points="16 17 22 17 22 11"></polyline></svg>
  );
}
