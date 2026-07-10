import React from 'react';
import { useTranslation } from 'react-i18next';
import { ArrowRight, Eye, Sparkles, LineChart, SplitSquareVertical } from 'lucide-react';

export const Home: React.FC = () => {
  const { t } = useTranslation();

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
    <div className="relative overflow-hidden py-16 sm:py-24 lg:py-32">
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
          <button className="flex items-center space-x-2 rounded-lg bg-primary px-6 py-3.5 text-sm font-semibold text-white shadow-md transition-all hover:bg-primary/90 hover:scale-105 active:scale-95">
            <span>{t('hero.ctaStart')}</span>
            <ArrowRight className="h-4 w-4" />
          </button>

          <button className="rounded-lg border border-border bg-background/50 px-6 py-3.5 text-sm font-semibold text-white transition-all hover:bg-muted hover:scale-105 active:scale-95">
            {t('hero.ctaDemo')}
          </button>
        </div>
      </div>

      {/* Feature Section */}
      <div className="mx-auto mt-24 max-w-7xl px-4 sm:px-6 lg:px-8">
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
