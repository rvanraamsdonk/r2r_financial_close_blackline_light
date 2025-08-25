/**
 * User Settings Panel
 * Comprehensive preferences and theme management interface
 */

import { useState } from 'react';
import { 
  Settings, 
  X, 
  Palette, 
  Monitor, 
  Bell, 
  Zap,
  Volume2,
  VolumeX
} from 'lucide-react';
import { useUserPreferencesStore, type Theme, type DateFormat, type NumberFormat } from '../stores/userPreferencesStore.js';

interface UserSettingsPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

export const UserSettingsPanel: React.FC<UserSettingsPanelProps> = ({ isOpen, onClose }) => {
  const [activeTab, setActiveTab] = useState<'appearance' | 'display' | 'workflow' | 'notifications'>('appearance');
  
  const {
    theme,
    compactMode,
    showAIBadges,
    animationsEnabled,
    dateFormat,
    numberFormat,
    defaultCurrency,
    rowsPerPage,
    autoRefresh,
    refreshInterval,
    confirmActions,
    keyboardShortcutsEnabled,
    showNotifications,
    soundEnabled,
    corporateLogo,
    corporateColors,
    setTheme,
    setCompactMode,
    setShowAIBadges,
    setAnimationsEnabled,
    setDateFormat,
    setNumberFormat,
    setDefaultCurrency,
    setRowsPerPage,
    setAutoRefresh,
    setRefreshInterval,
    setConfirmActions,
    setKeyboardShortcutsEnabled,
    setShowNotifications,
    setSoundEnabled,
    setCorporateLogo,
    setCorporateColors,
    resetToDefaults,
  } = useUserPreferencesStore();

  if (!isOpen) return null;

  const tabs = [
    { id: 'appearance', label: 'Appearance', icon: Palette },
    { id: 'display', label: 'Display', icon: Monitor },
    { id: 'workflow', label: 'Workflow', icon: Zap },
    { id: 'notifications', label: 'Notifications', icon: Bell },
  ] as const;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center space-x-2">
            <Settings className="w-5 h-5 text-gray-600" />
            <h2 className="text-xl font-semibold text-gray-900">User Preferences</h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="flex">
          {/* Sidebar */}
          <div className="w-64 bg-gray-50 border-r border-gray-200">
            <nav className="p-4 space-y-1">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`w-full flex items-center space-x-3 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                      activeTab === tab.id
                        ? 'bg-blue-100 text-blue-700'
                        : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    <span>{tab.label}</span>
                  </button>
                );
              })}
            </nav>
          </div>

          {/* Content */}
          <div className="flex-1 p-6 overflow-y-auto max-h-[calc(90vh-80px)]">
            {activeTab === 'appearance' && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Theme & Appearance</h3>
                  
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Theme</label>
                      <div className="grid grid-cols-3 gap-3">
                        {(['light', 'dark', 'corporate'] as Theme[]).map((themeOption) => (
                          <button
                            key={themeOption}
                            onClick={() => setTheme(themeOption)}
                            className={`p-3 rounded-lg border-2 transition-colors ${
                              theme === themeOption
                                ? 'border-blue-500 bg-blue-50'
                                : 'border-gray-200 hover:border-gray-300'
                            }`}
                          >
                            <div className="text-sm font-medium capitalize">{themeOption}</div>
                            <div className="text-xs text-gray-500 mt-1">
                              {themeOption === 'light' && 'Clean & bright'}
                              {themeOption === 'dark' && 'Easy on eyes'}
                              {themeOption === 'corporate' && 'Professional'}
                            </div>
                          </button>
                        ))}
                      </div>
                    </div>

                    <div className="flex items-center justify-between">
                      <div>
                        <label className="text-sm font-medium text-gray-700">Compact Mode</label>
                        <p className="text-xs text-gray-500">Reduce spacing for more data density</p>
                      </div>
                      <button
                        onClick={() => setCompactMode(!compactMode)}
                        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                          compactMode ? 'bg-blue-600' : 'bg-gray-200'
                        }`}
                      >
                        <span
                          className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                            compactMode ? 'translate-x-6' : 'translate-x-1'
                          }`}
                        />
                      </button>
                    </div>

                    <div className="flex items-center justify-between">
                      <div>
                        <label className="text-sm font-medium text-gray-700">Show AI Badges</label>
                        <p className="text-xs text-gray-500">Display AI transparency indicators</p>
                      </div>
                      <button
                        onClick={() => setShowAIBadges(!showAIBadges)}
                        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                          showAIBadges ? 'bg-blue-600' : 'bg-gray-200'
                        }`}
                      >
                        <span
                          className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                            showAIBadges ? 'translate-x-6' : 'translate-x-1'
                          }`}
                        />
                      </button>
                    </div>

                    <div className="flex items-center justify-between">
                      <div>
                        <label className="text-sm font-medium text-gray-700">Animations</label>
                        <p className="text-xs text-gray-500">Enable smooth transitions and effects</p>
                      </div>
                      <button
                        onClick={() => setAnimationsEnabled(!animationsEnabled)}
                        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                          animationsEnabled ? 'bg-blue-600' : 'bg-gray-200'
                        }`}
                      >
                        <span
                          className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                            animationsEnabled ? 'translate-x-6' : 'translate-x-1'
                          }`}
                        />
                      </button>
                    </div>
                  </div>
                </div>

                {theme === 'corporate' && (
                  <div>
                    <h4 className="text-md font-medium text-gray-900 mb-3">Corporate Branding</h4>
                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">Logo URL</label>
                        <input
                          type="url"
                          value={corporateLogo || ''}
                          onChange={(e) => setCorporateLogo(e.target.value || undefined)}
                          placeholder="https://example.com/logo.png"
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">Brand Colors</label>
                        <div className="grid grid-cols-3 gap-3">
                          <div>
                            <label className="block text-xs text-gray-500 mb-1">Primary</label>
                            <input
                              type="color"
                              value={corporateColors?.primary || '#4f46e5'}
                              onChange={(e) => setCorporateColors({
                                ...corporateColors,
                                primary: e.target.value,
                                secondary: corporateColors?.secondary || '#6b7280',
                                accent: corporateColors?.accent || '#059669'
                              })}
                              className="w-full h-10 rounded border border-gray-300"
                            />
                          </div>
                          <div>
                            <label className="block text-xs text-gray-500 mb-1">Secondary</label>
                            <input
                              type="color"
                              value={corporateColors?.secondary || '#6b7280'}
                              onChange={(e) => setCorporateColors({
                                ...corporateColors,
                                primary: corporateColors?.primary || '#4f46e5',
                                secondary: e.target.value,
                                accent: corporateColors?.accent || '#059669'
                              })}
                              className="w-full h-10 rounded border border-gray-300"
                            />
                          </div>
                          <div>
                            <label className="block text-xs text-gray-500 mb-1">Accent</label>
                            <input
                              type="color"
                              value={corporateColors?.accent || '#059669'}
                              onChange={(e) => setCorporateColors({
                                ...corporateColors,
                                primary: corporateColors?.primary || '#4f46e5',
                                secondary: corporateColors?.secondary || '#6b7280',
                                accent: e.target.value
                              })}
                              className="w-full h-10 rounded border border-gray-300"
                            />
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'display' && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Data Display</h3>
                  
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Date Format</label>
                      <select
                        value={dateFormat}
                        onChange={(e) => setDateFormat(e.target.value as DateFormat)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="US">US (MM/DD/YYYY)</option>
                        <option value="EU">European (DD/MM/YYYY)</option>
                        <option value="ISO">ISO (YYYY-MM-DD)</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Number Format</label>
                      <select
                        value={numberFormat}
                        onChange={(e) => setNumberFormat(e.target.value as NumberFormat)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="US">US (1,234.56)</option>
                        <option value="EU">European (1.234,56)</option>
                        <option value="UK">UK (1,234.56)</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Default Currency</label>
                      <select
                        value={defaultCurrency}
                        onChange={(e) => setDefaultCurrency(e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="USD">USD - US Dollar</option>
                        <option value="EUR">EUR - Euro</option>
                        <option value="GBP">GBP - British Pound</option>
                        <option value="JPY">JPY - Japanese Yen</option>
                        <option value="CAD">CAD - Canadian Dollar</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Rows Per Page</label>
                      <select
                        value={rowsPerPage}
                        onChange={(e) => setRowsPerPage(Number(e.target.value))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value={10}>10 rows</option>
                        <option value={25}>25 rows</option>
                        <option value={50}>50 rows</option>
                        <option value={100}>100 rows</option>
                      </select>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'workflow' && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Workflow Settings</h3>
                  
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <label className="text-sm font-medium text-gray-700">Auto Refresh</label>
                        <p className="text-xs text-gray-500">Automatically refresh data</p>
                      </div>
                      <button
                        onClick={() => setAutoRefresh(!autoRefresh)}
                        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                          autoRefresh ? 'bg-blue-600' : 'bg-gray-200'
                        }`}
                      >
                        <span
                          className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                            autoRefresh ? 'translate-x-6' : 'translate-x-1'
                          }`}
                        />
                      </button>
                    </div>

                    {autoRefresh && (
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">Refresh Interval</label>
                        <select
                          value={refreshInterval}
                          onChange={(e) => setRefreshInterval(Number(e.target.value))}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                          <option value={15}>15 seconds</option>
                          <option value={30}>30 seconds</option>
                          <option value={60}>1 minute</option>
                          <option value={300}>5 minutes</option>
                        </select>
                      </div>
                    )}

                    <div className="flex items-center justify-between">
                      <div>
                        <label className="text-sm font-medium text-gray-700">Confirm Actions</label>
                        <p className="text-xs text-gray-500">Show confirmation dialogs for destructive actions</p>
                      </div>
                      <button
                        onClick={() => setConfirmActions(!confirmActions)}
                        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                          confirmActions ? 'bg-blue-600' : 'bg-gray-200'
                        }`}
                      >
                        <span
                          className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                            confirmActions ? 'translate-x-6' : 'translate-x-1'
                          }`}
                        />
                      </button>
                    </div>

                    <div className="flex items-center justify-between">
                      <div>
                        <label className="text-sm font-medium text-gray-700">Keyboard Shortcuts</label>
                        <p className="text-xs text-gray-500">Enable keyboard navigation and shortcuts</p>
                      </div>
                      <button
                        onClick={() => setKeyboardShortcutsEnabled(!keyboardShortcutsEnabled)}
                        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                          keyboardShortcutsEnabled ? 'bg-blue-600' : 'bg-gray-200'
                        }`}
                      >
                        <span
                          className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                            keyboardShortcutsEnabled ? 'translate-x-6' : 'translate-x-1'
                          }`}
                        />
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'notifications' && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Notifications</h3>
                  
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <label className="text-sm font-medium text-gray-700">Show Notifications</label>
                        <p className="text-xs text-gray-500">Display system notifications</p>
                      </div>
                      <button
                        onClick={() => setShowNotifications(!showNotifications)}
                        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                          showNotifications ? 'bg-blue-600' : 'bg-gray-200'
                        }`}
                      >
                        <span
                          className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                            showNotifications ? 'translate-x-6' : 'translate-x-1'
                          }`}
                        />
                      </button>
                    </div>

                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        {soundEnabled ? <Volume2 className="w-4 h-4 text-gray-600" /> : <VolumeX className="w-4 h-4 text-gray-600" />}
                        <div>
                          <label className="text-sm font-medium text-gray-700">Sound Effects</label>
                          <p className="text-xs text-gray-500">Play sounds for notifications</p>
                        </div>
                      </div>
                      <button
                        onClick={() => setSoundEnabled(!soundEnabled)}
                        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                          soundEnabled ? 'bg-blue-600' : 'bg-gray-200'
                        }`}
                      >
                        <span
                          className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                            soundEnabled ? 'translate-x-6' : 'translate-x-1'
                          }`}
                        />
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t border-gray-200 bg-gray-50">
          <button
            onClick={resetToDefaults}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
          >
            Reset to Defaults
          </button>
          <div className="flex space-x-3">
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 transition-colors"
            >
              Save Changes
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// Hook for managing settings panel state
export const useUserSettingsPanel = () => {
  const [isOpen, setIsOpen] = useState(false);
  
  const openSettings = () => setIsOpen(true);
  const closeSettings = () => setIsOpen(false);
  
  return {
    isOpen,
    openSettings,
    closeSettings,
  };
};
