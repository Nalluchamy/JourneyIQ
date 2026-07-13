import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ArrowRight, Eye, Sparkles, LineChart, SplitSquareVertical, Flame, Star, Compass } from 'lucide-react';
import { recommendationsApi, eventsApi } from '../services/api';

interface Product {
  id: number;
  name: string;
  price: number;
  image_url?: string;
  brand?: string;
  slug: string;
}

interface Recommendation {
  id: number;
  product_id: int;
  explanation?: string;
  product: Product;
}

export const Home: React.FC = () => {
  const { t } = t => ({
    'hero.badge': '🚀 JourneyIQ 2.0 Storefront Active',
    'hero.title': 'The Next Dimension of Personalized Shopping',
    'hero.subtitle': 'Experience predictive retail powered by PyTorch neural recommendations and real-time behavioral diagnostics.',
    'hero.ctaStart': 'Explore Storefront',
    'hero.ctaDemo': 'Owner Dashboard',
    'features.sectionTitle': 'Intelligent Customer Journeys',
    'features.sectionSubtitle': 'Real-time telemetry and deep learning recommendation engine tailored for hyper-personalized commerce.',
  });
  const i18nMock = (key: string) => {
    const dict: Record<string, string> = {
      'hero.badge': '🚀 JourneyIQ 2.0 Storefront Active',
      'hero.title': 'The Next Dimension of Personalized Shopping',
      'hero.subtitle': 'Experience predictive retail powered by PyTorch neural recommendations and real-time behavioral diagnostics.',
      'hero.ctaStart': 'Explore Storefront',
      'hero.ctaDemo': 'Owner Dashboard',
      'features.sectionTitle': 'Intelligent Customer Journeys',
      'features.sectionSubtitle': 'Real-time telemetry and deep learning recommendation engine tailored for hyper-personalized commerce.',
    };
    return dict[key] || key;
  };

  const isAuthenticated = !!localStorage.getItem('token');
  const [recommended, setRecommended] = useState<Recommendation[]>([]);
  const [trending, setTrending] = useState<Product[]>([]);
  const [popular, setPopular] = useState<Product[]>([]);
  const [loading, setLoading] = useState(false);
  const [carouselIndex, setCarouselIndex] = useState(0);

  // Parallax Background position state
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });

  useEffect(() => {
    const handleMove = (e: MouseEvent) => {
      setMousePos({
        x: (e.clientX / window.innerWidth - 0.5) * 35,
        y: (e.clientY / window.innerHeight - 0.5) * 35,
      });
    };
    window.addEventListener('mousemove', handleMove);
    return () => window.removeEventListener('mousemove', handleMove);
  }, []);

  useEffect(() => {
    const fetchRecommendations = async () => {
      setLoading(true);

      // Always fetch trending and popular (public, no auth required)
      try {
        const trendData = await recommendationsApi.getTrending();
        setTrending(trendData || []);
      } catch (err) {
        console.error('Failed to load trending products:', err);
      }

      try {
        const popData = await recommendationsApi.getPopular();
        setPopular(popData || []);
      } catch (err) {
        console.error('Failed to load popular products:', err);
      }

      // Only fetch personalized recommendations if logged in
      if (isAuthenticated) {
        try {
          const recData = await recommendationsApi.getPersonalized();
          setRecommended(recData || []);

          if (recData && recData.length > 0) {
            const firstRecId = recData[0].product_id;
            eventsApi.trackEvent('recommendation_view', '/', firstRecId, {
              count: recData.length,
              recommended_pids: recData.map((r: any) => r.product_id),
            });
          }
        } catch (err) {
          console.error('Failed to load personalized recommendations:', err);
        }
      }

      setLoading(false);
    };

    fetchRecommendations();
  }, [isAuthenticated]);


  const handleRecClick = (productId: number) => {
    eventsApi.trackEvent('recommendation_click', '/', productId, { source: 'homepage_recommended' });
  };

  const features = [
    {
      title: 'Real-time Telemetry',
      desc: 'Track and map full customer intent loops from click, view, checkout, to order confirmation.',
      icon: <Eye className="h-6 w-6 text-primary" />,
    },
    {
      title: 'Neural Recommendations',
      desc: 'Predict next-action shopping intents using our PyTorch Neural Collaborative Filtering model.',
      icon: <Sparkles className="h-6 w-6 text-indigo-400" />,
    },
    {
      title: 'Calm Dashboard Controls',
      desc: 'Monitor sales and inventory alerts with high readability flat interfaces and plain-language groups.',
      icon: <LineChart className="h-6 w-6 text-cyan-400" />,
    },
    {
      title: 'A/B Model Switcher',
      desc: 'Dynamically toggle recommendation pipelines between Hybrid heuristics and Deep Learning.',
      icon: <SplitSquareVertical className="h-6 w-6 text-violet-400" />,
    },
  ];

  // 3D Tilt Card Sub-component
  const TiltCard: React.FC<{ children: React.ReactNode; className?: string; onClick?: () => void }> = ({ children, className = '', onClick }) => {
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
        onClick={onClick}
        className={`card-3d ${className}`}
        style={{
          transform: hovered
            ? `perspective(1000px) rotateX(${tilt.x}deg) rotateY(${tilt.y}deg) scale3d(1.03, 1.03, 1.03)`
            : 'perspective(1000px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)',
          boxShadow: hovered
            ? '0 25px 50px -12px rgba(99, 102, 241, 0.4), 0 0 25px 0px rgba(6, 182, 212, 0.2)'
            : '0 4px 12px -5px rgba(0, 0, 0, 0.4)',
        }}
      >
        {children}
      </div>
    );
  };

  return (
    <div className="relative overflow-hidden py-12 sm:py-20 lg:py-24 space-y-24">
      {/* 1. LAYERED PARALLAX BACKGROUND */}
      <div 
        className="absolute top-10 left-10 -z-20 h-[500px] w-[500px] rounded-full bg-indigo-500/10 blur-[130px] transition-transform duration-300 ease-out" 
        style={{ transform: `translate(${mousePos.x * 0.7}px, ${mousePos.y * 0.7}px)` }}
      />
      <div 
        className="absolute bottom-20 right-10 -z-20 h-[600px] w-[600px] rounded-full bg-cyan-500/10 blur-[150px] transition-transform duration-300 ease-out" 
        style={{ transform: `translate(${mousePos.x * -0.5}px, ${mousePos.y * -0.5}px)` }}
      />
      <div 
        className="absolute top-1/3 left-1/2 -z-20 h-[300px] w-[300px] rounded-full bg-violet-600/10 blur-[100px] transition-transform duration-300 ease-out" 
        style={{ transform: `translate(${mousePos.x * 0.3}px, ${mousePos.y * -0.8}px)` }}
      />

      {/* Hero Section */}
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 gap-12 lg:grid-cols-2 lg:items-center">
          {/* Hero Left Content */}
          <div className="text-left space-y-6">
            <div className="inline-flex items-center space-x-2 rounded-full border border-white/10 bg-white/5 backdrop-blur-md px-4 py-1.5 text-xs text-cyan-400 font-bold transition-all hover:bg-white/10">
              <span className="flex h-2 w-2 rounded-full bg-cyan-400 animate-pulse" />
              <span>{i18nMock('hero.badge')}</span>
            </div>

            <h1 className="text-4xl font-extrabold tracking-tight text-white sm:text-5xl lg:text-6xl">
              <span className="block">JourneyIQ Platform</span>
              <span className="block text-gradient mt-2 font-black">AI Customer Storefront</span>
            </h1>

            <p className="text-lg text-muted-foreground max-w-xl">
              {i18nMock('hero.subtitle')}
            </p>

            <div className="flex flex-wrap gap-4 pt-2">
              <Link to="/products" className="flex items-center space-x-2 rounded-xl bg-brand-gradient px-6 py-4 text-sm font-bold text-white shadow-lg shadow-indigo-500/20 transition-all hover:opacity-90 hover:scale-105 active:scale-95">
                <span>{i18nMock('hero.ctaStart')}</span>
                <ArrowRight className="h-4 w-4" />
              </Link>

              <Link to="/dashboard/overview" className="rounded-xl border border-white/10 bg-white/5 backdrop-blur-sm px-6 py-4 text-sm font-bold text-white transition-all hover:bg-white/15 hover:scale-105 active:scale-95">
                {i18nMock('hero.ctaDemo')}
              </Link>
            </div>
          </div>

          {/* Hero Right: 3D-style Floating Product Render */}
          <div className="relative flex justify-center items-center h-[400px]">
            {/* Holographic Glowing Base */}
            <div className="absolute bottom-10 h-6 w-48 rounded-full bg-cyan-500/20 blur-md scale-y-50 animate-pulse" />
            <div className="absolute bottom-11 h-2 w-36 rounded-full bg-indigo-500/40 blur-sm scale-y-50 animate-pulse" />
            
            {/* Floating 3D Object Render */}
            <div className="relative animate-float h-64 w-64 md:h-80 md:w-80 flex items-center justify-center">
              {/* Outer rotating neon ring */}
              <div className="absolute inset-0 rounded-full border border-cyan-500/20 border-t-cyan-400 border-b-indigo-400 animate-spin-slow" />
              
              {/* Floating holographic product body */}
              <div className="absolute h-48 w-48 rounded-3xl bg-gradient-to-tr from-indigo-600/30 via-violet-600/20 to-cyan-500/20 border border-white/20 shadow-[inset_0_0_20px_rgba(255,255,255,0.1)] flex flex-col items-center justify-center p-6 backdrop-blur-lg transform rotate-12 group hover:rotate-6 transition-all duration-700">
                
                {/* 3D layers using shadows and perspective */}
                <div className="absolute top-4 left-4 text-white/40 text-[9px] font-bold tracking-widest uppercase">J-IQ HYPERSPHERE</div>
                <div className="absolute bottom-4 right-4 text-cyan-400 text-xs font-black tracking-widest">v2.1</div>

                <div className="h-20 w-20 rounded-full bg-brand-gradient flex items-center justify-center shadow-lg shadow-indigo-500/50 text-white font-black text-2xl relative overflow-hidden group-hover:scale-110 transition-transform">
                  <div className="absolute inset-0 bg-white/20 transform -translate-x-full group-hover:translate-x-full transition-transform duration-1000" />
                  IQ
                </div>
                <div className="mt-4 text-center space-y-1">
                  <div className="text-white font-black text-sm uppercase tracking-wider">Holographic Hub</div>
                  <div className="text-cyan-400 text-xs font-semibold">Interactive intent sensor</div>
                </div>

                {/* Floating interactive sub-orb */}
                <div className="absolute -top-3 -right-3 h-10 w-10 rounded-full bg-cyan-400/20 border border-cyan-400/50 backdrop-blur-md flex items-center justify-center text-cyan-400 font-bold animate-bounce text-[10px]">
                  DL
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Featured-Product Carousel using Tilt/Hover Depth Cards */}
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 space-y-6">
        <div className="flex justify-between items-end border-b border-white/10 pb-4">
          <div>
            <h2 className="text-2xl font-black text-white tracking-tight flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-indigo-400" />
              <span>Hyped Predictions</span>
            </h2>
            <p className="text-xs text-muted-foreground">Premium 3D hover cards powered by neural recommendation engine</p>
          </div>
          <div className="flex space-x-2">
            <button
              onClick={() => setCarouselIndex(idx => Math.max(0, idx - 1))}
              disabled={carouselIndex === 0}
              className="p-2 rounded-lg border border-white/10 bg-white/5 text-white disabled:opacity-40 hover:bg-white/10 transition-colors"
            >
              ←
            </button>
            <button
              onClick={() => setCarouselIndex(idx => Math.min(Math.ceil((trending.length || 4) / 2) - 1, idx + 1))}
              disabled={carouselIndex >= Math.ceil((trending.length || 4) / 2) - 1}
              className="p-2 rounded-lg border border-white/10 bg-white/5 text-white disabled:opacity-40 hover:bg-white/10 transition-colors"
            >
              →
            </button>
          </div>
        </div>

        {/* Carousel Grid View */}
        <div className="relative overflow-hidden w-full">
          <div 
            className="flex transition-transform duration-500 ease-out gap-6"
            style={{ transform: `translateX(-${carouselIndex * 50}%)` }}
          >
            {trending.length > 0 ? (
              trending.map((prod) => (
                <div key={prod.id} className="min-w-[45%] md:min-w-[30%] lg:min-w-[23%] flex-shrink-0 py-4">
                  <TiltCard className="rounded-2xl border border-white/10 bg-white/5 p-4 flex flex-col justify-between h-[340px] backdrop-blur-md group relative">
                    <div className="absolute top-2 left-2 z-10 px-2 py-0.5 rounded bg-indigo-500/20 border border-indigo-500/30 text-[9px] font-black text-indigo-450 uppercase">
                      Neural Hit
                    </div>
                    <div>
                      <div className="h-40 w-full overflow-hidden rounded-lg bg-black/40 flex items-center justify-center mb-3 relative">
                        {prod.image_url ? (
                          <img src={prod.image_url} alt={prod.name} className="h-full w-full object-cover group-hover:scale-110 transition-transform duration-500" />
                        ) : (
                          <span className="text-xs text-muted-foreground font-black uppercase">{prod.brand}</span>
                        )}
                        {/* Premium Gradient Overlay */}
                        <div className="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent" />
                      </div>
                      <span className="text-[10px] font-black text-cyan-400 uppercase tracking-wider block">{prod.brand}</span>
                      <h3 className="font-bold text-white text-sm leading-tight line-clamp-1 group-hover:text-primary transition-colors mt-0.5">{prod.name}</h3>
                    </div>
                    <div className="flex justify-between items-center mt-3 pt-3 border-t border-white/5">
                      <span className="text-base font-black text-white">₹{Number(prod.price).toFixed(2)}</span>
                      <Link to={`/products/${prod.id}`} className="text-xs font-extrabold text-cyan-400 hover:underline">View details →</Link>
                    </div>
                  </TiltCard>
                </div>
              ))
            ) : (
              /* Fallback mock items */
              [1, 2, 3, 4].map((i) => (
                <div key={i} className="min-w-[45%] md:min-w-[30%] lg:min-w-[23%] flex-shrink-0 py-4">
                  <TiltCard className="rounded-2xl border border-white/10 bg-white/5 p-4 flex flex-col justify-between h-[340px] backdrop-blur-md">
                    <div>
                      <div className="h-40 w-full rounded-lg bg-black/30 flex items-center justify-center mb-3">
                        <span className="text-muted-foreground text-xs uppercase font-bold">Premium Render</span>
                      </div>
                      <span className="text-[10px] font-bold text-cyan-400 uppercase tracking-wider block">Pulse-IQ</span>
                      <h3 className="font-bold text-white text-sm mt-0.5">Vapor Glide Shoe v{i}</h3>
                    </div>
                    <div className="flex justify-between items-center mt-3 pt-3 border-t border-white/5">
                      <span className="text-base font-black text-white">₹149.99</span>
                      <span className="text-xs font-bold text-cyan-400">View details →</span>
                    </div>
                  </TiltCard>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* AI Personalized Recommendations Section (Only when logged in) */}
      {isAuthenticated && recommended.length > 0 && (
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex items-center space-x-2.5 mb-6">
            <Compass className="h-6 w-6 text-primary animate-spin-slow" />
            <h2 className="text-2xl font-black text-white tracking-tight">Recommended For You</h2>
          </div>
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
            {recommended.map((rec) => (
              <TiltCard
                key={rec.id}
                className="flex flex-col justify-between overflow-hidden rounded-2xl border border-white/10 bg-white/5 p-4 backdrop-blur-sm group"
              >
                <div>
                  {rec.explanation && (
                    <span className="inline-block px-2 py-0.5 mb-2 bg-indigo-500/20 border border-indigo-500/30 text-indigo-400 text-[10px] font-extrabold uppercase rounded">
                      💡 {rec.explanation}
                    </span>
                  )}
                  <Link to={`/products/${rec.product.id}`} onClick={() => handleRecClick(rec.product.id)}>
                    <div className="h-40 w-full overflow-hidden rounded-lg bg-black/30 flex items-center justify-center text-xs text-muted-foreground font-semibold uppercase mb-3">
                      {rec.product.image_url ? (
                        <img
                          src={rec.product.image_url}
                          alt={rec.product.name}
                          className="h-full w-full object-cover group-hover:scale-105 transition-transform duration-300"
                        />
                      ) : (
                        <span>{rec.product.brand}</span>
                      )}
                    </div>
                    <span className="text-2xs font-bold text-primary uppercase tracking-wider block">
                      {rec.product.brand}
                    </span>
                    <h3 className="font-bold text-white leading-tight line-clamp-1 hover:text-primary transition-colors mt-0.5">
                      {rec.product.name}
                    </h3>
                  </Link>
                </div>
                <div className="flex justify-between items-center mt-3 pt-3 border-t border-white/5">
                  <span className="text-md font-black text-white">₹{Number(rec.product.price).toFixed(2)}</span>
                  <Link
                    to={`/products/${rec.product.id}`}
                    onClick={() => handleRecClick(rec.product.id)}
                    className="text-xs font-bold text-primary hover:underline"
                  >
                    View details →
                  </Link>
                </div>
              </TiltCard>
            ))}
          </div>
        </div>
      )}

      {/* Popular Products */}
      {popular.length > 0 && (
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex items-center space-x-2.5 mb-6">
            <Star className="h-6 w-6 text-yellow-500 animate-bounce" />
            <h2 className="text-2xl font-black text-white tracking-tight">Popular Products</h2>
          </div>
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
            {popular.map((prod) => (
              <TiltCard
                key={prod.id}
                className="flex flex-col justify-between overflow-hidden rounded-2xl border border-white/10 bg-white/5 p-4 backdrop-blur-sm group"
              >
                <div>
                  <span className="inline-block px-2 py-0.5 mb-2 bg-yellow-500/10 border border-yellow-500/20 text-yellow-450 text-[10px] font-extrabold uppercase rounded">
                    ⭐ TOP SELLER
                  </span>
                  <Link to={`/products/${prod.id}`}>
                    <div className="h-40 w-full overflow-hidden rounded-lg bg-black/30 flex items-center justify-center mb-3">
                      {prod.image_url ? (
                        <img src={prod.image_url} alt={prod.name} className="h-full w-full object-cover group-hover:scale-105 transition-transform duration-300" />
                      ) : (
                        <span className="text-xs text-muted-foreground font-semibold uppercase">{prod.brand}</span>
                      )}
                    </div>
                    <span className="text-2xs font-bold text-yellow-450 uppercase tracking-wider block">{prod.brand}</span>
                    <h3 className="font-bold text-white leading-tight line-clamp-1 hover:text-yellow-450 transition-colors mt-0.5">{prod.name}</h3>
                  </Link>
                </div>
                <div className="flex justify-between items-center mt-3 pt-3 border-t border-white/5">
                  <span className="text-md font-black text-white">₹{Number(prod.price).toFixed(2)}</span>
                  <Link to={`/products/${prod.id}`} className="text-xs font-bold text-yellow-450 hover:underline">View details →</Link>
                </div>
              </TiltCard>
            ))}
          </div>
        </div>
      )}

      {/* Feature Section */}
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="text-center">
          <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
            {i18nMock('features.sectionTitle')}
          </h2>
          <p className="mx-auto mt-4 max-w-2xl text-base text-muted-foreground">
            {i18nMock('features.sectionSubtitle')}
          </p>
        </div>

        <div className="mx-auto mt-16 grid max-w-5xl grid-cols-1 gap-8 sm:grid-cols-2 lg:max-w-none">
          {features.map((feature, idx) => (
            <TiltCard
              key={idx}
              className="flex flex-col rounded-2xl border border-white/10 bg-white/5 p-8 backdrop-blur-sm group"
            >
              <div className="inline-flex h-12 w-12 items-center justify-center rounded-xl bg-white/5 border border-white/10 mb-6 group-hover:scale-110 transition-transform">
                {feature.icon}
              </div>
              <h3 className="text-xl font-bold text-white mb-2">{feature.title}</h3>
              <p className="text-sm leading-relaxed text-muted-foreground flex-grow">
                {feature.desc}
              </p>
            </TiltCard>
          ))}
        </div>
      </div>
    </div>
  );
};
