/**
 * i18n configuration for multi-language support
 */
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

import enUS from '../locales/en-US.json';
import zhCN from '../locales/zh-CN.json';

// Initialize i18next
i18n
  .use(initReactI18next) // Bind react-i18next to the i18next instance
  .init({
    resources: {
      en: {
        translation: enUS,
      },
      zh: {
        translation: zhCN,
      },
    },
    lng: localStorage.getItem('language') || 'en', // Default language
    fallbackLng: 'en', // Fallback language if translation is missing
    interpolation: {
      escapeValue: false, // React already escapes values
    },
    react: {
      useSuspense: true,
    },
  });

// Save language preference when it changes
i18n.on('languageChanged', (lng: string) => {
  localStorage.setItem('language', lng);
});

export default i18n;
