import React from 'react';
import {
  Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer
} from 'recharts';

export interface ScoreRadarProps {
  scores: {
    fundamental: number;
    technical: number;
    sentiment: number;
    macro: number;
    risk: number;
  };
}

export function ScoreRadar({ scores }: ScoreRadarProps) {
  const data = [
    { subject: 'Fundamentals', A: scores.fundamental, fullMark: 100 },
    { subject: 'Technicals', A: scores.technical, fullMark: 100 },
    { subject: 'Sentiment', A: scores.sentiment, fullMark: 100 },
    { subject: 'Macro', A: scores.macro, fullMark: 100 },
    { subject: 'Risk Mgr', A: scores.risk, fullMark: 100 },
  ];

  return (
    <div className="w-full h-[300px] bg-slate-900 rounded-xl p-4 border border-slate-800 shadow-xl">
      <h3 className="text-slate-200 font-semibold mb-2">Alpha Scoring Radar</h3>
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart cx="50%" cy="50%" outerRadius="70%" data={data}>
          <PolarGrid stroke="#334155" />
          <PolarAngleAxis dataKey="subject" tick={{ fill: '#94a3b8', fontSize: 12 }} />
          <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
          <Radar
            name="Score"
            dataKey="A"
            stroke="#10b981"
            fill="#10b981"
            fillOpacity={0.5}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}
