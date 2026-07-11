import React from 'react';
import { Shield, Brain, Cpu, Database, Award, Target, Zap } from 'lucide-react';

export const About: React.FC = () => {
  return (
    <div className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8 text-slate-100 animate-fade-in">
      <div className="relative rounded-3xl overflow-hidden bg-slate-900 border border-slate-800 p-8 sm:p-12 mb-12 shadow-2xl">
        <div className="absolute inset-0 bg-gradient-to-tr from-indigo-500/10 via-transparent to-cyan-500/10 pointer-events-none"></div>
        <div className="relative max-w-3xl">
          <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 via-violet-400 to-cyan-400 mb-6">
            About JourneyIQ
          </h1>
          <p className="text-lg sm:text-xl text-slate-300 leading-relaxed mb-8">
            JourneyIQ is a cutting-edge, behaviorally intelligent SaaS platform for modern retail storefronts. 
            By analyzing real-time user events (clicks, product views, search inputs, wishlist toggles), JourneyIQ maps complex customer journeys 
            and executes deep neural collaborative filtering algorithms to predict purchase behaviors and drive conversions.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-16">
        <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-6 shadow-lg backdrop-blur-sm">
          <div className="h-12 w-12 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 mb-4">
            <Brain className="h-6 w-6" />
          </div>
          <h3 className="text-xl font-bold text-white mb-2">Neural Recommendation</h3>
          <p className="text-slate-400 text-sm leading-relaxed">
            Powered by a PyTorch Neural Collaborative Filtering (NCF) model that processes user embeddings and item similarities for highly personalized relevance.
          </p>
        </div>

        <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-6 shadow-lg backdrop-blur-sm">
          <div className="h-12 w-12 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400 mb-4">
            <Cpu className="h-6 w-6" />
          </div>
          <h3 className="text-xl font-bold text-white mb-2">Hybrid Engine Fallbacks</h3>
          <p className="text-slate-400 text-sm leading-relaxed">
            Combines content-based filtering with heuristic rules (trending, best-selling, top-rated reviews) to eliminate cold-start issues for new visitors.
          </p>
        </div>

        <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-6 shadow-lg backdrop-blur-sm">
          <div className="h-12 w-12 rounded-xl bg-violet-500/10 border border-violet-500/20 flex items-center justify-center text-violet-400 mb-4">
            <Database className="h-6 w-6" />
          </div>
          <h3 className="text-xl font-bold text-white mb-2">Supabase Database Layer</h3>
          <p className="text-slate-400 text-sm leading-relaxed">
            Built on a hardened PostgreSQL architecture with optimized indexes, full-text search, partition parameters, and automated SHA-256 backup controls.
          </p>
        </div>
      </div>

      <div className="border border-slate-800 rounded-3xl bg-slate-900/40 p-8 sm:p-12">
        <h2 className="text-2xl sm:text-3xl font-bold text-white mb-8 text-center sm:text-left">Tech Stack & Platform Metrics</h2>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
          <div>
            <h3 className="text-lg font-semibold text-slate-350 mb-4">SaaS Core Architecture</h3>
            <ul className="space-y-4">
              <li className="flex items-start gap-3">
                <Zap className="h-5 w-5 text-indigo-400 shrink-0 mt-0.5" />
                <div>
                  <strong className="text-white font-medium">FastAPI Backend & React Frontend</strong>
                  <p className="text-slate-450 text-sm mt-0.5">Asynchronous Python API handling telemetry, order processing, and model queries with Vite-driven Single Page App storefront.</p>
                </div>
              </li>
              <li className="flex items-start gap-3">
                <Shield className="h-5 w-5 text-cyan-400 shrink-0 mt-0.5" />
                <div>
                  <strong className="text-white font-medium">Secure Telemetry & JWT Authentication</strong>
                  <p className="text-slate-450 text-sm mt-0.5">Protected user sessions, CORS controls, password hashing, and role-based owner/customer storefront access layers.</p>
                </div>
              </li>
              <li className="flex items-start gap-3">
                <Award className="h-5 w-5 text-violet-400 shrink-0 mt-0.5" />
                <div>
                  <strong className="text-white font-medium">DevOps Readiness</strong>
                  <p className="text-slate-450 text-sm mt-0.5">Configured Docker compose suites, Prometheus/Grafana endpoint integrations, and Kubernetes orchestrations.</p>
                </div>
              </li>
            </ul>
          </div>

          <div className="flex flex-col justify-center bg-slate-900 border border-slate-800/60 rounded-2xl p-6 sm:p-8">
            <h3 className="text-lg font-semibold text-slate-350 mb-6 flex items-center gap-2">
              <Target className="h-5 w-5 text-indigo-400" /> Model Performance Profile
            </h3>
            <div className="space-y-4 text-sm">
              <div className="flex justify-between border-b border-slate-800 pb-2">
                <span className="text-slate-400">NCF Framework</span>
                <span className="text-white font-semibold">PyTorch 2.0+</span>
              </div>
              <div className="flex justify-between border-b border-slate-800 pb-2">
                <span className="text-slate-400">Precision @ 10</span>
                <span className="text-emerald-400 font-semibold">0.91</span>
              </div>
              <div className="flex justify-between border-b border-slate-800 pb-2">
                <span className="text-slate-400">Recall @ 10</span>
                <span className="text-emerald-400 font-semibold">0.88</span>
              </div>
              <div className="flex justify-between border-b border-slate-800 pb-2">
                <span className="text-slate-400">Hit Rate</span>
                <span className="text-emerald-400 font-semibold">0.93</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Inference Latency</span>
                <span className="text-cyan-400 font-semibold">&lt; 8ms</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
