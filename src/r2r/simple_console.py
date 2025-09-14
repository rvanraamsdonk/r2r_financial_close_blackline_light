"""Simple progress console for R2R close execution."""

from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path
from typing import Optional


class SimpleConsole:
    """Lightweight console for tracking close execution progress."""
    
    def __init__(self, period: str, entity: str, ai_mode: str, run_id: str):
        self.period = period
        self.entity = entity
        self.ai_mode = ai_mode
        self.run_id = run_id
        self.start_time = time.time()
        self.phase_start_time = None
        self.current_phase = 0
        self.total_phases = 12
        self.phase_times = []  # Track individual phase times
        
    def header(self):
        """Print run header."""
        print("=" * 80)
        print(f"  R2R FINANCIAL CLOSE - {self.period}")
        print("=" * 80)
        print(f"  Entity: {self.entity} | AI: {self.ai_mode.upper()} | Run: {self.run_id}")
        print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 80)
    
    def start_phase(self, phase_name: str):
        """Start a new phase."""
        self.current_phase += 1
        self.phase_start_time = time.time()
    
    def progress(self, message: str, processed: Optional[int] = None, 
                total: Optional[int] = None, exceptions: Optional[int] = None):
        """Report progress within current phase (no-op for ultra-crisp mode)."""
        pass
    
    def complete_phase(self, status: str = "SUCCESS", summary: str = "", 
                      artifacts: Optional[list] = None):
        """Complete current phase with ultra-crisp output."""
        if self.phase_start_time:
            duration = time.time() - self.phase_start_time
            self.phase_times.append(duration)  # Track phase time
            phase_name = self._get_phase_name()
            print(f"[{self.current_phase:2d}/{self.total_phases}] {phase_name} ({duration:.2f}s)")
    
    def _get_phase_name(self) -> str:
        """Get phase name by number."""
        phases = [
            "PERIOD_INIT", "VALIDATE", "TB_INTEGRITY", "AP_RECONCILIATION", 
            "AR_RECONCILIATION", "FLUX_ANALYSIS", "BANK_RECONCILIATION", 
            "INTERCOMPANY_RECONCILIATION", "ACCRUALS", "AUTO_JOURNALS", 
            "CONTROLS_MAPPING", "CLOSE_REPORTING"
        ]
        return phases[self.current_phase - 1] if self.current_phase <= len(phases) else "UNKNOWN"
    
    def footer(self, output_dir: Path, audit_log: Path):
        """Print run completion footer."""
        # Use sum of phase times for accurate total, fallback to wall clock time
        total_time = sum(self.phase_times) if self.phase_times else time.time() - self.start_time
        print("\n" + "=" * 80)
        print(f"  EXECUTION COMPLETE ({total_time:.2f}s)")
        print(f"  Output: {output_dir}")
        print(f"  Audit: {audit_log.name}")
        print("=" * 80)
