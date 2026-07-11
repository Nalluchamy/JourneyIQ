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
  const { t } = useTranslation();
  const isAuthenticated = !!localStorage.getItem('token');

  const [recommended, setRecommended] = useState<Recommendation[]>([]);
  const [trending, setTrending] = useState<Product[]>([]);
  const [popular, setPopular] = useState<Product[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchRecommendations = async () => {
      try {
        setLoading(true);
        if (isAuthenticated) {
          const recData = await recommendationsApi.getPersonalized();
          setRecommended(recData || []);

          // Track recommendation views event
          if (recData && recData.length > 0) {
            const firstRecId = recData[0].product_id;
            eventsApi.trackEvent('recommendation_view', '/', firstRecId, {
              count: recData.length,
              recommended_pids: recData.map((r: any) => r.product_id),
            });
          }
        }

        const trendData = await recommendationsApi.getTrending();
        setTrending(trendData || []);

        const popData = await recommendationsApi.getPopular();
        setPopular(popData || []);
      } catch (err) {
        console.error('Failed to load recommendation blocks:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchRecommendations();
  }, [isAuthenticated]);

  const handleRecClick = (productId: number) => {
    eventsApi.trackEvent('recommendation_click', '/', productId, { source: 'homepage_recommended' });
  };

  const features = [
    {
      title: t('features.f1.title'),
      desc: t('features.f1.desc'),
      icon: <Eye className="h-6 w-6 text-primary" />,
    },
    {
      title: t('features.f2.title'),
      desc: t('features.f2.desc'),
      icon: <Sparkles className="h-6 w-6 text-indigo-400" />,
    },
    {
      title: t('features.f3.title'),
      desc: t('features.f3.desc'),
      icon: <LineChart className="h-6 w-6 text-cyan-400" />,
    },
    {
      title: t('features.f4.title'),
      desc: t('features.f4.desc'),
      icon: <SplitSquareVertical className="h-6 w-6 text-violet-400" />,
    },
  ];

  return (
    <div className="relative overflow-hidden py-16 sm:py-24 lg:py-32 space-y-24">
      {/* Background Gradient Orbs */}
      <div className="absolute top-0 left-1/4 -z-10 h-96 w-96 rounded-full bg-primary/20 blur-3xl" />
      <div className="absolute bottom-10 right-1/4 -z-10 h-96 w-96 rounded-full bg-indigo-500/10 blur-3xl" />

      {/* Hero Section */}
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 text-center">
        <div className="inline-flex items-center space-x-2 rounded-full border border-border bg-muted/50 px-4 py-1.5 text-xs text-muted-foreground transition-all hover:bg-muted/80 mb-6">
          <span className="flex h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
          <span>{t('hero.badge')}</span>
        </div>

        <h1 className="mx-auto max-w-4xl text-4xl font-extrabold tracking-tight text-white sm:text-5xl lg:text-6xl bg-clip-text text-transparent bg-gradient-to-r from-white via-slate-200 to-zinc-400">
          {t('hero.title')}
        </h1>

        <p className="mx-auto mt-6 max-w-2xl text-lg text-muted-foreground sm:text-xl">
          {t('hero.subtitle')}
        </p>

        <div className="mt-10 flex flex-wrap justify-center gap-4">
          <Link to="/products" className="flex items-center space-x-2 rounded-lg bg-primary px-6 py-3.5 text-sm font-semibold text-white shadow-md transition-all hover:bg-primary/90 hover:scale-105 active:scale-95">
            <span>{t('hero.ctaStart')}</span>
            <ArrowRight className="h-4 w-4" />
          </Link>

          {!isAuthenticated && (
            <Link to="/login" className="rounded-lg border border-border bg-background/50 px-6 py-3.5 text-sm font-semibold text-white transition-all hover:bg-muted hover:scale-105 active:scale-95">
              {t('hero.ctaDemo')}
            </Link>
          )}
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
              <div
                key={rec.id}
                className="flex flex-col justify-between overflow-hidden rounded-2xl border border-border bg-card p-4 transition-all hover:border-primary/50 hover:shadow-lg hover:shadow-primary/5 group"
              >
                <div>
                  {rec.explanation && (
                    <span className="inline-block px-2 py-0.5 mb-2 bg-primary/10 border border-primary/20 text-primary text-[10px] font-extrabold uppercase rounded">
                      💡 {rec.explanation}
                    </span>
                  )}
                  <Link to={`/products/${rec.product.id}`} onClick={() => handleRecClick(rec.product.id)}>
                    <div className="h-40 w-full overflow-hidden rounded-lg bg-muted flex items-center justify-center text-xs text-muted-foreground font-semibold uppercase mb-3">
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
                    <h3 className="font-bold text-white leading-tight line-clamp-1 hover:text-primary transition-colors">
                      {rec.product.name}
                    </h3>
                  </Link>
                </div>
                <div className="flex justify-between items-center mt-3 pt-3 border-t border-border/50">
                  <span className="text-md font-black text-white">${Number(rec.product.price).toFixed(2)}</span>
                  <Link
                    to={`/products/${rec.product.id}`}
                    onClick={() => handleRecClick(rec.product.id)}
                    className="text-xs font-bold text-primary hover:underline"
                  >
                    View details →
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Trending Products */}
      {trending.length > 0 && (
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex items-center space-x-2.5 mb-6">
            <Flame className="h-6 w-6 text-orange-500 animate-pulse" />
            <h2 className="text-2xl font-black text-white tracking-tight">Trending Products</h2>
          </div>
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
            {trending.map((prod) => (
              <div
                key={prod.id}
                className="flex flex-col justify-between overflow-hidden rounded-2xl border border-border bg-card p-4 transition-all hover:border-orange-500/40 hover:shadow-lg hover:shadow-orange-500/5 group"
              >
                <div>
                  <span className="inline-block px-2 py-0.5 mb-2 bg-orange-500/10 border border-orange-500/20 text-orange-450 text-[10px] font-extrabold uppercase rounded">
                    🔥 HOT VIEW
                  </span>
                  <Link to={`/products/${prod.id}`}>
                    <div className="h-40 w-full overflow-hidden rounded-lg bg-muted flex items-center justify-center mb-3">
                      {prod.image_url ? (
                        <img src={prod.image_url} alt={prod.name} className="h-full w-full object-cover group-hover:scale-105 transition-transform duration-300" />
                      ) : (
                        <span className="text-xs text-muted-foreground font-semibold uppercase">{prod.brand}</span>
                      )}
                    </div>
                    <span className="text-2xs font-bold text-orange-450 uppercase tracking-wider block">{prod.brand}</span>
                    <h3 className="font-bold text-white leading-tight line-clamp-1 hover:text-orange-450 transition-colors">{prod.name}</h3>
                  </Link>
                </div>
                <div className="flex justify-between items-center mt-3 pt-3 border-t border-border/50">
                  <span className="text-md font-black text-white">${Number(prod.price).toFixed(2)}</span>
                  <Link to={`/products/${prod.id}`} className="text-xs font-bold text-orange-450 hover:underline">View details →</Link>
                </div>
              </div>
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
              <div
                key={prod.id}
                className="flex flex-col justify-between overflow-hidden rounded-2xl border border-border bg-card p-4 transition-all hover:border-yellow-500/40 hover:shadow-lg hover:shadow-yellow-500/5 group"
              >
                <div>
                  <span className="inline-block px-2 py-0.5 mb-2 bg-yellow-500/10 border border-yellow-500/20 text-yellow-450 text-[10px] font-extrabold uppercase rounded">
                    ⭐ TOP SELLER
                  </span>
                  <Link to={`/products/${prod.id}`}>
                    <div className="h-40 w-full overflow-hidden rounded-lg bg-muted flex items-center justify-center mb-3">
                      {prod.image_url ? (
                        <img src={prod.image_url} alt={prod.name} className="h-full w-full object-cover group-hover:scale-105 transition-transform duration-300" />
                      ) : (
                        <span className="text-xs text-muted-foreground font-semibold uppercase">{prod.brand}</span>
                      )}
                    </div>
                    <span className="text-2xs font-bold text-yellow-450 uppercase tracking-wider block">{prod.brand}</span>
                    <h3 className="font-bold text-white leading-tight line-clamp-1 hover:text-yellow-450 transition-colors">{prod.name}</h3>
                  </Link>
                </div>
                <div className="flex justify-between items-center mt-3 pt-3 border-t border-border/50">
                  <span className="text-md font-black text-white">${Number(prod.price).toFixed(2)}</span>
                  <Link to={`/products/${prod.id}`} className="text-xs font-bold text-yellow-450 hover:underline">View details →</Link>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Feature Section */}
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="text-center">
          <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
            {t('features.sectionTitle')}
          </h2>
          <p className="mx-auto mt-4 max-w-2xl text-base text-muted-foreground">
            {t('features.sectionSubtitle')}
          </p>
        </div>

        <div className="mx-auto mt-16 grid max-w-5xl grid-cols-1 gap-8 sm:grid-cols-2 lg:max-w-none">
          {features.map((feature, idx) => (
            <div
              key={idx}
              className="flex flex-col rounded-2xl border border-border bg-card/40 p-8 transition-all hover:border-primary/40 hover:bg-card/70 hover:shadow-lg hover:shadow-primary/5 group"
            >
              <div className="inline-flex h-12 w-12 items-center justify-center rounded-xl bg-muted/80 mb-6 group-hover:scale-110 transition-transform">
                {feature.icon}
              </div>
              <h3 className="text-xl font-bold text-white mb-2">{feature.title}</h3>
              <p className="text-sm leading-relaxed text-muted-foreground flex-grow">
                {feature.desc}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
