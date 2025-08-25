/**
 * Evidence Viewer Sidebar
 * Slide-out sidebar for contextual evidence investigation
 */

import { useState, useRef, useEffect } from 'react';
import { 
  X, 
  Pin, 
  PinOff, 
  ArrowLeft, 
  ExternalLink, 
  Download,
  Search,
  ChevronDown,
  ChevronRight,
  Clock,
  User,
  FileText,
  Database,
  Cpu,
  Brain
} from 'lucide-react';
import { useEvidenceStore } from '../stores/evidenceStore.js';
import { useUserPreferencesStore, getThemeClasses } from '../stores/userPreferencesStore.js';

export const EvidenceViewerSidebar: React.FC = () => {
  const {
    isOpen,
    width,
    isPinned,
    currentEvidence,
    evidenceHistory,
    isLoading,
    closeEvidence,
    setSidebarWidth,
    togglePin,
    goBack,
  } = useEvidenceStore();

  const { theme, corporateColors } = useUserPreferencesStore();
  const themeClasses = getThemeClasses(theme, corporateColors);

  const [isResizing, setIsResizing] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set());
  const sidebarRef = useRef<HTMLDivElement>(null);
  const resizeRef = useRef<HTMLDivElement>(null);

  // Mock provenance data - in real app, this would come from artifactService
  const mockProvenance = currentEvidence ? [
    {
      id: '1',
      type: 'source_data',
      title: 'Trial Balance Entry',
      timestamp: '2024-08-23T10:30:00Z',
      user: 'System Import',
      value: currentEvidence.value,
      description: `Original TB entry for ${currentEvidence.account}`,
      confidence: 100,
      method: 'deterministic',
      children: [
        {
          id: '1.1',
          type: 'file_import',
          title: 'CSV Import',
          timestamp: '2024-08-23T10:25:00Z',
          user: 'batch_import',
          description: 'Imported from trial_balance_202408.csv',
          confidence: 100,
          method: 'deterministic',
        }
      ]
    },
    {
      id: '2',
      type: 'ai_analysis',
      title: 'AI Variance Analysis',
      timestamp: '2024-08-23T11:15:00Z',
      user: 'AI Engine',
      description: 'Analyzed variance patterns and generated narrative',
      confidence: 87,
      method: 'ai',
      children: [
        {
          id: '2.1',
          type: 'pattern_detection',
          title: 'Pattern Analysis',
          timestamp: '2024-08-23T11:12:00Z',
          user: 'AI Engine',
          description: 'Detected seasonal variance pattern',
          confidence: 92,
          method: 'ai',
        }
      ]
    },
    {
      id: '3',
      type: 'manual_review',
      title: 'Human Review',
      timestamp: '2024-08-23T14:20:00Z',
      user: 'john.doe@company.com',
      description: 'Reviewed and approved AI analysis',
      confidence: 100,
      method: 'manual',
    }
  ] : [];

  // Handle resize
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing) return;
      
      const newWidth = window.innerWidth - e.clientX;
      setSidebarWidth(newWidth);
    };

    const handleMouseUp = () => {
      setIsResizing(false);
    };

    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isResizing, setSidebarWidth]);

  // Handle escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen && !isPinned) {
        closeEvidence();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen, isPinned, closeEvidence]);

  const toggleExpanded = (id: string) => {
    const newExpanded = new Set(expandedItems);
    if (newExpanded.has(id)) {
      newExpanded.delete(id);
    } else {
      newExpanded.add(id);
    }
    setExpandedItems(newExpanded);
  };

  const getMethodIcon = (method: string) => {
    switch (method) {
      case 'ai': return <Brain className="w-4 h-4 text-purple-600" />;
      case 'deterministic': return <Cpu className="w-4 h-4 text-blue-600" />;
      case 'manual': return <User className="w-4 h-4 text-green-600" />;
      default: return <FileText className="w-4 h-4 text-gray-600" />;
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'source_data': return <Database className="w-4 h-4 text-blue-600" />;
      case 'ai_analysis': return <Brain className="w-4 h-4 text-purple-600" />;
      case 'manual_review': return <User className="w-4 h-4 text-green-600" />;
      case 'file_import': return <FileText className="w-4 h-4 text-gray-600" />;
      default: return <FileText className="w-4 h-4 text-gray-600" />;
    }
  };

  const renderProvenanceItem = (item: any, level = 0) => {
    const isExpanded = expandedItems.has(item.id);
    const hasChildren = item.children && item.children.length > 0;

    return (
      <div key={item.id} className={`${level > 0 ? 'ml-6 border-l border-gray-200 pl-4' : ''}`}>
        <div className={`p-3 rounded-lg border ${themeClasses.border} ${themeClasses.hover} transition-colors`}>
          <div className="flex items-start justify-between">
            <div className="flex items-start space-x-3 flex-1">
              <div className="flex items-center space-x-2">
                {hasChildren && (
                  <button
                    onClick={() => toggleExpanded(item.id)}
                    className="p-0.5 hover:bg-gray-100 rounded"
                  >
                    {isExpanded ? (
                      <ChevronDown className="w-4 h-4 text-gray-500" />
                    ) : (
                      <ChevronRight className="w-4 h-4 text-gray-500" />
                    )}
                  </button>
                )}
                {getTypeIcon(item.type)}
              </div>
              
              <div className="flex-1 min-w-0">
                <div className="flex items-center space-x-2 mb-1">
                  <h4 className={`font-medium ${themeClasses.text} truncate`}>{item.title}</h4>
                  {getMethodIcon(item.method)}
                  {item.confidence && (
                    <span className={`text-xs px-2 py-0.5 rounded-full ${
                      item.confidence >= 90 ? 'bg-green-100 text-green-800' :
                      item.confidence >= 70 ? 'bg-yellow-100 text-yellow-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {item.confidence}%
                    </span>
                  )}
                </div>
                
                <p className="text-sm text-gray-600 mb-2">{item.description}</p>
                
                <div className="flex items-center space-x-4 text-xs text-gray-500">
                  <div className="flex items-center space-x-1">
                    <Clock className="w-3 h-3" />
                    <span>{new Date(item.timestamp).toLocaleString()}</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <User className="w-3 h-3" />
                    <span>{item.user}</span>
                  </div>
                </div>
              </div>
            </div>
            
            <button className="p-1 hover:bg-gray-100 rounded">
              <ExternalLink className="w-4 h-4 text-gray-500" />
            </button>
          </div>
        </div>
        
        {hasChildren && isExpanded && (
          <div className="mt-2 space-y-2">
            {item.children.map((child: any) => renderProvenanceItem(child, level + 1))}
          </div>
        )}
      </div>
    );
  };

  if (!isOpen) return null;

  return (
    <>
      
      {/* Sidebar */}
      <div
        ref={sidebarRef}
        className={`fixed top-0 right-0 h-full ${themeClasses.bg} border-l ${themeClasses.border} shadow-xl z-50 flex transition-transform duration-300 ${
          isOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
        style={{ width: `${width}px` }}
      >
        {/* Resize Handle */}
        <div
          ref={resizeRef}
          className="w-1 bg-gray-300 hover:bg-gray-400 cursor-col-resize flex-shrink-0"
          onMouseDown={() => setIsResizing(true)}
        />
        
        {/* Content */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Header */}
          <div className={`p-4 border-b ${themeClasses.border} flex-shrink-0`}>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-2">
                {evidenceHistory.length > 0 && (
                  <button
                    onClick={goBack}
                    className={`p-1 ${themeClasses.hover} rounded transition-colors`}
                  >
                    <ArrowLeft className="w-4 h-4" />
                  </button>
                )}
                <h2 className={`text-lg font-semibold ${themeClasses.text}`}>Evidence Trail</h2>
              </div>
              
              <div className="flex items-center space-x-2">
                <button
                  onClick={togglePin}
                  className={`p-1 ${themeClasses.hover} rounded transition-colors ${
                    isPinned ? 'text-blue-600' : 'text-gray-500'
                  }`}
                >
                  {isPinned ? <Pin className="w-4 h-4" /> : <PinOff className="w-4 h-4" />}
                </button>
                
                <button
                  onClick={closeEvidence}
                  className={`p-1 ${themeClasses.hover} rounded transition-colors`}
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>
            
            {currentEvidence && (
              <div className={`p-3 rounded-lg border ${themeClasses.border} bg-blue-50`}>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-600">Investigating</span>
                  <span className="text-lg font-bold text-blue-900">
                    ${currentEvidence.value.toLocaleString()}
                  </span>
                </div>
                <p className="text-sm text-gray-700">{currentEvidence.description}</p>
                {currentEvidence.account && (
                  <p className="text-xs text-gray-500 mt-1">Account: {currentEvidence.account}</p>
                )}
              </div>
            )}
          </div>
          
          {/* Search */}
          <div className={`p-4 border-b ${themeClasses.border} flex-shrink-0`}>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search evidence..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className={`w-full pl-10 pr-4 py-2 border ${themeClasses.border} rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500`}
              />
            </div>
          </div>
          
          {/* Content */}
          <div className="flex-1 overflow-y-auto p-4">
            {isLoading ? (
              <div className="space-y-4">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="animate-pulse">
                    <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                    <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="space-y-4">
                <h3 className={`font-medium ${themeClasses.text} mb-3`}>Provenance Chain</h3>
                {mockProvenance.map((item) => renderProvenanceItem(item))}
              </div>
            )}
          </div>
          
          {/* Footer */}
          <div className={`p-4 border-t ${themeClasses.border} flex-shrink-0`}>
            <div className="flex items-center justify-between">
              <div className="text-xs text-gray-500">
                {evidenceHistory.length > 0 && (
                  <span>{evidenceHistory.length} previous item{evidenceHistory.length !== 1 ? 's' : ''}</span>
                )}
              </div>
              
              <div className="flex items-center space-x-2">
                <button className={`p-2 ${themeClasses.hover} rounded transition-colors`}>
                  <Download className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};
