import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link, Navigate } from 'react-router-dom';
import { Trash2, ShoppingCart, Heart, ArrowRight } from 'lucide-react';
import { wishlistApi, cartApi } from '../services/api';

export const Wishlist: React.FC = () => {
  const queryClient = useQueryClient();
  const isAuthenticated = !!localStorage.getItem('token');
  const [toastMsg, setToastMsg] = useState('');

  // Fetch Wishlist Items query
  const { data: items, isLoading, isError } = useQuery({
    queryKey: ['wishlist'],
    queryFn: wishlistApi.getWishlist,
    enabled: isAuthenticated,
  });

  // Mutations
  const removeMutation = useMutation({
    mutationFn: (productId: number) => wishlistApi.removeFromWishlist(productId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['wishlist'] });
      triggerToast('Removed from wishlist.');
    },
  });

  const moveToCartMutation = useMutation({
    mutationFn: async (productId: number) => {
      await cartApi.addToCart(productId, 1);
      return wishlistApi.removeFromWishlist(productId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['wishlist'] });
      queryClient.invalidateQueries({ queryKey: ['cart'] });
      triggerToast('Moved to shopping cart!');
    },
  });

  const triggerToast = (msg: string) => {
    setToastMsg(msg);
    setTimeout(() => setToastMsg(''), 3000);
  };

  // Redirect guests to login
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

      <div className="mb-8">
        <h1 className="text-3xl font-extrabold text-white tracking-tight">Your Wishlist</h1>
        <p className="mt-1 text-sm text-muted-foreground">Manage your saved products and move them to cart</p>
      </div>

      {isLoading && (
        <div className="text-center py-12 text-muted-foreground animate-pulse">Loading wishlist...</div>
      )}

      {isError && (
        <div className="text-center py-12 text-red-400">Failed to load your wishlist.</div>
      )}

      {items && items.length === 0 && (
        <div className="flex flex-col items-center justify-center rounded-2xl border border-border bg-card p-16 text-center">
          <Heart className="h-12 w-12 text-muted-foreground mb-4" />
          <h3 className="text-lg font-bold text-white mb-1">Your wishlist is empty</h3>
          <p className="text-sm text-muted-foreground mb-6">Explore our catalog and save items for later</p>
          <Link
            to="/products"
            className="flex items-center space-x-2 rounded-lg bg-primary px-6 py-3 text-sm font-semibold text-white transition-all hover:bg-primary/95"
          >
            <span>Explore Products</span>
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      )}

      {items && items.length > 0 && (
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
          {items.map((item: any) => (
            <div
              key={item.id}
              className="flex flex-col justify-between overflow-hidden rounded-2xl border border-border bg-card p-4 transition-all hover:border-primary/50"
            >
              <div>
                <Link to={`/products/${item.product_id}`}>
                  <div className="h-40 w-full overflow-hidden rounded-lg bg-muted flex items-center justify-center text-xs text-muted-foreground font-semibold uppercase mb-3">
                    {item.product?.image_url ? (
                      <img
                        src={item.product.image_url}
                        alt={item.product.name}
                        className="h-full w-full object-cover"
                      />
                    ) : (
                      <span>{item.product?.brand || 'Wishlist item'}</span>
                    )}
                  </div>
                  <span className="text-2xs font-bold text-primary uppercase tracking-wider">
                    {item.product?.brand}
                  </span>
                  <h3 className="font-bold text-white leading-tight line-clamp-1 hover:text-primary transition-colors">
                    {item.product?.name}
                  </h3>
                </Link>
                <div className="text-lg font-black text-white mt-1 mb-4">
                  ${item.product?.price?.toFixed(2)}
                </div>
              </div>

              <div className="flex space-x-2 mt-auto border-t border-border/50 pt-3">
                <button
                  onClick={() => moveToCartMutation.mutate(item.product_id)}
                  disabled={item.product?.stock === 0}
                  className="flex-grow flex items-center justify-center space-x-1.5 rounded-lg bg-primary py-2 text-xs font-semibold text-white transition-all hover:bg-primary/95 disabled:opacity-50"
                >
                  <ShoppingCart className="h-3.5 w-3.5" />
                  <span>Move to Cart</span>
                </button>
                <button
                  onClick={() => removeMutation.mutate(item.product_id)}
                  className="rounded-lg border border-border bg-card p-2 text-muted-foreground hover:border-destructive hover:text-red-400"
                  aria-label="Remove"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
