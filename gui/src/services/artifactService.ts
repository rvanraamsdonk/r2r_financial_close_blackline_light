// Real-time artifact consumption from /out directory
// Implements the ArtifactConsumer interface from the design brief

export interface EvidenceRef {
  id: string;
  type: string;
  timestamp: string;
  path?: string;
}

export interface AIContribution {
  method: 'DET' | 'AI' | 'HYBRID';
  confidence: number;
  contribution: string;
  output: string;
  evidence: EvidenceRef[];
  timestamp: string;
}

export interface JournalEntryException {
  je_id: string;
  entity: string;
  amount: number;
  currency: string;
  source_system: string;
  reason: string;
  approval_status?: string;
  approver?: string;
}

export interface CloseReport {
  generated_at: string;
  period: string;
  entity_scope: string;
  artifacts: Record<string, string>;
  summary: {
    period: string;
    entity: string;
    risk_level: string;
    block_close: boolean;
    open_hitl_cases: number;
    tb_balanced_by_entity: boolean;
    fx_coverage_ok: boolean;
    key_counts: {
      ap_exceptions: number;
      ar_exceptions: number;
      je_exceptions: number;
      flux_exceptions: number;
      accruals_exceptions: number;
    };
  };
  audit_log: string;
}

export interface JELifecycle {
  generated_at: string;
  period: string;
  entity_scope: string;
  rules: Record<string, boolean>;
  exceptions: JournalEntryException[];
  summary: {
    count: number;
    total_abs_amount: number;
    by_reason: Record<string, number>;
  };
}

class ArtifactService {
  private baseUrl = 'http://localhost:5001'; // Backend API base
  private cache = new Map<string, any>();
  private listeners = new Set<(data: any) => void>();
  private selectedRun: string = 'latest';

  // Get available runs
  async getAvailableRuns(): Promise<any> {
    try {
      const response = await fetch('/runs_manifest.json');
      if (!response.ok) return { runs: [], latest: null };
      return await response.json();
    } catch (error) {
      console.error('Failed to fetch runs manifest:', error);
      return { runs: [], latest: null };
    }
  }

  // Set selected run
  setSelectedRun(timestamp: string): void {
    this.selectedRun = timestamp;
    this.cache.clear(); // Clear cache when switching runs
    this.notifyListeners({ runChanged: timestamp });
  }

  // Get current run timestamp
  private async getCurrentRunTimestamp(): Promise<string> {
    if (this.selectedRun === 'latest') {
      const manifest = await this.getAvailableRuns();
      // Prefer explicit latest, otherwise fall back to first run (newest) if available
      const fallback = Array.isArray(manifest?.runs) && manifest.runs.length > 0
        ? manifest.runs[0].timestamp
        : '';
      return manifest.latest || fallback;
    }
    return this.selectedRun;
  }

  // Build canonical artifact URL resolved by backend to timestamped file
  private async buildArtifactUrl(canonicalPath: string): Promise<string> {
    const timestamp = await this.getCurrentRunTimestamp();
    return `${this.baseUrl}/api/runs/run_${timestamp}/artifact/${canonicalPath}`;
  }

  // Get close report for selected run
  async getLatestCloseReport(): Promise<CloseReport | null> {
    try {
      const url = await this.buildArtifactUrl('close_report.json');
      const response = await fetch(url);
      if (!response.ok) return null;
      
      const data = await response.json();
      this.cache.set('close_report', data);
      return data;
    } catch (error) {
      console.error('Failed to fetch close report:', error);
      return null;
    }
  }

  // Get JE lifecycle data for selected run
  async getJELifecycle(): Promise<JELifecycle | null> {
    try {
      const url = await this.buildArtifactUrl('je_lifecycle.json');
      const response = await fetch(url);
      if (!response.ok) return null;
      
      const data = await response.json();
      this.cache.set('je_lifecycle', data);
      return data;
    } catch (error) {
      console.error('Failed to fetch JE lifecycle:', error);
      return null;
    }
  }

  // Get reconciliation data for selected run
  async getReconciliationData(type: 'ap' | 'ar' | 'bank' | 'intercompany'): Promise<any> {
    try {
      const url = await this.buildArtifactUrl(`${type}_reconciliation.json`);
      const response = await fetch(url);
      if (!response.ok) return null;
      
      const data = await response.json();
      this.cache.set(`${type}_reconciliation`, data);
      return data;
    } catch (error) {
      console.error(`Failed to fetch ${type} reconciliation:`, error);
      return null;
    }
  }

  // Get flux analysis data for selected run
  async getFluxAnalysis(): Promise<any> {
    try {
      const url = await this.buildArtifactUrl('flux_analysis.json');
      const response = await fetch(url);
      if (!response.ok) return { rows: [] };
      
      return await response.json();
    } catch (error) {
      console.error('Failed to fetch flux analysis:', error);
      return { rows: [] };
    }
  }

  async getFluxAINarratives(): Promise<any> {
    try {
      const url = await this.buildArtifactUrl('ai_cache/flux_ai_narratives.json');
      const response = await fetch(url);
      if (response.ok) {
        return await response.json();
      }
      
      return { narratives: [] };
    } catch (error) {
      console.error('Failed to fetch flux AI narratives:', error);
      return { narratives: [] };
    }
  }

  // Build provenance chain for a given value
  async buildProvenanceChain(value: number, description: string): Promise<any> {
    try {
      // In a real implementation, this would trace through multiple artifacts
      // to build the complete provenance chain
      
      // Mock implementation - would normally trace actual dependencies
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
            timestamp: new Date().toISOString(),
            description: 'Final calculated balance',
            value: value,
            children: [
              {
                id: '1.1',
                type: 'ai_output',
                timestamp: new Date(Date.now() - 300000).toISOString(),
                description: 'AI variance analysis adjustment',
                value: value * 0.1,
                ai_method: 'regression',
                confidence: 0.87,
                source_file: '/out/flux_analysis_20250823T194318Z.json'
              },
              {
                id: '1.2',
                type: 'source_data',
                timestamp: new Date(Date.now() - 600000).toISOString(),
                description: 'Base period amount from GL',
                value: value * 0.9,
                source_file: '/data/lite/budget.csv',
                user: 'system'
              }
            ]
          }
        ]
      };
    } catch (error) {
      console.error('Failed to build provenance chain:', error);
      throw error;
    }
  }


  // Get AI cache data
  async getAICache(type: string): Promise<any> {
    try {
      // This would need to be enhanced to find the correct AI cache file
      const response = await fetch(`${this.baseUrl}/ai_cache/${type}_ai_20250823T194318Z.json`);
      if (!response.ok) return null;
      
      return await response.json();
    } catch (error) {
      console.error(`Failed to fetch AI cache for ${type}:`, error);
      return null;
    }
  }

  // Subscribe to real-time updates
  subscribe(callback: (data: any) => void): () => void {
    this.listeners.add(callback);
    return () => this.listeners.delete(callback);
  }

  private notifyListeners(data: any): void {
    this.listeners.forEach(callback => callback(data));
  }

  // Watch out directory for changes (would use file system watcher in real implementation)
  watchOutDirectory(): void {
    // In a real implementation, this would use fs.watch or similar
    // For now, we'll poll periodically
    setInterval(async () => {
      await this.getLatestCloseReport();
    }, 30000); // Poll every 30 seconds
  }
}

export const artifactService = new ArtifactService();
