import { useState, useEffect } from 'react';
import { DenseDataTable } from './DenseDataTable';
import { CompactAIBadge } from './AITransparency';
import { renderCurrency } from './DenseDataTable';
import type { ColumnDefinition, ID } from './DenseDataTable';
import { artifactService } from '../services/artifactService';
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
  const [bankExceptions, setBankExceptions] = useState<ReconciliationException[]>([]);
  const [icExceptions, setIcExceptions] = useState<ReconciliationException[]>([]);
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
        console.log('Fetched AP Data:', apData);
        const apItems = apData?.exceptions ? transformAPExceptions(apData.exceptions) : [];
        setApExceptions(apItems);
      } else if (activeTab === 'ar') {
        const arData = await artifactService.getReconciliationData('ar');
        console.log('Fetched AR Data:', arData);
        const arItems = arData?.exceptions ? transformARExceptions(arData.exceptions) : [];
        setArExceptions(arItems);
      } else if (activeTab === 'bank') {
        const bankData = await artifactService.getReconciliationData('bank');
        console.log('Fetched Bank Data:', bankData);
        const bankItems = bankData?.exceptions ? transformBankExceptions(bankData.exceptions) : [];
        setBankExceptions(bankItems);
      } else if (activeTab === 'ic') {
        const icData = await artifactService.getReconciliationData('intercompany');
        console.log('Fetched Intercompany Data:', icData);
        const icItems = icData?.exceptions ? transformICExceptions(icData.exceptions) : [];
        setIcExceptions(icItems);
      }
    } catch (error) {
      console.error('Failed to load reconciliation data:', error);
    } finally {
      setLoading(false);
    }
  };

  // Transform AP exceptions from artifact format
  const transformAPExceptions = (exceptions: any[]): ReconciliationException[] => {
    return exceptions.map((exc, index) => {
      const reason: string = (exc.reason || '').toString();
      let type: ReconciliationException['type'] = 'variance';
      const r = reason.toLowerCase();
      if (r.includes('unmatched')) type = 'unmatched';
      else if (r.includes('missing')) type = 'missing';
      else if (r.includes('timing')) type = 'timing';

      return {
        id: exc.invoice_id || exc.id || `AP-${index + 1}`,
        account: exc.account || 'N/A',
        description: exc.description || exc.vendor_name || reason || 'AP exception',
        amount: Math.abs(exc.amount ?? exc.diff_abs ?? exc.open_amount ?? 0),
        currency: exc.currency || 'USD',
        type,
        age_days: exc.age_days ?? 0,
        entity: exc.entity || exc.company || 'N/A',
        source: 'AP Subledger',
        ai_suggestion: exc.ai_suggestion || undefined
      };
    });
  };

  // Transform AR exceptions from artifact format
  const transformARExceptions = (exceptions: any[]): ReconciliationException[] => {
    return exceptions.map((exc, index) => {
      const reason: string = (exc.reason || '').toString();
      let type: ReconciliationException['type'] = 'variance';
      const r = reason.toLowerCase();
      if (r.includes('unmatched')) type = 'unmatched';
      else if (r.includes('missing')) type = 'missing';
      else if (r.includes('timing')) type = 'timing';

      return {
        id: exc.invoice_id || exc.id || `AR-${index + 1}`,
        account: exc.account || 'N/A',
        description: exc.description || exc.customer_name || reason || 'AR exception',
        amount: Math.abs(exc.amount ?? exc.diff_abs ?? exc.open_amount ?? 0),
        currency: exc.currency || 'USD',
        type,
        age_days: exc.age_days ?? 0,
        entity: exc.entity || exc.company || 'N/A',
        source: 'AR Subledger',
        ai_suggestion: exc.ai_suggestion || undefined
      };
    });
  };

  const transformBankExceptions = (exceptions: any[]): ReconciliationException[] => {
    return exceptions.map((exc, index) => ({
      id: exc.id || exc.txn_id || `BANK-${index + 1}`,
      account: exc.account || exc.bank_account || 'N/A',
      description: exc.description || exc.reason,
      amount: Math.abs(exc.amount || exc.diff_abs || exc.unmatched_amount || 0),
      currency: exc.currency || 'USD',
      type: (exc.reason && exc.reason.toLowerCase().includes('unmatched')) ? 'unmatched' : 'variance',
      age_days: exc.age_days || 0,
      entity: exc.entity || exc.company || 'N/A',
      source: 'Bank Statement',
      ai_suggestion: exc.ai_suggestion || undefined
    }));
  };

  const transformICExceptions = (exceptions: any[]): ReconciliationException[] => {
    return exceptions.map((exc, index) => {
      const reason: string = exc.reason || '';
      let type: ReconciliationException['type'] = 'variance';
      if (reason.toLowerCase().includes('unmatched')) type = 'unmatched';
      else if (reason.toLowerCase().includes('missing')) type = 'missing';
      else if (reason.toLowerCase().includes('timing')) type = 'timing';

      const entityLabel = `${exc.entity_src || 'N/A'}->${exc.entity_dst || 'N/A'}`;
      const desc = exc.description || `IC ${exc.doc_id || `DOC-${index + 1}`}: ${reason || 'difference'}`;

      return {
        id: exc.doc_id || `IC-${index + 1}`,
        account: exc.transaction_type || 'Intercompany',
        description: desc,
        amount: Math.abs(exc.diff_abs ?? exc.amount ?? 0),
        currency: exc.currency || 'USD',
        type,
        age_days: exc.age_days || 0,
        entity: entityLabel,
        source: 'Intercompany',
        ai_suggestion: exc.ai_suggestion || undefined
      };
    });
  };

  const getCurrentExceptions = () => {
    let exceptions: ReconciliationException[] = [];
    if (activeTab === 'ap') exceptions = apExceptions;
    if (activeTab === 'ar') exceptions = arExceptions;
    if (activeTab === 'bank') exceptions = bankExceptions;
    if (activeTab === 'ic') exceptions = icExceptions;

    const filtered = exceptions.filter(exc => {
      const typeMatch = filterType === 'all' || exc.type === filterType;
      const ageMatch = filterAge === 'all' || exc.age_days >= parseInt(filterAge, 10);
      return typeMatch && ageMatch;
    });

    return filtered;
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
    { key: 'bank', label: 'Bank Reconciliation', count: bankExceptions.length },
    { key: 'ic', label: 'Intercompany', count: icExceptions.length }
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
        ) : currentExceptions.length === 0 ? (
          <div className="p-8 text-center text-sm text-gray-600">
            <p>No exceptions found for this tab.</p>
            <p className="mt-1 text-gray-500">If you expected items, ensure the latest run produced exceptions and the correct period/entity is selected.</p>
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
