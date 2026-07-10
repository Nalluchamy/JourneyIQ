import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link, Navigate } from 'react-router-dom';
import { Trash2, ShoppingCart, ArrowRight, Minus, Plus, RefreshCw } from 'lucide-react';
import { cartApi } from '../services/api';

export const Cart: React.FC = () => {
  const queryClient = useQueryClient();
  const isAuthenticated = !!localStorage.getItem('token');
  const [toastMsg, setToastMsg] = useState('');

  // Fetch Cart Items
  const { data: items, isLoading, isError } = useQuery({
    queryKey: ['cart'],
    queryFn: cartApi.getCart,
    enabled: isAuthenticated,
  });

  // Mutations
  const updateQtyMutation = useMutation({
    mutationFn: ({ productId, qty }: { productId: number; qty: number }) =>
      cartApi.updateQuantity(productId, qty),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cart'] });
    },
    onError: (err: any) => {
      triggerToast(err.message || 'Failed to update quantity.');
    },
  });

  const removeMutation = useMutation({
    mutationFn: (productId: number) => cartApi.removeFromCart(productId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cart'] });
      triggerToast('Item removed from cart.');
    },
  });

  const clearCartMutation = useMutation({
    mutationFn: cartApi.clearCart,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cart'] });
      triggerToast('Cart cleared.');
    },
  });

  const triggerToast = (msg: string) => {
    setToastMsg(msg);
    setTimeout(() => setToastMsg(''), 3000);
  };

  // Calculations
  const calculateSubtotal = () => {
    return items?.reduce((sum: number, item: any) => sum + item.product.price * item.quantity, 0) || 0;
  };

  const subtotal = calculateSubtotal();
  const estimatedTax = subtotal * 0.08; // 8% sales tax
  const grandTotal = subtotal + estimatedTax;

  // Redirect guest users
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      {/* Toast Alert */}
      {toastMsg && (
        <div className="fixed bottom-5 right-5 z-50 rounded-lg bg-primary px-6 py-3.5 text-sm font-semibold text-white shadow-lg animate-in fade-in">
          {toastMsg}
        </div>
      )}

      <div className="mb-8 flex flex-col items-start justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight">Shopping Cart</h1>
          <p className="mt-1 text-sm text-muted-foreground">Review items and adjust quantities before placing order</p>
        </div>
        {items && items.length > 0 && (
          <button
            onClick={() => clearCartMutation.mutate()}
            className="text-xs font-bold text-red-400 border border-destructive/30 rounded-lg px-3 py-2 hover:bg-destructive/10"
          >
            Clear Cart
          </button>
        )}
      </div>

      {isLoading && (
        <div className="text-center py-12 text-muted-foreground animate-pulse">Loading shopping cart...</div>
      )}

      {isError && (
        <div className="text-center py-12 text-red-400">Failed to load shopping cart.</div>
      )}

      {items && items.length === 0 && (
        <div className="flex flex-col items-center justify-center rounded-2xl border border-border bg-card p-16 text-center">
          <ShoppingCart className="h-12 w-12 text-muted-foreground mb-4" />
          <h3 className="text-lg font-bold text-white mb-1">Your cart is empty</h3>
          <p className="text-sm text-muted-foreground mb-6">Explore products and add them to your shopping cart</p>
          <Link
            to="/products"
            className="flex items-center space-x-2 rounded-lg bg-primary px-6 py-3 text-sm font-semibold text-white transition-all hover:bg-primary/95"
          >
            <span>Browse Products</span>
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      )}

      {items && items.length > 0 && (
        <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
          {/* Cart Items List */}
          <div className="lg:col-span-2 space-y-4">
            {items.map((item: any) => (
              <div
                key={item.id}
                className="flex items-center justify-between rounded-xl border border-border bg-card p-4 gap-4"
              >
                {/* Image Placeholder */}
                <div className="h-20 w-20 flex-shrink-0 overflow-hidden rounded-lg bg-muted flex items-center justify-center text-2xs text-muted-foreground uppercase font-bold text-center p-1">
                  {item.product.image_url ? (
                    <img src={item.product.image_url} alt={item.product.name} className="h-full w-full object-cover" />
                  ) : (
                    <span>{item.product.brand || 'Product'}</span>
                  )}
                </div>

                {/* Name / Brand */}
                <div className="flex-grow min-w-0">
                  <span className="text-3xs font-bold text-primary uppercase tracking-wider">{item.product.brand}</span>
                  <Link to={`/products/${item.product_id}`}>
                    <h4 className="font-bold text-white text-sm leading-tight hover:text-primary transition-colors truncate">
                      {item.product.name}
                    </h4>
                  </Link>
                  <span className="text-xs font-black text-white block mt-1">${item.product.price.toFixed(2)}</span>
                </div>

                {/* Quantity Controls */}
                <div className="flex items-center space-x-1 bg-black/35 rounded-lg border border-border p-1">
                  <button
                    disabled={item.quantity <= 1}
                    onClick={() => updateQtyMutation.mutate({ productId: item.product_id, qty: item.quantity - 1 })}
                    className="p-1.5 text-muted-foreground hover:text-white disabled:opacity-30"
                    aria-label="Decrease quantity"
                  >
                    <Minus className="h-3.5 w-3.5" />
                  </button>
                  <span className="px-2 text-xs font-bold text-white min-w-[20px] text-center">{item.quantity}</span>
                  <button
                    disabled={item.quantity >= item.product.stock}
                    onClick={() => updateQtyMutation.mutate({ productId: item.product_id, qty: item.quantity + 1 })}
                    className="p-1.5 text-muted-foreground hover:text-white disabled:opacity-30"
                    aria-label="Increase quantity"
                  >
                    <Plus className="h-3.5 w-3.5" />
                  </button>
                </div>

                {/* Delete Button */}
                <button
                  onClick={() => removeMutation.mutate(item.product_id)}
                  className="rounded-lg border border-border bg-card p-2.5 text-muted-foreground hover:border-destructive hover:text-red-400"
                  aria-label="Remove item"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>

          {/* Pricing Totals Box */}
          <div className="rounded-2xl border border-border bg-card p-6 h-fit space-y-6">
            <h3 className="font-extrabold text-white text-lg border-b border-border pb-4">Order Summary</h3>

            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Subtotal</span>
                <span className="font-semibold text-white">${subtotal.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Estimated Tax (8%)</span>
                <span className="font-semibold text-white">${estimatedTax.toFixed(2)}</span>
              </div>
              <div className="flex justify-between border-t border-border pt-4 text-base font-extrabold">
                <span className="text-white">Order Total</span>
                <span className="text-primary">${grandTotal.toFixed(2)}</span>
              </div>
            </div>

            <button
              onClick={() => triggerToast('Checkout is disabled for Phase 4 (as specified by user requirements).')}
              className="w-full flex items-center justify-center space-x-2 rounded-xl bg-primary py-3 text-sm font-bold text-white transition-all hover:bg-primary/90"
            >
              <span>Proceed to Checkout</span>
              <ArrowRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
