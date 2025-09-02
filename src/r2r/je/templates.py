"""
Journal Entry Template Registry - Module-specific JE calculation templates
"""

from typing import Dict, Optional
from .models import JETemplate


class JETemplateRegistry:
    """Registry for JE templates by module and scenario"""
    
    def __init__(self):
        self._templates: Dict[str, JETemplate] = {}
        self._load_default_templates()
    
    def _load_default_templates(self):
        """Load default templates for common scenarios"""
        
        # FX Translation Adjustment Template
        self.register_template(JETemplate(
            module="FX",
            scenario="translation_adjustment",
            description_template="FX translation adjustment - {currency} {amount} ({entity}/{account})",
            account_mappings={
                "fx_gain_loss": "7200",  # FX Gain/Loss account
                "translation_reserve": "3900"  # Translation reserve
            },
            calculation_rules={
                "amount_field": "diff_usd",
                "threshold_field": "tolerance_usd"
            },
            materiality_threshold=0.01,
            approval_required=True
        ))
        
        # Flux Variance Accrual Template
        self.register_template(JETemplate(
            module="Flux",
            scenario="accrual_adjustment", 
            description_template="Accrual adjustment for budget variance - {amount} ({entity}/{account})",
            account_mappings={
                "accrual_payable": "2100",  # Accrued expenses
                "accrual_receivable": "1300"  # Accrued revenue
            },
            calculation_rules={
                "amount_field": "var_vs_budget",
                "threshold_field": "threshold_usd"
            },
            materiality_threshold=1000.0,
            approval_required=True
        ))
        
        # AP Reconciliation Clearing Template
        self.register_template(JETemplate(
            module="AP",
            scenario="clearing_adjustment",
            description_template="AP clearing adjustment - {amount} ({entity})",
            account_mappings={
                "ap_clearing": "2000",  # AP clearing account
                "suspense": "1900"  # Suspense account
            },
            calculation_rules={
                "amount_field": "unmatched_amount"
            },
            materiality_threshold=100.0,
            approval_required=True
        ))
        
        # AR Reconciliation Clearing Template  
        self.register_template(JETemplate(
            module="AR",
            scenario="clearing_adjustment",
            description_template="AR clearing adjustment - {amount} ({entity})",
            account_mappings={
                "ar_clearing": "1200",  # AR clearing account
                "suspense": "1900"  # Suspense account
            },
            calculation_rules={
                "amount_field": "unmatched_amount"
            },
            materiality_threshold=100.0,
            approval_required=True
        ))
        
        # Intercompany Elimination Template
        self.register_template(JETemplate(
            module="Intercompany",
            scenario="elimination_entry",
            description_template="Intercompany elimination - {amount} ({entity})",
            account_mappings={
                "ic_receivable": "1400",  # IC receivable
                "ic_payable": "2400",  # IC payable
                "ic_revenue": "4100",  # IC revenue
                "ic_expense": "6100"  # IC expense
            },
            calculation_rules={
                "amount_field": "elimination_amount"
            },
            materiality_threshold=500.0,
            approval_required=True
        ))
        
        # Accrual Reversal Template
        self.register_template(JETemplate(
            module="Accruals",
            scenario="reversal_entry",
            description_template="Accrual reversal - {amount} ({entity}/{account})",
            account_mappings={
                "accrual_expense": "6000",  # Accrued expense
                "accrual_payable": "2100"  # Accrued payable
            },
            calculation_rules={
                "amount_field": "reversal_amount"
            },
            materiality_threshold=250.0,
            approval_required=False  # Reversals often auto-approved
        ))
    
    def register_template(self, template: JETemplate):
        """Register a new JE template"""
        key = f"{template.module}:{template.scenario}"
        self._templates[key] = template
    
    def get_template(self, module: str, scenario: str) -> Optional[JETemplate]:
        """Get JE template for module/scenario"""
        key = f"{module}:{scenario}"
        return self._templates.get(key)
    
    def list_templates(self, module: Optional[str] = None) -> Dict[str, JETemplate]:
        """List all templates, optionally filtered by module"""
        if module:
            return {k: v for k, v in self._templates.items() if v.module == module}
        return self._templates.copy()
    
    def get_scenarios_for_module(self, module: str) -> list[str]:
        """Get all available scenarios for a module"""
        return [t.scenario for t in self._templates.values() if t.module == module]
