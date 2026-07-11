import React, { useState } from 'react';
import { WifiOff, RefreshCw } from 'lucide-react';

export const OfflinePage: React.FC = () => {
  const [isReconnecting, setIsReconnecting] = useState(false);

  const checkConnection = () => {
    setIsReconnecting(true);
    setTimeout(() => {
      setIsReconnecting(false);
      if (navigator.onLine) {
        window.location.reload();
      }
    }, 1000);
  };

  return (
    <div className="min-h-[70vh] flex flex-col items-center justify-center px-4 text-center">
      <div className="relative mb-8">
        <div className="absolute inset-0 bg-gradient-to-r from-slate-500 to-indigo-500 rounded-full blur-2xl opacity-20 scale-150 animate-pulse"></div>
        <div className="relative bg-slate-900 border border-slate-700/35 p-6 rounded-full">
          <WifiOff className="h-16 w-16 text-slate-400" />
        </div>
      </div>

      <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-slate-300 via-indigo-400 to-slate-300 mb-4">
        You are Offline
      </h1>
      
      <p className="max-w-md text-slate-400 text-lg mb-8 leading-relaxed">
        Please check your internet connection. We will automatically reconnect you once a connection is re-established.
      </p>

      <button
        onClick={checkConnection}
        disabled={isReconnecting}
        className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-slate-700 to-indigo-700 hover:from-slate-600 hover:to-indigo-600 disabled:from-slate-800 disabled:to-indigo-900 text-white font-semibold shadow-lg hover:shadow-indigo-500/10 transition-all duration-200"
      >
        <RefreshCw className={`h-4 w-4 ${isReconnecting ? 'animate-spin' : ''}`} />
        {isReconnecting ? 'Checking Connection...' : 'Check Connection'}
      </button>
    </div>
  );
};
