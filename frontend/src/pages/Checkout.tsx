import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { cartApi, addressesApi, checkoutApi, couponsApi, paymentsApi } from '../services/api';

interface CartItem {
  id: number;
  quantity: number;
  product: {
    id: number;
    name: string;
    price: number;
    image_url?: string;
    brand?: string;
  };
}

interface Address {
  id: number;
  full_name: string;
  phone: string;
  address_line1: string;
  address_line2?: string;
  city: string;
  state: string;
  postal_code: string;
  country: string;
  is_default: boolean;
}

export const Checkout: React.FC = () => {
  const navigate = useNavigate();
  const [cartItems, setCartItems] = useState<CartItem[]>([]);
  const [addresses, setAddresses] = useState<Address[]>([]);
  const [selectedAddressId, setSelectedAddressId] = useState<number | null>(null);

  // Coupon states
  const [couponCode, setCouponCode] = useState('');
  const [activeCoupon, setActiveCoupon] = useState<string | null>(null);
  const [couponMsg, setCouponMsg] = useState({ text: '', type: '' }); // type: 'success' | 'error'

  // Summary states
  const [summary, setSummary] = useState({
    subtotal: 0,
    tax: 0,
    shipping: 10,
    discount: 0,
    grand_total: 0,
  });

  // Action states
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [createdOrderId, setCreatedOrderId] = useState<number | null>(null);
  const [invoiceNum, setInvoiceNum] = useState<string | null>(null);
  const [paymentStep, setPaymentStep] = useState(false); // true shows mock payment popup/overlay
  const [paymentStatus, setPaymentStatus] = useState<string | null>(null);

  const fetchCheckoutData = async () => {
    try {
      setLoading(true);
      const cart = await cartApi.getCart();
      setCartItems(cart);

      const addrs = await addressesApi.getAddresses();
      setAddresses(addrs);

      const defaultAddr = addrs.find((a: Address) => a.is_default) || addrs[0];
      if (defaultAddr) {
        setSelectedAddressId(defaultAddr.id);
      }
    } catch (err) {
      console.error('Failed to load checkout details:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCheckoutData();
  }, []);

  // Update summary when address or coupon changes
  useEffect(() => {
    if (cartItems.length === 0) return;

    const fetchSummary = async () => {
      try {
        const summaryData = await checkoutApi.getSummary(activeCoupon || undefined);
        setSummary({
          subtotal: Number(summaryData.subtotal),
          tax: Number(summaryData.tax),
          shipping: Number(summaryData.shipping),
          discount: Number(summaryData.discount),
          grand_total: Number(summaryData.grand_total),
        });
      } catch (err) {
        console.error('Error fetching cart summary:', err);
      }
    };

    fetchSummary();
  }, [cartItems, activeCoupon]);

  const handleApplyCoupon = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!couponCode.trim()) return;

    const cartTotal = cartItems.reduce((sum, item) => sum + (item.product.price * item.quantity), 0);

    try {
      const res = await couponsApi.applyCoupon(couponCode, cartTotal);
      if (res.is_valid) {
        setActiveCoupon(res.code);
        setCouponMsg({ text: res.message, type: 'success' });
      } else {
        setActiveCoupon(null);
        setCouponMsg({ text: res.message, type: 'error' });
      }
    } catch (err: any) {
      setCouponMsg({ text: err.message || 'Error applying coupon.', type: 'error' });
    }
  };

  const handlePlaceOrder = async () => {
    if (!selectedAddressId) {
      alert('Please select a shipping address.');
      return;
    }

    if (submitting) return; // Prevent duplicate clicks
    setSubmitting(true);

    try {
      const res = await checkoutApi.checkout({
        shipping_address_id: selectedAddressId,
        coupon_code: activeCoupon || undefined,
      });

      setCreatedOrderId(res.order_id);
      setInvoiceNum(res.invoice_number);
      setPaymentStep(true); // Open mock payment options
    } catch (err: any) {
      alert(err.message || 'Checkout failed.');
    } finally {
      setSubmitting(false);
    }
  };

  const handlePaymentMock = async (success: boolean) => {
    if (!createdOrderId) return;
    try {
      setSubmitting(true);
      if (success) {
        await paymentsApi.mockSuccess(createdOrderId);
        setPaymentStatus('success');
      } else {
        await paymentsApi.mockFailure(createdOrderId);
        setPaymentStatus('failed');
      }
    } catch (err: any) {
      alert(err.message || 'Payment execution failed.');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-96">
        <div className="w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  if (cartItems.length === 0 && !paymentStep) {
    return (
      <div className="max-w-md mx-auto text-center py-16 px-4">
        <svg className="w-16 h-16 mx-auto text-slate-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
        </svg>
        <h2 className="text-2xl font-extrabold text-slate-900 dark:text-white mb-2">Your cart is empty</h2>
        <p className="text-sm text-slate-500 dark:text-slate-400 mb-6">Add items to your cart before proceeding to checkout.</p>
        <button
          onClick={() => navigate('/products')}
          className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-bold transition-colors shadow-md shadow-blue-500/10"
        >
          Continue Shopping
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Title */}
      <h1 className="text-3xl font-black text-slate-900 dark:text-white tracking-tight mb-8">Secure Checkout</h1>

      {/* Main Grid */}
      {!paymentStep ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column: Address and Payment Options */}
          <div className="lg:col-span-2 space-y-6">
            {/* Shipping Address Section */}
            <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-100 dark:border-slate-700 p-6 shadow-sm">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-bold text-slate-900 dark:text-white">1. Shipping Address</h3>
                <button
                  onClick={() => navigate('/address')}
                  className="text-sm font-bold text-blue-650 hover:text-blue-700 flex items-center gap-1"
                >
                  Manage Addresses
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </button>
              </div>

              {addresses.length === 0 ? (
                <div className="text-center py-6 border-2 border-dashed border-slate-200 dark:border-slate-700 rounded-xl">
                  <p className="text-sm text-slate-500 dark:text-slate-400 mb-4">No shipping addresses saved.</p>
                  <button
                    onClick={() => navigate('/address')}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-sm font-bold transition-colors"
                  >
                    Create Address
                  </button>
                </div>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {addresses.map((addr) => (
                    <div
                      key={addr.id}
                      onClick={() => setSelectedAddressId(addr.id)}
                      className={`p-4 rounded-xl border-2 cursor-pointer transition-all ${
                        selectedAddressId === addr.id
                          ? 'border-blue-500 bg-blue-50/20 dark:bg-blue-950/10'
                          : 'border-slate-100 dark:border-slate-700 hover:border-slate-200'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-bold text-slate-900 dark:text-white text-sm">{addr.full_name}</span>
                        {selectedAddressId === addr.id && (
                          <span className="w-4.5 h-4.5 bg-blue-500 rounded-full flex items-center justify-center text-white text-[10px]">
                            ✓
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                        {addr.address_line1}, {addr.address_line2 && `${addr.address_line2}, `}{addr.city}, {addr.state} {addr.postal_code}
                      </p>
                      <p className="text-xs text-slate-500 dark:text-slate-400 mt-2 font-medium">Phone: {addr.phone}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Cart Review Items */}
            <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-100 dark:border-slate-700 p-6 shadow-sm">
              <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-4">2. Review Items</h3>
              <div className="divide-y divide-slate-100 dark:divide-slate-700">
                {cartItems.map((item) => (
                  <div key={item.id} className="flex gap-4 py-4 first:pt-0 last:pb-0">
                    {item.product.image_url ? (
                      <img src={item.product.image_url} alt={item.product.name} className="w-16 h-16 rounded-xl object-cover" />
                    ) : (
                      <div className="w-16 h-16 rounded-xl bg-slate-100 dark:bg-slate-900 flex items-center justify-center text-slate-400">
                        📦
                      </div>
                    )}
                    <div className="flex-1 min-w-0">
                      <h4 className="font-bold text-slate-900 dark:text-white text-sm truncate">{item.product.name}</h4>
                      {item.product.brand && <p className="text-xs text-slate-450 dark:text-slate-400">{item.product.brand}</p>}
                      <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 font-medium">Qty: {item.quantity}</p>
                    </div>
                    <div className="text-right">
                      <span className="font-bold text-slate-900 dark:text-white">${(item.product.price * item.quantity).toFixed(2)}</span>
                      <p className="text-xs text-slate-500 dark:text-slate-400">${item.product.price.toFixed(2)} each</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Right Column: Coupon Box & Final Totals */}
          <div className="space-y-6">
            {/* Promo Codes */}
            <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-100 dark:border-slate-700 p-6 shadow-sm">
              <h3 className="text-md font-bold text-slate-900 dark:text-white mb-3">Apply Promo Code</h3>
              <form onSubmit={handleApplyCoupon} className="flex gap-2">
                <input
                  type="text"
                  placeholder="e.g. WELCOME10"
                  value={couponCode}
                  onChange={(e) => setCouponCode(e.target.value)}
                  className="flex-1 px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm uppercase font-semibold"
                />
                <button
                  type="submit"
                  className="px-4 py-2.5 bg-slate-900 dark:bg-slate-750 hover:bg-slate-800 text-white rounded-xl text-sm font-bold transition-colors"
                >
                  Apply
                </button>
              </form>
              {couponMsg.text && (
                <p className={`text-xs mt-2 font-medium ${couponMsg.type === 'success' ? 'text-green-600' : 'text-red-500'}`}>
                  {couponMsg.text}
                </p>
              )}
            </div>

            {/* Price Calculations */}
            <div className="bg-slate-50 dark:bg-slate-800/50 rounded-2xl border border-slate-100 dark:border-slate-700 p-6 shadow-sm">
              <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-4">Order Summary</h3>
              <div className="space-y-3 text-sm border-b border-slate-100 dark:border-slate-700 pb-4">
                <div className="flex justify-between text-slate-600 dark:text-slate-400">
                  <span>Subtotal</span>
                  <span className="font-semibold text-slate-900 dark:text-white">${summary.subtotal.toFixed(2)}</span>
                </div>
                {summary.discount > 0 && (
                  <div className="flex justify-between text-green-600">
                    <span>Discount {activeCoupon && `(${activeCoupon})`}</span>
                    <span className="font-semibold">-${summary.discount.toFixed(2)}</span>
                  </div>
                )}
                <div className="flex justify-between text-slate-600 dark:text-slate-400">
                  <span>Tax (8%)</span>
                  <span className="font-semibold text-slate-900 dark:text-white">${summary.tax.toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-slate-600 dark:text-slate-400">
                  <span>Shipping</span>
                  <span className="font-semibold text-slate-900 dark:text-white">
                    {summary.shipping === 0 ? 'Free' : `$${summary.shipping.toFixed(2)}`}
                  </span>
                </div>
              </div>
              <div className="flex justify-between items-center pt-4 mb-6">
                <span className="font-bold text-slate-900 dark:text-white">Grand Total</span>
                <span className="text-2xl font-black text-slate-900 dark:text-white">${summary.grand_total.toFixed(2)}</span>
              </div>

              <button
                onClick={handlePlaceOrder}
                disabled={submitting || !selectedAddressId}
                className={`w-full py-4 rounded-xl font-bold transition-all text-center flex items-center justify-center gap-2 ${
                  submitting || !selectedAddressId
                    ? 'bg-slate-200 dark:bg-slate-700 text-slate-400 cursor-not-allowed'
                    : 'bg-blue-600 hover:bg-blue-700 text-white shadow-lg shadow-blue-500/10 active:scale-[0.98]'
                }`}
              >
                {submitting ? 'Processing Checkout...' : 'Confirm & Place Order'}
              </button>
            </div>
          </div>
        </div>
      ) : (
        /* MOCK PAYMENT DIALOG OVERLAY */
        <div className="max-w-md mx-auto bg-white dark:bg-slate-800 rounded-3xl border border-slate-100 dark:border-slate-700 p-8 text-center shadow-lg">
          {!paymentStatus ? (
            <>
              <div className="w-16 h-16 bg-yellow-50 dark:bg-yellow-950/20 rounded-full flex items-center justify-center text-yellow-600 mx-auto mb-4">
                💳
              </div>
              <h2 className="text-xl font-extrabold text-slate-900 dark:text-white mb-2">Simulate Payment Auth</h2>
              <p className="text-sm text-slate-500 dark:text-slate-400 mb-6">
                Your order <strong className="text-slate-750 dark:text-slate-350">{invoiceNum}</strong> has been initialized. Authorize mock payment callback below.
              </p>
              <div className="space-y-3">
                <button
                  onClick={() => handlePaymentMock(true)}
                  disabled={submitting}
                  className="w-full py-3 bg-green-600 hover:bg-green-700 text-white font-bold rounded-xl transition-colors shadow-md shadow-green-500/10"
                >
                  Simulate Payment SUCCESS
                </button>
                <button
                  onClick={() => handlePaymentMock(false)}
                  disabled={submitting}
                  className="w-full py-3 bg-red-650 hover:bg-red-700 text-white font-bold rounded-xl transition-colors shadow-md shadow-red-500/10"
                >
                  Simulate Payment FAILURE
                </button>
              </div>
            </>
          ) : paymentStatus === 'success' ? (
            <>
              <div className="w-16 h-16 bg-green-50 dark:bg-green-950/20 rounded-full flex items-center justify-center text-green-600 mx-auto mb-4">
                ✓
              </div>
              <h2 className="text-2xl font-extrabold text-slate-900 dark:text-white mb-2">Order Confirmed!</h2>
              <p className="text-sm text-slate-500 dark:text-slate-400 mb-6">
                Thank you! Your payment was authorized. Order <strong className="text-slate-750 dark:text-slate-350">{invoiceNum}</strong> is currently Confirmed.
              </p>
              <div className="flex gap-3">
                <button
                  onClick={() => navigate(`/orders/${createdOrderId}`)}
                  className="flex-1 py-3 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl transition-colors"
                >
                  View Order Status
                </button>
                <button
                  onClick={() => navigate('/products')}
                  className="flex-1 py-3 bg-slate-100 hover:bg-slate-200 dark:bg-slate-700 dark:hover:bg-slate-600 text-slate-700 dark:text-slate-200 font-bold rounded-xl transition-colors"
                >
                  Continue Shop
                </button>
              </div>
            </>
          ) : (
            <>
              <div className="w-16 h-16 bg-red-50 dark:bg-red-950/20 rounded-full flex items-center justify-center text-red-650 mx-auto mb-4">
                ✕
              </div>
              <h2 className="text-2xl font-extrabold text-slate-900 dark:text-white mb-2">Payment Failed</h2>
              <p className="text-sm text-slate-500 dark:text-slate-400 mb-6">
                We couldn't authorize payment for invoice <strong className="text-slate-750 dark:text-slate-350">{invoiceNum}</strong>. You can try again or cancel the order.
              </p>
              <div className="flex gap-3">
                <button
                  onClick={() => { setPaymentStatus(null); }}
                  className="flex-1 py-3 bg-blue-650 hover:bg-blue-750 text-white font-bold rounded-xl transition-colors"
                >
                  Retry Payment
                </button>
                <button
                  onClick={() => navigate('/orders')}
                  className="flex-1 py-3 bg-slate-100 hover:bg-slate-200 dark:bg-slate-700 dark:hover:bg-slate-600 text-slate-700 dark:text-slate-200 font-bold rounded-xl transition-colors"
                >
                  View Order History
                </button>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
};
