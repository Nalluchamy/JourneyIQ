import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Heart, ShoppingCart, Star, MessageSquare, ArrowLeft, Eye } from 'lucide-react';
import { productsApi, wishlistApi, cartApi, reviewsApi, eventsApi, getOrCreateSessionId, recommendationsApi } from '../services/api';
import { useNotification } from '../context/NotificationContext';

export const ProductDetails: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const productId = Number(id);
  const queryClient = useQueryClient();

  const [quantity, setQuantity] = useState(1);
  const [rating, setRating] = useState(5);
  const [reviewText, setReviewText] = useState('');
  const { showNotification } = useNotification();
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

  // Fetch similar products
  const { data: similarProducts } = useQuery({
    queryKey: ['similarProducts', productId],
    queryFn: () => recommendationsApi.getSimilar(productId),
    enabled: !!productId,
  });

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
      showNotification('Wishlist updated!', 'success');
    },
    onError: (err: any) => {
      showNotification(err.message || 'Auth required.', 'error');
    },
  });

  const addToCartMutation = useMutation({
    mutationFn: () => cartApi.addToCart(productId, quantity),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cart'] });
      showNotification('Product added to cart!', 'success');
    },
    onError: (err: any) => {
      showNotification(err.message || 'Auth required.', 'error');
    },
  });

  const createReviewMutation = useMutation({
    mutationFn: (data: any) => reviewsApi.createReview(productId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reviews', productId] });
      setReviewText('');
      setReviewError('');
      showNotification('Review submitted successfully!', 'success');
    },
    onError: (err: any) => {
      setReviewError(err.message || 'Could not post review. Did you purchase this product?');
    },
  });

  const handleReviewSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setReviewError('');
    if (!isAuthenticated) {
      setReviewError('You must sign in to leave reviews.');
      return;
    }
    createReviewMutation.mutate({ rating, review: reviewText });
  };

  // 360 degree rotation simulation state
  const [rotation, setRotation] = useState(0);
  const [isDragging, setIsDragging] = useState(false);
  const [startX, setStartX] = useState(0);

  // Active gallery image index
  const [activeImgIndex, setActiveImgIndex] = useState(0);

  const handleMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true);
    setStartX(e.clientX);
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging) return;
    const deltaX = e.clientX - startX;
    // Rotate 1 degree per 2 pixels dragged
    setRotation((prev) => {
      let next = prev + deltaX * 0.8;
      if (next < 0) next += 360;
      return next % 360;
    });
    setStartX(e.clientX);
  };

  const handleMouseUpOrLeave = () => {
    setIsDragging(false);
  };

  // Mock angles/sides of a product for 360 view
  // Since we only have one image, we can apply custom CSS 3D distortions based on rotation to simulate depth!

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
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8 relative pb-24">


      {/* Back button */}
      <Link to="/products" className="mb-6 inline-flex items-center space-x-1.5 text-sm text-muted-foreground hover:text-white">
        <ArrowLeft className="h-4 w-4" />
        <span>Back to Products</span>
      </Link>

      <div className="grid grid-cols-1 gap-8 md:grid-cols-2">
        {/* Left: 360-rotation viewer & Depth-layered gallery */}
        <div className="space-y-6">
          {/* 360°-Rotation Viewer Container */}
          <div 
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUpOrLeave}
            onMouseLeave={handleMouseUpOrLeave}
            className={`relative rounded-3xl border border-white/10 bg-white/5 p-6 flex flex-col items-center justify-center min-h-[380px] cursor-grab select-none overflow-hidden backdrop-blur-md ${isDragging ? 'cursor-grabbing' : ''}`}
          >
            {/* Degree Indicator */}
            <div className="absolute top-3 left-3 px-3 py-1 rounded-full bg-black/40 border border-white/10 text-[10px] text-cyan-400 font-black font-mono">
              360° VIEW MODE: {Math.round(rotation)}°
            </div>

            {/* Orbit Circle Background */}
            <div className="absolute h-64 w-64 rounded-full border border-dashed border-white/10 animate-spin-slow pointer-events-none" />

            {/* Simulated 3D Product Body with rotateY style */}
            <div 
              className="relative transition-transform duration-100 ease-out flex items-center justify-center"
              style={{
                transform: `perspective(1000px) rotateY(${rotation}deg) scale(1.05)`,
                filter: `drop-shadow(0 25px 35px rgba(0,0,0,0.5))`,
              }}
            >
              {product.image_url ? (
                <img
                  src={product.image_url}
                  alt={product.name}
                  className="max-h-[280px] object-contain pointer-events-none"
                />
              ) : (
                <div className="h-48 w-48 rounded-full bg-brand-gradient flex items-center justify-center text-white font-black text-2xl">
                  {product.brand}
                </div>
              )}
            </div>

            {/* Control Slider Overlay */}
            <div className="absolute bottom-4 left-4 right-4 flex flex-col items-center space-y-1 bg-black/35 rounded-xl px-4 py-2 border border-white/5 backdrop-blur-sm">
              <span className="text-[10px] text-muted-foreground uppercase font-black tracking-wider">Drag image or use slider to rotate 360°</span>
              <input
                type="range"
                min="0"
                max="359"
                value={Math.round(rotation)}
                onChange={(e) => setRotation(Number(e.target.value))}
                className="w-full h-1 bg-white/10 rounded-lg appearance-none cursor-pointer accent-cyan-400 focus:outline-none"
              />
            </div>
          </div>

          {/* Depth-layered Gallery thumbnails (simulates stack depth) */}
          <div className="flex justify-center gap-4 py-2">
            {[0, 1, 2].map((idx) => {
              // Different layer offsets
              const rotateDeg = idx === 0 ? '-3deg' : (idx === 1 ? '0deg' : '3deg');
              const translateVal = idx === 0 ? '-4px' : '0px';

              return (
                <button
                  key={idx}
                  onClick={() => {
                    setActiveImgIndex(idx);
                    setRotation(idx * 120);
                  }}
                  className={`relative h-16 w-16 rounded-xl border overflow-hidden bg-black/40 transition-all duration-300 hover:scale-110 ${
                    activeImgIndex === idx ? 'border-cyan-400 shadow-md shadow-cyan-500/20' : 'border-white/10 opacity-70 hover:opacity-100'
                  }`}
                  style={{
                    transform: `rotate(${rotateDeg}) translateY(${translateVal})`,
                  }}
                >
                  {product.image_url ? (
                    <img src={product.image_url} alt={product.name} className="h-full w-full object-cover pointer-events-none" />
                  ) : (
                    <div className="h-full w-full bg-brand-gradient opacity-80" />
                  )}
                </button>
              );
            })}
          </div>
        </div>

        {/* Product Info Description */}
        <div className="space-y-6">
          <div>
            <span className="text-xs font-bold text-cyan-400 uppercase tracking-wider">
              {product.brand || 'No Brand'}
            </span>
            <h1 className="text-4xl font-extrabold text-white tracking-tight mt-1">{product.name}</h1>
          </div>

          <div className="flex items-center space-x-4 border-y border-white/10 py-4">
            <span className="text-3xl font-black text-white">${Number(product.price).toFixed(2)}</span>
            <span
              className={`rounded px-2.5 py-1 text-xs font-black uppercase tracking-wider ${
                product.stock > 0 ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-red-500/10 text-red-400 border border-red-500/20'
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
                  className="rounded-lg border border-white/10 bg-black/40 px-3 py-1.5 text-sm text-white focus:outline-none focus:ring-1 focus:ring-cyan-500"
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
              className="flex-grow flex items-center justify-center space-x-2 rounded-xl bg-brand-gradient py-3.5 text-sm font-bold text-white transition-all hover:opacity-90 disabled:opacity-50"
            >
              <ShoppingCart className="h-5 w-5" />
              <span>Add to Shopping Cart</span>
            </button>

            <button
              onClick={() => toggleWishlistMutation.mutate()}
              className="rounded-xl border border-white/10 bg-white/5 p-3.5 transition-colors hover:bg-white/10"
              aria-label="Add to Wishlist"
            >
              <Heart className={`h-5 w-5 ${isProductInWishlist ? 'fill-cyan-400 text-cyan-400' : 'text-white'}`} />
            </button>
          </div>
        </div>
      </div>

      {/* Sticky Add to Cart Bar */}
      {product.stock > 0 && (
        <div className="fixed bottom-0 left-0 right-0 z-40 bg-black/85 backdrop-blur-lg border-t border-white/10 py-3 shadow-2xl animate-in slide-in-from-bottom-20 duration-300">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 flex items-center justify-between">
            <div className="flex items-center space-x-3">
              {product.image_url && <img src={product.image_url} alt="" className="h-10 w-10 object-cover rounded bg-white/5 border border-white/10" />}
              <div>
                <span className="text-white text-xs font-bold block truncate max-w-[120px] sm:max-w-xs">{product.name}</span>
                <span className="text-cyan-400 text-xs font-black">${Number(product.price).toFixed(2)}</span>
              </div>
            </div>
            
            <div className="flex items-center space-x-3">
              <select
                value={quantity}
                onChange={(e) => setQuantity(Number(e.target.value))}
                className="rounded-lg border border-white/10 bg-black/40 px-2 py-1.5 text-xs text-white focus:outline-none focus:ring-1 focus:ring-cyan-500"
              >
                {Array.from({ length: Math.min(product.stock, 5) }).map((_, i) => (
                  <option key={i + 1} value={i + 1}>
                    {i + 1}
                  </option>
                ))}
              </select>

              <button
                onClick={() => addToCartMutation.mutate()}
                className="rounded-lg bg-brand-gradient px-4 py-2 text-xs font-bold text-white transition-all hover:opacity-90 shadow-md shadow-indigo-500/20"
              >
                Add To Cart
              </button>
            </div>
          </div>
        </div>
      )}


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

      {/* Customers also viewed Section */}
      {relatedProducts.length > 0 && (
        <div className="mt-16 border-t border-border pt-12">
          <h2 className="text-2xl font-bold text-white mb-6">Customers also viewed</h2>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            {relatedProducts.map((p: any) => (
              <Link
                key={p.id}
                to={`/products/${p.id}`}
                className="group rounded-xl border border-border bg-card p-3 transition-all hover:border-primary/50"
              >
                <div className="h-32 w-full rounded bg-muted overflow-hidden flex items-center justify-center text-xs text-muted-foreground mb-2">
                  {p.image_url ? (
                    <img src={p.image_url} alt={p.name} className="h-full w-full object-cover" />
                  ) : (
                    <span>{p.brand}</span>
                  )}
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

      {/* Similar Products Section */}
      {similarProducts && similarProducts.length > 0 && (
        <div className="mt-16 border-t border-border pt-12">
          <h2 className="text-2xl font-bold text-white mb-6">Similar Products</h2>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-5">
            {similarProducts.map((p: any) => (
              <Link
                key={p.id}
                to={`/products/${p.id}`}
                className="group rounded-xl border border-border bg-card p-3 transition-all hover:border-primary/50"
              >
                <div className="h-32 w-full rounded bg-muted overflow-hidden flex items-center justify-center text-xs text-muted-foreground mb-2">
                  {p.image_url ? (
                    <img src={p.image_url} alt={p.name} className="h-full w-full object-cover" />
                  ) : (
                    <span>{p.brand}</span>
                  )}
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
