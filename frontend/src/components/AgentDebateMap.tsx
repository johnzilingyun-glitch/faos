import React from 'react';

export interface DebateNode {
  agent: string;
  role: string;
  opinion: string;
  color: string;
}

export interface AgentDebateMapProps {
  bull: string;
  bear: string;
  manager: string;
  risk: string;
}

export function AgentDebateMap({ bull, bear, manager, risk }: AgentDebateMapProps) {
  return (
    <div className="w-full bg-slate-900 rounded-xl p-6 border border-slate-800 shadow-xl overflow-x-auto">
      <h3 className="text-slate-200 font-semibold mb-6">Agent Debate Map</h3>
      
      <div className="flex flex-col items-center min-w-[600px] gap-8">
        {/* Tier 1: Researchers */}
        <div className="flex justify-between w-full max-w-2xl gap-8 relative">
          <div className="flex-1 bg-green-900/30 border border-green-500/30 p-4 rounded-lg relative z-10">
            <h4 className="text-green-400 font-bold mb-2">Bull Researcher</h4>
            <p className="text-slate-300 text-sm h-32 overflow-y-auto">{bull}</p>
          </div>
          
          <div className="flex-1 bg-red-900/30 border border-red-500/30 p-4 rounded-lg relative z-10">
            <h4 className="text-red-400 font-bold mb-2">Bear Researcher</h4>
            <p className="text-slate-300 text-sm h-32 overflow-y-auto">{bear}</p>
          </div>
        </div>

        {/* Connecting Lines (Simulated with div borders) */}
        <div className="w-px h-8 bg-slate-600 -my-8 z-0"></div>

        {/* Tier 2: Research Manager */}
        <div className="w-full max-w-xl bg-blue-900/30 border border-blue-500/30 p-4 rounded-lg relative z-10">
          <h4 className="text-blue-400 font-bold mb-2">Research Manager (Consensus)</h4>
          <p className="text-slate-300 text-sm h-24 overflow-y-auto">{manager}</p>
        </div>
        
        <div className="w-px h-8 bg-slate-600 -my-8 z-0"></div>

        {/* Tier 3: Chief Risk Officer */}
        <div className="w-full max-w-md bg-orange-900/30 border border-orange-500/30 p-4 rounded-lg relative z-10">
          <h4 className="text-orange-400 font-bold mb-2">Chief Risk Officer (Guardrails)</h4>
          <p className="text-slate-300 text-sm h-24 overflow-y-auto">{risk}</p>
        </div>
      </div>
    </div>
  );
}
