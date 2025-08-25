/**
 * Main App Component
 * R2R Financial Close GUI - Modern, Professional Alternative to BlackLine
 * Implements "Trust but Verify" principle with complete drill-through capability
 */

import React, { useState } from 'react';
import { CloseCalendar } from './components/CloseCalendar';
import { DenseDataTable } from './components/DenseDataTable';
import { CompactAIBadge } from './components/AITransparency';
import { renderCurrency, renderStatus, renderAIBadge } from './components/DenseDataTable';
import { ClosePhase, CloseTask, JournalEntry, ColumnDefinition } from './types';
import { 
  BarChart3, 
  FileText, 
  Calculator, 
  AlertTriangle, 
  Settings, 
  Search,
  Bell,
  User,
  Menu,
  Calendar
} from 'lucide-react';

// Mock data for demonstration
const mockPhases: ClosePhase[] = [
  {
    id: 'phase-1',
    name: 'Period Close',
    startDate: '2025-08-01',
    endDate: '2025-08-05',
    status: 'complete',
    tasks: [
      {
        id: 'task-1',
        name: 'Trial Balance Validation',
        phase: 'phase-1',
        assignee: 'John Smith',
        dueDate: '2025-08-02',
        status: 'complete',
        priority: 'high',
        dependencies: [],
        evidence: [{ id: 'ev-1', type: 'TB Validation', timestamp: '2025-08-02T10:00:00Z' }],
        aiContribution: { method: 'DET', confidence: 100, contribution: 'Deterministic calculation', output: 'TB validated', evidence: [], timestamp: '2025-08-02T10:00:00Z' }
      },
      {
        id: 'task-2',
        name: 'FX Translation',
        phase: 'phase-1',
        assignee: 'Sarah Johnson',
        dueDate: '2025-08-03',
        status: 'complete',
        priority: 'high',
        dependencies: ['task-1'],
        evidence: [{ id: 'ev-2', type: 'FX Rates', timestamp: '2025-08-03T14:00:00Z' }],
        aiContribution: { method: 'DET', confidence: 100, contribution: 'FX calculation', output: 'Translation complete', evidence: [], timestamp: '2025-08-03T14:00:00Z' }
      }
    ]
  },
  {
    id: 'phase-2',
    name: 'Reconciliation',
    startDate: '2025-08-06',
    endDate: '2025-08-10',
    status: 'in-progress',
    tasks: [
      {
        id: 'task-3',
        name: 'Bank Reconciliation',
        phase: 'phase-2',
        assignee: 'Mike Wilson',
        dueDate: '2025-08-08',
        status: 'in-progress',
        priority: 'high',
        dependencies: [],
        evidence: [{ id: 'ev-3', type: 'Bank Statement', timestamp: '2025-08-07T09:00:00Z' }],
        aiContribution: { method: 'AI', confidence: 85, contribution: 'AI matching suggestions', output: '15 items matched', evidence: [], timestamp: '2025-08-07T09:00:00Z' }
      },
      {
        id: 'task-4',
        name: 'Intercompany Reconciliation',
        phase: 'phase-2',
        assignee: 'Lisa Brown',
        dueDate: '2025-08-09',
        status: 'pending',
        priority: 'medium',
        dependencies: ['task-3'],
        evidence: [],
        aiContribution: { method: 'HYBRID', confidence: 92, contribution: 'Hybrid approach', output: 'IC analysis ready', evidence: [], timestamp: '2025-08-07T16:00:00Z' }
      }
    ]
  }
];

const mockJournalEntries: JournalEntry[] = [
  {
    id: 'je-1',
    date: '2025-08-02',
    reference: 'JE-001',
    description: 'Payroll Accrual',
    status: 'approved',
    lines: [
      { id: 'line-1', account: '5000', accountName: 'Payroll Expense', debit: 150000, credit: 0, description: 'August payroll', aiContribution: { method: 'AI', confidence: 90, contribution: 'AI calculated accrual', output: '150,000', evidence: [], timestamp: '2025-08-02T10:00:00Z' }, evidence: [] },
      { id: 'line-2', account: '2100', accountName: 'Accrued Liabilities', debit: 0, credit: 150000, description: 'Payroll accrual', aiContribution: { method: 'DET', confidence: 100, contribution: 'Deterministic offset', output: '150,000', evidence: [], timestamp: '2025-08-02T10:00:00Z' }, evidence: [] }
    ],
    aiContribution: { method: 'AI', confidence: 90, contribution: 'AI generated JE', output: 'Payroll accrual posted', evidence: [], timestamp: '2025-08-02T10:00:00Z' },
    evidence: [],
    auditTrail: []
  }
];

