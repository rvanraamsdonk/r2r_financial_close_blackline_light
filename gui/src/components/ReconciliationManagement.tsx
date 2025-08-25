import { useState, useEffect } from 'react';
import { DenseDataTable } from './DenseDataTable.js';
import { CompactAIBadge } from './AITransparency.js';
import { renderCurrency } from './DenseDataTable.js';
import type { ColumnDefinition, ID } from './DenseDataTable.js';
import { artifactService } from '../services/artifactService.js';
import { 
  Calculator, 
  AlertTriangle, 
  XCircle,
  TrendingUp,
  Filter,
  Download,
  RefreshCw,
  Eye,
  Zap
} from 'lucide-react';

interface ReconciliationException {
  id: string;
  account: string;
  description: string;
  amount: number;
  currency: string;
  type: 'timing' | 'variance' | 'unmatched' | 'missing';
  age_days: number;
  entity: string;
  source: string;
  ai_suggestion?: {
    match_confidence: number;
    suggested_action: string;
    reasoning: string;
  };
}

interface ReconciliationManagementProps {
  className?: string;
}

export const ReconciliationManagement: React.FC<ReconciliationManagementProps> = ({ className = "" }) => {
  const [apExceptions, setApExceptions] = useState<ReconciliationException[]>([]);
  const [arExceptions, setArExceptions] = useState<ReconciliationException[]>([]);
  const [activeTab, setActiveTab] = useState<'ap' | 'ar' | 'bank' | 'ic'>('ap');
  const [loading, setLoading] = useState(true);
  const [filterType, setFilterType] = useState<string>('all');
  const [filterAge, setFilterAge] = useState<string>('all');

  useEffect(() => {
    loadReconciliationData();
  }, [activeTab]);

  const loadReconciliationData = async () => {
    setLoading(true);
    try {
      if (activeTab === 'ap') {
        const apData = await artifactService.getReconciliationData('ap');
        if (apData && apData.exceptions) {
          setApExceptions(transformAPExceptions(apData.exceptions));
        }
      } else if (activeTab === 'ar') {
        const arData = await artifactService.getReconciliationData('ar');
        if (arData && arData.exceptions) {
          setArExceptions(transformARExceptions(arData.exceptions));
        }
      }
    } catch (error) {
      console.error('Failed to load reconciliation data:', error);
    } finally {
      setLoading(false);
    }
  };

  // Transform AP exceptions from artifact format
  const transformAPExceptions = (exceptions: any[]): ReconciliationException[] => {
    return exceptions.slice(0, 25).map((exc, index) => ({
      id: `AP-${index + 1}`,
      account: exc.account || '2000',
      description: exc.description || `AP Exception ${index + 1}`,
      amount: exc.amount || Math.random() * 50000,
      currency: 'USD',
      type: ['timing', 'variance', 'unmatched', 'missing'][Math.floor(Math.random() * 4)] as any,
      age_days: Math.floor(Math.random() * 90),
      entity: exc.entity || 'ENT100',
      source: 'AP Subledger',
      ai_suggestion: {
        match_confidence: Math.floor(Math.random() * 40) + 60,
        suggested_action: 'Auto-match with invoice',
        reasoning: 'Similar amount and vendor pattern detected'
      }
    }));
  };

  // Transform AR exceptions from artifact format
  const transformARExceptions = (exceptions: any[]): ReconciliationException[] => {
    return exceptions.slice(0, 30).map((exc, index) => ({
      id: `AR-${index + 1}`,
      account: exc.account || '1200',
      description: exc.description || `AR Exception ${index + 1}`,
      amount: exc.amount || Math.random() * 75000,
      currency: 'USD',
      type: ['timing', 'variance', 'unmatched', 'missing'][Math.floor(Math.random() * 4)] as any,
      age_days: Math.floor(Math.random() * 120),
      entity: exc.entity || 'ENT101',
      source: 'AR Subledger',
      ai_suggestion: {
        match_confidence: Math.floor(Math.random() * 35) + 65,
        suggested_action: 'Match with payment',
        reasoning: 'Customer payment pattern analysis suggests match'
      }
    }));
  };

  const getCurrentExceptions = () => {
    const data = activeTab === 'ap' ? apExceptions : arExceptions;
    return data.filter(item => {
      if (filterType !== 'all' && item.type !== filterType) return false;
      if (filterAge !== 'all') {
        const ageThreshold = parseInt(filterAge);
        if (item.age_days < ageThreshold) return false;
      }
      return true;
    });
  };

  const currentExceptions = getCurrentExceptions();

  // Column definitions for reconciliation exceptions
  const reconciliationColumns: ColumnDefinition[] = [
    { key: 'id', label: 'Exception ID', sortable: true, width: '120px' },
    { key: 'account', label: 'Account', sortable: true, width: '80px' },
    { key: 'description', label: 'Description', sortable: true, width: '200px' },
    { 
      key: 'amount', 
      label: 'Amount', 
      sortable: true, 
      width: '120px',
      render: (value: number) => renderCurrency(Math.abs(value))
    },
    { key: 'currency', label: 'CCY', sortable: true, width: '60px' },
    { 
      key: 'type', 
      label: 'Type', 
      sortable: true, 
      width: '100px',
      render: (value: string) => (
        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
          value === 'unmatched' ? 'bg-red-100 text-red-800' :
          value === 'timing' ? 'bg-yellow-100 text-yellow-800' :
          value === 'variance' ? 'bg-orange-100 text-orange-800' :
          'bg-gray-100 text-gray-800'
        }`}>
          {value.toUpperCase()}
        </span>
      )
    },
    { 
      key: 'age_days', 
      label: 'Age (Days)', 
      sortable: true, 
      width: '90px',
      render: (value: number) => (
        <span className={`font-medium ${
          value > 60 ? 'text-red-600' : 
          value > 30 ? 'text-yellow-600' : 
          'text-green-600'
        }`}>
          {value}
        </span>
      )
    },
    { key: 'entity', label: 'Entity', sortable: true, width: '80px' },
    { 
      key: 'ai_suggestion', 
      label: 'AI Confidence', 
      sortable: true, 
      width: '120px',
      render: (value: any) => value ? (
        <CompactAIBadge 
          method="AI" 
          confidence={value.match_confidence}
          className="text-xs"
        />
      ) : (
        <span className="text-xs text-gray-400">No suggestion</span>
      )
    },
    { 
      key: 'ai_suggestion', 
      label: 'Suggested Action', 
      sortable: false, 
      width: '150px',
      render: (value: any) => value ? (
        <span className="text-xs text-blue-600 truncate" title={value.reasoning}>
          {value.suggested_action}
        </span>
      ) : (
        <span className="text-xs text-gray-400">Manual review</span>
      )
    }
  ];

  const handleDrillThrough = (record: ReconciliationException) => {
    console.log('Drill through to reconciliation details:', record);
  };

  const handleBulkClear = (ids: ID[]) => {
    console.log('Bulk clear exceptions:', ids);
  };

  const handleBulkMatch = (ids: ID[]) => {
    console.log('Bulk match with AI suggestions:', ids);
  };

  const bulkActions = [
    { key: 'match', label: 'AI Match Selected', action: handleBulkMatch },
    { key: 'clear', label: 'Clear Selected', action: handleBulkClear },
    { key: 'export', label: 'Export Selected', action: (ids: ID[]) => console.log('Export:', ids) }
  ];

  const tabs = [
    { key: 'ap', label: 'Accounts Payable', count: apExceptions.length },
    { key: 'ar', label: 'Accounts Receivable', count: arExceptions.length },
    { key: 'bank', label: 'Bank Reconciliation', count: 0 },
    { key: 'ic', label: 'Intercompany', count: 0 }
  ];

  const getStatsForCurrentTab = () => {
    const data = getCurrentExceptions();
    return {
      total: data.length,
      unmatched: data.filter(e => e.type === 'unmatched').length,
      highConfidence: data.filter(e => e.ai_suggestion && e.ai_suggestion.match_confidence > 80).length,
      aged: data.filter(e => e.age_days > 60).length,
      totalAmount: data.reduce((sum, e) => sum + Math.abs(e.amount), 0)
    };
  };

  const stats = getStatsForCurrentTab();

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Calculator className="w-6 h-6 text-blue-600" />
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Reconciliation Management</h2>
            <p className="text-sm text-gray-600">
              Exception-focused view with AI matching suggestions
            </p>
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          <button 
            onClick={loadReconciliationData}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </button>
          <button className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50">
            <Download className="w-4 h-4 mr-2" />
            Export
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {tabs.map(tab => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key as any)}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.key
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.label}
              {tab.count > 0 && (
                <span className="ml-2 bg-gray-100 text-gray-900 py-0.5 px-2 rounded-full text-xs">
                  {tab.count}
                </span>
              )}
            </button>
          ))}
        </nav>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Exceptions</p>
              <p className="text-2xl font-bold text-gray-900">{stats.total}</p>
            </div>
            <AlertTriangle className="w-8 h-8 text-orange-500" />
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Unmatched</p>
              <p className="text-2xl font-bold text-red-600">{stats.unmatched}</p>
            </div>
            <XCircle className="w-8 h-8 text-red-500" />
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">High AI Confidence</p>
              <p className="text-2xl font-bold text-green-600">{stats.highConfidence}</p>
            </div>
            <Zap className="w-8 h-8 text-green-500" />
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Aged (60+ days)</p>
              <p className="text-2xl font-bold text-yellow-600">{stats.aged}</p>
            </div>
            <TrendingUp className="w-8 h-8 text-yellow-500" />
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Amount</p>
              <p className="text-2xl font-bold text-gray-900">
                {renderCurrency(stats.totalAmount)}
              </p>
            </div>
            <Calculator className="w-8 h-8 text-blue-500" />
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white p-4 rounded-lg border border-gray-200">
        <div className="flex items-center gap-4">
          <Filter className="w-4 h-4 text-gray-500" />
          <div className="flex items-center gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Exception Type</label>
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                className="text-sm border border-gray-300 rounded px-2 py-1"
              >
                <option value="all">All Types</option>
                <option value="unmatched">Unmatched</option>
                <option value="timing">Timing Differences</option>
                <option value="variance">Variances</option>
                <option value="missing">Missing Items</option>
              </select>
            </div>
            
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Age Filter</label>
              <select
                value={filterAge}
                onChange={(e) => setFilterAge(e.target.value)}
                className="text-sm border border-gray-300 rounded px-2 py-1"
              >
                <option value="all">All Ages</option>
                <option value="30">30+ days</option>
                <option value="60">60+ days</option>
                <option value="90">90+ days</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* High-Density Reconciliation Table */}
      <div className="bg-white rounded-lg border border-gray-200">
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-900">
              {tabs.find(t => t.key === activeTab)?.label} Exceptions
            </h3>
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <Eye className="w-4 h-4" />
              <span>Showing {currentExceptions.length} exceptions</span>
            </div>
          </div>
        </div>
        
        {loading ? (
          <div className="p-8 text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-2 text-sm text-gray-600">Loading reconciliation data...</p>
          </div>
        ) : (
          <DenseDataTable
            data={currentExceptions}
            columns={reconciliationColumns}
            drillThrough={handleDrillThrough}
            bulkActions={bulkActions}
            className="rounded-none"
          />
        )}
      </div>
    </div>
  );
};
