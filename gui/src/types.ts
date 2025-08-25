// Shared type definitions for the R2R GUI

export interface EvidenceRef {
  id: string;
  type: string;
  timestamp: string; // ISO string
}

export interface AIContribution {
  method: 'DET' | 'AI' | 'HYBRID';
  confidence: number; // 0-100
  contribution: string;
  output: string;
  evidence: EvidenceRef[];
  timestamp: string;
}

export interface CloseTask {
  id: string;
  name: string;
  phase: string; // phase id
  assignee: string;
  dueDate: string; // ISO date
  status: 'pending' | 'in-progress' | 'complete' | 'blocked' | 'overdue' | 'approved' | 'rejected';
  priority: 'low' | 'medium' | 'high' | 'critical';
  dependencies: string[];
  evidence: EvidenceRef[];
  aiContribution: AIContribution;
}

export interface ClosePhase {
  id: string;
  name: string;
  startDate: string; // ISO date
  endDate: string;   // ISO date
  status: 'not-started' | 'in-progress' | 'complete' | 'overdue';
  tasks: CloseTask[];
}

export interface JournalEntryLine {
  id: string;
  account: string;
  accountName: string;
  debit: number;
  credit: number;
  description?: string;
  aiContribution?: AIContribution;
  evidence: EvidenceRef[];
}

export interface JournalEntry {
  id: string;
  date: string; // ISO date
  reference: string;
  description: string;
  status: 'approved' | 'pending' | 'rejected';
  lines: JournalEntryLine[];
  aiContribution?: AIContribution;
  evidence: EvidenceRef[];
  auditTrail: any[];
}

export interface ColumnDefinition<T = any> {
  key: keyof T | string;
  label: string;
  sortable?: boolean;
  width?: string | number;
  render?: (value: any, record: T) => React.ReactNode;
}
