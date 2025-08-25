/**
 * User Preferences Store
 * Manages user settings, themes, and personalization options
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type Theme = 'light' | 'dark' | 'corporate';
export type DateFormat = 'US' | 'EU' | 'ISO';
export type NumberFormat = 'US' | 'EU' | 'UK';

export interface UserPreferences {
  // Theme and appearance
  theme: Theme;
  compactMode: boolean;
  showAIBadges: boolean;
  animationsEnabled: boolean;
  
  // Data display
  dateFormat: DateFormat;
  numberFormat: NumberFormat;
  defaultCurrency: string;
  rowsPerPage: number;
  
  // Workflow preferences
  autoRefresh: boolean;
  refreshInterval: number; // seconds
  confirmActions: boolean;
  keyboardShortcutsEnabled: boolean;
  
  // Notifications
  showNotifications: boolean;
  soundEnabled: boolean;
  
  // Corporate branding
  corporateLogo?: string;
  corporateColors?: {
    primary: string;
    secondary: string;
    accent: string;
  };
}

interface UserPreferencesStore extends UserPreferences {
  // Actions
  setTheme: (theme: Theme) => void;
  setCompactMode: (compact: boolean) => void;
  setShowAIBadges: (show: boolean) => void;
  setAnimationsEnabled: (enabled: boolean) => void;
  setDateFormat: (format: DateFormat) => void;
  setNumberFormat: (format: NumberFormat) => void;
  setDefaultCurrency: (currency: string) => void;
  setRowsPerPage: (rows: number) => void;
  setAutoRefresh: (enabled: boolean) => void;
  setRefreshInterval: (seconds: number) => void;
  setConfirmActions: (confirm: boolean) => void;
  setKeyboardShortcutsEnabled: (enabled: boolean) => void;
  setShowNotifications: (show: boolean) => void;
  setSoundEnabled: (enabled: boolean) => void;
  setCorporateLogo: (logo?: string) => void;
  setCorporateColors: (colors?: { primary: string; secondary: string; accent: string }) => void;
  resetToDefaults: () => void;
}

const defaultPreferences: UserPreferences = {
  theme: 'light',
  compactMode: false,
  showAIBadges: true,
  animationsEnabled: true,
  dateFormat: 'US',
  numberFormat: 'US',
  defaultCurrency: 'USD',
  rowsPerPage: 25,
  autoRefresh: true,
  refreshInterval: 30,
  confirmActions: true,
  keyboardShortcutsEnabled: true,
  showNotifications: true,
  soundEnabled: false,
};

export const useUserPreferencesStore = create<UserPreferencesStore>()(
  persist(
    (set) => ({
      ...defaultPreferences,
      
      setTheme: (theme) => set({ theme }),
      setCompactMode: (compactMode) => set({ compactMode }),
      setShowAIBadges: (showAIBadges) => set({ showAIBadges }),
      setAnimationsEnabled: (animationsEnabled) => set({ animationsEnabled }),
      setDateFormat: (dateFormat) => set({ dateFormat }),
      setNumberFormat: (numberFormat) => set({ numberFormat }),
      setDefaultCurrency: (defaultCurrency) => set({ defaultCurrency }),
      setRowsPerPage: (rowsPerPage) => set({ rowsPerPage }),
      setAutoRefresh: (autoRefresh) => set({ autoRefresh }),
      setRefreshInterval: (refreshInterval) => set({ refreshInterval }),
      setConfirmActions: (confirmActions) => set({ confirmActions }),
      setKeyboardShortcutsEnabled: (keyboardShortcutsEnabled) => set({ keyboardShortcutsEnabled }),
      setShowNotifications: (showNotifications) => set({ showNotifications }),
      setSoundEnabled: (soundEnabled) => set({ soundEnabled }),
      setCorporateLogo: (corporateLogo) => set({ corporateLogo }),
      setCorporateColors: (corporateColors) => set({ corporateColors }),
      
      resetToDefaults: () => set(defaultPreferences),
    }),
    {
      name: 'r2r-user-preferences',
      version: 1,
    }
  )
);

// Theme utilities
export const getThemeClasses = (theme: Theme, corporateColors?: UserPreferences['corporateColors']) => {
  const baseClasses = {
    light: {
      bg: 'bg-white',
      text: 'text-gray-900',
      border: 'border-gray-200',
      hover: 'hover:bg-gray-50',
      accent: 'bg-blue-600 text-white',
    },
    dark: {
      bg: 'bg-gray-900',
      text: 'text-gray-100',
      border: 'border-gray-700',
      hover: 'hover:bg-gray-800',
      accent: 'bg-blue-500 text-white',
    },
    corporate: {
      bg: 'bg-slate-50',
      text: 'text-slate-900',
      border: 'border-slate-300',
      hover: 'hover:bg-slate-100',
      accent: corporateColors?.primary ? `bg-[${corporateColors.primary}] text-white` : 'bg-indigo-600 text-white',
    },
  };
  
  return baseClasses[theme];
};

// Format utilities
export const formatDate = (date: Date | string, format: DateFormat): string => {
  const d = typeof date === 'string' ? new Date(date) : date;
  
  switch (format) {
    case 'US':
      return d.toLocaleDateString('en-US');
    case 'EU':
      return d.toLocaleDateString('en-GB');
    case 'ISO':
      return d.toISOString().split('T')[0];
    default:
      return d.toLocaleDateString();
  }
};

export const formatNumber = (num: number, format: NumberFormat, currency?: string): string => {
  const options: Intl.NumberFormatOptions = {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  };
  
  if (currency) {
    options.style = 'currency';
    options.currency = currency;
  }
  
  switch (format) {
    case 'US':
      return new Intl.NumberFormat('en-US', options).format(num);
    case 'EU':
      return new Intl.NumberFormat('de-DE', options).format(num);
    case 'UK':
      return new Intl.NumberFormat('en-GB', options).format(num);
    default:
      return new Intl.NumberFormat('en-US', options).format(num);
  }
};
