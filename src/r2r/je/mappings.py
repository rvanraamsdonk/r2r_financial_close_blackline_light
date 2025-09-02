"""
Account Mapping Service - GL account assignment by entity/module/scenario
"""

from typing import Dict, Optional
import json
import os


class AccountMappingService:
    """Service for mapping JE roles to GL accounts by entity and scenario"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "data/je_account_mappings.json"
        self._mappings: Dict[str, Dict[str, Dict[str, str]]] = {}
        self._load_mappings()
    
    def _load_mappings(self):
        """Load account mappings from configuration file"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    self._mappings = json.load(f)
            except Exception:
                self._load_default_mappings()
        else:
            self._load_default_mappings()
    
    def _load_default_mappings(self):
        """Load default account mappings if config file not found"""
        self._mappings = {
            "ENT100": {  # US Entity
                "FX": {
                    "fx_gain_loss": "7200",
                    "translation_reserve": "3900"
                },
                "Flux": {
                    "accrual_payable": "2100",
                    "accrual_receivable": "1300"
                },
                "AP": {
                    "ap_clearing": "2000",
                    "suspense": "1900"
                },
                "AR": {
                    "ar_clearing": "1200", 
                    "suspense": "1900"
                },
                "Intercompany": {
                    "ic_receivable": "1400",
                    "ic_payable": "2400",
                    "ic_revenue": "4100",
                    "ic_expense": "6100"
                },
                "Accruals": {
                    "accrual_expense": "6000",
                    "accrual_payable": "2100"
                }
            },
            "ENT101": {  # UK Entity
                "FX": {
                    "fx_gain_loss": "7201",  # Different FX account for UK
                    "translation_reserve": "3901"
                },
                "Flux": {
                    "accrual_payable": "2101",
                    "accrual_receivable": "1301"
                },
                "AP": {
                    "ap_clearing": "2001",
                    "suspense": "1901"
                },
                "AR": {
                    "ar_clearing": "1201",
                    "suspense": "1901"
                },
                "Intercompany": {
                    "ic_receivable": "1401",
                    "ic_payable": "2401", 
                    "ic_revenue": "4101",
                    "ic_expense": "6101"
                },
                "Accruals": {
                    "accrual_expense": "6001",
                    "accrual_payable": "2101"
                }
            },
            "ENT102": {  # APAC Entity
                "FX": {
                    "fx_gain_loss": "7202",
                    "translation_reserve": "3902"
                },
                "Flux": {
                    "accrual_payable": "2102",
                    "accrual_receivable": "1302"
                },
                "AP": {
                    "ap_clearing": "2002",
                    "suspense": "1902"
                },
                "AR": {
                    "ar_clearing": "1202",
                    "suspense": "1902"
                },
                "Intercompany": {
                    "ic_receivable": "1402",
                    "ic_payable": "2402",
                    "ic_revenue": "4102", 
                    "ic_expense": "6102"
                },
                "Accruals": {
                    "accrual_expense": "6002",
                    "accrual_payable": "2102"
                }
            }
        }
    
    def get_accounts(self, entity: str, module: str, scenario: str) -> Dict[str, str]:
        """
        Get account mappings for entity/module combination
        
        Args:
            entity: Entity code (e.g., "ENT100")
            module: Module name (e.g., "FX", "Flux")
            scenario: Not used in current implementation, for future extensibility
            
        Returns:
            Dict mapping role names to GL account codes
        """
        entity_mappings = self._mappings.get(entity, {})
        module_mappings = entity_mappings.get(module, {})
        
        # Fallback to ENT100 if entity not found
        if not module_mappings and entity != "ENT100":
            fallback_mappings = self._mappings.get("ENT100", {})
            module_mappings = fallback_mappings.get(module, {})
        
        return module_mappings
    
    def get_account(self, entity: str, module: str, role: str, scenario: str = "default") -> Optional[str]:
        """
        Get specific account for entity/module/role
        
        Args:
            entity: Entity code
            module: Module name  
            role: Account role (e.g., "fx_gain_loss", "accrual_payable")
            scenario: Scenario name (for future use)
            
        Returns:
            GL account code or None if not found
        """
        accounts = self.get_accounts(entity, module, scenario)
        return accounts.get(role)
    
    def set_account_mapping(self, entity: str, module: str, role: str, account: str):
        """Set account mapping for entity/module/role"""
        if entity not in self._mappings:
            self._mappings[entity] = {}
        if module not in self._mappings[entity]:
            self._mappings[entity][module] = {}
        
        self._mappings[entity][module][role] = account
    
    def save_mappings(self):
        """Save current mappings to configuration file"""
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(self._mappings, f, indent=2)
    
    def list_entities(self) -> list[str]:
        """Get list of all configured entities"""
        return list(self._mappings.keys())
    
    def list_modules(self, entity: str) -> list[str]:
        """Get list of modules configured for an entity"""
        return list(self._mappings.get(entity, {}).keys())
