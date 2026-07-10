import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import enTranslation from './en.json';

i18n.use(initReactI18next).init({
  resources: {
    en: {
      translation: enTranslation,
    },
  },
  lng: 'en',
  fallbackLng: 'en',
  interpolation: {
    escapeValue: false, // React already protects against XSS
  },
});

export default i18n;
