import React from 'react';
import { 
  TrendingUp, 
  ShoppingBag, 
  Percent, 
  Smile, 
  Package, 
  Cpu, 
  ShieldAlert, 
  Award 
} from 'lucide-react';

interface BusinessKPIProps {
  kpis: {
    total_revenue: number;
    confirmed_orders: number;
    conversion_rate_pct: number;
    customer_satisfaction_score: number;
    inventory_health_pct: number;
    recommendation_accuracy_pct: number;
    agent_decisions_count: number;
    business_risk_score: number;
  } | null;
}

export const BusinessKPI: React.FC<BusinessKPIProps> = ({ kpis }) => {
  if (!kpis) return null;

  const cardConfig = [
    {
      title: "Total Revenue",
      value: `₹${kpis.total_revenue.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`,
      icon: <TrendingUp className="w-5 h-5 text-indigo-400" />,
      colorClass: "from-indigo-500/10 to-purple-500/10 border-indigo-500/20"
    },
    {
      title: "Confirmed Orders",
      value: kpis.confirmed_orders.toLocaleString(),
      icon: <ShoppingBag className="w-5 h-5 text-emerald-400" />,
      colorClass: "from-emerald-500/10 to-teal-500/10 border-emerald-500/20"
    },
    {
      title: "Conversion Rate",
      value: `${kpis.conversion_rate_pct}%`,
      icon: <Percent className="w-5 h-5 text-cyan-400" />,
      colorClass: "from-cyan-500/10 to-blue-500/10 border-cyan-500/20"
    },
    {
      title: "Satisfaction Score",
      value: `${kpis.customer_satisfaction_score}/100`,
      icon: <Smile className="w-5 h-5 text-pink-400" />,
      colorClass: "from-pink-500/10 to-rose-500/10 border-pink-500/20"
    },
    {
      title: "Inventory Health",
      value: `${kpis.inventory_health_pct}%`,
      icon: <Package className="w-5 h-5 text-amber-400" />,
      colorClass: "from-amber-500/10 to-orange-500/10 border-amber-500/20"
    },
    {
      title: "Recommendation Accuracy",
      value: `${kpis.recommendation_accuracy_pct}%`,
      icon: <Cpu className="w-5 h-5 text-violet-400" />,
      colorClass: "from-violet-500/10 to-fuchsia-500/10 border-violet-500/20"
    },
    {
      title: "Agent Decisions",
      value: kpis.agent_decisions_count,
      icon: <Award className="w-5 h-5 text-blue-400" />,
      colorClass: "from-blue-500/10 to-indigo-500/10 border-blue-500/20"
    },
    {
      title: "Business Risk Score",
      value: `${kpis.business_risk_score}/100`,
      icon: <ShieldAlert className="w-5 h-5 text-rose-450" />,
      colorClass: "from-rose-500/10 to-red-500/10 border-rose-500/20"
    }
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {cardConfig.map((card, i) => (
        <div 
          key={i} 
          className={`relative overflow-hidden rounded-xl border bg-gradient-to-br ${card.colorClass} p-4 shadow-sm backdrop-blur-md transition-all duration-300 hover:scale-[1.02]`}
        >
          <div className="flex justify-between items-start mb-2">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">{card.title}</span>
            <span className="p-1.5 rounded-lg bg-slate-900/60 border border-slate-800">
              {card.icon}
            </span>
          </div>
          <div className="text-xl font-black text-white">{card.value}</div>
        </div>
      ))}
    </div>
  );
};
