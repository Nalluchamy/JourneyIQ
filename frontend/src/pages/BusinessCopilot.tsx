import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { RefreshCw, FileText } from 'lucide-react';
import { copilotApi } from '../services/api';
import { BusinessKPI } from '../components/BusinessKPI';
import { BusinessChat } from '../components/BusinessChat';
import { BusinessRiskCard } from '../components/BusinessRiskCard';
import { InsightCard } from '../components/InsightCard';
import { ExecutiveSummary } from '../components/ExecutiveSummary';

interface BusinessCopilotProps {
  onDrillDown: (tab: string) => void;
}

export const BusinessCopilot: React.FC<BusinessCopilotProps> = ({ onDrillDown }) => {
  // 1. Fetch Executive Summary data
  const { data: summary, refetch, isFetching } = useQuery({
    queryKey: ['copilot_summary_dashboard'],
    queryFn: async () => {
      return await copilotApi.getSummary();
    },
    refetchInterval: 60000 // every 60s
  });

  // Mock revenue chart timeline data grounded in real kpis
  const chartData = [
    { name: 'Mon', Revenue: (summary?.kpi_cards?.total_revenue || 120000) * 0.12, Orders: (summary?.kpi_cards?.confirmed_orders || 40) * 0.10 },
    { name: 'Tue', Revenue: (summary?.kpi_cards?.total_revenue || 120000) * 0.15, Orders: (summary?.kpi_cards?.confirmed_orders || 40) * 0.13 },
    { name: 'Wed', Revenue: (summary?.kpi_cards?.total_revenue || 120000) * 0.11, Orders: (summary?.kpi_cards?.confirmed_orders || 40) * 0.09 },
    { name: 'Thu', Revenue: (summary?.kpi_cards?.total_revenue || 120000) * 0.18, Orders: (summary?.kpi_cards?.confirmed_orders || 40) * 0.16 },
    { name: 'Fri', Revenue: (summary?.kpi_cards?.total_revenue || 120000) * 0.14, Orders: (summary?.kpi_cards?.confirmed_orders || 40) * 0.12 },
    { name: 'Sat', Revenue: (summary?.kpi_cards?.total_revenue || 120000) * 0.16, Orders: (summary?.kpi_cards?.confirmed_orders || 40) * 0.18 },
    { name: 'Sun', Revenue: (summary?.kpi_cards?.total_revenue || 120000) * 0.14, Orders: (summary?.kpi_cards?.confirmed_orders || 40) * 0.22 },
  ];

  return (
    <div className="space-y-6 text-slate-200 p-1">
      {/* Header Row */}
      <div className="rounded-lg border border-slate-800 bg-[#111827] p-6 flex justify-between items-center shadow-lg">
        <div>
          <h3 className="text-xl font-bold text-white flex items-center gap-2">
            AI Business Copilot Workspace
            <span className="bg-indigo-500/10 border border-indigo-500/25 text-indigo-400 px-2 py-0.5 rounded text-[10px] font-black uppercase">
              Enterprise v1.4
            </span>
          </h3>
          <p className="text-xs text-slate-450 mt-0.5">
            Query analytics parameters, download executive daily briefs, and audit operational anomalies securely.
          </p>
        </div>
        <button
          onClick={() => refetch()}
          disabled={isFetching}
          className="bg-slate-800 hover:bg-slate-850 border border-slate-700 text-slate-300 px-3.5 py-2 rounded-lg flex items-center gap-1.5 transition-colors cursor-pointer disabled:opacity-50 text-xs font-bold"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isFetching ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* KPI Cards section */}
      <BusinessKPI kpis={summary?.kpi_cards || null} />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Side: Natural Language Copilot Chat */}
        <div className="lg:col-span-2 space-y-6">
          <BusinessChat onDrillDown={onDrillDown} />
          <ExecutiveSummary />
        </div>

        {/* Right Side: Risks, Actions & Charts */}
        <div className="space-y-6">
          <BusinessRiskCard risks={summary?.business_risks || null} onDrillDown={onDrillDown} />
          
          <InsightCard insights={summary?.suggested_actions || null} onDrillDown={onDrillDown} />

          {/* Revenue and orders chart card */}
          <div className="rounded-xl border border-slate-800 bg-[#111827] p-5 space-y-4 shadow-lg">
            <h4 className="font-bold text-white text-xs uppercase tracking-wide">Weekly Sales Operations</h4>
            <div className="h-[180px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#6366f1" stopOpacity={0.2}/>
                      <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                  <XAxis dataKey="name" stroke="#64748b" fontSize={10} tickLine={false} />
                  <YAxis stroke="#64748b" fontSize={10} tickLine={false} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b' }} 
                    labelStyle={{ color: '#fff', fontWeight: 'bold' }}
                  />
                  <Area type="monotone" dataKey="Revenue" stroke="#6366f1" strokeWidth={2} fillOpacity={1} fill="url(#colorRevenue)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
