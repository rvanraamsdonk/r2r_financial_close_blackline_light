import { useState } from 'react';
import { 
  Keyboard, 
  X, 
  ArrowRight,
  Copy,
  Edit,
  Filter
} from 'lucide-react';

interface KeyboardShortcut {
  keys: string[];
  description: string;
  category: 'navigation' | 'editing' | 'selection' | 'actions';
}

const shortcuts: KeyboardShortcut[] = [
  // Navigation
  { keys: ['↑', '↓', '←', '→'], description: 'Navigate between cells', category: 'navigation' },
  { keys: ['Tab'], description: 'Move to next field/cell', category: 'navigation' },
  { keys: ['Shift', 'Tab'], description: 'Move to previous field/cell', category: 'navigation' },
  { keys: ['Enter'], description: 'Confirm entry and move down', category: 'navigation' },
  { keys: ['Escape'], description: 'Cancel editing/close dialogs', category: 'navigation' },
  
  // Editing
  { keys: ['F2'], description: 'Edit selected cell', category: 'editing' },
  { keys: ['Delete'], description: 'Clear cell content', category: 'editing' },
  { keys: ['Ctrl', 'Z'], description: 'Undo last action', category: 'editing' },
  { keys: ['Ctrl', 'Y'], description: 'Redo last action', category: 'editing' },
  
  // Selection
  { keys: ['Ctrl', 'A'], description: 'Select all items', category: 'selection' },
  { keys: ['Shift', 'Click'], description: 'Select range', category: 'selection' },
  { keys: ['Ctrl', 'Click'], description: 'Toggle selection', category: 'selection' },
  
  // Actions
  { keys: ['Ctrl', 'C'], description: 'Copy selected data', category: 'actions' },
  { keys: ['Ctrl', 'V'], description: 'Paste data', category: 'actions' },
  { keys: ['Ctrl', 'F'], description: 'Search/Filter', category: 'actions' },
  { keys: ['Ctrl', 'S'], description: 'Save changes', category: 'actions' },
  { keys: ['Ctrl', 'E'], description: 'Export data', category: 'actions' },
  { keys: ['?'], description: 'Show this help panel', category: 'actions' }
];

const categoryIcons = {
  navigation: <ArrowRight className="text-blue-600" size={16} />,
  editing: <Edit className="text-green-600" size={16} />,
  selection: <Copy className="text-purple-600" size={16} />,
  actions: <Filter className="text-orange-600" size={16} />
};

const categoryNames = {
  navigation: 'Navigation',
  editing: 'Editing',
  selection: 'Selection',
  actions: 'Actions'
};

interface KeyboardShortcutsHelpProps {
  isOpen: boolean;
  onClose: () => void;
}

export const KeyboardShortcutsHelp: React.FC<KeyboardShortcutsHelpProps> = ({ isOpen, onClose }) => {
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  if (!isOpen) return null;

  const filteredShortcuts = selectedCategory === 'all' 
    ? shortcuts 
    : shortcuts.filter(s => s.category === selectedCategory);

  const categories = Object.keys(categoryNames) as Array<keyof typeof categoryNames>;

  const renderKeys = (keys: string[]) => {
    return (
      <div className="flex items-center gap-1">
        {keys.map((key, index) => (
          <span key={index} className="flex items-center gap-1">
            <kbd className="px-2 py-1 text-xs font-semibold text-gray-800 bg-gray-100 border border-gray-300 rounded">
              {key}
            </kbd>
            {index < keys.length - 1 && <span className="text-gray-400">+</span>}
          </span>
        ))}
      </div>
    );
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[80vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div className="flex items-center gap-3">
            <Keyboard className="text-blue-600" size={24} />
            <div>
              <h2 className="text-xl font-bold text-gray-900">Keyboard Shortcuts</h2>
              <p className="text-sm text-gray-600">Spreadsheet-like efficiency for power users</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded"
          >
            <X size={20} />
          </button>
        </div>

        {/* Category Filter */}
        <div className="p-4 border-b bg-gray-50">
          <div className="flex items-center gap-2 flex-wrap">
            <button
              onClick={() => setSelectedCategory('all')}
              className={`px-3 py-1.5 text-sm rounded ${
                selectedCategory === 'all'
                  ? 'bg-blue-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-100'
              }`}
            >
              All Shortcuts
            </button>
            {categories.map(category => (
              <button
                key={category}
                onClick={() => setSelectedCategory(category)}
                className={`flex items-center gap-2 px-3 py-1.5 text-sm rounded ${
                  selectedCategory === category
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-gray-700 hover:bg-gray-100'
                }`}
              >
                {categoryIcons[category]}
                {categoryNames[category]}
              </button>
            ))}
          </div>
        </div>

        {/* Shortcuts List */}
        <div className="p-6 overflow-y-auto max-h-96">
          <div className="space-y-4">
            {filteredShortcuts.map((shortcut, index) => (
              <div key={index} className="flex items-center justify-between py-2">
                <div className="flex items-center gap-3">
                  {categoryIcons[shortcut.category]}
                  <span className="text-gray-900">{shortcut.description}</span>
                </div>
                {renderKeys(shortcut.keys)}
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t bg-gray-50">
          <div className="text-sm text-gray-600">
            <p className="mb-2">
              <strong>Pro Tip:</strong> Use these shortcuts to navigate and edit data like in Excel or Google Sheets.
            </p>
            <p>
              Press <kbd className="px-1 py-0.5 text-xs bg-gray-200 rounded">?</kbd> anytime to show this help panel.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

// Hook to manage keyboard shortcuts help
export const useKeyboardShortcutsHelp = () => {
  const [isOpen, setIsOpen] = useState(false);

  const openHelp = () => setIsOpen(true);
  const closeHelp = () => setIsOpen(false);
  const toggleHelp = () => setIsOpen(prev => !prev);

  // Listen for ? key to open help
  useState(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === '?' && !event.ctrlKey && !event.metaKey && !event.altKey) {
        // Only trigger if not in an input field
        const target = event.target as HTMLElement;
        if (target.tagName !== 'INPUT' && target.tagName !== 'TEXTAREA' && !target.isContentEditable) {
          event.preventDefault();
          toggleHelp();
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  });

  return {
    isOpen,
    openHelp,
    closeHelp,
    toggleHelp
  };
};
