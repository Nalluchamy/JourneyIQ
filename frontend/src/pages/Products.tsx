import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link, useSearchParams } from 'react-router-dom';
import { Search, Filter, SlidersHorizontal, Heart, ShoppingCart, RefreshCw } from 'lucide-react';
import { productsApi, wishlistApi, cartApi, eventsApi, apiClient } from '../services/api';
import { useNotification } from '../context/NotificationContext';

export const Products: React.FC = () => {
  const queryClient = useQueryClient();
  const [searchParams, setSearchParams] = useSearchParams();

  // Filter State synced with URL search params where possible
  const [search, setSearch] = useState(searchParams.get('search') || '');
  const [debouncedSearch, setDebouncedSearch] = useState(search);
  const [categoryId, setCategoryId] = useState<number | null>(
    searchParams.get('category_id') ? Number(searchParams.get('category_id')) : null
  );
  const [brand, setBrand] = useState(searchParams.get('brand') || '');
  const [priceMin, setPriceMin] = useState(searchParams.get('price_min') || '');
  const [priceMax, setPriceMax] = useState(searchParams.get('price_max') || '');
  const [inStock, setInStock] = useState<boolean | null>(
    searchParams.get('in_stock') === 'true' ? true : null
  );
  const [sortBy, setSortBy] = useState(searchParams.get('sort_by') || 'created_at');
  const [sortOrder, setSortOrder] = useState(searchParams.get('sort_order') || 'desc');
  const [page, setPage] = useState(Number(searchParams.get('page')) || 1);

  const [categories, setCategories] = useState<any[]>([]);
  const { showNotification } = useNotification();

  // Fetch Categories list for the sidebar filter
  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const res = await apiClient.get('/api/v1/categories');
        setCategories(res.data.items || []);
      } catch (err) {
        console.error('Failed to load categories', err);
      }
    };
    fetchCategories();
  }, []);

  // Debounce search query
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(search);
      setPage(1);
    }, 500);
    return () => clearTimeout(timer);
  }, [search]);

  // Track search event on debounced search change
  useEffect(() => {
    if (debouncedSearch) {
      eventsApi.trackEvent('search', '/products', undefined, { query: debouncedSearch });
    }
  }, [debouncedSearch]);

  // Track category view event
  useEffect(() => {
    if (categoryId) {
      eventsApi.trackEvent('category_view', '/products', undefined, { category_id: categoryId });
    }
  }, [categoryId]);

  // Sync state changes with URL Search Params
  useEffect(() => {
    const params: any = { page: String(page) };
    if (debouncedSearch) params.search = debouncedSearch;
    if (categoryId) params.category_id = String(categoryId);
    if (brand) params.brand = brand;
    if (priceMin) params.price_min = priceMin;
    if (priceMax) params.price_max = priceMax;
    if (inStock !== null) params.in_stock = String(inStock);
    params.sort_by = sortBy;
    params.sort_order = sortOrder;
    setSearchParams(params);
  }, [debouncedSearch, categoryId, brand, priceMin, priceMax, inStock, sortBy, sortOrder, page]);

  // Fetch products query
  const { data: productsData, isLoading, isError, refetch } = useQuery({
    queryKey: ['products', debouncedSearch, categoryId, brand, priceMin, priceMax, inStock, sortBy, sortOrder, page],
    queryFn: () =>
      productsApi.getProducts({
        page,
        size: 12,
        search: debouncedSearch || undefined,
        category_id: categoryId || undefined,
        brand: brand || undefined,
        price_min: priceMin ? Number(priceMin) : undefined,
        price_max: priceMax ? Number(priceMax) : undefined,
        in_stock: inStock !== null ? inStock : undefined,
        sort_by: sortBy,
        sort_order: sortOrder,
      }),
  });

  // Query user wishlist & cart to check active status and item counts
  const isAuthenticated = !!localStorage.getItem('token');

  const { data: wishlistItems } = useQuery({
    queryKey: ['wishlist'],
    queryFn: wishlistApi.getWishlist,
    enabled: isAuthenticated,
  });

  const { data: cartItems } = useQuery({
    queryKey: ['cart'],
    queryFn: cartApi.getCart,
    enabled: isAuthenticated,
  });

  const isInWishlist = (productId: number) => {
    return wishlistItems?.some((item: any) => item.product_id === productId);
  };

  // Mutations
  const toggleWishlistMutation = useMutation({
    mutationFn: async (productId: number) => {
      if (isInWishlist(productId)) {
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
      showNotification(err.message || 'Auth required for wishlist.', 'error');
    },
  });

  const addToCartMutation = useMutation({
    mutationFn: (productId: number) => cartApi.addToCart(productId, 1),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cart'] });
      showNotification('Product added to shopping cart!', 'success');
    },
    onError: (err: any) => {
      showNotification(err.message || 'Auth required to shop.', 'error');
    },
  });

  const handleResetFilters = () => {
    setSearch('');
    setCategoryId(null);
    setBrand('');
    setPriceMin('');
    setPriceMax('');
    setInStock(null);
    setSortBy('created_at');
    setSortOrder('desc');
    setPage(1);
  };

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">


      {/* Top Banner / Heading */}
      <div className="mb-8 flex flex-col items-start justify-between gap-4 md:flex-row md:items-center">
        <div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight">Explore Products</h1>
          <p className="mt-1 text-sm text-muted-foreground">Browse, filter, and track customized products catalog</p>
        </div>

        {/* Sorting Dropdown */}
        <div className="flex items-center space-x-2">
          <SlidersHorizontal className="h-4 w-4 text-muted-foreground" />
          <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Sort:</span>
          <select
            value={`${sortBy}-${sortOrder}`}
            onChange={(e) => {
              const [by, order] = e.target.value.split('-');
              setSortBy(by);
              setSortOrder(order);
              setPage(1);
            }}
            className="rounded-lg border border-border bg-card px-3 py-1.5 text-sm text-white focus:outline-none focus:ring-1 focus:ring-primary"
          >
            <option value="created_at-desc">Newest First</option>
            <option value="price-asc">Price: Low to High</option>
            <option value="price-desc">Price: High to Low</option>
            <option value="stock-desc">Stock: High to Low</option>
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-4">
        {/* Sidebar Filters - Glassmorphism style */}
        <div className="space-y-6 rounded-2xl border border-white/10 bg-white/5 backdrop-blur-md p-6 shadow-xl h-fit">
          <div className="flex items-center justify-between border-b border-white/10 pb-4">
            <span className="flex items-center space-x-2 font-bold text-white">
              <Filter className="h-4 w-4 text-cyan-400" />
              <span>Filters</span>
            </span>
            <button
              onClick={handleResetFilters}
              className="text-xs font-semibold text-cyan-400 hover:underline"
            >
              Reset All
            </button>
          </div>

          {/* Live Search Input */}
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-muted-foreground mb-2">Search</label>
            <div className="relative">
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Name, brand..."
                className="w-full rounded-lg border border-white/10 bg-black/40 py-2 pl-10 pr-4 text-sm text-white placeholder-muted-foreground focus:outline-none focus:ring-1 focus:ring-cyan-500"
              />
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
            </div>
          </div>

          {/* Category Dropdown */}
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-muted-foreground mb-2">Category</label>
            <select
              value={categoryId || ''}
              onChange={(e) => {
                setCategoryId(e.target.value ? Number(e.target.value) : null);
                setPage(1);
              }}
              className="w-full rounded-lg border border-white/10 bg-black/40 px-3 py-2.5 text-sm text-white focus:outline-none focus:ring-1 focus:ring-cyan-500"
            >
              <option value="">All Categories</option>
              {categories.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>

          {/* Brand Filter */}
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-muted-foreground mb-2">Brand</label>
            <input
              type="text"
              value={brand}
              onChange={(e) => {
                setBrand(e.target.value);
                setPage(1);
              }}
              placeholder="e.g. Apple, Nike"
              className="w-full rounded-lg border border-white/10 bg-black/40 px-3 py-2.5 text-sm text-white placeholder-muted-foreground focus:outline-none focus:ring-1 focus:ring-cyan-500"
            />
          </div>

          {/* Price Range Filter */}
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-muted-foreground mb-2">Price Range</label>
            <div className="flex gap-2">
              <input
                type="number"
                value={priceMin}
                onChange={(e) => {
                  setPriceMin(e.target.value);
                  setPage(1);
                }}
                placeholder="Min"
                className="w-full rounded-lg border border-white/10 bg-black/40 px-3 py-2 text-sm text-white placeholder-muted-foreground focus:outline-none focus:ring-1 focus:ring-cyan-500"
              />
              <input
                type="number"
                value={priceMax}
                onChange={(e) => {
                  setPriceMax(e.target.value);
                  setPage(1);
                }}
                placeholder="Max"
                className="w-full rounded-lg border border-white/10 bg-black/40 px-3 py-2 text-sm text-white placeholder-muted-foreground focus:outline-none focus:ring-1 focus:ring-cyan-500"
              />
            </div>
          </div>

          {/* In Stock toggle */}
          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              id="inStockCheckbox"
              checked={inStock === true}
              onChange={(e) => {
                setInStock(e.target.checked ? true : null);
                setPage(1);
              }}
              className="h-4 w-4 rounded border-white/10 bg-black/40 text-cyan-500 focus:ring-cyan-500"
            />
            <label htmlFor="inStockCheckbox" className="text-sm text-white font-medium select-none cursor-pointer">
              Only Show In Stock
            </label>
          </div>
        </div>

        {/* Catalog Products Display Grid */}
        <div className="lg:col-span-3 space-y-6">
          {isLoading && (
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 xl:grid-cols-3">
              {Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="animate-pulse rounded-2xl border border-white/10 bg-white/5 p-4 space-y-4">
                  <div className="h-48 w-full rounded-lg bg-muted" />
                  <div className="h-4 w-2/3 rounded bg-muted" />
                  <div className="h-4 w-1/3 rounded bg-muted" />
                  <div className="flex justify-between items-center">
                    <div className="h-8 w-1/4 rounded bg-muted" />
                    <div className="h-8 w-1/2 rounded bg-muted" />
                  </div>
                </div>
              ))}
            </div>
          )}

          {isError && (
            <div className="flex flex-col items-center justify-center rounded-2xl border border-white/10 bg-white/5 p-12 text-center">
              <span className="text-red-400 font-semibold mb-2">Error Loading Catalog</span>
              <button
                onClick={() => refetch()}
                className="flex items-center space-x-2 rounded-lg bg-primary px-4 py-2 text-sm text-white"
              >
                <RefreshCw className="h-4 w-4" />
                <span>Retry</span>
              </button>
            </div>
          )}

          {productsData && productsData.items.length === 0 && (
            <div className="flex flex-col items-center justify-center rounded-2xl border border-white/10 bg-white/5 p-16 text-center">
              <span className="text-muted-foreground font-medium text-lg">No Products Found</span>
              <p className="text-sm text-muted-foreground mt-1 mb-6">Try refining your sidebar search filters</p>
              <button
                onClick={handleResetFilters}
                className="rounded-lg bg-primary px-4 py-2 text-sm text-white"
              >
                Clear All Filters
              </button>
            </div>
          )}

          {productsData && productsData.items.length > 0 && (
            <>
              <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 xl:grid-cols-3">
                {productsData.items.map((prod: any) => {
                  // Interactive 3D Tilt Hook/State representation
                  return (
                    <ProductCatalogCard
                      key={prod.id}
                      prod={prod}
                      isInWishlist={isInWishlist(prod.id)}
                      onToggleWishlist={() => toggleWishlistMutation.mutate(prod.id)}
                      onAddToCart={() => addToCartMutation.mutate(prod.id)}
                    />
                  );
                })}
              </div>

              {/* Pagination Controls */}
              <div className="flex items-center justify-between border-t border-white/10 pt-6">
                <span className="text-xs text-muted-foreground font-medium">
                  Page {productsData.page} of {productsData.pages} (Total: {productsData.total} products)
                </span>
                <div className="flex space-x-2">
                  <button
                    disabled={page === 1}
                    onClick={() => setPage(page - 1)}
                    className="rounded-lg border border-white/10 bg-white/5 px-4 py-2 text-xs font-semibold text-white disabled:opacity-50 hover:bg-white/10"
                  >
                    Previous
                  </button>
                  <button
                    disabled={page === productsData.pages}
                    onClick={() => setPage(page + 1)}
                    className="rounded-lg border border-white/10 bg-white/5 px-4 py-2 text-xs font-semibold text-white disabled:opacity-50 hover:bg-white/10"
                  >
                    Next
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

// Helper component for 3D card tilt and premium hover-lift
const ProductCatalogCard: React.FC<{
  prod: any;
  isInWishlist: boolean;
  onToggleWishlist: () => void;
  onAddToCart: () => void;
}> = ({ prod, isInWishlist, onToggleWishlist, onAddToCart }) => {
  const [tilt, setTilt] = useState({ x: 0, y: 0 });
  const [hovered, setHovered] = useState(false);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left - rect.width / 2;
    const y = e.clientY - rect.top - rect.height / 2;
    setTilt({
      x: -(y / (rect.height / 2)) * 12,
      y: (x / (rect.width / 2)) * 12,
    });
  };

  return (
    <div
      onMouseMove={handleMouseMove}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => {
        setHovered(false);
        setTilt({ x: 0, y: 0 });
      }}
      className="card-3d relative flex flex-col justify-between overflow-hidden rounded-2xl border border-white/10 bg-white/5 p-4 backdrop-blur-sm group"
      style={{
        transform: hovered
          ? `perspective(1000px) rotateX(${tilt.x}deg) rotateY(${tilt.y}deg) scale3d(1.04, 1.04, 1.04)`
          : 'perspective(1000px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)',
        boxShadow: hovered
          ? '0 20px 40px -15px rgba(99, 102, 241, 0.35), 0 0 20px 0px rgba(6, 182, 212, 0.15)'
          : '0 4px 12px -5px rgba(0, 0, 0, 0.4)',
      }}
    >
      {/* Wishlist Button Overlay */}
      <button
        onClick={(e) => {
          e.preventDefault();
          e.stopPropagation();
          onToggleWishlist();
        }}
        className="absolute right-3 top-3 z-10 rounded-full bg-black/40 p-2 backdrop-blur-sm transition-colors hover:bg-black/60 border border-white/10"
        aria-label="Add to Wishlist"
      >
        <Heart
          className={`h-4 w-4 transition-colors ${
            isInWishlist ? 'fill-cyan-400 text-cyan-400' : 'text-white'
          }`}
        />
      </button>

      <Link to={`/products/${prod.id}`}>
        {/* Image layout with brand badges */}
        <div className="relative mb-4 h-48 w-full overflow-hidden rounded-lg bg-black/30 flex items-center justify-center text-muted-foreground text-sm font-semibold tracking-wider uppercase">
          {prod.image_url ? (
            <img
              src={prod.image_url}
              alt={prod.name}
              className="h-full w-full object-cover transition-transform group-hover:scale-105"
            />
          ) : (
            <span className="text-xs text-slate-500 font-bold">{prod.brand || 'Storefront'}</span>
          )}
          {/* Stock status badge */}
          <span
            className={`absolute bottom-2 left-2 rounded px-2 py-0.5 text-2xs font-black uppercase tracking-wider ${
              prod.stock > 0 ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-red-500/10 text-red-400 border border-red-500/20'
            }`}
          >
            {prod.stock > 0 ? `${prod.stock} In Stock` : 'Out of Stock'}
          </span>
        </div>

        <div className="space-y-1 mb-4">
          <span className="text-2xs font-bold text-cyan-400 uppercase tracking-wider">
            {prod.brand || 'No Brand'}
          </span>
          <h3 className="font-bold text-white leading-tight group-hover:text-cyan-400 transition-colors line-clamp-1">
            {prod.name}
          </h3>
          <p className="text-xs text-muted-foreground line-clamp-2 leading-relaxed">
            {prod.description || 'No description provided.'}
          </p>
        </div>
      </Link>

      {/* Bottom row actions */}
      <div className="flex items-center justify-between mt-auto border-t border-white/5 pt-3">
        <span className="text-lg font-black text-white">₹{Number(prod.price).toFixed(2)}</span>
        <button
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            onAddToCart();
          }}
          disabled={prod.stock === 0}
          className="flex items-center space-x-1.5 rounded-lg bg-brand-gradient px-3 py-1.5 text-xs font-bold text-white transition-all hover:opacity-90 disabled:opacity-50"
        >
          <ShoppingCart className="h-3.5 w-3.5" />
          <span>Add</span>
        </button>
      </div>
    </div>
  );
};


