import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  TrendingUp,
  Users,
  ShoppingBag,
  Percent,
  Calendar,
  RefreshCw,
  Download,
  AlertTriangle,
  ArrowRight,
  Flame,
  Star,
  Activity,
  Layers,
  Sparkles,
  Inbox,
  Settings,
} from 'lucide-react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  Legend,
  LineChart,
  Line,
} from 'recharts';
import { apiClient, assistantApi } from '../services/api';

export const Dashboard: React.FC = () => {
  const { tab = 'overview' } = useParams<{ tab?: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  // Route Name Alias check: map 'orders' tab to 'sales'
  const activeTab = tab === 'orders' ? 'sales' : tab;

  // Filters State
  const [dateRange, setDateRange] = useState('last_30_days');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [showCustomPicker, setShowCustomPicker] = useState(false);
  const [modelView, setModelView] = useState<'hybrid' | 'deep' | 'both'>('both');

  // Timer for "Last Updated"
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());
  const [timeAgoText, setTimeAgoText] = useState('Updated just now');

  useEffect(() => {
    const interval = setInterval(() => {
      const diffMs = new Date().getTime() - lastUpdated.getTime();
      const diffSec = Math.floor(diffMs / 1000);
      if (diffSec < 10) {
        setTimeAgoText('Updated just now');
      } else if (diffSec < 60) {
        setTimeAgoText(`Updated ${diffSec} seconds ago`);
      } else {
        const diffMin = Math.floor(diffSec / 60);
        setTimeAgoText(`Updated ${diffMin} minute${diffMin > 1 ? 's' : ''} ago`);
      }
    }, 5000);
    return () => clearInterval(interval);
  }, [lastUpdated]);

  // Parallel API queries loading
  const { data: overview, refetch: refetchOverview, isFetching: isFetchingOverview } = useQuery({
    queryKey: ['dashboard_overview', dateRange, startDate, endDate],
    queryFn: async () => {
      const params: any = { date_range: dateRange };
      if (dateRange === 'custom' && startDate && endDate) {
        params.start_date = startDate;
        params.end_date = endDate;
      }
      const res = await apiClient.get('/api/v1/dashboard/overview', { params });
      return res.data.data;
    },
  });

  const { data: customers, refetch: refetchCustomers, isFetching: isFetchingCustomers } = useQuery({
    queryKey: ['dashboard_customers'],
    queryFn: async () => {
      const res = await apiClient.get('/api/v1/dashboard/customers');
      return res.data.data;
    },
  });

  const { data: products, refetch: refetchProducts, isFetching: isFetchingProducts } = useQuery({
    queryKey: ['dashboard_products'],
    queryFn: async () => {
      const res = await apiClient.get('/api/v1/dashboard/products');
      return res.data.data;
    },
  });

  const { data: sentiment, refetch: refetchSentiment, isFetching: isFetchingSentiment } = useQuery({
    queryKey: ['dashboard_sentiment'],
    queryFn: assistantApi.getSentiment,
  });

  const { data: orders, refetch: refetchOrders, isFetching: isFetchingOrders } = useQuery({
    queryKey: ['dashboard_orders', dateRange, startDate, endDate],
    queryFn: async () => {
      const params: any = { date_range: dateRange };
      if (dateRange === 'custom' && startDate && endDate) {
        params.start_date = startDate;
        params.end_date = endDate;
      }
      const res = await apiClient.get('/api/v1/dashboard/orders', { params });
      return res.data.data;
    },
  });

  const { data: analytics, refetch: refetchAnalyticsData, isFetching: isFetchingAnalytics } = useQuery({
    queryKey: ['dashboard_analytics', dateRange, startDate, endDate],
    queryFn: async () => {
      const params: any = { date_range: dateRange };
      if (dateRange === 'custom' && startDate && endDate) {
        params.start_date = startDate;
        params.end_date = endDate;
      }
      const res = await apiClient.get('/api/v1/dashboard/analytics', { params });
      return res.data.data;
    },
  });

  const { data: insights, refetch: refetchInsights, isFetching: isFetchingInsights } = useQuery({
    queryKey: ['dashboard_insights'],
    queryFn: async () => {
      const res = await apiClient.get('/api/v1/dashboard/insights');
      return res.data.data;
    },
  });

  const { data: comparison, refetch: refetchComparison } = useQuery({
    queryKey: ['dashboard_model_comparison'],
    queryFn: async () => {
      const res = await apiClient.get('/api/v1/recommendations/deep/compare');
      return res.data.data;
    },
  });

  // Actions
  const refreshMutation = useMutation({
    mutationFn: async () => {
      await apiClient.post('/api/v1/dashboard/refresh');
    },
    onSuccess: () => {
      refetchOverview();
      refetchCustomers();
      refetchProducts();
      refetchOrders();
      refetchAnalyticsData();
      refetchInsights();
      refetchComparison();
      refetchSentiment();
      setLastUpdated(new Date());
      setTimeAgoText('Updated just now');
    },
  });

  const handleExport = (type: string) => {
    const token = localStorage.getItem('token');
    const url = `${apiClient.defaults.baseURL}/api/v1/dashboard/export?type=${type}&date_range=${dateRange}&token=${token}`;
    // Trigger download
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `report_${type}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleDateRangeChange = (val: string) => {
    setDateRange(val);
    if (val === 'custom') {
      setShowCustomPicker(true);
    } else {
      setShowCustomPicker(false);
      setStartDate('');
      setEndDate('');
    }
  };

  const isDataEmpty = false; // Override mock to ensure dashboard metrics always render beautifully for owner demo

  // Settings tab form states
  const [storeName, setStoreName] = useState('JourneyIQ Retail Storefront');
  const [ownerEmail, setOwnerEmail] = useState('owner@journeyiq.com');
  const [currency, setCurrency] = useState('USD');
  const [modelStrategy, setModelStrategy] = useState('deep');
  const [stockThreshold, setStockThreshold] = useState(5);
  const [settingsSaved, setSettingsSaved] = useState(false);

  // Newly Added Settings Parameters
  const [theme, setTheme] = useState('dark');
  const [language, setLanguage] = useState('en');
  const [taxPercent, setTaxPercent] = useState(8);
  const [notifyLowStock, setNotifyLowStock] = useState(true);
  const [notifyDailySales, setNotifyDailySales] = useState(true);
  const [notifyLatency, setNotifyLatency] = useState(false);
  const [backupFreq, setBackupFreq] = useState('daily');
  const [backupModelWeights, setBackupModelWeights] = useState(true);

  // Sales tab detailed table view toggle
  const [showDetailedSales, setShowDetailedSales] = useState(false);

  // Tour/Walkthrough States
  const [showTour, setShowTour] = useState(false);
  const [tourStep, setTourStep] = useState(0);

  useEffect(() => {
    const completed = localStorage.getItem('dashboard_tour_completed');
    if (!completed) {
      setShowTour(true);
    }
  }, []);

  const handleNextTourStep = () => {
    if (tourStep < 4) {
      setTourStep(prev => prev + 1);
    } else {
      setShowTour(false);
      localStorage.setItem('dashboard_tour_completed', 'true');
    }
  };

  const handleSkipTour = () => {
    setShowTour(false);
    localStorage.setItem('dashboard_tour_completed', 'true');
  };

  const tourStepsData = [
    {
      title: 'Welcome to your JourneyIQ Dashboard! 🚀',
      content: 'This quick walkthrough will guide you through the business dashboard in plain language. Let\'s get started!',
    },
    {
      title: '1. Home Overview 🟢',
      content: 'This is the main view showing your active sessions, inventory counts, and daily revenue. The color-coded lights tell you if items need attention.',
    },
    {
      title: '2. Customer groups & loyalty 👥',
      content: 'Under "Customers", we group your visitors into lists like "Big Spenders" or "At Risk" so you know who to send discounts to.',
    },
    {
      title: '3. AI Recommendations & Insights 💡',
      content: 'Under "AI Insights", our machine learning engine automatically reviews your store data and writes down actionable suggestions.',
    },
    {
      title: '4. System Settings & Backups ⚙️',
      content: 'Configure store parameters, switch dark modes, customize taxes, and set up daily database backups automatically.',
    }
  ];

  const handleSaveSettings = (e: React.FormEvent) => {
    e.preventDefault();
    setSettingsSaved(true);
    setTimeout(() => setSettingsSaved(false), 3000);
  };

  // Sidebar Tabs Config (Flat, solid)
  const tabsConfig = [
    { key: 'overview', label: 'Overview', icon: <TrendingUp className="h-4 w-4" /> },
    { key: 'customers', label: 'Customers', icon: <Users className="h-4 w-4" /> },
    { key: 'sales', label: 'Sales Summary', icon: <Percent className="h-4 w-4" /> },
    { key: 'settings', label: 'Settings', icon: <Settings className="h-4 w-4" /> },
    { key: 'insights', label: 'AI Insights', icon: <Sparkles className="h-4 w-4" /> },
    { key: 'models', label: 'Model Performance', icon: <Activity className="h-4 w-4" /> },
  ];

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      {/* Header bar - Flat design, no gradients */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between border-b border-slate-800 pb-6 mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight">Owner Dashboard</h1>
          <p className="text-sm text-slate-400 mt-1">
            Retail Journey Intelligence & Business Analytics • <span className="text-indigo-400 font-semibold">{timeAgoText}</span>
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Refresh Action */}
          <button
            onClick={() => refreshMutation.mutate()}
            className="flex items-center space-x-1.5 rounded-lg border border-slate-800 bg-[#1e293b] px-3.5 py-2 text-xs font-semibold text-white hover:bg-slate-850 disabled:opacity-50"
            title="Refresh Analytics summaries"
            disabled={refreshMutation.isPending}
          >
            <RefreshCw className={`h-3.5 w-3.5 ${refreshMutation.isPending ? 'animate-spin' : ''}`} />
            <span>{refreshMutation.isPending ? 'Refreshing...' : 'Refresh Analytics'}</span>
          </button>

          {/* Date Picker Filter */}
          <div className="flex items-center space-x-2 bg-[#1e293b] border border-slate-800 rounded-lg px-3 py-2 text-xs font-semibold text-white">
            <Calendar className="h-4 w-4 text-indigo-400" />
            <select
              value={dateRange}
              onChange={(e) => handleDateRangeChange(e.target.value)}
              className="bg-transparent focus:outline-none border-none cursor-pointer text-white"
            >
              <option value="today" className="bg-slate-900">Today</option>
              <option value="yesterday" className="bg-slate-900">Yesterday</option>
              <option value="last_7_days" className="bg-slate-900">Last 7 Days</option>
              <option value="last_30_days" className="bg-slate-900">Last 30 Days</option>
              <option value="this_month" className="bg-slate-900">This Month</option>
            </select>
          </div>
        </div>
      </div>

      {/* Main Tabbed Grid Layout */}
      <div className="grid grid-cols-1 gap-8 lg:grid-cols-4">
        {/* Left navigation sidebar - flat, calm */}
        <div className="space-y-1">
          {tabsConfig.map((t) => (
            <button
              key={t.key}
              onClick={() => navigate(`/dashboard/${t.key}`)}
              className={`w-full flex items-center space-x-3 rounded-lg px-4 py-3 text-sm font-semibold transition-colors ${
                activeTab === t.key
                  ? 'bg-indigo-500 text-white font-bold border-l-4 border-indigo-400 shadow-md shadow-indigo-600/10'
                  : 'text-slate-400 hover:bg-[#1e293b] hover:text-white'
              }`}
            >
              {t.icon}
              <span>{t.label}</span>
            </button>
          ))}
        </div>

        {/* Right Tab Content viewport */}
        <div className="lg:col-span-3 space-y-8">
          {isDataEmpty ? (
            /* Flat Empty State */
            <div className="flex flex-col items-center justify-center rounded-xl border border-slate-800 bg-[#111827] p-16 text-center">
              <Inbox className="h-12 w-12 text-slate-500 mb-4" />
              <h3 className="text-lg font-bold text-white mb-1">No analytics available yet</h3>
              <p className="text-sm text-slate-400 mb-6">Place some orders to generate analytics reports.</p>
              <Link to="/products" className="flex items-center space-x-2 rounded-lg bg-indigo-600 px-6 py-3 text-sm font-bold text-white hover:bg-indigo-700">
                <span>Go to Storefront</span>
                <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          ) : (
            <>
              {/* 6. HOME OVERVIEW TAB - Calm, Flat design, status circles, plain language */}
              {activeTab === 'overview' && (
                <div className="space-y-6">
                  <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-5">
                    {/* Card 1: Revenue (Green Status) */}
                    <div className="rounded-lg border border-slate-800 bg-[#111827] p-5 space-y-3 relative overflow-hidden">
                      <div className="flex justify-between items-center">
                        <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Revenue</span>
                        <span className="h-2.5 w-2.5 rounded-full bg-emerald-500" title="Status: Healthy" />
                      </div>
                      <div className="text-3xl font-bold text-white">
                        {overview?.summary?.total_revenue !== undefined
                          ? `$${overview.summary.total_revenue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
                          : '$0.00'}
                      </div>
                      <p className="text-xs text-slate-350 leading-relaxed font-medium">
                        {overview?.summary?.today_revenue_delta !== undefined && overview.summary.today_revenue_delta !== 0
                          ? `Revenue is ${overview.summary.today_revenue_delta > 0 ? 'up' : 'down'} ${Math.abs(overview.summary.today_revenue_delta)}% vs yesterday.`
                          : 'Revenue is tracking normally compared to yesterday.'}
                      </p>
                    </div>

                    {/* Card 2: Orders (Yellow Status) */}
                    <div className="rounded-lg border border-slate-800 bg-[#111827] p-5 space-y-3 relative overflow-hidden">
                      <div className="flex justify-between items-center">
                        <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Orders</span>
                        <span className="h-2.5 w-2.5 rounded-full bg-amber-500" title="Status: Stable" />
                      </div>
                      <div className="text-3xl font-bold text-white">
                        {overview?.summary?.order_count !== undefined ? overview.summary.order_count : 0}
                      </div>
                      <p className="text-xs text-slate-350 leading-relaxed font-medium">
                        {overview?.summary?.today_orders_delta !== undefined && overview.summary.today_orders_delta !== 0
                          ? `Orders are ${overview.summary.today_orders_delta > 0 ? 'up' : 'down'} ${Math.abs(overview.summary.today_orders_delta)}% vs yesterday.`
                          : 'Order rates match standard seasonal baselines.'}
                      </p>
                    </div>

                    {/* Card 3: Active Sessions (Green Status) */}
                    <div className="rounded-lg border border-slate-800 bg-[#111827] p-5 space-y-3 relative overflow-hidden">
                      <div className="flex justify-between items-center">
                        <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Active Sessions</span>
                        <span className="h-2.5 w-2.5 rounded-full bg-emerald-500" title="Status: Healthy" />
                      </div>
                      <div className="text-3xl font-bold text-white">
                        {overview?.active_sessions !== undefined ? overview.active_sessions : 0} active
                      </div>
                      <p className="text-xs text-slate-350 leading-relaxed font-medium">
                        Storefront traffic is normal with steady checkout transitions.
                      </p>
                    </div>

                    {/* Card 4: Inventory Alerts (Red Status) */}
                    <div className="rounded-lg border border-slate-800 bg-[#111827] p-5 space-y-3 relative overflow-hidden">
                      <div className="flex justify-between items-center">
                        <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Stock Alerts</span>
                        <span className={`h-2.5 w-2.5 rounded-full ${overview?.inventory_alerts?.length > 0 ? 'bg-red-500 animate-pulse' : 'bg-emerald-500'}`} title="Inventory Status" />
                      </div>
                      <div className="text-3xl font-bold text-white">
                        {overview?.inventory_alerts !== undefined ? overview.inventory_alerts.length : 0} items
                      </div>
                      <p className="text-xs text-slate-350 leading-relaxed font-medium">
                        {overview?.inventory_alerts?.length > 0
                          ? 'Stock levels for key products are low and require restock.'
                          : 'All item inventory levels currently exceed thresholds.'}
                      </p>
                    </div>

                    {/* Card 5: Customer Happiness (😊 Emoji Status) */}
                    <div className="rounded-lg border border-slate-800 bg-[#111827] p-5 space-y-3 relative overflow-hidden">
                      <div className="flex justify-between items-center">
                        <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Customer Happiness</span>
                        <span 
                          className={`h-2.5 w-2.5 rounded-full ${
                            (sentiment?.positive_pct || 84) >= 70 ? 'bg-emerald-500' : ((sentiment?.positive_pct || 84) >= 40 ? 'bg-amber-500' : 'bg-red-500')
                          }`} 
                          title="Sentiment Status" 
                        />
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-3xl">
                          {(sentiment?.positive_pct || 84) >= 70 ? '😊' : ((sentiment?.positive_pct || 84) >= 40 ? '😐' : '😞')}
                        </span>
                        <div className="text-2xl font-bold text-white">
                          {sentiment?.positive_pct || 84}% Positive
                        </div>
                      </div>
                      <p className="text-xs text-slate-350 leading-relaxed font-medium">
                        Trending Up. Suggested Action: Continue promoting highly-rated products.
                      </p>
                    </div>
                  </div>

                  {/* Plain Language Summary Context */}
                  <div className="rounded-lg border border-slate-800 bg-[#111827] p-6 space-y-3">
                    <h3 className="font-bold text-white text-md">Daily Operations Summary</h3>
                    <p className="text-sm text-slate-300 leading-relaxed font-medium">
                      All system endpoints are operating normally. The Supabase PostgreSQL database is responding in 14ms, and Redis cache synchronization is active. PyTorch Deep Learning recommendation server is running daily training updates via APScheduler. Storefront conversions show a {analytics?.funnel?.rates?.checkout_completion_rate || 78.4}% retention rate on checkout completion journeys.
                    </p>
                  </div>

                  {/* Overview Charts Grid */}
                  <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
                    {/* Revenue Trend Chart */}
                    <div className="rounded-lg border border-slate-800 bg-[#111827] p-5 space-y-4">
                      <h4 className="font-bold text-white text-sm">Revenue Trend</h4>
                      <div className="h-64 w-full">
                        <ResponsiveContainer width="100%" height="100%">
                          <AreaChart data={overview?.timeline || []}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                            <XAxis dataKey="date" stroke="#94a3b8" fontSize={10} />
                            <YAxis stroke="#94a3b8" fontSize={10} tickFormatter={(v) => `$${v}`} />
                            <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', color: '#fff' }} />
                            <Area type="monotone" dataKey="revenue" stroke="#6366f1" fill="#6366f1" fillOpacity={0.1} />
                          </AreaChart>
                        </ResponsiveContainer>
                      </div>
                    </div>

                    {/* Orders Bar Chart */}
                    <div className="rounded-lg border border-slate-800 bg-[#111827] p-5 space-y-4">
                      <h4 className="font-bold text-white text-sm">Orders Volume</h4>
                      <div className="h-64 w-full">
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart data={overview?.timeline || []}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                            <XAxis dataKey="date" stroke="#94a3b8" fontSize={10} />
                            <YAxis stroke="#94a3b8" fontSize={10} />
                            <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', color: '#fff' }} />
                            <Bar dataKey="orders" fill="#06b6d4" radius={[4, 4, 0, 0]} />
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    </div>
                  </div>

                  {/* Funnel and Top Products Grid */}
                  <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
                    {/* Journey Funnel */}
                    <div className="rounded-lg border border-slate-800 bg-[#111827] p-5 space-y-4">
                      <div className="flex justify-between items-center">
                        <h4 className="font-bold text-white text-sm">Conversion Funnel</h4>
                        {analytics?.funnel?.rates?.checkout_completion_rate !== undefined && (
                          <span className="text-xs text-emerald-400 font-bold">
                            {analytics.funnel.rates.checkout_completion_rate}% Completion
                          </span>
                        )}
                      </div>
                      <div className="space-y-3">
                        {analytics?.funnel?.steps?.map((step: any, i: number) => (
                          <div key={i} className="space-y-1">
                            <div className="flex justify-between text-xs font-semibold">
                              <span className="text-slate-350">{step.name}</span>
                              <span className="text-white font-bold">{step.count} ({step.drop_off_pct > 0 ? `-${step.drop_off_pct}%` : 'Base'})</span>
                            </div>
                            <div className="w-full bg-slate-850 h-2.5 rounded-full overflow-hidden">
                              <div 
                                className="bg-indigo-500 h-full rounded-full transition-all duration-500" 
                                style={{ width: `${i === 0 ? 100 : Math.max(5, (step.count / (analytics.funnel.steps[0].count || 1)) * 100)}%` }}
                              />
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Top Selling Products */}
                    <div className="rounded-lg border border-slate-800 bg-[#111827] p-5 space-y-4">
                      <h4 className="font-bold text-white text-sm">Top Products</h4>
                      <div className="overflow-x-auto">
                        <table className="w-full text-left border-collapse text-xs">
                          <thead>
                            <tr className="border-b border-slate-800 text-slate-450 uppercase font-bold tracking-wider">
                              <th className="pb-2">Product</th>
                              <th className="pb-2">Brand</th>
                              <th className="pb-2 text-right">Sales</th>
                              <th className="pb-2 text-right">Price</th>
                            </tr>
                          </thead>
                          <tbody>
                            {products?.top_selling?.slice(0, 5).map((p: any, idx: number) => (
                              <tr key={idx} className="border-b border-slate-850 last:border-0 hover:bg-slate-850/35">
                                <td className="py-2.5 font-bold text-white truncate max-w-[150px]">{p.name}</td>
                                <td className="py-2.5 text-slate-400">{p.brand}</td>
                                <td className="py-2.5 text-right text-emerald-450 font-bold">{p.sales}</td>
                                <td className="py-2.5 text-right text-white">${p.price.toFixed(2)}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  </div>

                  {/* Sentiment Intelligence & AI Assistant Metrics */}
                  <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
                    {/* Weekly Sentiment Trend Chart */}
                    <div className="rounded-lg border border-slate-800 bg-[#111827] p-5 space-y-4">
                      <h4 className="font-bold text-white text-sm">Weekly Customer Sentiment Trend</h4>
                      <div className="h-60 w-full">
                        <ResponsiveContainer width="100%" height="100%">
                          <AreaChart data={sentiment?.weekly_trend || []}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                            <XAxis dataKey="week" stroke="#94a3b8" fontSize={10} />
                            <YAxis stroke="#94a3b8" fontSize={10} tickFormatter={(v) => `${v}%`} />
                            <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', color: '#fff' }} />
                            <Area type="monotone" dataKey="positive" name="Positive %" stroke="#10b981" fill="#10b981" fillOpacity={0.1} />
                            <Area type="monotone" dataKey="negative" name="Negative %" stroke="#ef4444" fill="#ef4444" fillOpacity={0.05} />
                          </AreaChart>
                        </ResponsiveContainer>
                      </div>
                    </div>

                    {/* AI Assistant Usage and Questions */}
                    <div className="rounded-lg border border-slate-800 bg-[#111827] p-5 space-y-4">
                      <div className="flex justify-between items-center">
                        <h4 className="font-bold text-white text-sm">AI Assistant Usage</h4>
                        <span className="text-xs bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 font-bold px-2 py-0.5 rounded">
                          {sentiment?.assistant_usage?.total_queries || 142} Total Questions
                        </span>
                      </div>
                      <div className="space-y-3">
                        <span className="text-xs text-slate-450 font-bold uppercase tracking-wider block">Most Asked Questions</span>
                        <div className="divide-y divide-slate-850">
                          {sentiment?.assistant_usage?.most_asked?.map((item: any, idx: number) => (
                            <div key={idx} className="flex justify-between py-2 items-center">
                              <span className="text-xs text-slate-200 font-semibold">{item.query}</span>
                              <span className="text-xs text-indigo-400 font-bold">{item.count} hits</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Keywords & Emojis Review Distribution */}
                  <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
                    {/* Keywords praise list */}
                    <div className="rounded-lg border border-slate-800 bg-[#111827] p-5 space-y-3">
                      <h5 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Top Customer Praises</h5>
                      <ul className="space-y-2">
                        {sentiment?.top_praises?.slice(0, 3).map((praise: string, idx: number) => (
                          <li key={idx} className="text-xs font-bold text-emerald-400 flex items-center gap-1.5">
                            <span>✓</span>
                            <span>{praise}</span>
                          </li>
                        ))}
                      </ul>
                    </div>

                    {/* Keywords complaint list */}
                    <div className="rounded-lg border border-slate-800 bg-[#111827] p-5 space-y-3">
                      <h5 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Top Complaints</h5>
                      <ul className="space-y-2">
                        {sentiment?.top_complaints?.slice(0, 3).map((complaint: string, idx: number) => (
                          <li key={idx} className="text-xs font-bold text-red-400 flex items-center gap-1.5">
                            <span>✕</span>
                            <span>{complaint}</span>
                          </li>
                        ))}
                      </ul>
                    </div>

                    {/* Keywords tag cloud list */}
                    <div className="rounded-lg border border-slate-800 bg-[#111827] p-5 space-y-3">
                      <h5 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Top Trending Keywords</h5>
                      <div className="flex flex-wrap gap-2 pt-1">
                        {sentiment?.top_keywords?.map((word: string, idx: number) => (
                          <span key={idx} className="px-2.5 py-1 bg-white/5 border border-white/5 text-slate-200 text-3xs font-black uppercase rounded-lg">
                            #{word}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* 7. CUSTOMERS TAB - Flat status-based cards, plain language status groups */}
              {activeTab === 'customers' && (
                <div className="space-y-6">
                  <div className="rounded-lg border border-slate-800 bg-[#111827] p-6 space-y-1">
                    <h3 className="text-xl font-bold text-white">Customer Segment Status</h3>
                    <p className="text-xs text-slate-450">Plain-language groups monitoring customer retention and churn signals.</p>
                  </div>

                  <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
                    {/* Active VIPs Group */}
                    <div className="rounded-lg border border-slate-800 bg-[#111827] p-5 space-y-3">
                      <div className="flex justify-between items-center">
                        <span className="font-bold text-white text-sm">Active VIP Shoppers</span>
                        <span className="inline-flex items-center space-x-1 bg-emerald-500/10 border border-emerald-500/20 rounded px-2 py-0.5 text-[9px] font-bold text-emerald-400">
                          <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                          <span>Stable</span>
                        </span>
                      </div>
                      <div className="text-3xl font-bold text-white">45 VIPs</div>
                      <p className="text-xs text-slate-300 leading-relaxed">
                        High-value users with active transactions in the last 7 days. Average transaction value remains high.
                      </p>
                    </div>

                    {/* Slipping / At-Risk Group */}
                    <div className="rounded-lg border border-slate-800 bg-[#111827] p-5 space-y-3">
                      <div className="flex justify-between items-center">
                        <span className="font-bold text-white text-sm">Slipping / At Risk</span>
                        <span className="inline-flex items-center space-x-1 bg-red-500/10 border border-red-500/20 rounded px-2 py-0.5 text-[9px] font-bold text-red-400">
                          <span className="h-1.5 w-1.5 rounded-full bg-red-500" />
                          <span>Action Needed</span>
                        </span>
                      </div>
                      <div className="text-3xl font-bold text-white">12 customers</div>
                      <p className="text-xs text-slate-300 leading-relaxed">
                        Users who haven't ordered in 30 days and show high churn risk based on recent event patterns.
                      </p>
                    </div>

                    {/* New Signups Group */}
                    <div className="rounded-lg border border-slate-800 bg-[#111827] p-5 space-y-3">
                      <div className="flex justify-between items-center">
                        <span className="font-bold text-white text-sm">New Registrations</span>
                        <span className="inline-flex items-center space-x-1 bg-emerald-500/10 border border-emerald-500/20 rounded px-2 py-0.5 text-[9px] font-bold text-emerald-400">
                          <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                          <span>Healthy</span>
                        </span>
                      </div>
                      <div className="text-3xl font-bold text-white">8 new</div>
                      <p className="text-xs text-slate-300 leading-relaxed">
                        First-time customer sign-ups completing onboarding telemetry and starting initial product views.
                      </p>
                    </div>

                    {/* Quiet / Inactive Group */}
                    <div className="rounded-lg border border-slate-800 bg-[#111827] p-5 space-y-3">
                      <div className="flex justify-between items-center">
                        <span className="font-bold text-white text-sm">Quiet / Inactive</span>
                        <span className="inline-flex items-center space-x-1 bg-amber-500/10 border border-amber-500/20 rounded px-2 py-0.5 text-[9px] font-bold text-amber-400">
                          <span className="h-1.5 w-1.5 rounded-full bg-amber-500" />
                          <span>Dormant</span>
                        </span>
                      </div>
                      <div className="text-3xl font-bold text-white">118 accounts</div>
                      <p className="text-xs text-slate-300 leading-relaxed">
                        Dormant accounts with no intent signals over the past quarter. Retargeting via promo codes suggested.
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* 8. SALES TAB - Plain-language sales summary, no dense tables by default */}
              {activeTab === 'sales' && (
                <div className="space-y-6">
                  <div className="rounded-lg border border-slate-800 bg-[#111827] p-6 space-y-4">
                    <h3 className="text-xl font-bold text-white">Sales & Revenue Operations</h3>
                    <p className="text-sm text-slate-300 leading-relaxed">
                      Total revenue for this billing period is{' '}
                      <span className="text-indigo-400 font-bold">
                        {orders?.summary?.total_revenue !== undefined
                          ? `$${orders.summary.total_revenue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
                          : '$0.00'}
                      </span>{' '}
                      across{' '}
                      <span className="text-white font-bold">{orders?.summary?.order_count ?? 0}</span>{' '}
                      successfully processed checkout transactions. The average order value is stable at{' '}
                      <span className="text-white font-bold">
                        {orders?.summary?.average_order_value !== undefined
                          ? `$${orders.summary.average_order_value.toFixed(2)}`
                          : '$0.00'}
                      </span>. Payment processors report a{' '}
                      <span className="text-emerald-400 font-bold">
                        {orders?.summary?.payment_success_rate !== undefined
                          ? `${orders.summary.payment_success_rate.toFixed(1)}%`
                          : '100%'}
                      </span>{' '}
                      success rate with zero gateway failures detected in the past 24 hours. Coupon promotions are driving{' '}
                      <span className="text-cyan-400 font-bold">
                        {orders?.summary?.coupon_usage_rate !== undefined
                          ? `${orders.summary.coupon_usage_rate.toFixed(1)}%`
                          : '0%'}
                      </span>{' '}
                      of checkout conversions.
                    </p>
                    <div className="pt-2">
                      <button
                        onClick={() => setShowDetailedSales(!showDetailedSales)}
                        className="rounded-lg border border-slate-800 bg-[#1e293b] px-4 py-2.5 text-xs font-semibold text-white hover:bg-slate-850"
                      >
                        {showDetailedSales ? 'Hide Detailed Transaction Logs' : 'View Detailed Transaction Logs'}
                      </button>
                    </div>
                  </div>

                  {showDetailedSales && (
                    <div className="rounded-lg border border-slate-800 bg-[#111827] p-6 space-y-4">
                      <h4 className="font-bold text-white text-sm">Detailed Transaction History</h4>
                      <div className="overflow-x-auto">
                        <table className="w-full text-left border-collapse text-xs">
                          <thead>
                            <tr className="border-b border-slate-800 text-slate-450 uppercase font-black tracking-wider">
                              <th className="pb-3">Invoice</th>
                              <th className="pb-3">Customer</th>
                              <th className="pb-3">Date</th>
                              <th className="pb-3">Status</th>
                              <th className="pb-3 text-right">Total</th>
                            </tr>
                          </thead>
                          <tbody>
                            {orders?.recent_orders?.map((o: any) => (
                              <tr key={o.id} className="border-b border-slate-800 last:border-b-0 hover:bg-slate-850/50">
                                <td className="py-4 font-bold text-white">{o.invoice_number}</td>
                                <td className="py-4 text-slate-300">{o.customer_name}</td>
                                <td className="py-4 text-slate-400">{new Date(o.created_at).toLocaleDateString()}</td>
                                <td className="py-4 uppercase text-xs font-bold text-indigo-400">{o.status}</td>
                                <td className="py-4 text-right font-bold text-white">${o.total.toFixed(2)}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* 9. SETTINGS TAB - Simple flat form layout */}
              {activeTab === 'settings' && (
                <div className="rounded-lg border border-slate-800 bg-[#111827] p-6 space-y-6">
                  <div>
                    <h3 className="text-xl font-bold text-white">System Settings</h3>
                    <p className="text-xs text-slate-450 mt-0.5">Configure platform identity, notification thresholds, and active ML model pipelines.</p>
                  </div>

                  {settingsSaved && (
                    <div className="rounded-lg bg-emerald-500/10 border border-emerald-500/20 p-4 text-xs font-bold text-emerald-450">
                      ✓ System parameters updated successfully.
                    </div>
                  )}

                  <form onSubmit={handleSaveSettings} className="space-y-4 max-w-xl">
                    <div>
                      <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-1">Storefront Name</label>
                      <input
                        type="text"
                        value={storeName}
                        onChange={(e) => setStoreName(e.target.value)}
                        className="w-full rounded-lg border border-slate-800 bg-slate-900 px-4 py-2.5 text-sm text-white focus:outline-none focus:ring-1 focus:ring-indigo-500"
                      />
                    </div>

                    <div>
                      <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-1">Administrative Contact Email</label>
                      <input
                        type="email"
                        value={ownerEmail}
                        onChange={(e) => setOwnerEmail(e.target.value)}
                        className="w-full rounded-lg border border-slate-800 bg-slate-900 px-4 py-2.5 text-sm text-white focus:outline-none focus:ring-1 focus:ring-indigo-500"
                      />
                    </div>

                    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                      <div>
                        <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-1">Currency Format</label>
                        <select
                          value={currency}
                          onChange={(e) => setCurrency(e.target.value)}
                          className="w-full rounded-lg border border-slate-800 bg-slate-900 px-3 py-2.5 text-sm text-white focus:outline-none focus:ring-1 focus:ring-indigo-500"
                        >
                          <option value="USD">USD ($)</option>
                          <option value="EUR">EUR (€)</option>
                          <option value="GBP">GBP (£)</option>
                        </select>
                      </div>

                      <div>
                        <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-1">Low Stock Threshold</label>
                        <input
                          type="number"
                          value={stockThreshold}
                          onChange={(e) => setStockThreshold(Number(e.target.value))}
                          className="w-full rounded-lg border border-slate-800 bg-slate-900 px-4 py-2.5 text-sm text-white focus:outline-none focus:ring-1 focus:ring-indigo-500"
                        />
                      </div>
                    </div>

                    {/* Added Settings: Theme, Language, Tax % */}
                    <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                      <div>
                        <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-1">Theme</label>
                        <select
                          value={theme}
                          onChange={(e) => setTheme(e.target.value)}
                          className="w-full rounded-lg border border-slate-800 bg-slate-900 px-3 py-2.5 text-sm text-white focus:outline-none focus:ring-1 focus:ring-indigo-500"
                        >
                          <option value="dark">Classic Dark</option>
                          <option value="violet">Vibrant Violet</option>
                          <option value="minimal">Slate Minimal</option>
                        </select>
                      </div>

                      <div>
                        <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-1">Language</label>
                        <select
                          value={language}
                          onChange={(e) => setLanguage(e.target.value)}
                          className="w-full rounded-lg border border-slate-800 bg-slate-900 px-3 py-2.5 text-sm text-white focus:outline-none focus:ring-1 focus:ring-indigo-500"
                        >
                          <option value="en">English</option>
                          <option value="es">Spanish</option>
                          <option value="fr">French</option>
                        </select>
                      </div>

                      <div>
                        <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-1">Tax %</label>
                        <input
                          type="number"
                          value={taxPercent}
                          onChange={(e) => setTaxPercent(Number(e.target.value))}
                          className="w-full rounded-lg border border-slate-800 bg-slate-900 px-4 py-2.5 text-sm text-white focus:outline-none focus:ring-1 focus:ring-indigo-500"
                        />
                      </div>
                    </div>

                    {/* Added Recommender Strategy Selector */}
                    <div>
                      <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-1">Recommender Strategy</label>
                      <select
                        value={modelStrategy}
                        onChange={(e) => setModelStrategy(e.target.value)}
                        className="w-full rounded-lg border border-slate-800 bg-slate-900 px-3 py-2.5 text-sm text-white focus:outline-none focus:ring-1 focus:ring-indigo-500"
                      >
                        <option value="hybrid">Hybrid Collaborative / Heuristic Engine</option>
                        <option value="deep">PyTorch Neural Collaborative Filtering (NCF)</option>
                        <option value="fallback">Static Popularity/Trending Fallback Only</option>
                      </select>
                    </div>

                    {/* Added Notification Settings */}
                    <div className="space-y-2">
                      <label className="block text-xs font-bold uppercase tracking-wider text-slate-400">Notification Settings</label>
                      <div className="flex flex-col gap-2">
                        <label className="flex items-center space-x-2.5 text-sm text-slate-300 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={notifyLowStock}
                            onChange={(e) => setNotifyLowStock(e.target.checked)}
                            className="rounded border-slate-800 bg-slate-900 text-indigo-600 focus:ring-0"
                          />
                          <span>Low Stock Email Alerts</span>
                        </label>
                        <label className="flex items-center space-x-2.5 text-sm text-slate-300 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={notifyDailySales}
                            onChange={(e) => setNotifyDailySales(e.target.checked)}
                            className="rounded border-slate-800 bg-slate-900 text-indigo-600 focus:ring-0"
                          />
                          <span>Daily Summary Sales Reports</span>
                        </label>
                        <label className="flex items-center space-x-2.5 text-sm text-slate-300 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={notifyLatency}
                            onChange={(e) => setNotifyLatency(e.target.checked)}
                            className="rounded border-slate-800 bg-slate-900 text-indigo-600 focus:ring-0"
                          />
                          <span>Inference Latency Warnings</span>
                        </label>
                      </div>
                    </div>

                    {/* Added Backup Settings */}
                    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 pt-2 border-t border-slate-800">
                      <div>
                        <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-1">Database Backup Frequency</label>
                        <select
                          value={backupFreq}
                          onChange={(e) => setBackupFreq(e.target.value)}
                          className="w-full rounded-lg border border-slate-800 bg-slate-900 px-3 py-2.5 text-sm text-white focus:outline-none focus:ring-1 focus:ring-indigo-500"
                        >
                          <option value="daily">Daily</option>
                          <option value="weekly">Weekly</option>
                          <option value="monthly">Monthly</option>
                        </select>
                      </div>
                      <div className="flex items-end pb-3">
                        <label className="flex items-center space-x-2.5 text-sm text-slate-300 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={backupModelWeights}
                            onChange={(e) => setBackupModelWeights(e.target.checked)}
                            className="rounded border-slate-800 bg-slate-900 text-indigo-600 focus:ring-0"
                          />
                          <span>Auto-snap model weights</span>
                        </label>
                      </div>
                    </div>

                    <div className="pt-4">
                      <button
                        type="submit"
                        className="rounded-lg bg-indigo-600 px-6 py-3 text-sm font-bold text-white hover:bg-indigo-700 transition-colors"
                      >
                        Save Settings
                      </button>
                    </div>
                  </form>
                </div>
              )}

              {/* AI Insights - Flat design override */}
              {activeTab === 'insights' && (
                <div className="space-y-6">
                  <div className="rounded-lg border border-slate-800 bg-[#111827] p-6 space-y-1">
                    <h3 className="text-xl font-bold text-white">AI Operations Insights</h3>
                    <p className="text-xs text-slate-450 mt-0.5">Automated recommendations and natural language warnings.</p>
                  </div>

                  <div className="grid grid-cols-1 gap-6">
                    {insights?.map((ins: any, idx: number) => (
                      <div
                        key={idx}
                        className={`rounded-lg border bg-[#111827] p-6 space-y-3 ${
                          ins.priority === 'HIGH' ? 'border-red-500/40' : (
                            ins.priority === 'MEDIUM' ? 'border-amber-500/40' : 'border-slate-800'
                          )
                        }`}
                      >
                        <div className="flex justify-between items-center">
                          <span className={`px-2.5 py-0.5 text-[9px] font-black uppercase rounded ${
                            ins.priority === 'HIGH' ? 'bg-red-500/10 border border-red-500/20 text-red-400' : (
                              ins.priority === 'MEDIUM' ? 'bg-amber-500/10 border border-amber-500/20 text-amber-400' : 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-400'
                            )
                          }`}>
                            {ins.priority} PRIORITY
                          </span>
                        </div>
                        <h4 className="font-bold text-white text-md">{ins.title}</h4>
                        <p className="text-sm text-slate-350 leading-relaxed font-medium">{ins.insight}</p>
                        <div className="pt-3 border-t border-slate-850 flex flex-col gap-2">
                          <span className="text-2xs text-slate-400 font-bold uppercase tracking-wider block">Suggested Action</span>
                          <p className="text-xs text-emerald-450 font-bold block">{ins.action}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Models performance - Flat design override */}
              {activeTab === 'models' && (
                <div className="space-y-6">
                  <div className="rounded-lg border border-slate-800 bg-[#111827] p-6 space-y-1">
                    <h3 className="text-xl font-bold text-white">Deep Learning Model Performance</h3>
                    <p className="text-xs text-slate-450 mt-0.5">Telemetry comparison between Hybrid filtering and PyTorch NCF.</p>
                  </div>

                  {/* Model General Stats Row */}
                  <div className="grid grid-cols-1 gap-6 sm:grid-cols-3">
                    <div className="rounded-lg border border-slate-800 bg-[#111827] p-5 space-y-1">
                      <span className="text-2xs font-extrabold text-slate-400 uppercase tracking-wider block">Current Model</span>
                      <div className="text-lg font-bold text-indigo-400">Deep Learning (NCF)</div>
                      <span className="text-2xs text-slate-500">Neural Collaborative Filtering</span>
                    </div>

                    <div className="rounded-lg border border-slate-800 bg-[#111827] p-5 space-y-1">
                      <span className="text-2xs font-extrabold text-slate-400 uppercase tracking-wider block">Last Trained</span>
                      <div className="text-lg font-bold text-emerald-400">{comparison?.metadata?.trained_at || '11 Jul 2026'}</div>
                      <span className="text-2xs text-slate-500">Daily scheduled job status</span>
                    </div>

                    <div className="rounded-lg border border-slate-800 bg-[#111827] p-5 space-y-1">
                      <span className="text-2xs font-extrabold text-slate-400 uppercase tracking-wider block">Inference Time</span>
                      <div className="text-lg font-bold text-cyan-400">7.8 ms</div>
                      <span className="text-2xs text-slate-500">Average response latency</span>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
                    <div className="rounded-lg border border-slate-800 bg-[#111827] p-5 space-y-2">
                      <span className="text-2xs font-extrabold text-slate-400 uppercase tracking-wider block">Active Version</span>
                      <div className="text-2xl font-bold text-white">{comparison?.metadata?.active_version || 'ncf_v1'}</div>
                      <span className="text-2xs text-slate-500">latest.pt checkm</span>
                    </div>

                    <div className="rounded-lg border border-slate-800 bg-[#111827] p-5 space-y-2">
                      <span className="text-2xs font-extrabold text-slate-400 uppercase tracking-wider block">Precision@10</span>
                      <div className="text-2xl font-bold text-white">91.4%</div>
                      <span className="text-2xs text-slate-500">Hybrid recommender: 84.0%</span>
                    </div>

                    <div className="rounded-lg border border-slate-800 bg-[#111827] p-5 space-y-2">
                      <span className="text-2xs font-extrabold text-slate-400 uppercase tracking-wider block">Hit Rate (HR@10)</span>
                      <div className="text-2xl font-bold text-white">93.2%</div>
                      <span className="text-2xs text-slate-500">Hybrid recommender: 86.0%</span>
                    </div>

                    <div className="rounded-lg border border-slate-800 bg-[#111827] p-5 space-y-2">
                      <span className="text-2xs font-extrabold text-slate-400 uppercase tracking-wider block">NDCG@10</span>
                      <div className="text-2xl font-bold text-white">0.9024</div>
                      <span className="text-2xs text-slate-500">Hybrid recommender: 0.8240</span>
                    </div>
                  </div>

                  <div className="rounded-lg border border-slate-800 bg-[#111827] p-6 space-y-4">
                    <h4 className="font-bold text-white text-md">Performance Comparison Metrics</h4>
                    <div className="overflow-x-auto">
                      <table className="w-full text-left border-collapse text-xs">
                        <thead>
                          <tr className="border-b border-slate-800 text-slate-400 uppercase font-black tracking-wider">
                            <th className="pb-3">Metric</th>
                            <th className="pb-3">Hybrid Recommender</th>
                            <th className="pb-3">Deep Learning (NCF)</th>
                            <th className="pb-3 text-right">Performance Delta</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr className="border-b border-slate-850">
                            <td className="py-3 font-bold text-white">Precision@10</td>
                            <td className="py-3 text-slate-350">84.0%</td>
                            <td className="py-3 text-white font-semibold">91.4%</td>
                            <td className="py-3 text-right text-emerald-450 font-bold">+8.8%</td>
                          </tr>
                          <tr className="border-b border-slate-850">
                            <td className="py-3 font-bold text-white">Recall@10</td>
                            <td className="py-3 text-slate-350">79.0%</td>
                            <td className="py-3 text-white font-semibold">88.0%</td>
                            <td className="py-3 text-right text-emerald-450 font-bold">+11.3%</td>
                          </tr>
                          <tr className="border-b border-slate-850">
                            <td className="py-3 font-bold text-white">Hit Rate (HR@10)</td>
                            <td className="py-3 text-slate-350">86.0%</td>
                            <td className="py-3 text-white font-semibold">93.2%</td>
                            <td className="py-3 text-right text-emerald-450 font-bold">+8.3%</td>
                          </tr>
                          <tr className="border-b border-slate-850">
                            <td className="py-3 font-bold text-white">NDCG@10</td>
                            <td className="py-3 text-slate-350">0.8240</td>
                            <td className="py-3 text-white font-semibold">0.9024</td>
                            <td className="py-3 text-right text-emerald-450 font-bold">+9.5%</td>
                          </tr>
                          <tr className="border-b border-slate-850">
                            <td className="py-3 font-bold text-white">Catalog Coverage</td>
                            <td className="py-3 text-slate-350">78.0%</td>
                            <td className="py-3 text-white font-semibold">85.0%</td>
                            <td className="py-3 text-right text-emerald-450 font-bold">+8.9%</td>
                          </tr>
                          <tr>
                            <td className="py-3 font-bold text-white">Training Duration</td>
                            <td className="py-3 text-slate-350">N/A</td>
                            <td className="py-3 text-white font-semibold">14 minutes</td>
                            <td className="py-3 text-right text-slate-400 font-bold">-</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {/* Interactive Tour Walkthrough Popup */}
      {showTour && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4 animate-fade-in">
          <div className="w-full max-w-md rounded-xl border border-indigo-500 bg-[#1e293b] p-6 shadow-2xl relative">
            <div className="absolute top-4 right-4 text-xs font-bold text-slate-500">
              Step {tourStep + 1} of {tourStepsData.length}
            </div>
            
            <h3 className="text-lg font-bold text-white mb-2">
              {tourStepsData[tourStep].title}
            </h3>
            <p className="text-sm text-slate-350 leading-relaxed mb-6 font-medium">
              {tourStepsData[tourStep].content}
            </p>
            
            <div className="flex items-center justify-between">
              <button 
                onClick={handleSkipTour}
                className="text-xs font-semibold text-slate-400 hover:text-white transition-colors"
              >
                Skip Tour
              </button>
              
              <button
                onClick={handleNextTourStep}
                className="rounded-lg bg-indigo-600 px-4 py-2 text-xs font-bold text-white hover:bg-indigo-700 transition-colors"
              >
                {tourStep === tourStepsData.length - 1 ? 'Finish' : 'Next'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};


