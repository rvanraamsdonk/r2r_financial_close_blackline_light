import { useState, useEffect } from 'react';
import { DenseDataTable } from './DenseDataTable.js';
import { CompactAIBadge } from './AITransparency.js';
import { renderCurrency } from './DenseDataTable.js';
import type { ColumnDefinition, ID } from './DenseDataTable.js';
import { artifactService } from '../services/artifactService.js';
import { 
  TrendingUp, 
  TrendingDown, 
  AlertTriangle, 
  Edit3,
  Check,
  X,
  Filter,
  Download,
  RefreshCw,
  Eye,
  BarChart3
} from 'lucide-react';

interface FluxVariance {
  id?: string;
  entity: string;
  account: string;
  actual_usd: number;
  budget_amount: number;
  prior_usd: number;
  var_vs_budget: number;
  var_vs_prior: number;
  pct_vs_budget: number;
  pct_vs_prior: number;
  threshold_usd: number;
  band_vs_budget: string;
  band_vs_prior: string;
  ai_basis: string;
  ai_narrative: string;
}

interface VarianceAnalysisProps {
  className?: string;
}

export const VarianceAnalysis: React.FC<VarianceAnalysisProps> = ({ className = "" }) => {
  const [variances, setVariances] = useState<FluxVariance[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterBand, setFilterBand] = useState<string>('all');
  const [filterBasis, setFilterBasis] = useState<string>('all');
  const [editingNarrative, setEditingNarrative] = useState<string | null>(null);
  const [narrativeText, setNarrativeText] = useState<string>('');

  useEffect(() => {
    loadVarianceData();
  }, []);

  const loadVarianceData = async () => {
    setLoading(true);
    try {
      const data = await artifactService.getFluxAnalysis();
      const rowsWithIds = (data.rows || []).map((row: any, index: number) => ({
        ...row,
        id: `${row.entity}-${row.account}-${index}`
      }));
      setVariances(rowsWithIds);
    } catch (error) {
      console.error('Failed to load variance data:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredVariances = variances.filter(v => {
    if (filterBand !== 'all' && v.band_vs_budget !== filterBand && v.band_vs_prior !== filterBand) return false;
    if (filterBasis !== 'all' && v.ai_basis !== filterBasis) return false;
    return true;
  });

  const stats = {
    total: variances.length,
    aboveThreshold: variances.filter(v => v.band_vs_budget === 'above' || v.band_vs_prior === 'above').length,
    withinThreshold: variances.filter(v => v.band_vs_budget === 'within' && v.band_vs_prior === 'within').length,
    aiGenerated: variances.filter(v => v.ai_narrative.includes('[AI]')).length
  };

  const handleEditNarrative = (variance: FluxVariance) => {
    setEditingNarrative(`${variance.entity}-${variance.account}`);
    setNarrativeText(variance.ai_narrative);
  };

  const handleSaveNarrative = () => {
    // In real implementation, this would save to backend
    console.log('Saving narrative:', narrativeText);
    setEditingNarrative(null);
  };

  const handleCancelEdit = () => {
    setEditingNarrative(null);
    setNarrativeText('');
  };

  const renderVarianceBand = (band: string) => {
    const colors = {
      above: 'bg-red-100 text-red-800',
      within: 'bg-green-100 text-green-800',
      below: 'bg-yellow-100 text-yellow-800'
    };
    return (
      <span className={`px-2 py-1 text-xs rounded-full ${colors[band as keyof typeof colors] || 'bg-gray-100 text-gray-800'}`}>
        {band.toUpperCase()}
      </span>
    );
  };

  const renderVarianceAmount = (amount: number, percentage: number) => {
    const isPositive = amount >= 0;
    const Icon = isPositive ? TrendingUp : TrendingDown;
    const colorClass = isPositive ? 'text-green-600' : 'text-red-600';
    
    return (
      <div className={`flex items-center gap-1 ${colorClass}`}>
        <Icon size={14} />
        <span className="font-mono text-sm">
          {renderCurrency(Math.abs(amount))} ({(percentage * 100).toFixed(1)}%)
        </span>
      </div>
    );
  };

  const renderNarrative = (variance: FluxVariance) => {
    const key = `${variance.entity}-${variance.account}`;
    const isEditing = editingNarrative === key;
    
    if (isEditing) {
      return (
        <div className="space-y-2">
          <textarea
            value={narrativeText}
            onChange={(e) => setNarrativeText(e.target.value)}
            className="w-full p-2 text-sm border rounded resize-none"
            rows={3}
          />
          <div className="flex gap-2">
            <button
              onClick={handleSaveNarrative}
              className="flex items-center gap-1 px-2 py-1 text-xs bg-green-600 text-white rounded hover:bg-green-700"
            >
              <Check size={12} />
              Save
            </button>
            <button
              onClick={handleCancelEdit}
              className="flex items-center gap-1 px-2 py-1 text-xs bg-gray-600 text-white rounded hover:bg-gray-700"
            >
              <X size={12} />
              Cancel
            </button>
          </div>
        </div>
      );
    }

    return (
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <CompactAIBadge method="AI" confidence={0.85} />
            <span className="text-xs text-gray-500">Based on {variance.ai_basis}</span>
          </div>
          <p className="text-sm text-gray-700">{variance.ai_narrative}</p>
        </div>
        <button
          onClick={() => handleEditNarrative(variance)}
          className="flex items-center gap-1 px-2 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          <Edit3 size={12} />
          Edit
        </button>
      </div>
    );
  };

  const columns: ColumnDefinition[] = [
    {
      key: 'entity',
      label: 'Entity',
      width: 80,
      sortable: true
    },
    {
      key: 'account',
      label: 'Account',
      width: 100,
      sortable: true
    },
    {
      key: 'actual_usd',
      label: 'Actual',
      width: 120,
      sortable: true,
      render: renderCurrency
    },
    {
      key: 'budget_amount',
      label: 'Budget',
      width: 120,
      sortable: true,
      render: renderCurrency
    },
    {
      key: 'prior_usd',
      label: 'Prior Period',
      width: 120,
      sortable: true,
      render: renderCurrency
    },
    {
      key: 'var_vs_budget',
      label: 'Var vs Budget',
      width: 140,
      sortable: true,
      render: (val, row) => renderVarianceAmount(val, (row as FluxVariance).pct_vs_budget)
    },
    {
      key: 'var_vs_prior',
      label: 'Var vs Prior',
      width: 140,
      sortable: true,
      render: (val, row) => renderVarianceAmount(val, (row as FluxVariance).pct_vs_prior)
    },
    {
      key: 'band_vs_budget',
      label: 'Budget Band',
      width: 100,
      sortable: true,
      render: renderVarianceBand
    },
    {
      key: 'band_vs_prior',
      label: 'Prior Band',
      width: 100,
      sortable: true,
      render: renderVarianceBand
    },
    {
      key: 'ai_narrative',
      label: 'AI Analysis & Narrative',
      width: 400,
      render: (_, row) => renderNarrative(row as FluxVariance)
    }
  ];

  const bulkActions = [
    {
      key: 'approve',
      label: 'Approve Narratives',
      action: (ids: ID[]) => console.log('Approving narratives:', ids)
    },
    {
      key: 'regenerate',
      label: 'Regenerate AI',
      action: (ids: ID[]) => console.log('Regenerating AI narratives:', ids)
    }
  ];

  if (loading) {
    return (
      <div className={`p-6 ${className}`}>
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded mb-4"></div>
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-16 bg-gray-200 rounded"></div>
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
            <BarChart3 className="text-blue-600" />
            Variance Analysis
          </h2>
          <p className="text-gray-600 mt-1">
            AI-powered variance explanations with human oversight
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={loadVarianceData}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            <RefreshCw size={16} />
            Refresh
          </button>
          <button className="flex items-center gap-2 px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700">
            <Download size={16} />
            Export
          </button>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-lg border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Variances</p>
              <p className="text-2xl font-bold text-gray-900">{stats.total}</p>
            </div>
            <BarChart3 className="text-blue-500" size={24} />
          </div>
        </div>
        <div className="bg-white p-4 rounded-lg border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Above Threshold</p>
              <p className="text-2xl font-bold text-red-600">{stats.aboveThreshold}</p>
            </div>
            <AlertTriangle className="text-red-500" size={24} />
          </div>
        </div>
        <div className="bg-white p-4 rounded-lg border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Within Threshold</p>
              <p className="text-2xl font-bold text-green-600">{stats.withinThreshold}</p>
            </div>
            <TrendingUp className="text-green-500" size={24} />
          </div>
        </div>
        <div className="bg-white p-4 rounded-lg border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">AI Generated</p>
              <p className="text-2xl font-bold text-purple-600">{stats.aiGenerated}</p>
            </div>
            <Eye className="text-purple-500" size={24} />
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white p-4 rounded-lg border">
        <div className="flex items-center gap-4">
          <Filter size={16} className="text-gray-500" />
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium text-gray-700">Band:</label>
            <select
              value={filterBand}
              onChange={(e) => setFilterBand(e.target.value)}
              className="px-3 py-1 border rounded text-sm"
            >
              <option value="all">All Bands</option>
              <option value="above">Above Threshold</option>
              <option value="within">Within Threshold</option>
              <option value="below">Below Threshold</option>
            </select>
          </div>
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium text-gray-700">AI Basis:</label>
            <select
              value={filterBasis}
              onChange={(e) => setFilterBasis(e.target.value)}
              className="px-3 py-1 border rounded text-sm"
            >
              <option value="all">All Basis</option>
              <option value="budget">Budget</option>
              <option value="prior">Prior Period</option>
            </select>
          </div>
          <div className="text-sm text-gray-600 ml-auto">
            Showing {filteredVariances.length} of {variances.length} variances
          </div>
        </div>
      </div>

      {/* Variance Table */}
      <div className="bg-white rounded-lg border">
        <DenseDataTable
          data={filteredVariances}
          columns={columns}
          bulkActions={bulkActions}
          drillThrough={(row) => console.log('Drill-through variance:', row)}
          className="variance-table"
        />
      </div>
    </div>
  );
};
