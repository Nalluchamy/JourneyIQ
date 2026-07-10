import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ordersApi } from '../services/api';

interface Order {
  id: number;
  status: string;
  total: number;
  invoice_number: string;
  created_at: string;
  items: Array<{
    id: number;
    quantity: number;
    unit_price: number;
  }>;
}

export const OrderHistory: React.FC = () => {
  const navigate = useNavigate();
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchOrders = async () => {
      try {
        setLoading(true);
        const data = await ordersApi.getMyOrders();
        // Since getMyOrders returns paginated results (e.g. { items: [...], total: ... })
        setOrders(data.items || []);
        setError(null);
      } catch (err: any) {
        setError(err.message || 'Failed to load order history.');
      } finally {
        setLoading(false);
      }
    };

    fetchOrders();
  }, []);

  const getStatusBadge = (status: string) => {
    switch (status.toLowerCase()) {
      case 'pending':
        return <span className="px-2.5 py-1 text-xs font-bold rounded-lg bg-yellow-50 dark:bg-yellow-950/20 text-yellow-700 dark:text-yellow-400 border border-yellow-100 dark:border-yellow-900/30">Pending</span>;
      case 'confirmed':
        return <span className="px-2.5 py-1 text-xs font-bold rounded-lg bg-blue-50 dark:bg-blue-950/20 text-blue-700 dark:text-blue-400 border border-blue-100 dark:border-blue-900/30">Confirmed</span>;
      case 'shipped':
        return <span className="px-2.5 py-1 text-xs font-bold rounded-lg bg-indigo-50 dark:bg-indigo-950/20 text-indigo-700 dark:text-indigo-400 border border-indigo-100 dark:border-indigo-900/30">Shipped</span>;
      case 'completed':
        return <span className="px-2.5 py-1 text-xs font-bold rounded-lg bg-green-50 dark:bg-green-950/20 text-green-700 dark:text-green-400 border border-green-100 dark:border-green-900/30">Completed</span>;
      case 'cancelled':
        return <span className="px-2.5 py-1 text-xs font-bold rounded-lg bg-red-50 dark:bg-red-950/20 text-red-650 dark:text-red-400 border border-red-100 dark:border-red-900/30">Cancelled</span>;
      default:
        return <span className="px-2.5 py-1 text-xs font-bold rounded-lg bg-slate-50 dark:bg-slate-900 text-slate-700 dark:text-slate-400">{status}</span>;
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">Order History</h1>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">Review your recent store purchases and tracking details.</p>
      </div>

      {loading ? (
        <div className="text-center py-12">
          <div className="inline-block w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
          <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">Loading order list...</p>
        </div>
      ) : error ? (
        <div className="bg-red-50 dark:bg-red-950/20 text-red-650 dark:text-red-400 p-4 rounded-xl border border-red-100 dark:border-red-900/30 text-center">
          {error}
        </div>
      ) : orders.length === 0 ? (
        <div className="text-center py-16 bg-slate-50 dark:bg-slate-900 rounded-2xl border-2 border-dashed border-slate-200 dark:border-slate-800 p-8">
          <svg className="w-12 h-12 mx-auto text-slate-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
          <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-1">No orders found</h3>
          <p className="text-sm text-slate-500 dark:text-slate-400 mb-6">You haven't placed any orders with JourneyIQ yet.</p>
          <button
            onClick={() => navigate('/products')}
            className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-medium transition-colors shadow-md shadow-blue-500/10"
          >
            Start Shopping
          </button>
        </div>
      ) : (
        <div className="bg-white dark:bg-slate-800 border border-slate-100 dark:border-slate-700 rounded-2xl overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50 dark:bg-slate-900/50 text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider border-b border-slate-100 dark:border-slate-700">
                  <th className="px-6 py-4">Invoice #</th>
                  <th className="px-6 py-4">Date</th>
                  <th className="px-6 py-4">Status</th>
                  <th className="px-6 py-4 text-right">Total Price</th>
                  <th className="px-6 py-4 text-center">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-700 text-sm text-slate-700 dark:text-slate-350">
                {orders.map((order) => (
                  <tr key={order.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-750/30 transition-colors">
                    <td className="px-6 py-4 font-bold text-slate-900 dark:text-white">{order.invoice_number}</td>
                    <td className="px-6 py-4">
                      {new Date(order.created_at).toLocaleDateString(undefined, {
                        year: 'numeric',
                        month: 'short',
                        day: 'numeric',
                      })}
                    </td>
                    <td className="px-6 py-4">{getStatusBadge(order.status)}</td>
                    <td className="px-6 py-4 text-right font-black text-slate-900 dark:text-white">
                      ${Number(order.total).toFixed(2)}
                    </td>
                    <td className="px-6 py-4 text-center">
                      <button
                        onClick={() => navigate(`/orders/${order.id}`)}
                        className="px-3.5 py-1.5 border border-slate-200 dark:border-slate-700 hover:border-slate-300 hover:bg-slate-50 dark:hover:bg-slate-900 text-slate-750 dark:text-slate-300 rounded-lg text-xs font-semibold transition-all"
                      >
                        Details
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
