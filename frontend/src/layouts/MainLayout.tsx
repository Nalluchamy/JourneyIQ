import React, { useState, useEffect } from 'react';
import { Link, NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Menu, X, Rocket, Heart, ShoppingCart, User, LogOut } from 'lucide-react';
import { cartApi, wishlistApi, eventsApi, authApi } from '../services/api';

export const MainLayout: React.FC = () => {
  const { t } = useTranslation();
  const location = useLocation();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(!!localStorage.getItem('token'));

  // Sync auth state with localStorage changes across tabs/windows
  useEffect(() => {
    const syncAuth = () => {
      setIsAuthenticated(!!localStorage.getItem('token'));
    };
    window.addEventListener('storage', syncAuth);
    return () => window.removeEventListener('storage', syncAuth);
  }, []);

  // Track page views automatically on route changes
  useEffect(() => {
    let eventType = 'page_view';
    if (location.pathname === '/') {
      eventType = 'homepage_view';
    } else if (location.pathname === '/products') {
      eventType = 'category_view';
    }

    // Details page logs its own view with product_id, so we skip it here
    if (location.pathname !== '/' && !location.pathname.startsWith('/products/')) {
      eventsApi.trackEvent(eventType, location.pathname);
    } else if (location.pathname === '/') {
      eventsApi.trackEvent('homepage_view', location.pathname);
    }
  }, [location.pathname]);

  // Fetch profile to verify if user is admin
  const { data: profile } = useQuery({
    queryKey: ['profile'],
    queryFn: authApi.getProfile,
    enabled: isAuthenticated,
  });

  // Fetch cart & wishlist queries to display badges in header
  const { data: cart } = useQuery({
    queryKey: ['cart'],
    queryFn: cartApi.getCart,
    enabled: isAuthenticated,
  });

  const { data: wishlist } = useQuery({
    queryKey: ['wishlist'],
    queryFn: wishlistApi.getWishlist,
    enabled: isAuthenticated,
  });

  const cartCount = cart?.reduce((sum: number, item: any) => sum + item.quantity, 0) || 0;
  const wishlistCount = wishlist?.length || 0;

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('refresh_token');
    queryClient.clear();
    setIsAuthenticated(false);
    navigate('/');
  };

  const navItems = [
    { name: t('nav.home'), path: '/' },
    { name: t('nav.products'), path: '/products' },
    { name: t('nav.about'), path: '/about' },
    { name: t('nav.contact'), path: '/contact' },
  ];
  if (profile?.role === 'admin') {
    navItems.push({ name: 'Dashboard', path: '/dashboard/overview' });
  }

  return (
    <div className="flex min-h-screen flex-col bg-background text-foreground">
      {/* Navigation Header */}
      <header className="sticky top-0 z-50 w-full border-b border-border bg-background/80 backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-2">
            <Rocket className="h-6 w-6 text-primary" />
            <span className="text-xl font-bold tracking-tight text-white">
              {t('nav.platformName')}
            </span>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex space-x-8">
            {navItems.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  `text-sm font-medium transition-colors hover:text-primary ${
                    isActive ? 'text-primary' : 'text-muted-foreground'
                  }`
                }
              >
                {item.name}
              </NavLink>
            ))}
          </nav>

          {/* Quick Actions & Auth */}
          <div className="hidden md:flex items-center space-x-6">
            {isAuthenticated ? (
              <>
                <Link to="/wishlist" className="relative p-1.5 text-muted-foreground hover:text-white" aria-label="Wishlist">
                  <Heart className="h-5 w-5" />
                  {wishlistCount > 0 && (
                    <span className="absolute -top-0.5 -right-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-primary text-3xs font-bold text-white">
                      {wishlistCount}
                    </span>
                  )}
                </Link>

                <Link to="/cart" className="relative p-1.5 text-muted-foreground hover:text-white" aria-label="Cart">
                  <ShoppingCart className="h-5 w-5" />
                  {cartCount > 0 && (
                    <span className="absolute -top-0.5 -right-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-primary text-3xs font-bold text-white">
                      {cartCount}
                    </span>
                  )}
                </Link>

                <Link to="/profile" className="p-1.5 text-muted-foreground hover:text-white" aria-label="Profile">
                  <User className="h-5 w-5" />
                </Link>

                <button
                  onClick={handleLogout}
                  className="flex items-center space-x-1.5 text-sm font-medium text-muted-foreground hover:text-white"
                  aria-label="Logout"
                >
                  <LogOut className="h-4 w-4" />
                </button>
              </>
            ) : (
              <Link
                to="/login"
                className="rounded-lg bg-primary px-4 py-2 text-xs font-semibold text-white transition-all hover:bg-primary/90"
              >
                Sign In
              </Link>
            )}
          </div>

          {/* Mobile Menu Button */}
          <div className="flex md:hidden items-center space-x-4">
            {isAuthenticated && (
              <>
                <Link to="/cart" className="relative p-1.5 text-muted-foreground" aria-label="Cart">
                  <ShoppingCart className="h-5 w-5" />
                  {cartCount > 0 && (
                    <span className="absolute -top-0.5 -right-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-primary text-3xs font-bold text-white">
                      {cartCount}
                    </span>
                  )}
                </Link>
              </>
            )}

            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="inline-flex items-center justify-center rounded-md p-2 text-muted-foreground hover:bg-muted hover:text-foreground focus:outline-none"
              aria-label="Toggle Menu"
            >
              {mobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
            </button>
          </div>
        </div>

        {/* Mobile Navigation Drawer */}
        {mobileMenuOpen && (
          <div className="md:hidden border-b border-border bg-background px-2 pb-3 pt-2">
            <div className="space-y-1 px-2">
              {navItems.map((item) => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  onClick={() => setMobileMenuOpen(false)}
                  className={({ isActive }) =>
                    `block rounded-md px-3 py-2 text-base font-medium transition-colors hover:bg-muted hover:text-primary ${
                      isActive ? 'bg-muted text-primary' : 'text-muted-foreground'
                    }`
                  }
                >
                  {item.name}
                </NavLink>
              ))}

              {isAuthenticated ? (
                <>
                  <Link
                    to="/wishlist"
                    onClick={() => setMobileMenuOpen(false)}
                    className="block rounded-md px-3 py-2 text-base font-medium text-muted-foreground hover:bg-muted hover:text-primary"
                  >
                    Wishlist ({wishlistCount})
                  </Link>
                  <Link
                    to="/profile"
                    onClick={() => setMobileMenuOpen(false)}
                    className="block rounded-md px-3 py-2 text-base font-medium text-muted-foreground hover:bg-muted hover:text-primary"
                  >
                    Profile
                  </Link>
                  <button
                    onClick={() => {
                      setMobileMenuOpen(false);
                      handleLogout();
                    }}
                    className="w-full text-left block rounded-md px-3 py-2 text-base font-medium text-muted-foreground hover:bg-muted hover:text-primary"
                  >
                    Logout
                  </button>
                </>
              ) : (
                <Link
                  to="/login"
                  onClick={() => setMobileMenuOpen(false)}
                  className="block rounded-md px-3 py-2 text-base font-medium text-primary hover:bg-muted"
                >
                  Sign In
                </Link>
              )}
            </div>
          </div>
        )}
      </header>

      {/* Main Page Area */}
      <main className="flex-grow">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="border-t border-border bg-black/40 py-8">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col items-center justify-between space-y-4 md:flex-row md:space-y-0">
            <div className="flex items-center space-x-2 text-sm text-muted-foreground">
              <span>{t('footer.copyright', { year: new Date().getFullYear() })}</span>
            </div>

            <div className="text-xs text-muted-foreground">JourneyIQ v1.0.0 | AI-Powered Customer Journey Intelligence</div>
          </div>
        </div>
      </footer>
    </div>
  );
};
