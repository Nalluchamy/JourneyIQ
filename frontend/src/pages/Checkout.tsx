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
        <h2 className="text-2xl font-extrabold text-white mb-2">Your cart is empty</h2>
        <p className="text-sm text-muted-foreground mb-6">Add items to your cart before proceeding to checkout.</p>
        <button
          onClick={() => navigate('/products')}
          className="px-6 py-3 bg-brand-gradient text-white rounded-xl font-bold transition-all hover:opacity-90 shadow-lg shadow-indigo-500/20"
        >
          Continue Shopping
        </button>
      </div>
    );
  }

  // Determine current active step for animated progress indicator
  const currentStep = paymentStatus === 'success' ? 3 : (paymentStep ? 2 : 1);

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 relative">
      {/* Multi-step progress bar with animations */}
      <div className="mb-12 max-w-2xl mx-auto">
        <div className="flex items-center justify-between text-xs font-black uppercase tracking-wider text-muted-foreground mb-4">
          <span className={currentStep >= 1 ? 'text-cyan-400' : ''}>1. Shipping</span>
          <span className={currentStep >= 2 ? 'text-indigo-400' : ''}>2. Payment</span>
          <span className={currentStep >= 3 ? 'text-emerald-400' : ''}>3. Confirmed</span>
        </div>
        <div className="h-2 w-full bg-white/5 rounded-full overflow-hidden border border-white/5">
          <div 
            className="h-full bg-brand-gradient transition-all duration-700 ease-out" 
            style={{ width: currentStep === 1 ? '33.3%' : (currentStep === 2 ? '66.6%' : '100%') }}
          />
        </div>
      </div>

      {currentStep !== 3 && (
        <h1 className="text-3xl font-black text-white tracking-tight mb-8">Secure Checkout</h1>
      )}

      {/* Main Grid */}
      {!paymentStep ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column: Address and Payment Options */}
          <div className="lg:col-span-2 space-y-6">
            {/* Shipping Address Section - Glassmorphism */}
            <div className="bg-white/5 backdrop-blur-md rounded-2xl border border-white/10 p-6 shadow-xl">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-bold text-white">1. Shipping Address</h3>
                <button
                  onClick={() => navigate('/address')}
                  className="text-sm font-bold text-cyan-400 hover:underline flex items-center gap-1"
                >
                  Manage Addresses
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </button>
              </div>

              {addresses.length === 0 ? (
                <div className="text-center py-6 border-2 border-dashed border-white/10 rounded-xl">
                  <p className="text-sm text-muted-foreground mb-4">No shipping addresses saved.</p>
                  <button
                    onClick={() => navigate('/address')}
                    className="px-4 py-2 bg-brand-gradient text-white rounded-xl text-sm font-bold transition-all hover:opacity-90"
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
                      className={`p-4 rounded-xl border cursor-pointer transition-all ${
                        selectedAddressId === addr.id
                          ? 'border-cyan-500 bg-cyan-500/10'
                          : 'border-white/10 hover:border-white/20 bg-black/25'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-bold text-white text-sm">{addr.full_name}</span>
                        {selectedAddressId === addr.id && (
                          <span className="w-4.5 h-4.5 bg-cyan-500 rounded-full flex items-center justify-center text-white text-[10px] px-1 font-bold">
                            ✓
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-muted-foreground leading-relaxed">
                        {addr.address_line1}, {addr.address_line2 && `${addr.address_line2}, `}{addr.city}, {addr.state} {addr.postal_code}
                      </p>
                      <p className="text-xs text-slate-500 mt-2 font-medium">Phone: {addr.phone}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Cart Review Items - Glassmorphism */}
            <div className="bg-white/5 backdrop-blur-md rounded-2xl border border-white/10 p-6 shadow-xl">
              <h3 className="text-lg font-bold text-white mb-4">2. Review Items</h3>
              <div className="divide-y divide-white/10">
                {cartItems.map((item) => (
                  <div key={item.id} className="flex gap-4 py-4 first:pt-0 last:pb-0">
                    {item.product.image_url ? (
                      <img src={item.product.image_url} alt={item.product.name} className="w-16 h-16 rounded-xl object-cover border border-white/5" />
                    ) : (
                      <div className="w-16 h-16 rounded-xl bg-black/40 flex items-center justify-center text-slate-400">
                        📦
                      </div>
                    )}
                    <div className="flex-1 min-w-0">
                      <h4 className="font-bold text-white text-sm truncate">{item.product.name}</h4>
                      {item.product.brand && <p className="text-xs text-cyan-400">{item.product.brand}</p>}
                      <p className="text-xs text-muted-foreground mt-1 font-medium">Qty: {item.quantity}</p>
                    </div>
                    <div className="text-right">
                      <span className="font-bold text-white">${(item.product.price * item.quantity).toFixed(2)}</span>
                      <p className="text-xs text-muted-foreground">${item.product.price.toFixed(2)} each</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Right Column: Coupon Box & Floating Summary Card */}
          <div className="space-y-6">
            {/* Promo Codes */}
            <div className="bg-white/5 backdrop-blur-md rounded-2xl border border-white/10 p-6 shadow-xl">
              <h3 className="text-md font-bold text-white mb-3">Apply Promo Code</h3>
              <form onSubmit={handleApplyCoupon} className="flex gap-2">
                <input
                  type="text"
                  placeholder="e.g. WELCOME10"
                  value={couponCode}
                  onChange={(e) => setCouponCode(e.target.value)}
                  className="flex-1 px-4 py-2.5 rounded-xl border border-white/10 bg-black/40 text-white focus:outline-none focus:ring-1 focus:ring-cyan-500 text-sm uppercase font-semibold"
                />
                <button
                  type="submit"
                  className="px-4 py-2.5 bg-white/10 hover:bg-white/20 text-white rounded-xl text-sm font-bold transition-all border border-white/10"
                >
                  Apply
                </button>
              </form>
              {couponMsg.text && (
                <p className={`text-xs mt-2 font-bold ${couponMsg.type === 'success' ? 'text-emerald-450' : 'text-red-400'}`}>
                  {couponMsg.text}
                </p>
              )}
            </div>

            {/* Floating Price Calculations Summary Card */}
            <div className="sticky top-24 bg-white/5 backdrop-blur-lg rounded-2xl border border-white/10 p-6 shadow-2xl space-y-6">
              <h3 className="text-lg font-bold text-white border-b border-white/10 pb-3">Order Summary</h3>
              <div className="space-y-3 text-sm border-b border-white/10 pb-4">
                <div className="flex justify-between text-muted-foreground">
                  <span>Subtotal</span>
                  <span className="font-semibold text-white">${summary.subtotal.toFixed(2)}</span>
                </div>
                {summary.discount > 0 && (
                  <div className="flex justify-between text-emerald-450">
                    <span>Discount {activeCoupon && `(${activeCoupon})`}</span>
                    <span className="font-semibold">-${summary.discount.toFixed(2)}</span>
                  </div>
                )}
                <div className="flex justify-between text-muted-foreground">
                  <span>Tax (8%)</span>
                  <span className="font-semibold text-white">${summary.tax.toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-muted-foreground">
                  <span>Shipping</span>
                  <span className="font-semibold text-white">
                    {summary.shipping === 0 ? 'Free' : `$${summary.shipping.toFixed(2)}`}
                  </span>
                </div>
              </div>
              <div className="flex justify-between items-center pt-2 mb-6">
                <span className="font-bold text-white">Grand Total</span>
                <span className="text-2xl font-black text-cyan-400">${summary.grand_total.toFixed(2)}</span>
              </div>

              <button
                onClick={handlePlaceOrder}
                disabled={submitting || !selectedAddressId}
                className={`w-full py-4 rounded-xl font-bold transition-all text-center flex items-center justify-center gap-2 ${
                  submitting || !selectedAddressId
                    ? 'bg-white/5 border border-white/5 text-muted-foreground cursor-not-allowed'
                    : 'bg-brand-gradient text-white shadow-lg shadow-indigo-500/25 active:scale-[0.98]'
                }`}
              >
                {submitting ? 'Processing Checkout...' : 'Confirm & Place Order'}
              </button>
            </div>
          </div>
        </div>
      ) : (
        /* MOCK PAYMENT DIALOG OVERLAY & CELEBRATION BADGES */
        <div className="max-w-md mx-auto bg-white/5 backdrop-blur-md rounded-3xl border border-white/10 p-8 text-center shadow-2xl relative overflow-hidden">
          {!paymentStatus ? (
            <>
              {/* Payment Loading Orb animation */}
              <div className="relative w-20 h-20 mx-auto mb-6 flex items-center justify-center">
                <div className="absolute inset-0 rounded-full border-4 border-indigo-500/20 border-t-indigo-500 animate-spin" />
                <span className="text-3xl">💳</span>
              </div>
              <h2 className="text-xl font-extrabold text-white mb-2">Simulate Payment Auth</h2>
              <p className="text-sm text-muted-foreground mb-6 leading-relaxed">
                Your order <strong className="text-white">{invoiceNum}</strong> has been initialized. Authorize mock payment callback below.
              </p>
              <div className="space-y-3">
                <button
                  onClick={() => handlePaymentMock(true)}
                  disabled={submitting}
                  className="w-full py-3 bg-brand-gradient text-white font-bold rounded-xl transition-all shadow-lg hover:opacity-95"
                >
                  Simulate Payment SUCCESS
                </button>
                <button
                  onClick={() => handlePaymentMock(false)}
                  disabled={submitting}
                  className="w-full py-3 bg-red-600/30 hover:bg-red-600/50 text-white font-bold rounded-xl transition-all border border-red-500/20"
                >
                  Simulate Payment FAILURE
                </button>
              </div>
            </>
          ) : paymentStatus === 'success' ? (
            /* 3. ORDER CONFIRMATION CELEBRATORY SCREEN WITH 3D CHECKMARK BADGE */
            <div className="space-y-6 py-4">
              {/* 3D celebratory checkmark badge */}
              <div className="relative w-24 h-24 mx-auto mb-6 flex items-center justify-center">
                {/* Glowing expanding pulse rings */}
                <div className="absolute inset-0 rounded-full bg-emerald-500/20 animate-ping duration-1000" />
                <div className="absolute -inset-2 rounded-full border border-emerald-500/30 animate-pulse" />
                
                {/* 3D badge container */}
                <div 
                  className="h-20 w-20 rounded-full bg-gradient-to-tr from-emerald-500 to-teal-400 flex items-center justify-center shadow-lg shadow-emerald-500/50 text-white font-black text-4xl border border-white/20 transform rotate-6 transition-transform"
                  style={{ transform: 'perspective(500px) rotateX(15deg) rotateY(15deg)' }}
                >
                  ✓
                </div>
              </div>

              <h2 className="text-3xl font-black text-white tracking-tight">Order Confirmed!</h2>
              <p className="text-sm text-muted-foreground leading-relaxed">
                Thank you! Your payment was authorized. Order <strong className="text-white">{invoiceNum}</strong> is currently Confirmed.
              </p>
              <div className="flex gap-3 pt-4">
                <button
                  onClick={() => navigate(`/orders/${createdOrderId}`)}
                  className="flex-1 py-3 bg-brand-gradient text-white font-bold rounded-xl transition-all"
                >
                  View Order Status
                </button>
                <button
                  onClick={() => navigate('/products')}
                  className="flex-1 py-3 bg-white/5 hover:bg-white/10 text-white border border-white/10 font-bold rounded-xl transition-all"
                >
                  Continue Shopping
                </button>
              </div>
            </div>
          ) : (
            <>
              <div className="w-16 h-16 bg-red-500/10 border border-red-500/20 rounded-full flex items-center justify-center text-red-400 mx-auto mb-4 text-2xl font-bold">
                ✕
              </div>
              <h2 className="text-2xl font-extrabold text-white mb-2">Payment Failed</h2>
              <p className="text-sm text-muted-foreground mb-6 leading-relaxed">
                We couldn't authorize payment for invoice <strong className="text-white">{invoiceNum}</strong>. You can try again or cancel the order.
              </p>
              <div className="flex gap-3">
                <button
                  onClick={() => { setPaymentStatus(null); }}
                  className="flex-1 py-3 bg-brand-gradient text-white font-bold rounded-xl transition-all"
                >
                  Retry Payment
                </button>
                <button
                  onClick={() => navigate('/orders')}
                  className="flex-1 py-3 bg-white/5 hover:bg-white/10 border border-white/10 text-white font-bold rounded-xl transition-all"
                >
                  Order History
                </button>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
};

