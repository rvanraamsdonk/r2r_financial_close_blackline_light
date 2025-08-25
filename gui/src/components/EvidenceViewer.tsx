import { useState, useEffect } from 'react';
import { CompactAIBadge } from './AITransparency.js';
import { artifactService } from '../services/artifactService.js';
import { 
  FileText, 
  Link, 
  Clock, 
  User,
  Database,
  ArrowRight,
  Search,
  Filter,
  Download,
  Eye,
  ChevronRight,
  ChevronDown,
  ExternalLink
} from 'lucide-react';

interface EvidenceItem {
  id: string;
  type: 'calculation' | 'source_data' | 'ai_output' | 'manual_entry' | 'system_rule';
  timestamp: string;
  description: string;
  value?: number;
  source_file?: string;
  user?: string;
  ai_method?: string;
  confidence?: number;
  children?: EvidenceItem[];
  metadata?: Record<string, any>;
}

interface ProvenanceChain {
  target_value: number;
  target_description: string;
  chain: EvidenceItem[];
  total_steps: number;
  ai_contributions: number;
  manual_contributions: number;
}

interface EvidenceViewerProps {
  className?: string;
  initialValue?: number;
  initialDescription?: string;
}

export const EvidenceViewer: React.FC<EvidenceViewerProps> = ({ 
  className = "",
  initialValue,
  initialDescription 
}) => {
  const [provenanceChain, setProvenanceChain] = useState<ProvenanceChain | null>(null);
  const [loading, setLoading] = useState(false);
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set());
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState<string>('all');

  useEffect(() => {
    if (initialValue !== undefined) {
      loadProvenanceChain(initialValue, initialDescription || 'Selected Value');
    }
  }, [initialValue, initialDescription]);

  const loadProvenanceChain = async (value: number, description: string) => {
    setLoading(true);
    try {
      // Simulate building provenance chain from artifacts
      const chain = await artifactService.buildProvenanceChain(value, description);
      setProvenanceChain(chain);
    } catch (error) {
      console.error('Failed to load provenance chain:', error);
      // Create mock data for demonstration
      setProvenanceChain(createMockProvenanceChain(value, description));
    } finally {
      setLoading(false);
    }
  };

  const createMockProvenanceChain = (value: number, description: string): ProvenanceChain => {
    return {
      target_value: value,
      target_description: description,
      total_steps: 8,
      ai_contributions: 3,
      manual_contributions: 2,
      chain: [
        {
          id: '1',
          type: 'calculation',
          timestamp: '2025-08-23T19:43:39Z',
          description: 'Final calculated balance',
          value: value,
          children: [
            {
              id: '1.1',
              type: 'ai_output',
              timestamp: '2025-08-23T19:43:35Z',
              description: 'AI variance analysis adjustment',
              value: value * 0.1,
              ai_method: 'regression',
              confidence: 0.87,
              source_file: '/out/flux_analysis_20250823T194318Z.json'
            },
            {
              id: '1.2',
              type: 'source_data',
              timestamp: '2025-08-23T19:40:00Z',
              description: 'Base period amount from GL',
              value: value * 0.9,
              source_file: '/data/lite/budget.csv',
              user: 'system'
            }
          ]
        },
        {
          id: '2',
          type: 'system_rule',
          timestamp: '2025-08-23T19:43:30Z',
          description: 'Materiality threshold check',
          metadata: { threshold: 1000, passed: true },
          children: [
            {
              id: '2.1',
              type: 'source_data',
              timestamp: '2025-08-23T19:30:00Z',
              description: 'Entity materiality configuration',
              source_file: '/out/period_init_20250823T194318Z.json'
            }
          ]
        },
        {
          id: '3',
          type: 'manual_entry',
          timestamp: '2025-08-23T18:15:00Z',
          description: 'Manual journal entry adjustment',
          value: value * 0.05,
          user: 'jane.doe@company.com',
          metadata: { je_number: 'JE-2025-08-001' }
        }
      ]
    };
  };

  const toggleExpanded = (id: string) => {
    const newExpanded = new Set(expandedItems);
    if (newExpanded.has(id)) {
      newExpanded.delete(id);
    } else {
      newExpanded.add(id);
    }
    setExpandedItems(newExpanded);
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'calculation': return <ArrowRight className="text-blue-600" size={16} />;
      case 'source_data': return <Database className="text-green-600" size={16} />;
      case 'ai_output': return <Eye className="text-purple-600" size={16} />;
      case 'manual_entry': return <User className="text-orange-600" size={16} />;
      case 'system_rule': return <FileText className="text-gray-600" size={16} />;
      default: return <FileText className="text-gray-600" size={16} />;
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'calculation': return 'border-l-blue-500 bg-blue-50';
      case 'source_data': return 'border-l-green-500 bg-green-50';
      case 'ai_output': return 'border-l-purple-500 bg-purple-50';
      case 'manual_entry': return 'border-l-orange-500 bg-orange-50';
      case 'system_rule': return 'border-l-gray-500 bg-gray-50';
      default: return 'border-l-gray-500 bg-gray-50';
    }
  };

  const renderValue = (value?: number) => {
    if (value === undefined) return null;
    return (
      <span className="font-mono text-sm font-medium">
        ${value.toLocaleString('en-US', { minimumFractionDigits: 2 })}
      </span>
    );
  };

  const renderEvidenceItem = (item: EvidenceItem, level: number = 0) => {
    const hasChildren = item.children && item.children.length > 0;
    const isExpanded = expandedItems.has(item.id);
    const indent = level * 24;

    return (
      <div key={item.id} className="mb-2">
        <div 
          className={`border-l-4 p-4 rounded-r-lg ${getTypeColor(item.type)}`}
          style={{ marginLeft: `${indent}px` }}
        >
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                {hasChildren && (
                  <button
                    onClick={() => toggleExpanded(item.id)}
                    className="p-1 hover:bg-white rounded"
                  >
                    {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                  </button>
                )}
                {getTypeIcon(item.type)}
                <span className="text-sm font-medium capitalize">
                  {item.type.replace('_', ' ')}
                </span>
                {item.ai_method && (
                  <CompactAIBadge method="AI" confidence={item.confidence || 0.8} />
                )}
                <span className="text-xs text-gray-500 flex items-center gap-1">
                  <Clock size={12} />
                  {new Date(item.timestamp).toLocaleString()}
                </span>
              </div>
              
              <p className="text-sm text-gray-700 mb-2">{item.description}</p>
              
              <div className="flex items-center gap-4 text-xs text-gray-600">
                {item.value !== undefined && (
                  <div className="flex items-center gap-1">
                    <span>Value:</span>
                    {renderValue(item.value)}
                  </div>
                )}
                {item.user && (
                  <div className="flex items-center gap-1">
                    <User size={12} />
                    <span>{item.user}</span>
                  </div>
                )}
                {item.source_file && (
                  <div className="flex items-center gap-1">
                    <Link size={12} />
                    <button className="text-blue-600 hover:underline">
                      {item.source_file.split('/').pop()}
                    </button>
                  </div>
                )}
              </div>

              {item.metadata && (
                <div className="mt-2 p-2 bg-white rounded text-xs">
                  <strong>Metadata:</strong>
                  <pre className="mt-1 text-gray-600">
                    {JSON.stringify(item.metadata, null, 2)}
                  </pre>
                </div>
              )}
            </div>
            
            <div className="flex gap-2">
              <button className="p-1 text-gray-500 hover:text-gray-700">
                <ExternalLink size={14} />
              </button>
            </div>
          </div>
        </div>

        {hasChildren && isExpanded && (
          <div className="mt-2">
            {item.children!.map(child => renderEvidenceItem(child, level + 1))}
          </div>
        )}
      </div>
    );
  };

  const filteredChain = provenanceChain?.chain.filter(item => {
    if (filterType !== 'all' && item.type !== filterType) return false;
    if (searchTerm && !item.description.toLowerCase().includes(searchTerm.toLowerCase())) return false;
    return true;
  }) || [];

  if (loading) {
    return (
      <div className={`p-6 ${className}`}>
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded mb-4"></div>
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-20 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <FileText className="text-blue-600" />
            Evidence Viewer
          </h2>
          <p className="text-gray-600 mt-1">
            Complete audit trail with provenance chain
          </p>
        </div>
        <div className="flex gap-2">
          <button className="flex items-center gap-2 px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700">
            <Download size={16} />
            Export Trail
          </button>
        </div>
      </div>

      {provenanceChain && (
        <>
          {/* Target Value Summary */}
          <div className="bg-white p-6 rounded-lg border">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Target Value</h3>
              <div className="text-2xl font-bold text-blue-600">
                {renderValue(provenanceChain.target_value)}
              </div>
            </div>
            <p className="text-gray-700 mb-4">{provenanceChain.target_description}</p>
            
            <div className="grid grid-cols-3 gap-4 text-sm">
              <div className="text-center p-3 bg-gray-50 rounded">
                <div className="text-2xl font-bold text-gray-900">{provenanceChain.total_steps}</div>
                <div className="text-gray-600">Total Steps</div>
              </div>
              <div className="text-center p-3 bg-purple-50 rounded">
                <div className="text-2xl font-bold text-purple-600">{provenanceChain.ai_contributions}</div>
                <div className="text-gray-600">AI Contributions</div>
              </div>
              <div className="text-center p-3 bg-orange-50 rounded">
                <div className="text-2xl font-bold text-orange-600">{provenanceChain.manual_contributions}</div>
                <div className="text-gray-600">Manual Entries</div>
              </div>
            </div>
          </div>

          {/* Search and Filters */}
          <div className="bg-white p-4 rounded-lg border">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 flex-1">
                <Search size={16} className="text-gray-500" />
                <input
                  type="text"
                  placeholder="Search evidence items..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="flex-1 px-3 py-2 border rounded text-sm"
                />
              </div>
              <div className="flex items-center gap-2">
                <Filter size={16} className="text-gray-500" />
                <select
                  value={filterType}
                  onChange={(e) => setFilterType(e.target.value)}
                  className="px-3 py-2 border rounded text-sm"
                >
                  <option value="all">All Types</option>
                  <option value="calculation">Calculations</option>
                  <option value="source_data">Source Data</option>
                  <option value="ai_output">AI Output</option>
                  <option value="manual_entry">Manual Entry</option>
                  <option value="system_rule">System Rules</option>
                </select>
              </div>
            </div>
          </div>

          {/* Provenance Chain */}
          <div className="bg-white rounded-lg border">
            <div className="p-4 border-b">
              <h3 className="text-lg font-semibold text-gray-900">Provenance Chain</h3>
              <p className="text-sm text-gray-600 mt-1">
                Showing {filteredChain.length} of {provenanceChain.chain.length} evidence items
              </p>
            </div>
            <div className="p-4">
              {filteredChain.length > 0 ? (
                <div className="space-y-2">
                  {filteredChain.map(item => renderEvidenceItem(item))}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  No evidence items match your search criteria
                </div>
              )}
            </div>
          </div>
        </>
      )}

      {!provenanceChain && !loading && (
        <div className="bg-white p-8 rounded-lg border text-center">
          <FileText className="mx-auto text-gray-400 mb-4" size={48} />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">No Evidence Selected</h3>
          <p className="text-gray-600">
            Click on any value in the application to view its complete audit trail and provenance chain.
          </p>
        </div>
      )}
    </div>
  );
};
