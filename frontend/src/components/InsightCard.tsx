import React from 'react';
import { Lightbulb, ArrowUpRight } from 'lucide-react';

interface SuggestedAction {
  id: number;
  insight: string;
  action: string;
  severity: string;
}

interface InsightCardProps {
  insights: SuggestedAction[] | null;
  onDrillDown: (type: string) => void;
}

export const InsightCard: React.FC<InsightCardProps> = ({ insights, onDrillDown }) => {
  if (!insights || insights.length === 0) {
    return (
      <div className="rounded-xl border border-slate-800 bg-[#111827] p-5 text-center">
        <span className="text-xs text-slate-500 font-semibold block">Awaiting observation events. Running telemetry diagnostic monitors...</span>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-slate-800 bg-[#111827] p-5 space-y-4">
      <div className="flex items-center gap-2">
        <span className="p-1.5 bg-indigo-500/10 rounded-lg text-indigo-400 border border-indigo-500/25">
          <Lightbulb className="w-4 h-4" />
        </span>
        <h4 className="font-bold text-white text-sm">Suggested Business Action Plans</h4>
      </div>

      <div className="space-y-3.5 divide-y divide-slate-850">
        {insights.map((ins) => (
          <div key={ins.id} className="pt-3.5 first:pt-0 space-y-2">
            <div className="flex justify-between items-start">
              <h5 className="text-xs font-bold text-white leading-snug">{ins.insight}</h5>
              <button
                onClick={() => onDrillDown('agent')}
                className="text-[10px] text-indigo-400 font-black flex items-center gap-0.5 hover:text-indigo-300 transition-colors uppercase cursor-pointer shrink-0 ml-2"
              >
                Approve Action <ArrowUpRight className="w-3.5 h-3.5" />
              </button>
            </div>
            
            <p className="text-xs text-indigo-400 leading-relaxed font-semibold italic bg-indigo-500/5 p-2 rounded border border-indigo-500/10">
              AI Action: {ins.action}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
};