// Column definitions for Journal Entry table
const jeColumns: ColumnDefinition[] = [
  { key: 'date', label: 'Date', sortable: true, width: '100px' },
  { key: 'reference', label: 'Reference', sortable: true, width: '120px' },
  { key: 'description', label: 'Description', sortable: true },
  { 
    key: 'totalDebit', 
    label: 'Total Debit', 
    sortable: true, 
    width: '120px',
    render: (value) => renderCurrency(value)
  },
  { 
    key: 'totalCredit', 
    label: 'Total Credit', 
    sortable: true, 
    width: '120px',
    render: (value) => renderCurrency(value)
  },
  { 
    key: 'status', 
    label: 'Status', 
    sortable: true, 
    width: '100px',
    render: (value) => renderStatus(value)
  },
  { 
    key: 'aiContribution', 
    label: 'AI Method', 
    sortable: false, 
    width: '100px',
    render: (value) => renderAIBadge(value)
  }
];

function App() {
  const [activeModule, setActiveModule] = useState('dashboard');
  const [selectedTask, setSelectedTask] = useState<CloseTask | null>(null);

  // Calculate totals for JE table
  const jeTableData = mockJournalEntries.map(je => ({
    ...je,
    totalDebit: je.lines.reduce((sum, line) => sum + line.debit, 0),
    totalCredit: je.lines.reduce((sum, line) => sum + line.credit, 0)
  }));

  const handleTaskClick = (task: CloseTask) => {
    setSelectedTask(task);
  };

  const handlePhaseClick = (phase: ClosePhase) => {
    console.log('Phase clicked:', phase.name);
  };

  const handleDrillThrough = (record: any) => {
    console.log('Drill through:', record);
  };

  const navigationItems = [
    { id: 'dashboard', label: 'Control Tower', icon: BarChart3 },
    { id: 'calendar', label: 'Close Calendar', icon: Calendar },
    { id: 'journal-entries', label: 'Journal Entries', icon: FileText },
    { id: 'reconciliations', label: 'Reconciliations', icon: Calculator },
    { id: 'exceptions', label: 'Exceptions', icon: AlertTriangle },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top Navigation Bar */}
      <header className="bg-white border-b border-gray-200">
        <div className="flex items-center justify-between px-4 py-3">
          <div className="flex items-center gap-4">
            <button className="p-2 hover:bg-gray-100 rounded-lg">
              <Menu className="w-5 h-5 text-gray-600" />
            </button>
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">R2R</span>
              </div>
              <h1 className="text-lg font-semibold text-gray-900">Financial Close</h1>
            </div>
          </div>

          <div className="flex items-center gap-4">
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search..."
                className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            {/* Notifications */}
            <button className="p-2 hover:bg-gray-100 rounded-lg relative">
              <Bell className="w-5 h-5 text-gray-600" />
              <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
            </button>

            {/* User Menu */}
            <button className="p-2 hover:bg-gray-100 rounded-lg">
              <User className="w-5 h-5 text-gray-600" />
            </button>
          </div>
        </div>
      </header>

      <div className="flex">
        {/* Sidebar Navigation */}
        <aside className="w-64 bg-white border-r border-gray-200 min-h-screen">
          <nav className="p-4">
            <ul className="space-y-2">
              {navigationItems.map(item => (
                <li key={item.id}>
                  <button
                    onClick={() => setActiveModule(item.id)}
                    className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                      activeModule === item.id
                        ? 'bg-blue-50 text-blue-700 border border-blue-200'
                        : 'text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    <item.icon className="w-4 h-4" />
                    {item.label}
                  </button>
                </li>
              ))}
            </ul>
          </nav>
        </aside>

        {/* Main Content Area */}
        <main className="flex-1 p-6">
          {activeModule === 'dashboard' && (
            <div className="space-y-6">
              {/* Close Calendar - Prominently Displayed */}
              <CloseCalendar
                phases={mockPhases}
                onTaskClick={handleTaskClick}
                onPhaseClick={handlePhaseClick}
              />

              {/* Quick Stats */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-white p-4 rounded-lg border border-gray-200">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">Total JEs</p>
                      <p className="text-2xl font-bold text-gray-900">24</p>
                    </div>
                    <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                      <FileText className="w-4 h-4 text-blue-600" />
                    </div>
                  </div>
                </div>

                <div className="bg-white p-4 rounded-lg border border-gray-200">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">Pending Approvals</p>
                      <p className="text-2xl font-bold text-gray-900">8</p>
                    </div>
                    <div className="w-8 h-8 bg-yellow-100 rounded-lg flex items-center justify-center">
                      <AlertTriangle className="w-4 h-4 text-yellow-600" />
                    </div>
                  </div>
                </div>

                <div className="bg-white p-4 rounded-lg border border-gray-200">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">Exceptions</p>
                      <p className="text-2xl font-bold text-gray-900">3</p>
                    </div>
                    <div className="w-8 h-8 bg-red-100 rounded-lg flex items-center justify-center">
                      <AlertTriangle className="w-4 h-4 text-red-600" />
                    </div>
                  </div>
                </div>

                <div className="bg-white p-4 rounded-lg border border-gray-200">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">AI Confidence</p>
                      <p className="text-2xl font-bold text-gray-900">92%</p>
                    </div>
                    <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
                      <BarChart3 className="w-4 h-4 text-green-600" />
                    </div>
                  </div>
                </div>
              </div>

              {/* Recent Journal Entries */}
              <div className="bg-white rounded-lg border border-gray-200">
                <div className="p-4 border-b border-gray-200">
                  <h3 className="text-lg font-semibold text-gray-900">Recent Journal Entries</h3>
                </div>
                <DenseDataTable
                  data={jeTableData}
                  columns={jeColumns}
                  drillThrough={handleDrillThrough}
                  className="rounded-none"
                />
              </div>
            </div>
          )}

          {activeModule === 'journal-entries' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold text-gray-900">Journal Entry Workbench</h2>
                <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                  Create JE
                </button>
              </div>
              
              <DenseDataTable
                data={jeTableData}
                columns={jeColumns}
                drillThrough={handleDrillThrough}
                bulkActions={[
                  { key: 'approve', label: 'Approve Selected', action: (ids) => console.log('Approve:', ids) },
                  { key: 'reject', label: 'Reject Selected', action: (ids) => console.log('Reject:', ids) }
                ]}
              />
            </div>
          )}

          {activeModule === 'calendar' && (
            <div className="space-y-6">
              <h2 className="text-2xl font-bold text-gray-900">Close Calendar</h2>
              <CloseCalendar
                phases={mockPhases}
                onTaskClick={handleTaskClick}
                onPhaseClick={handlePhaseClick}
              />
            </div>
          )}
        </main>
      </div>

      {/* Task Detail Modal */}
      {selectedTask && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">{selectedTask.name}</h3>
              <button
                onClick={() => setSelectedTask(null)}
                className="text-gray-500 hover:text-gray-700"
              >
                ×
              </button>
            </div>

            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Assignee</label>
                  <p className="text-sm text-gray-900">{selectedTask.assignee}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Due Date</label>
                  <p className="text-sm text-gray-900">{selectedTask.dueDate}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
                  <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                    selectedTask.status === 'complete' ? 'bg-green-100 text-green-800' :
                    selectedTask.status === 'in-progress' ? 'bg-blue-100 text-blue-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {selectedTask.status}
                  </span>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">AI Method</label>
                  <CompactAIBadge
                    method={selectedTask.aiContribution.method}
                    confidence={selectedTask.aiContribution.confidence}
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">AI Contribution</label>
                <p className="text-sm text-gray-900 bg-blue-50 p-3 rounded border">
                  {selectedTask.aiContribution.contribution}
                </p>
              </div>

              {selectedTask.evidence.length > 0 && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Evidence</label>
                  <div className="space-y-2">
                    {selectedTask.evidence.map(evidence => (
                      <div key={evidence.id} className="flex items-center justify-between p-2 bg-gray-50 rounded border">
                        <div>
                          <p className="text-sm font-medium">{evidence.type}</p>
                          <p className="text-xs text-gray-600">{evidence.timestamp}</p>
                        </div>
                        <button className="text-xs text-blue-600 hover:text-blue-800">
                          View Evidence
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
