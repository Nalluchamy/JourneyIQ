import React from 'react';
import { HelpCircle, ArrowLeft, Home } from 'lucide-react';
import { Link } from 'react-router-dom';

export const NotFound: React.FC = () => {
  return (
    <div className="min-h-[70vh] flex flex-col items-center justify-center px-4 text-center">
      <div className="relative mb-8">
        <div className="absolute inset-0 bg-gradient-to-r from-indigo-500 to-cyan-500 rounded-full blur-2xl opacity-20 scale-150 animate-pulse"></div>
        <div className="relative bg-slate-900 border border-indigo-500/20 p-6 rounded-full">
          <HelpCircle className="h-16 w-16 text-indigo-400" />
        </div>
      </div>

      <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 via-violet-400 to-cyan-400 mb-4">
        404 - Page Not Found
      </h1>
      
      <p className="max-w-md text-slate-400 text-lg mb-8 leading-relaxed">
        The page you are looking for might have been removed, had its name changed, or is temporarily unavailable.
      </p>

      <div className="flex flex-col sm:flex-row gap-4 justify-center">
        <Link
          to="/"
          className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-indigo-600 to-cyan-600 hover:from-indigo-500 hover:to-cyan-500 text-white font-semibold shadow-lg hover:shadow-indigo-500/20 transition-all duration-200"
        >
          <Home className="h-4 w-4" />
          Back to Home
        </Link>
        <Link
          to="/products"
          className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold border border-slate-700/50 transition-colors duration-200"
        >
          <ArrowLeft className="h-4 w-4" />
          Browse Catalog
        </Link>
      </div>
    </div>
  );
};
