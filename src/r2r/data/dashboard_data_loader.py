import pandas as pd
import json
from pathlib import Path

class DashboardDataLoader:
    """Loads and processes financial data for the dashboard."""
    
    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)
    
    def load_trial_balance(self):
        """Load trial balance data from CSV."""
        tb_path = self.data_dir / 'trial_balance_aug.csv'
        df = pd.read_csv(tb_path)
        return df.to_dict('records')
    
    def load_accruals(self):
        """Load accruals data from CSV."""
        accruals_path = self.data_dir / 'supporting' / 'accruals.csv'
        df = pd.read_csv(accruals_path)
        return df.to_dict('records')
    
    def load_emails(self):
        """Load email evidence from JSON."""
        emails_path = self.data_dir / 'supporting' / 'emails.json'
        with open(emails_path) as f:
            return json.load(f)
    
    def get_dashboard_context(self):
        """Generate complete dashboard context with all data sources."""
        return {
            'trial_balance': self.load_trial_balance(),
            'accruals': self.load_accruals(),
            'emails': self.load_emails()
        }
