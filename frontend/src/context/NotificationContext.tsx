import React, { createContext, useState, useContext, useCallback } from 'react';
import { X, CheckCircle, AlertCircle, Info } from 'lucide-react';

export type NotificationType = 'success' | 'error' | 'info';

export interface Notification {
  id: string;
  type: NotificationType;
  message: string;
  duration?: number;
}

interface NotificationContextProps {
  showNotification: (message: string, type: NotificationType, duration?: number) => void;
}

const NotificationContext = createContext<NotificationContextProps | undefined>(undefined);

export const useNotification = () => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotification must be used within a NotificationProvider');
  }
  return context;
};

export const NotificationProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [notifications, setNotifications] = useState<Notification[]>([]);

  const showNotification = useCallback((message: string, type: NotificationType, duration = 4000) => {
    const id = Math.random().toString(36).substring(2, 9);
    setNotifications((prev) => [...prev, { id, type, message, duration }]);

    setTimeout(() => {
      setNotifications((prev) => prev.filter((n) => n.id !== id));
    }, duration);
  }, []);

  const removeNotification = (id: string) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id));
  };

  return (
    <NotificationContext.Provider value={{ showNotification }}>
      {children}
      {/* Toast Alert Portal container */}
      <div className="fixed bottom-5 right-5 z-50 flex flex-col gap-3 max-w-sm w-full pointer-events-none">
        {notifications.map((n) => (
          <div
            key={n.id}
            className={`pointer-events-auto flex items-start gap-3 rounded-xl border p-4 shadow-xl transition-all duration-300 transform translate-y-0 animate-in slide-in-from-bottom-5 duration-300 ${
              n.type === 'success'
                ? 'bg-slate-900/90 border-emerald-500/30 text-white'
                : n.type === 'error'
                ? 'bg-slate-900/90 border-red-500/30 text-white'
                : 'bg-slate-900/90 border-cyan-500/30 text-white'
            }`}
            style={{
              backdropFilter: 'blur(12px)',
              boxShadow: n.type === 'success' 
                ? '0 10px 25px -5px rgba(16, 185, 129, 0.15)' 
                : n.type === 'error'
                ? '0 10px 25px -5px rgba(239, 68, 68, 0.15)'
                : '0 10px 25px -5px rgba(6, 182, 212, 0.15)'
            }}
          >
            {n.type === 'success' && <CheckCircle className="h-5 w-5 text-emerald-400 shrink-0 mt-0.5" />}
            {n.type === 'error' && <AlertCircle className="h-5 w-5 text-red-450 shrink-0 mt-0.5" />}
            {n.type === 'info' && <Info className="h-5 w-5 text-cyan-400 shrink-0 mt-0.5" />}

            <div className="flex-1 text-sm font-semibold leading-relaxed">
              {n.message}
            </div>

            <button
              onClick={() => removeNotification(n.id)}
              className="text-slate-400 hover:text-white transition-colors"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        ))}
      </div>
    </NotificationContext.Provider>
  );
};
