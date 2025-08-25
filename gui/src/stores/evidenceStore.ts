/**
 * Evidence Store
 * Manages Evidence Viewer sidebar state and evidence data
 */

import { create } from 'zustand';

export interface EvidenceItem {
  id: string;
  value: number;
  description: string;
  account?: string;
  entity?: string;
  period?: string;
  source?: string;
}

export interface EvidenceStore {
  // Sidebar state
  isOpen: boolean;
  width: number;
  isPinned: boolean;
  
  // Evidence data
  currentEvidence: EvidenceItem | null;
  evidenceHistory: EvidenceItem[];
  isLoading: boolean;
  
  // Actions
  openEvidence: (evidence: EvidenceItem) => void;
  closeEvidence: () => void;
  setSidebarWidth: (width: number) => void;
  togglePin: () => void;
  clearHistory: () => void;
  goBack: () => void;
}

export const useEvidenceStore = create<EvidenceStore>((set, get) => ({
  // Initial state
  isOpen: false,
  width: 400,
  isPinned: false,
  currentEvidence: null,
  evidenceHistory: [],
  isLoading: false,
  
  // Actions
  openEvidence: (evidence) => {
    const { currentEvidence, evidenceHistory } = get();
    
    set({
      isOpen: true,
      currentEvidence: evidence,
      evidenceHistory: currentEvidence 
        ? [...evidenceHistory, currentEvidence]
        : evidenceHistory,
      isLoading: true,
    });
    
    // Simulate loading delay
    setTimeout(() => set({ isLoading: false }), 500);
  },
  
  closeEvidence: () => set({
    isOpen: false,
    currentEvidence: null,
  }),
  
  setSidebarWidth: (width) => set({ width: Math.max(300, Math.min(800, width)) }),
  
  togglePin: () => set((state) => ({ isPinned: !state.isPinned })),
  
  clearHistory: () => set({ evidenceHistory: [] }),
  
  goBack: () => {
    const { evidenceHistory } = get();
    if (evidenceHistory.length > 0) {
      const previous = evidenceHistory[evidenceHistory.length - 1];
      const newHistory = evidenceHistory.slice(0, -1);
      
      set({
        currentEvidence: previous,
        evidenceHistory: newHistory,
        isLoading: true,
      });
      
      setTimeout(() => set({ isLoading: false }), 300);
    }
  },
}));
