import React, { useState } from 'react';
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
import { apiClient } from '../services/api';

export const Dashboard: React.FC = () => {
  const { tab = 'overview' } = useParams<{ tab?: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  // Filters State
  const [dateRange, setDateRange] = useState('last_30_days');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [showCustomPicker, setShowCustomPicker] = useState(false);

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

  const isDataEmpty = !overview?.summary?.total_revenue && !overview?.summary?.order_count;

  // Sidebar Tabs Config
  const tabsConfig = [
    { key: 'overview', label: 'Overview', icon: <TrendingUp className="h-4 w-4" /> },
    { key: 'customers', label: 'Customers', icon: <Users className="h-4 w-4" /> },
    { key: 'products', label: 'Products', icon: <ShoppingBag className="h-4 w-4" /> },
    { key: 'orders', label: 'Orders', icon: <Percent className="h-4 w-4" /> },
    { key: 'analytics', label: 'Analytics', icon: <Layers className="h-4 w-4" /> },
    { key: 'insights', label: 'AI Insights', icon: <Sparkles className="h-4 w-4" /> },
  ];

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      {/* Header bar */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between border-b border-border/80 pb-6 mb-8">
        <div>
          <h1 className="text-3xl font-black text-white tracking-tight">Owner Dashboard</h1>
          <p className="text-sm text-muted-foreground mt-1">Retail Journey Intelligence & Business Analytics</p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Refresh Action */}
          <button
            onClick={() => refreshMutation.mutate()}
            className="flex items-center space-x-1.5 rounded-lg border border-border bg-card px-3.5 py-2 text-xs font-bold text-white transition-all hover:bg-muted"
            title="Refresh Analytics summaries"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${refreshMutation.isPending ? 'animate-spin' : ''}`} />
            <span>Refresh Analytics</span>
          </button>

          {/* Export Options dropdown placeholder */}
          <div className="relative group">
            <button className="flex items-center space-x-1.5 rounded-lg border border-border bg-card px-3.5 py-2 text-xs font-bold text-white transition-all hover:bg-muted">
              <Download className="h-3.5 w-3.5" />
              <span>Export Report</span>
            </button>
            <div className="absolute right-0 top-full mt-1.5 hidden w-44 rounded-lg border border-border bg-card p-1 shadow-lg group-hover:block z-50">
              <button onClick={() => handleExport('orders')} className="w-full text-left rounded-md px-3 py-1.5 text-xs text-muted-foreground hover:bg-muted hover:text-white">Orders CSV</button>
              <button onClick={() => handleExport('customers')} className="w-full text-left rounded-md px-3 py-1.5 text-xs text-muted-foreground hover:bg-muted hover:text-white">Customers CSV</button>
              <button onClick={() => handleExport('products')} className="w-full text-left rounded-md px-3 py-1.5 text-xs text-muted-foreground hover:bg-muted hover:text-white">Products CSV</button>
              <button onClick={() => handleExport('revenue')} className="w-full text-left rounded-md px-3 py-1.5 text-xs text-muted-foreground hover:bg-muted hover:text-white">Revenue CSV</button>
            </div>
          </div>

          {/* Date Picker Filter */}
          <div className="flex items-center space-x-2 bg-card border border-border rounded-lg px-3 py-2 text-xs font-bold text-white">
            <Calendar className="h-4 w-4 text-primary" />
            <select
              value={dateRange}
              onChange={(e) => handleDateRangeChange(e.target.value)}
              className="bg-transparent focus:outline-none border-none cursor-pointer"
            >
              <option value="today">Today</option>
              <option value="yesterday">Yesterday</option>
              <option value="last_7_days">Last 7 Days</option>
              <option value="last_30_days">Last 30 Days</option>
              <option value="this_month">This Month</option>
              <option value="custom">Custom Range</option>
            </select>
          </div>
        </div>
      </div>

      {/* Custom Picker range selections */}
      {showCustomPicker && (
        <div className="flex flex-wrap gap-4 items-center bg-card border border-border rounded-xl p-4 mb-6">
          <div className="flex items-center space-x-2 text-xs">
            <span className="text-muted-foreground uppercase font-bold">Start:</span>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="rounded bg-black/35 border border-border px-3 py-1 text-white focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </div>
          <div className="flex items-center space-x-2 text-xs">
            <span className="text-muted-foreground uppercase font-bold">End:</span>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="rounded bg-black/35 border border-border px-3 py-1 text-white focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </div>
        </div>
      )}

      {/* Main Tabbed Grid Layout */}
      <div className="grid grid-cols-1 gap-8 lg:grid-cols-4">
        {/* Left navigation sidebar */}
        <div className="space-y-1">
          {tabsConfig.map((t) => (
            <button
              key={t.key}
              onClick={() => navigate(`/dashboard/${t.key}`)}
              className={`w-full flex items-center space-x-3 rounded-xl px-4 py-3 text-sm font-semibold transition-all ${
                tab === t.key
                  ? 'bg-primary text-white shadow-md shadow-primary/20 scale-[1.02]'
                  : 'text-muted-foreground hover:bg-card hover:text-white'
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
            /* Empty State fallback representation */
            <div className="flex flex-col items-center justify-center rounded-2xl border border-border bg-card p-16 text-center">
              <Inbox className="h-12 w-12 text-muted-foreground mb-4 animate-bounce" />
              <h3 className="text-lg font-bold text-white mb-1">No analytics available yet</h3>
              <p className="text-sm text-muted-foreground mb-6">Place some orders to generate analytics reports.</p>
              <Link to="/products" className="flex items-center space-x-2 rounded-lg bg-primary px-6 py-3 text-sm font-semibold text-white transition-all hover:bg-primary/95">
                <span>Go to Storefront</span>
                <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          ) : (
            <>
              {/* 1. OVERVIEW TAB */}
              {tab === 'overview' && (
                <div className="space-y-6">
                  {/* Executive summary cards */}
                  <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
                    <div className="rounded-xl border border-border bg-card p-5 space-y-2">
                      <span className="text-2xs font-extrabold text-muted-foreground uppercase tracking-wider block">Today's Revenue</span>
                      <div className="text-2xl font-black text-white">${Number(overview?.summary?.today_revenue || 0).toFixed(2)}</div>
                      <span className={`text-2xs font-bold ${Number(overview?.summary?.today_revenue_delta || 0) >= 0 ? 'text-emerald-500' : 'text-red-400'}`}>
                        {Number(overview?.summary?.today_revenue_delta || 0) >= 0 ? '+' : ''}
                        {overview?.summary?.today_revenue_delta || 0}% vs Yesterday
                      </span>
                    </div>

                    <div className="rounded-xl border border-border bg-card p-5 space-y-2">
                      <span className="text-2xs font-extrabold text-muted-foreground uppercase tracking-wider block">Today's Orders</span>
                      <div className="text-2xl font-black text-white">{overview?.summary?.today_orders || 0}</div>
                      <span className={`text-2xs font-bold ${Number(overview?.summary?.today_orders_delta || 0) >= 0 ? 'text-emerald-500' : 'text-red-400'}`}>
                        {Number(overview?.summary?.today_orders_delta || 0) >= 0 ? '+' : ''}
                        {overview?.summary?.today_orders_delta || 0}% vs Yesterday
                      </span>
                    </div>

                    <div className="rounded-xl border border-border bg-card p-5 space-y-2">
                      <span className="text-2xs font-extrabold text-muted-foreground uppercase tracking-wider block">Returning Customers</span>
                      <div className="text-2xl font-black text-white">{overview?.summary?.returning_customer_rate || 0}%</div>
                      <span className="text-2xs text-muted-foreground">Historical order count &gt; 1</span>
                    </div>

                    <div className="rounded-xl border border-border bg-card p-5 space-y-2">
                      <span className="text-2xs font-extrabold text-muted-foreground uppercase tracking-wider block">Active Sessions</span>
                      <div className="text-2xl font-black text-white">{overview?.active_sessions || 0}</div>
                      <span className="text-2xs text-muted-foreground">Sessions active in 24h</span>
                    </div>
                  </div>

                  {/* General KPIs widget */}
                  <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
                    <div className="rounded-xl border border-border bg-card p-6 flex justify-between items-center">
                      <div>
                        <span className="text-xs text-muted-foreground block">Period Revenue</span>
                        <span className="text-2xl font-black text-white mt-1 block">${Number(overview?.summary?.total_revenue || 0).toFixed(2)}</span>
                      </div>
                      <TrendingUp className="h-8 w-8 text-primary opacity-60" />
                    </div>

                    <div className="rounded-xl border border-border bg-card p-6 flex justify-between items-center">
                      <div>
                        <span className="text-xs text-muted-foreground block">Avg Order Value (AOV)</span>
                        <span className="text-2xl font-black text-white mt-1 block">${Number(overview?.summary?.average_order_value || 0).toFixed(2)}</span>
                      </div>
                      <Activity className="h-8 w-8 text-indigo-400 opacity-60" />
                    </div>

                    <div className="rounded-xl border border-border bg-card p-6 flex justify-between items-center">
                      <div>
                        <span className="text-xs text-muted-foreground block">Payment Success Rate</span>
                        <span className="text-2xl font-black text-white mt-1 block">{overview?.summary?.payment_success_rate || 0}%</span>
                      </div>
                      <Percent className="h-8 w-8 text-emerald-400 opacity-60" />
                    </div>
                  </div>

                  {/* Alerts & Orders Grid */}
                  <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
                    {/* Inventory alerts */}
                    <div className="rounded-xl border border-border bg-card p-6 space-y-4">
                      <h3 className="font-bold text-white text-lg flex items-center space-x-2">
                        <AlertTriangle className="h-5 w-5 text-amber-500" />
                        <span>Inventory Alerts</span>
                      </h3>
                      <div className="space-y-3">
                        {!overview?.inventory_alerts || overview.inventory_alerts.length === 0 ? (
                          <p className="text-sm text-muted-foreground">All products are healthy and well-stocked.</p>
                        ) : (
                          overview.inventory_alerts.map((alert: any, idx: number) => (
                            <div key={idx} className="rounded-lg border border-border/50 bg-black/20 p-4 space-y-1">
                              <div className="flex justify-between items-center">
                                <span className={`px-2 py-0.5 text-[9px] font-extrabold uppercase rounded ${
                                  alert.priority === 'HIGH' ? 'bg-red-500/10 border border-red-500/20 text-red-400' : 'bg-amber-500/10 border border-amber-500/20 text-amber-400'
                                }`}>
                                  {alert.alert_type}
                                </span>
                                <span className="text-[10px] text-muted-foreground">Stock: {alert.stock}</span>
                              </div>
                              <p className="text-xs text-white font-medium">{alert.message}</p>
                              <p className="text-2xs text-muted-foreground mt-1">💡 {alert.recommendation}</p>
                            </div>
                          ))
                        )}
                      </div>
                    </div>

                    {/* Recent Orders */}
                    <div className="rounded-xl border border-border bg-card p-6 space-y-4">
                      <h3 className="font-bold text-white text-lg flex items-center space-x-2">
                        <ShoppingBag className="h-5 w-5 text-indigo-400" />
                        <span>Recent Orders</span>
                      </h3>
                      <div className="space-y-3">
                        {!orders?.recent_orders || orders.recent_orders.length === 0 ? (
                          <p className="text-sm text-muted-foreground">No recent orders found.</p>
                        ) : (
                          orders.recent_orders.slice(0, 5).map((o: any) => (
                            <div key={o.id} className="flex justify-between items-center border-b border-border/50 pb-2.5 last:border-b-0 last:pb-0">
                              <div>
                                <span className="text-xs font-bold text-white block">{o.invoice_number}</span>
                                <span className="text-2xs text-muted-foreground block">{o.customer_name}</span>
                              </div>
                              <div className="text-right">
                                <span className="text-xs font-black text-white block">${Number(o.total).toFixed(2)}</span>
                                <span className="text-2xs text-muted-foreground">{o.status}</span>
                              </div>
                            </div>
                          ))
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* 2. CUSTOMERS TAB */}
              {tab === 'customers' && (
                <div className="rounded-xl border border-border bg-card p-6 space-y-6">
                  <div>
                    <h3 className="text-xl font-bold text-white">Customer Intelligence</h3>
                    <p className="text-xs text-muted-foreground mt-0.5">Aggregated RFM profiles, churn risks, and CLV metrics.</p>
                  </div>

                  <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse text-xs">
                      <thead>
                        <tr className="border-b border-border text-muted-foreground uppercase font-black tracking-wider">
                          <th className="pb-3">Customer</th>
                          <th className="pb-3">Segment</th>
                          <th className="pb-3">Spend</th>
                          <th className="pb-3">Orders</th>
                          <th className="pb-3">RFM (R/F/M)</th>
                          <th className="pb-3">Churn Risk</th>
                          <th className="pb-3 text-right">Expected CLV</th>
                        </tr>
                      </thead>
                      <tbody>
                        {customers?.map((c: any) => (
                          <tr key={c.user_id} className="border-b border-border/60 hover:bg-muted/30">
                            <td className="py-4">
                              <span className="font-bold text-white block">{c.customer_name}</span>
                              <span className="text-2xs text-muted-foreground block">{c.email}</span>
                            </td>
                            <td className="py-4">
                              <span className="inline-block px-2 py-0.5 bg-primary/10 border border-primary/25 text-primary text-[10px] font-extrabold rounded">
                                {c.segment}
                              </span>
                            </td>
                            <td className="py-4 font-bold text-white">${Number(c.total_spend).toFixed(2)}</td>
                            <td className="py-4 font-bold text-white">{c.order_count}</td>
                            <td className="py-4 text-muted-foreground font-medium">
                              {c.rfm.recency} / {c.rfm.frequency} / {c.rfm.monetary}
                            </td>
                            <td className="py-4">
                              <span className={`inline-block px-2 py-0.5 text-[9px] font-extrabold rounded ${
                                c.churn.risk_level === 'High' ? 'bg-red-500/10 border border-red-500/20 text-red-400' : (
                                  c.churn.risk_level === 'Medium' ? 'bg-amber-500/10 border border-amber-500/20 text-amber-400' : 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-400'
                                )
                              }`} title={c.churn.explanation}>
                                {c.churn.risk_level}
                              </span>
                            </td>
                            <td className="py-4 text-right font-black text-white">${Number(c.clv.expected_value).toFixed(2)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* 3. PRODUCTS TAB */}
              {tab === 'products' && (
                <div className="space-y-6">
                  {/* Top/Lowest selling grid */}
                  <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
                    {/* Top selling */}
                    <div className="rounded-xl border border-border bg-card p-6 space-y-4">
                      <h3 className="font-bold text-white text-lg flex items-center space-x-2">
                        <Flame className="h-5 w-5 text-orange-500 animate-pulse" />
                        <span>Top Selling Products</span>
                      </h3>
                      <div className="space-y-3">
                        {products?.top_selling?.map((p: any) => (
                          <div key={p.product_id} className="flex justify-between items-center border-b border-border/50 pb-2 last:border-b-0 last:pb-0">
                            <div>
                              <span className="text-xs font-bold text-white block">{p.name}</span>
                              <span className="text-2xs text-muted-foreground block">{p.brand}</span>
                            </div>
                            <div className="text-right">
                              <span className="text-xs font-black text-white block">${p.price.toFixed(2)}</span>
                              <span className="text-2xs text-emerald-400 font-bold block">{p.sales} Sales</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Lowest selling */}
                    <div className="rounded-xl border border-border bg-card p-6 space-y-4">
                      <h3 className="font-bold text-white text-lg flex items-center space-x-2">
                        <Star className="h-5 w-5 text-yellow-500" />
                        <span>Lowest Selling Products</span>
                      </h3>
                      <div className="space-y-3">
                        {products?.lowest_selling?.map((p: any) => (
                          <div key={p.product_id} className="flex justify-between items-center border-b border-border/50 pb-2 last:border-b-0 last:pb-0">
                            <div>
                              <span className="text-xs font-bold text-white block">{p.name}</span>
                              <span className="text-2xs text-muted-foreground block">{p.brand}</span>
                            </div>
                            <div className="text-right">
                              <span className="text-xs font-black text-white block">${p.price.toFixed(2)}</span>
                              <span className="text-2xs text-muted-foreground block">{p.sales} Sales</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Stock alerts widget details list */}
                  <div className="rounded-xl border border-border bg-card p-6 space-y-4">
                    <h3 className="font-bold text-white text-lg flex items-center space-x-2">
                      <AlertTriangle className="h-5 w-5 text-amber-500" />
                      <span>Stock Status & Restock Metrics</span>
                    </h3>
                    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                      {products?.inventory_alerts?.map((alert: any, idx: number) => (
                        <div key={idx} className="rounded-xl border border-border/60 bg-black/25 p-4 space-y-1">
                          <div className="flex justify-between items-center">
                            <span className={`px-2 py-0.5 text-[8px] font-extrabold uppercase rounded ${
                              alert.priority === 'HIGH' ? 'bg-red-500/10 border border-red-500/25 text-red-400' : (
                                alert.priority === 'MEDIUM' ? 'bg-amber-500/10 border border-amber-500/25 text-amber-400' : 'bg-primary/10 border border-primary/25 text-primary'
                              )
                            }`}>
                              {alert.alert_type}
                            </span>
                            <span className="text-[10px] text-muted-foreground">Stock: {alert.stock}</span>
                          </div>
                          <h4 className="text-xs font-bold text-white">{alert.message}</h4>
                          <p className="text-2xs text-muted-foreground mt-1">💡 {alert.recommendation}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* 4. ORDERS TAB */}
              {tab === 'orders' && (
                <div className="space-y-6">
                  {/* General KPIs widget */}
                  <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
                    <div className="rounded-xl border border-border bg-card p-6 flex justify-between items-center">
                      <div>
                        <span className="text-xs text-muted-foreground block">Coupon Usage Rate</span>
                        <span className="text-2xl font-black text-white mt-1 block">{overview?.summary?.coupon_usage_rate || 0}%</span>
                      </div>
                      <Percent className="h-8 w-8 text-primary opacity-60" />
                    </div>

                    <div className="rounded-xl border border-border bg-card p-6 flex justify-between items-center">
                      <div>
                        <span className="text-xs text-muted-foreground block">Order Conversion Rate</span>
                        <span className="text-2xl font-black text-white mt-1 block">{analytics?.funnel?.rates?.checkout_completion_rate || 0}%</span>
                      </div>
                      <TrendingUp className="h-8 w-8 text-emerald-400 opacity-60" />
                    </div>
                  </div>

                  {/* List of orders */}
                  <div className="rounded-xl border border-border bg-card p-6 space-y-4">
                    <h3 className="font-bold text-white text-lg">Detailed Orders Summary</h3>
                    <div className="overflow-x-auto">
                      <table className="w-full text-left border-collapse text-xs">
                        <thead>
                          <tr className="border-b border-border text-muted-foreground uppercase font-black tracking-wider">
                            <th className="pb-3">Invoice</th>
                            <th className="pb-3">Customer</th>
                            <th className="pb-3">Date</th>
                            <th className="pb-3">Status</th>
                            <th className="pb-3 text-right">Total</th>
                          </tr>
                        </thead>
                        <tbody>
                          {orders?.recent_orders?.map((o: any) => (
                            <tr key={o.id} className="border-b border-border/50 last:border-b-0 hover:bg-muted/30">
                              <td className="py-4 font-bold text-white">{o.invoice_number}</td>
                              <td className="py-4 text-muted-foreground">{o.customer_name}</td>
                              <td className="py-4 text-muted-foreground">{new Date(o.created_at).toLocaleDateString()}</td>
                              <td className="py-4 uppercase text-xs font-semibold text-primary">{o.status}</td>
                              <td className="py-4 text-right font-black text-white">${o.total.toFixed(2)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              )}

              {/* 5. ANALYTICS TAB */}
              {tab === 'analytics' && (
                <div className="space-y-6">
                  {/* Revenue area chart */}
                  <div className="rounded-xl border border-border bg-card p-6 space-y-4">
                    <h3 className="font-bold text-white text-lg">Sales Revenue Timeline</h3>
                    <div className="h-72 w-full">
                      <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={analytics?.sales_timeline}>
                          <defs>
                            <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor="#10b981" stopOpacity={0.4}/>
                              <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                            </linearGradient>
                          </defs>
                          <CartesianGrid strokeDasharray="3 3" stroke="#2a2e35" />
                          <XAxis dataKey="date" stroke="#94a3b8" fontSize={10} />
                          <YAxis stroke="#94a3b8" fontSize={10} />
                          <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }} />
                          <Area type="monotone" dataKey="revenue" stroke="#10b981" fillOpacity={1} fill="url(#colorRevenue)" />
                        </AreaChart>
                      </ResponsiveContainer>
                    </div>
                  </div>

                  {/* Funnel & Conversion diagram */}
                  <div className="rounded-xl border border-border bg-card p-6 space-y-4">
                    <h3 className="font-bold text-white text-lg flex items-center space-x-2">
                      <Layers className="h-5 w-5 text-indigo-400" />
                      <span>Conversion Funnel Drop-offs</span>
                    </h3>
                    <div className="h-72 w-full">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={analytics?.funnel?.steps}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#2a2e35" />
                          <XAxis dataKey="name" stroke="#94a3b8" fontSize={10} />
                          <YAxis stroke="#94a3b8" fontSize={10} />
                          <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }} />
                          <Bar dataKey="count" fill="#4f46e5" radius={[4, 4, 0, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                </div>
              )}

              {/* 6. INSIGHTS TAB */}
              {tab === 'insights' && (
                <div className="space-y-6">
                  <div>
                    <h3 className="text-xl font-bold text-white flex items-center space-x-2">
                      <Sparkles className="h-5 w-5 text-primary" />
                      <span>AI Business Insights</span>
                    </h3>
                    <p className="text-xs text-muted-foreground mt-0.5">Automated recommendations and natural language warnings.</p>
                  </div>

                  <div className="grid grid-cols-1 gap-6">
                    {insights?.map((ins: any, idx: number) => (
                      <div
                        key={idx}
                        className={`rounded-2xl border bg-card/65 p-6 space-y-3 transition-all hover:scale-[1.01] ${
                          ins.priority === 'HIGH' ? 'border-red-500/40 shadow-lg shadow-red-500/5' : (
                            ins.priority === 'MEDIUM' ? 'border-amber-500/40 shadow-lg shadow-amber-500/5' : 'border-border'
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
                          <span className="text-2xs text-muted-foreground">Generated Just Now</span>
                        </div>
                        <h4 className="font-extrabold text-white text-md">{ins.title}</h4>
                        <p className="text-sm text-white/90 leading-relaxed font-medium">{ins.insight}</p>
                        <div className="pt-3 border-t border-border/50 flex flex-col gap-2">
                          <span className="text-2xs text-muted-foreground font-bold uppercase tracking-wider block">Suggested Action</span>
                          <p className="text-xs text-emerald-400 font-bold block">{ins.action}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};
