import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ordersApi, paymentsApi } from '../services/api';

interface OrderItem {
  id: number;
  quantity: number;
  unit_price: number;
  subtotal: number;
  product_id: number;
  product?: {
    name: string;
    image_url?: string;
    brand?: string;
  };
}

interface Address {
  full_name: string;
  phone: string;
  address_line1: string;
  address_line2?: string;
  city: string;
  state: string;
  postal_code: string;
  country: string;
}

interface StatusHistory {
  id: number;
  status: string;
  notes?: string;
  created_at: string;
}

interface Order {
  id: number;
  status: string;
  subtotal: number;
  tax: number;
  discount: number;
  total: number;
  invoice_number: string;
  created_at: string;
  items: OrderItem[];
  status_history: StatusHistory[];
  shipping_address?: Address;
}

export const OrderDetails: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [order, setOrder] = useState<Order | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const fetchOrderDetails = async () => {
    if (!id) return;
    try {
      setLoading(true);
      const data = await ordersApi.getOrderDetails(Number(id));
      setOrder(data);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load order details.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrderDetails();
  }, [id]);

  const handleCancelOrder = async () => {
    if (!order) return;
    if (!window.confirm('Are you sure you want to cancel this order? This will release the stock immediately.')) return;

    try {
      setSubmitting(true);
      await ordersApi.cancelOrder(order.id);
      fetchOrderDetails(); // Reload fresh state
    } catch (err: any) {
      alert(err.message || 'Failed to cancel order.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleSimulatePayment = async (success: boolean) => {
    if (!order) return;
    try {
      setSubmitting(true);
      if (success) {
        await paymentsApi.mockSuccess(order.id);
      } else {
        await paymentsApi.mockFailure(order.id);
      }
      fetchOrderDetails(); // Reload fresh state
    } catch (err: any) {
      alert(err.message || 'Payment simulation failed.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDownloadInvoice = async () => {
    if (!order) return;
    try {
      const invoiceData = await ordersApi.getInvoice(order.id);
      const blob = new Blob([JSON.stringify(invoiceData, null, 2)], { type: 'application/json' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `invoice-${order.invoice_number}.json`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err: any) {
      alert(err.message || 'Failed to download invoice.');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'pending': return 'text-yellow-600 dark:text-yellow-450';
      case 'confirmed': return 'text-blue-600 dark:text-blue-450';
      case 'cancelled': return 'text-red-500';
      case 'completed': return 'text-green-600 dark:text-green-450';
      default: return 'text-slate-600 dark:text-slate-400';
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-96">
        <div className="w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  if (error || !order) {
    return (
      <div className="max-w-md mx-auto text-center py-16 px-4">
        <div className="bg-red-50 dark:bg-red-950/20 text-red-650 dark:text-red-400 p-4 rounded-xl border border-red-100 dark:border-red-900/30 mb-6">
          {error || 'Order not found.'}
        </div>
        <button
          onClick={() => navigate('/orders')}
          className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-bold transition-colors"
        >
          Back to Orders
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      {/* Header Info */}
      <div className="flex flex-col md:flex-row md:justify-between md:items-center gap-4 mb-8">
        <div>
          <button
            onClick={() => navigate('/orders')}
            className="text-sm font-bold text-slate-550 dark:text-slate-450 hover:text-slate-700 flex items-center gap-1.5 mb-2"
          >
            ← Back to Orders
          </button>
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-black text-slate-900 dark:text-white tracking-tight">Order #{order.invoice_number}</h1>
            <span className={`text-lg font-black uppercase tracking-wider ${getStatusColor(order.status)}`}>
              {order.status}
            </span>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Placed on: {new Date(order.created_at).toLocaleString()}
          </p>
        </div>

        <div className="flex flex-wrap gap-2.5">
          <button
            onClick={handleDownloadInvoice}
            className="px-4 py-2 border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-900 text-slate-700 dark:text-slate-350 rounded-xl font-semibold text-sm transition-colors flex items-center gap-2"
          >
            📥 Download Invoice
          </button>

          {(order.status === 'pending' || order.status === 'confirmed') && (
            <button
              onClick={handleCancelOrder}
              disabled={submitting}
              className="px-4 py-2 bg-red-50 dark:bg-red-950/20 text-red-500 hover:bg-red-100 dark:hover:bg-red-950/40 rounded-xl font-semibold text-sm transition-colors"
            >
              Cancel Order
            </button>
          )}
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Columns (Col Span 2): Items, Addresses, Payment Simulator */}
        <div className="lg:col-span-2 space-y-6">
          {/* Mock Payment Simulator Overlay */}
          {order.status === 'pending' && (
            <div className="bg-yellow-50/50 dark:bg-yellow-950/10 border border-yellow-200/50 dark:border-yellow-900/30 rounded-2xl p-6">
              <h3 className="text-sm font-bold text-yellow-800 dark:text-yellow-400 mb-2">Simulate Payment Authorization</h3>
              <p className="text-xs text-yellow-750 dark:text-yellow-500 mb-4">
                This order is currently pending authorization. Click below to simulate checkout payment status outcomes.
              </p>
              <div className="flex flex-wrap gap-3">
                <button
                  onClick={() => handleSimulatePayment(true)}
                  disabled={submitting}
                  className="px-4 py-2.5 bg-green-600 hover:bg-green-700 text-white rounded-xl text-xs font-bold transition-colors shadow-sm"
                >
                  Simulate Payment Success
                </button>
                <button
                  onClick={() => handleSimulatePayment(false)}
                  disabled={submitting}
                  className="px-4 py-2.5 bg-red-650 hover:bg-red-700 text-white rounded-xl text-xs font-bold transition-colors shadow-sm"
                >
                  Simulate Payment Failure
                </button>
              </div>
            </div>
          )}

          {/* Items Table */}
          <div className="bg-white dark:bg-slate-800 border border-slate-100 dark:border-slate-700 rounded-2xl p-6 shadow-sm">
            <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-4">Order Items</h3>
            <div className="divide-y divide-slate-100 dark:divide-slate-700">
              {order.items.map((item) => (
                <div key={item.id} className="flex gap-4 py-4 first:pt-0 last:pb-0">
                  {item.product?.image_url ? (
                    <img src={item.product.image_url} alt={item.product.name} className="w-16 h-16 rounded-xl object-cover" />
                  ) : (
                    <div className="w-16 h-16 rounded-xl bg-slate-100 dark:bg-slate-900 flex items-center justify-center text-slate-450">
                      📦
                    </div>
                  )}
                  <div className="flex-1 min-w-0">
                    <h4 className="font-bold text-slate-900 dark:text-white text-sm truncate">{item.product?.name || 'Unknown Product'}</h4>
                    {item.product?.brand && <p className="text-xs text-slate-450 dark:text-slate-400">{item.product.brand}</p>}
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Qty: {item.quantity}</p>
                  </div>
                  <div className="text-right">
                    <span className="font-bold text-slate-900 dark:text-white">${Number(item.subtotal).toFixed(2)}</span>
                    <p className="text-xs text-slate-500 dark:text-slate-400">${Number(item.unit_price).toFixed(2)} each</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Shipping Address and Cost Summary */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Delivery address */}
            <div className="bg-white dark:bg-slate-800 border border-slate-100 dark:border-slate-700 rounded-2xl p-6 shadow-sm">
              <h3 className="text-md font-bold text-slate-900 dark:text-white mb-3">Shipping Address</h3>
              {order.shipping_address ? (
                <div className="text-sm text-slate-650 dark:text-slate-350 space-y-1">
                  <p className="font-bold text-slate-900 dark:text-white">{order.shipping_address.full_name}</p>
                  <p>{order.shipping_address.address_line1}</p>
                  {order.shipping_address.address_line2 && <p>{order.shipping_address.address_line2}</p>}
                  <p>{order.shipping_address.city}, {order.shipping_address.state} {order.shipping_address.postal_code}</p>
                  <p>{order.shipping_address.country}</p>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-3">Phone: {order.shipping_address.phone}</p>
                </div>
              ) : (
                <p className="text-sm text-slate-400">No address information recorded.</p>
              )}
            </div>

            {/* Invoice Cost Breakdowns */}
            <div className="bg-slate-50 dark:bg-slate-800/40 border border-slate-100 dark:border-slate-700 rounded-2xl p-6 shadow-sm">
              <h3 className="text-md font-bold text-slate-900 dark:text-white mb-3">Order Cost Summary</h3>
              <div className="space-y-2.5 text-sm text-slate-600 dark:text-slate-400 border-b border-slate-100 dark:border-slate-700 pb-3 mb-3">
                <div className="flex justify-between">
                  <span>Subtotal</span>
                  <span className="font-semibold text-slate-900 dark:text-white">${Number(order.subtotal).toFixed(2)}</span>
                </div>
                {Number(order.discount) > 0 && (
                  <div className="flex justify-between text-green-600">
                    <span>Discount</span>
                    <span className="font-semibold">-${Number(order.discount).toFixed(2)}</span>
                  </div>
                )}
                <div className="flex justify-between">
                  <span>Tax (8%)</span>
                  <span className="font-semibold text-slate-900 dark:text-white">${Number(order.tax).toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Shipping</span>
                  <span className="font-semibold text-slate-900 dark:text-white">
                    {order.subtotal > 0 ? '$10.00' : '$0.00'}
                  </span>
                </div>
              </div>
              <div className="flex justify-between items-center text-slate-900 dark:text-white">
                <span className="font-bold">Total Cost</span>
                <span className="text-xl font-black">${Number(order.total).toFixed(2)}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Order Timeline (Status History) */}
        <div>
          <div className="bg-white dark:bg-slate-800 border border-slate-100 dark:border-slate-700 rounded-2xl p-6 shadow-sm">
            <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-5">Status Timeline</h3>
            <div className="space-y-6 relative before:absolute before:left-[11px] before:top-2 before:bottom-2 before:w-[2px] before:bg-slate-100 dark:before:bg-slate-700">
              {order.status_history.map((hist, idx) => (
                <div key={hist.id} className="flex gap-4 relative">
                  <div className={`w-6 h-6 rounded-full border-4 border-white dark:border-slate-850 flex items-center justify-center text-[10px] text-white z-10 ${
                    idx === order.status_history.length - 1
                      ? 'bg-blue-500 ring-4 ring-blue-500/20'
                      : 'bg-slate-300 dark:bg-slate-600'
                  }`}>
                    ●
                  </div>
                  <div className="flex-1 min-w-0">
                    <span className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wider">
                      {hist.status}
                    </span>
                    <p className="text-xs text-slate-500 dark:text-slate-400">
                      {new Date(hist.created_at).toLocaleString()}
                    </p>
                    {hist.notes && (
                      <p className="text-xs text-slate-650 dark:text-slate-350 bg-slate-50 dark:bg-slate-900/50 p-2.5 rounded-xl mt-1.5 leading-relaxed">
                        {hist.notes}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
