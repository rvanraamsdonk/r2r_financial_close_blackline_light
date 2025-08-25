/**
 * Main App Component
 * R2R Financial Close GUI - Modern, Professional Alternative to BlackLine
 * Implements "Trust but Verify" principle with complete drill-through capability
 */

import { useState } from 'react';
import { CloseCalendar } from './components/CloseCalendar.js';
import { DenseDataTable } from './components/DenseDataTable.js';
import { JournalEntryWorkbench } from './components/JournalEntryWorkbench.js';
import { ReconciliationManagement } from './components/ReconciliationManagement.js';
import { VarianceAnalysis } from './components/VarianceAnalysis.js';
import { EvidenceViewerSidebar } from './components/EvidenceViewerSidebar.js';
import { KeyboardShortcutsHelp, useKeyboardShortcutsHelp } from './components/KeyboardShortcutsHelp.js';
import { UserSettingsPanel, useUserSettingsPanel } from './components/UserSettingsPanel.js';
import { useUserPreferencesStore, getThemeClasses } from './stores/userPreferencesStore.js';
import { useEvidenceStore } from './stores/evidenceStore.js';
import { renderCurrency, renderStatus, renderAIBadge } from './components/DenseDataTable.js';
import type { ClosePhase, CloseTask, JournalEntry, ColumnDefinition } from './types.js';
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
    render: (value: number) => renderCurrency(value)
  },
  { 
    key: 'totalCredit', 
    label: 'Total Credit', 
    sortable: true, 
    width: '120px',
    render: (value: number) => renderCurrency(value)
  },
  { 
    key: 'status', 
    label: 'Status', 
    sortable: true, 
    width: '100px',
    render: (value: string) => renderStatus(value)
  },
  { 
    key: 'aiContribution', 
    label: 'AI Method', 
    sortable: false, 
    width: '100px',
    render: (value: any) => renderAIBadge(value)
  }
];

function App() {
  const [activeModule, setActiveModule] = useState('dashboard');
  const [selectedTask, setSelectedTask] = useState<CloseTask | null>(null);
  const { isOpen: isHelpOpen, toggleHelp } = useKeyboardShortcutsHelp();
  const { isOpen: isSettingsOpen, openSettings, closeSettings } = useUserSettingsPanel();
  const { theme, corporateColors, corporateLogo } = useUserPreferencesStore();
  const themeClasses = getThemeClasses(theme, corporateColors);
  const { openEvidence } = useEvidenceStore();

  // Calculate totals for JE table
  const jeTableData = mockJournalEntries.map(je => ({
    ...je,
    totalDebit: je.lines.reduce((sum: number, line: any) => sum + line.debit, 0),
    totalCredit: je.lines.reduce((sum: number, line: any) => sum + line.credit, 0)
  }));

  const handleTaskClick = (task: CloseTask) => {
    setSelectedTask(task);
  };

  const handlePhaseClick = (phase: ClosePhase) => {
    console.log('Phase clicked:', phase.name);
  };

  const handleDrillThrough = (record: any) => {
    // Extract value and description from the record
    const value = record.amount || record.actual_usd || record.var_vs_budget || record.totalDebit || record.totalCredit || 0;
    const description = `${record.entity || record.account || record.description || 'Financial Item'}`;
    const account = record.account || record.accountCode;
    const entity = record.entity;
    
    openEvidence({
      id: `${Date.now()}`,
      value,
      description,
      account,
      entity,
      period: '2024-08',
      source: 'drill_through'
    });
  };

  const navigationItems = [
    { id: 'dashboard', label: 'Control Tower', icon: BarChart3 },
    { id: 'calendar', label: 'Close Calendar', icon: Calendar },
    { id: 'journal-entries', label: 'Journal Entries', icon: FileText },
    { id: 'reconciliations', label: 'Reconciliations', icon: Calculator },
    { id: 'variance', label: 'Variance Analysis', icon: BarChart3 },
    { id: 'exceptions', label: 'Exceptions', icon: AlertTriangle },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  return (
    <div className={`min-h-screen ${themeClasses.bg} transition-colors duration-200`}>
      {/* Top Navigation Bar */}
      <header className="bg-white border-b border-gray-200">
        <div className="flex items-center justify-between px-4 py-3">
          <div className="flex items-center gap-4">
            <button className="p-2 hover:bg-gray-100 rounded-lg">
              <Menu className="w-5 h-5 text-gray-600" />
            </button>
            <div className="flex justify-between items-center py-4">
              <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">R2R</span>
              </div>
              <div className="flex items-center space-x-3">
                {corporateLogo && (
                  <img src={corporateLogo} alt="Corporate Logo" className="h-8 w-auto" />
                )}
                <h1 className={`text-2xl font-bold ${themeClasses.text}`}>R2R Financial Close</h1>
              </div>
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
            <button 
              onClick={openSettings}
              className={`p-2 ${themeClasses.text} ${themeClasses.hover} rounded-md transition-colors`}
            >
              <Settings className="w-5 h-5" />
            </button>
            <button className={`p-2 ${themeClasses.text} ${themeClasses.hover} rounded-md transition-colors`}>
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
                        ? `${themeClasses.accent} text-white`
                        : `${themeClasses.text} ${themeClasses.hover}`
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
              <div className={`${themeClasses.bg} shadow-sm border-b ${themeClasses.border}`}>
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
            <JournalEntryWorkbench onDrillThrough={handleDrillThrough} />
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

          {activeModule === 'reconciliations' && (
            <ReconciliationManagement />
          )}

          {activeModule === 'variance' && (
            <VarianceAnalysis className="p-6" />
          )}

        </main>
      </div>

      {/* Keyboard Shortcuts Help */}
      <EvidenceViewerSidebar />
      <KeyboardShortcutsHelp isOpen={isHelpOpen} onClose={toggleHelp} />
      <UserSettingsPanel isOpen={isSettingsOpen} onClose={closeSettings} />

      {/* Task Detail Modal */}
      {selectedTask && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className={`${themeClasses.bg} rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto`}>
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className={`text-lg font-semibold ${themeClasses.text}`}>{selectedTask.name}</h3>
                <button
                  onClick={() => setSelectedTask(null)}
                  className={`${themeClasses.text} hover:opacity-70`}
                >
                  ×
                </button>
              </div>
              <div className="space-y-4">
                <div>
                  <span className={`text-sm font-medium ${themeClasses.text}`}>Status:</span>
                  <span className={`ml-2 px-2 py-1 text-xs rounded-full ${
                    selectedTask.status === 'complete' ? 'bg-green-100 text-green-800' :
                    selectedTask.status === 'in-progress' ? 'bg-blue-100 text-blue-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {selectedTask.status.replace('_', ' ').toUpperCase()}
                  </span>
                </div>
                <div>
                  <span className={`text-sm font-medium ${themeClasses.text}`}>Description:</span>
                  <p className={`mt-1 text-sm ${themeClasses.text}`}>{selectedTask.name}</p>
                </div>
                <div>
                  <span className={`text-sm font-medium ${themeClasses.text}`}>Due Date:</span>
                  <p className={`mt-1 text-sm ${themeClasses.text}`}>{selectedTask.dueDate}</p>
                </div>
                {selectedTask.assignee && (
                  <div>
                    <span className={`text-sm font-medium ${themeClasses.text}`}>Assignee:</span>
                    <p className={`mt-1 text-sm ${themeClasses.text}`}>{selectedTask.assignee}</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
