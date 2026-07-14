import React from 'react';
import { AlertOctagon, ArrowUpRight } from 'lucide-react';

interface Risk {
  category: string;
  threat: string;
  description: string;
  impact: string;
  action: string;
  severity: string;
}

interface BusinessRiskCardProps {
  risks: Risk[] | null;
  onDrillDown: (category: string) => void;
}

export const BusinessRiskCard: React.FC<BusinessRiskCardProps> = ({ risks, onDrillDown }) => {
  if (!risks || risks.length === 0) {
    return (
      <div className="rounded-xl border border-slate-800 bg-[#111827] p-5 text-center">
        <span className="text-xs text-slate-500 font-semibold block">No immediate operational threats detected. Baseline performance remains optimal.</span>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-slate-800 bg-[#111827] p-5 space-y-4">
      <div className="flex items-center gap-2">
        <span className="p-1.5 bg-rose-500/10 rounded-lg text-rose-450 border border-rose-500/25">
          <AlertOctagon className="w-4 h-4" />
        </span>
        <h4 className="font-bold text-white text-sm">Operational Risks & Anomalies</h4>
      </div>

      <div className="space-y-3.5 divide-y divide-slate-850">
        {risks.map((risk, idx) => (
          <div key={idx} className="pt-3.5 first:pt-0 space-y-2">
            <div className="flex justify-between items-start">
              <div>
                <span className="bg-rose-500/10 border border-rose-500/25 text-rose-450 px-2 py-0.5 text-[9px] font-black uppercase rounded block w-fit mb-1">
                  {risk.severity} Severity
                </span>
                <h5 className="text-xs font-bold text-white">{risk.threat}</h5>
              </div>
              <button
                onClick={() => onDrillDown(risk.category.toLowerCase())}
                className="text-[10px] text-indigo-400 font-black flex items-center gap-0.5 hover:text-indigo-300 transition-colors uppercase cursor-pointer"
              >
                Explore <ArrowUpRight className="w-3.5 h-3.5" />
              </button>
            </div>
            
            <p className="text-xs text-slate-350 leading-relaxed font-semibold">{risk.description}</p>
            <div className="text-[11px] text-slate-450"><span className="text-slate-400 font-extrabold">Proposed:</span> {risk.action}</div>
          </div>
        ))}
      </div>
    </div>
  );
};
