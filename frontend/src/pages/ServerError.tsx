import React from 'react';
import { ServerCrash, RefreshCw, Home } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export const ServerError: React.FC = () => {
  const navigate = useNavigate();

  const handleRetry = () => {
    window.location.reload();
  };

  const handleGoHome = () => {
    navigate('/');
    window.location.reload();
  };

  return (
    <div className="min-h-[70vh] flex flex-col items-center justify-center px-4 text-center">
      <div className="relative mb-8">
        <div className="absolute inset-0 bg-gradient-to-r from-red-500 to-amber-500 rounded-full blur-2xl opacity-20 scale-150 animate-pulse"></div>
        <div className="relative bg-slate-900 border border-red-500/20 p-6 rounded-full">
          <ServerCrash className="h-16 w-16 text-red-500 animate-bounce" />
        </div>
      </div>

      <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-red-400 via-amber-400 to-orange-500 mb-4">
        500 - Server Error
      </h1>
      
      <p className="max-w-md text-slate-400 text-lg mb-8 leading-relaxed">
        Something went wrong on our end. The server encountered an internal error or misconfiguration.
      </p>

      <div className="flex flex-col sm:flex-row gap-4 justify-center">
        <button
          onClick={handleRetry}
          className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-semibold shadow-lg hover:shadow-indigo-500/20 transition-all duration-200"
        >
          <RefreshCw className="h-4 w-4" />
          Retry Request
        </button>
        <button
          onClick={handleGoHome}
          className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold border border-slate-700/50 transition-colors duration-200"
        >
          <Home className="h-4 w-4" />
          Back to Home
        </button>
      </div>
    </div>
  );
};
