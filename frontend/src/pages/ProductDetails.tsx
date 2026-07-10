import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Heart, ShoppingCart, Star, MessageSquare, ArrowLeft, Eye } from 'lucide-react';
import { productsApi, wishlistApi, cartApi, reviewsApi, eventsApi, getOrCreateSessionId } from '../services/api';

export const ProductDetails: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const productId = Number(id);
  const queryClient = useQueryClient();

  const [quantity, setQuantity] = useState(1);
  const [rating, setRating] = useState(5);
  const [reviewText, setReviewText] = useState('');
  const [toastMsg, setToastMsg] = useState('');
  const [reviewError, setReviewError] = useState('');

  const isAuthenticated = !!localStorage.getItem('token');
  const sessionId = getOrCreateSessionId();

  // Track product view event on load
  useEffect(() => {
    if (productId) {
      eventsApi.trackEvent('product_view', `/products/${productId}`, productId);
    }
  }, [productId]);

  // Fetch product data
  const { data: product, isLoading, isError } = useQuery({
    queryKey: ['product', productId],
    queryFn: () => productsApi.getProduct(productId),
    enabled: !!productId,
  });

  // Fetch reviews data
  const { data: reviews } = useQuery({
    queryKey: ['reviews', productId],
    queryFn: () => reviewsApi.getReviews(productId),
    enabled: !!productId,
  });

  // Fetch recently viewed products
  const { data: recentViews } = useQuery({
    queryKey: ['recentViews', sessionId],
    queryFn: () => eventsApi.getRecentViews(sessionId),
  });

  // Fetch related products (same category)
  const { data: relatedProductsData } = useQuery({
    queryKey: ['relatedProducts', product?.category_id],
    queryFn: () =>
      productsApi.getProducts({
        category_id: product?.category_id || undefined,
        size: 5,
      }),
    enabled: !!product?.category_id,
  });

  // Filter out current product from related list
  const relatedProducts = relatedProductsData?.items.filter((p: any) => p.id !== productId) || [];

  // Check wishlist status
  const { data: wishlistItems } = useQuery({
    queryKey: ['wishlist'],
    queryFn: wishlistApi.getWishlist,
    enabled: isAuthenticated,
  });

  const isProductInWishlist = wishlistItems?.some((item: any) => item.product_id === productId);

  // Mutations
  const toggleWishlistMutation = useMutation({
    mutationFn: async () => {
      if (isProductInWishlist) {
        return wishlistApi.removeFromWishlist(productId);
      } else {
        return wishlistApi.addToWishlist(productId);
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['wishlist'] });
      triggerToast('Wishlist updated!');
    },
    onError: (err: any) => {
      triggerToast(err.message || 'Auth required.');
    },
  });

  const addToCartMutation = useMutation({
    mutationFn: () => cartApi.addToCart(productId, quantity),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cart'] });
      triggerToast('Product added to cart!');
    },
    onError: (err: any) => {
      triggerToast(err.message || 'Auth required.');
    },
  });

  const createReviewMutation = useMutation({
    mutationFn: (data: any) => reviewsApi.createReview(productId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reviews', productId] });
      setReviewText('');
      setReviewError('');
      triggerToast('Review submitted successfully!');
    },
    onError: (err: any) => {
      setReviewError(err.message || 'Could not post review. Did you purchase this product?');
    },
  });

  const triggerToast = (msg: string) => {
    setToastMsg(msg);
    setTimeout(() => setToastMsg(''), 3000);
  };

  const handleReviewSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setReviewError('');
    if (!isAuthenticated) {
      setReviewError('You must sign in to leave reviews.');
      return;
    }
    createReviewMutation.mutate({ rating, review: reviewText });
  };

  if (isLoading) {
    return (
      <div className="mx-auto max-w-7xl px-4 py-16 text-center text-muted-foreground animate-pulse">
        Loading product details...
      </div>
    );
  }

  if (isError || !product) {
    return (
      <div className="mx-auto max-w-7xl px-4 py-16 text-center text-red-400">
        Product not found or failed to load.
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      {/* Toast Alert */}
      {toastMsg && (
        <div className="fixed bottom-5 right-5 z-50 rounded-lg bg-primary px-6 py-3.5 text-sm font-semibold text-white shadow-lg animate-in fade-in">
          {toastMsg}
        </div>
      )}

      {/* Back button */}
      <Link to="/products" className="mb-6 flex items-center space-x-1.5 text-sm text-muted-foreground hover:text-white">
        <ArrowLeft className="h-4 w-4" />
        <span>Back to Products</span>
      </Link>

      <div className="grid grid-cols-1 gap-8 md:grid-cols-2">
        {/* Product Image Gallery */}
        <div className="relative rounded-2xl border border-border bg-card p-6 flex items-center justify-center min-h-[350px]">
          {product.image_url ? (
            <img
              src={product.image_url}
              alt={product.name}
              className="max-h-[400px] rounded-lg object-contain"
            />
          ) : (
            <span className="text-xl font-bold uppercase tracking-wider text-muted-foreground">
              {product.brand || 'Storefront Gallery'}
            </span>
          )}
        </div>

        {/* Product Info Description */}
        <div className="space-y-6">
          <div>
            <span className="text-xs font-bold text-primary uppercase tracking-wider">
              {product.brand || 'No Brand'}
            </span>
            <h1 className="text-4xl font-extrabold text-white tracking-tight mt-1">{product.name}</h1>
          </div>

          <div className="flex items-center space-x-4 border-y border-border py-4">
            <span className="text-3xl font-black text-white">${Number(product.price).toFixed(2)}</span>
            <span
              className={`rounded px-2.5 py-1 text-xs font-extrabold uppercase tracking-wider ${
                product.stock > 0 ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'
              }`}
            >
              {product.stock > 0 ? `${product.stock} In Stock` : 'Out of Stock'}
            </span>
          </div>

          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-1">Description</h3>
            <p className="text-sm text-muted-foreground leading-relaxed">
              {product.description || 'No description available for this item.'}
            </p>
          </div>

          {/* Quantity and Actions */}
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
            {product.stock > 0 && (
              <div className="flex items-center space-x-2">
                <span className="text-xs font-bold text-muted-foreground uppercase">Qty:</span>
                <select
                  value={quantity}
                  onChange={(e) => setQuantity(Number(e.target.value))}
                  className="rounded-lg border border-border bg-card px-3 py-1.5 text-sm text-white focus:outline-none focus:ring-1 focus:ring-primary"
                >
                  {Array.from({ length: Math.min(product.stock, 5) }).map((_, i) => (
                    <option key={i + 1} value={i + 1}>
                      {i + 1}
                    </option>
                  ))}
                </select>
              </div>
            )}

            <button
              onClick={() => addToCartMutation.mutate()}
              disabled={product.stock === 0}
              className="flex-grow flex items-center justify-center space-x-2 rounded-xl bg-primary py-3 text-sm font-bold text-white transition-all hover:bg-primary/90 disabled:opacity-50"
            >
              <ShoppingCart className="h-5 w-5" />
              <span>Add to Shopping Cart</span>
            </button>

            <button
              onClick={() => toggleWishlistMutation.mutate()}
              className="rounded-xl border border-border bg-card p-3 transition-colors hover:bg-muted"
              aria-label="Add to Wishlist"
            >
              <Heart className={`h-5 w-5 ${isProductInWishlist ? 'fill-primary text-primary' : 'text-white'}`} />
            </button>
          </div>
        </div>
      </div>

      {/* Reviews Section */}
      <div className="mt-16 border-t border-border pt-12">
        <h2 className="text-2xl font-bold text-white mb-6 flex items-center space-x-2">
          <MessageSquare className="h-6 w-6 text-primary" />
          <span>Product Reviews</span>
        </h2>

        <div className="grid grid-cols-1 gap-8 md:grid-cols-3">
          {/* Review List */}
          <div className="md:col-span-2 space-y-6">
            {!reviews || reviews.length === 0 ? (
              <p className="text-sm text-muted-foreground">No reviews yet for this product. Be the first to buy and review it!</p>
            ) : (
              reviews.map((rev: any) => (
                <div key={rev.id} className="rounded-xl border border-border bg-card p-5 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-white text-sm">{rev.user?.full_name || 'Anonymous User'}</span>
                    <div className="flex items-center text-yellow-400">
                      {Array.from({ length: rev.rating }).map((_, i) => (
                        <Star key={i} className="h-3.5 w-3.5 fill-current" />
                      ))}
                    </div>
                  </div>
                  <p className="text-sm text-muted-foreground leading-relaxed">{rev.review || 'No comment left.'}</p>
                </div>
              ))
            )}
          </div>

          {/* Leave a Review Form */}
          <div className="rounded-xl border border-border bg-card p-6 space-y-4 h-fit">
            <h3 className="font-bold text-white text-lg">Write a Review</h3>
            <p className="text-xs text-muted-foreground leading-relaxed">
              Only verified purchasers who completed an order for this product can leave reviews.
            </p>

            {reviewError && (
              <div className="rounded bg-destructive/15 border border-destructive/20 p-3 text-xs text-red-400">
                {reviewError}
              </div>
            )}

            <form onSubmit={handleReviewSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-muted-foreground uppercase mb-1">Rating</label>
                <div className="flex space-x-1">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <button
                      key={star}
                      type="button"
                      onClick={() => setRating(star)}
                      className="text-yellow-400 focus:outline-none"
                    >
                      <Star className={`h-6 w-6 ${rating >= star ? 'fill-current' : ''}`} />
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-muted-foreground uppercase mb-1">Comment</label>
                <textarea
                  value={reviewText}
                  onChange={(e) => setReviewText(e.target.value)}
                  placeholder="Share your thoughts about this product..."
                  rows={4}
                  className="w-full rounded-lg border border-border bg-black/30 p-3 text-sm text-white focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>

              <button
                type="submit"
                className="w-full rounded-lg bg-primary py-2 text-xs font-semibold text-white transition-all hover:bg-primary/90"
              >
                Submit Review
              </button>
            </form>
          </div>
        </div>
      </div>

      {/* Related Products Section */}
      {relatedProducts.length > 0 && (
        <div className="mt-16 border-t border-border pt-12">
          <h2 className="text-2xl font-bold text-white mb-6">Related Products</h2>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            {relatedProducts.map((p: any) => (
              <Link
                key={p.id}
                to={`/products/${p.id}`}
                className="group rounded-xl border border-border bg-card p-3 transition-all hover:border-primary/50"
              >
                <div className="h-32 w-full rounded bg-muted flex items-center justify-center text-xs text-muted-foreground mb-2">
                  <span>{p.brand}</span>
                </div>
                <h4 className="font-bold text-white text-xs leading-snug line-clamp-1 group-hover:text-primary transition-colors">
                  {p.name}
                </h4>
                <span className="font-black text-white text-xs">${Number(p.price).toFixed(2)}</span>
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* Recently Viewed Products Section */}
      {recentViews && recentViews.length > 0 && (
        <div className="mt-16 border-t border-border pt-12">
          <h2 className="text-2xl font-bold text-white mb-6 flex items-center space-x-2">
            <Eye className="h-5 w-5 text-primary" />
            <span>Recently Viewed</span>
          </h2>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-5">
            {recentViews.map((view: any) => (
              <Link
                key={view.id}
                to={`/products/${view.product_id}`}
                className="group rounded-xl border border-border bg-card p-3 transition-all hover:border-primary/50"
              >
                <div className="h-28 w-full rounded bg-muted flex items-center justify-center text-xs text-muted-foreground mb-2">
                  <span>{view.product?.brand || 'Viewed'}</span>
                </div>
                <h4 className="font-bold text-white text-xs leading-snug line-clamp-1 group-hover:text-primary transition-colors">
                  {view.product?.name || 'Product'}
                </h4>
                <span className="font-black text-white text-xs">${view.product?.price?.toFixed(2) || '0.00'}</span>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
