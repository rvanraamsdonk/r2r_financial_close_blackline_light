import { useState, useEffect } from 'react';
import { DenseDataTable } from './DenseDataTable.js';
import { renderCurrency, renderStatus, renderAIBadge } from './DenseDataTable.js';
import type { ColumnDefinition, ID } from './DenseDataTable.js';
import type { JournalEntryException } from '../services/artifactService.js';
import { artifactService } from '../services/artifactService.js';
import { 
  FileText, 
  XCircle, 
  AlertTriangle, 
  Clock,
  Filter,
  Download,
  Upload,
  Eye
} from 'lucide-react';

interface JournalEntryWorkbenchProps {
  className?: string;
  onDrillThrough?: (row: any) => void;
}

export const JournalEntryWorkbench: React.FC<JournalEntryWorkbenchProps> = ({ className = "", onDrillThrough }) => {
  const [jeExceptions, setJeExceptions] = useState<JournalEntryException[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [filterReason, setFilterReason] = useState<string>('all');

  useEffect(() => {
    loadJEData();
  }, []);

  const loadJEData = async () => {
    setLoading(true);
    try {
      const jeLifecycle = await artifactService.getJELifecycle();
      if (jeLifecycle) {
        setJeExceptions(jeLifecycle.exceptions);
      }
    } catch (error) {
      console.error('Failed to load JE data:', error);
    } finally {
      setLoading(false);
    }
  };

  // Transform exceptions into table data with additional computed fields
  const tableData = jeExceptions.map(exception => ({
    ...exception,
    id: exception.je_id,
    status: exception.approval_status || 'Unknown',
    formattedAmount: Math.abs(exception.amount),
    riskLevel: exception.amount > 50000 ? 'High' : exception.amount > 10000 ? 'Medium' : 'Low',
    aiContribution: {
      method: 'DET' as const,
      confidence: 100,
      contribution: 'Deterministic validation',
      output: `Flagged: ${exception.reason}`,
      evidence: [],
      timestamp: new Date().toISOString()
    }
  }));

  // Filter data based on current filters
  const filteredData = tableData.filter(item => {
    if (filterStatus !== 'all' && item.status !== filterStatus) return false;
    if (filterReason !== 'all' && item.reason !== filterReason) return false;
    return true;
  });

  // Column definitions for JE exceptions table
  const jeColumns: ColumnDefinition[] = [
    { key: 'je_id', label: 'JE ID', sortable: true, width: '120px' },
    { key: 'entity', label: 'Entity', sortable: true, width: '80px' },
    { 
      key: 'formattedAmount', 
      label: 'Amount', 
      sortable: true, 
      width: '120px',
      render: (value: number) => renderCurrency(value)
    },
    { key: 'currency', label: 'CCY', sortable: true, width: '60px' },
    { key: 'source_system', label: 'Source', sortable: true, width: '100px' },
    { 
      key: 'reason', 
      label: 'Issue', 
      sortable: true, 
      width: '140px',
      render: (value: string) => (
        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
          value === 'approval_pending' ? 'bg-yellow-100 text-yellow-800' :
          value === 'reversal_flagged' ? 'bg-red-100 text-red-800' :
          'bg-gray-100 text-gray-800'
        }`}>
          {value.replace('_', ' ').toUpperCase()}
        </span>
      )
    },
    { 
      key: 'status', 
      label: 'Status', 
      sortable: true, 
      width: '100px',
      render: (value: string) => renderStatus(value)
    },
    { key: 'approver', label: 'Approver', sortable: true, width: '120px' },
    { 
      key: 'riskLevel', 
      label: 'Risk', 
      sortable: true, 
      width: '80px',
      render: (value: string) => (
        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
          value === 'High' ? 'bg-red-100 text-red-800' :
          value === 'Medium' ? 'bg-yellow-100 text-yellow-800' :
          'bg-green-100 text-green-800'
        }`}>
          {value}
        </span>
      )
    },
    { 
      key: 'aiContribution', 
      label: 'AI Method', 
      sortable: false, 
      width: '100px',
      render: (value: any) => renderAIBadge(value)
    }
  ];


  const handleBulkApprove = (ids: ID[]) => {
    console.log('Bulk approve JEs:', ids);
    // This would call the backend to approve selected JEs
  };

  const handleBulkReject = (ids: ID[]) => {
    console.log('Bulk reject JEs:', ids);
    // This would call the backend to reject selected JEs
  };

  const handleExport = () => {
    console.log('Export JE exceptions');
    // This would export the current view to Excel/CSV
  };

  const bulkActions = [
    { key: 'approve', label: 'Approve Selected', action: handleBulkApprove },
    { key: 'reject', label: 'Reject Selected', action: handleBulkReject },
    { key: 'export', label: 'Export Selected', action: (ids: ID[]) => console.log('Export:', ids) }
  ];

  // Get unique values for filters
  const uniqueStatuses = [...new Set(tableData.map(item => item.status))];
  const uniqueReasons = [...new Set(tableData.map(item => item.reason))];

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <FileText className="w-6 h-6 text-blue-600" />
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Journal Entry Workbench</h2>
            <p className="text-sm text-gray-600">
              {filteredData.length} exceptions requiring attention
            </p>
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          <button 
            onClick={loadJEData}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            Refresh
          </button>
          <button 
            onClick={handleExport}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            <Download className="w-4 h-4 mr-2" />
            Export
          </button>
          <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
            <Upload className="w-4 h-4 mr-2" />
            Create JE
          </button>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Pending Approval</p>
              <p className="text-2xl font-bold text-yellow-600">
                {tableData.filter(je => je.reason === 'approval_pending').length}
              </p>
            </div>
            <Clock className="w-8 h-8 text-yellow-500" />
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Reversals Flagged</p>
              <p className="text-2xl font-bold text-red-600">
                {tableData.filter(je => je.reason === 'reversal_flagged').length}
              </p>
            </div>
            <AlertTriangle className="w-8 h-8 text-red-500" />
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">High Risk</p>
              <p className="text-2xl font-bold text-red-600">
                {tableData.filter(je => je.riskLevel === 'High').length}
              </p>
            </div>
            <XCircle className="w-8 h-8 text-red-500" />
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Amount</p>
              <p className="text-2xl font-bold text-gray-900">
                {renderCurrency(tableData.reduce((sum, je) => sum + je.formattedAmount, 0))}
              </p>
            </div>
            <FileText className="w-8 h-8 text-blue-500" />
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white p-4 rounded-lg border border-gray-200">
        <div className="flex items-center gap-4">
          <Filter className="w-4 h-4 text-gray-500" />
          <div className="flex items-center gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Status</label>
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                className="text-sm border border-gray-300 rounded px-2 py-1"
              >
                <option value="all">All Statuses</option>
                {uniqueStatuses.map(status => (
                  <option key={status} value={status}>{status}</option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Issue Type</label>
              <select
                value={filterReason}
                onChange={(e) => setFilterReason(e.target.value)}
                className="text-sm border border-gray-300 rounded px-2 py-1"
              >
                <option value="all">All Issues</option>
                {uniqueReasons.map(reason => (
                  <option key={reason} value={reason}>
                    {reason.replace('_', ' ').toUpperCase()}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* High-Density JE Table */}
      <div className="bg-white rounded-lg border border-gray-200">
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-900">Journal Entry Exceptions</h3>
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <Eye className="w-4 h-4" />
              <span>Showing {filteredData.length} of {tableData.length} entries</span>
            </div>
          </div>
        </div>
        
        {loading ? (
          <div className="p-8 text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-2 text-sm text-gray-600">Loading journal entries...</p>
          </div>
        ) : (
          <DenseDataTable
            data={filteredData}
            columns={jeColumns}
            drillThrough={onDrillThrough || ((row) => console.log('Drill-through JE:', row))}
            bulkActions={bulkActions}
            className="rounded-none"
          />
        )}
      </div>
    </div>
  );
};
