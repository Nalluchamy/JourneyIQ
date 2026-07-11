import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import './index.css';
import App from './App.tsx';

// Register PWA Service Worker for offline asset caching
if ('serviceWorker' in navigator && import.meta.env.PROD) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js')
      .then((reg) => {
        console.log('JourneyIQ Service Worker registered successfully: ', reg.scope);
      })
      .catch((err) => {
        console.error('Service Worker registration failed: ', err);
      });
  });
}

// Intercept PWA Install Prompts for user experience
let deferredPrompt: any = null;
window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredPrompt = e;
  // Trigger custom notification event or log prompt available
  console.log('beforeinstallprompt event triggered. JourneyIQ is ready for PWA installation.');
});

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>
);

