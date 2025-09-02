"""
Journal Entry Engine - Core JE calculation and proposal logic
"""

from typing import Dict, Any, List, Optional
from .models import JEProposal, JELine, JEStatus, JETemplate
from .templates import JETemplateRegistry
from .mappings import AccountMappingService
import uuid
from datetime import datetime


class JEEngine:
    """Core engine for calculating and proposing journal entries"""
    
    def __init__(self):
        self.template_registry = JETemplateRegistry()
        self.account_mapping = AccountMappingService()
    
    def propose_je(
        self,
        module: str,
        scenario: str,
        source_data: Dict[str, Any],
        period: str,
        entity: str,
        user_id: Optional[str] = None
    ) -> Optional[JEProposal]:
        """
        Generate a JE proposal for the given module/scenario/data
        
        Args:
            module: "FX", "Flux", "AP", "AR", etc.
            scenario: "translation_adjustment", "accrual_reversal", etc.
            source_data: Original data triggering the JE (e.g., FX difference row)
            period: Accounting period
            entity: Entity code
            user_id: User proposing the JE
        
        Returns:
            JEProposal if calculation successful, None if no JE needed
        """
        template = self.template_registry.get_template(module, scenario)
        if not template:
            raise ValueError(f"No template found for {module}/{scenario}")
        
        # Check materiality threshold
        amount = self._extract_amount(source_data, template)
        if abs(amount) < template.materiality_threshold:
            return None  # Below materiality, no JE needed
        
        # Calculate JE lines using template rules
        lines = self._calculate_lines(template, source_data, entity, amount)
        if not lines:
            return None
        
        # Generate description from template
        description = self._format_description(template, source_data, amount)
        
        proposal = JEProposal(
            id=str(uuid.uuid4()),
            module=module,
            scenario=scenario,
            period=period,
            entity=entity,
            description=description,
            lines=lines,
            source_data=source_data,
            status=JEStatus.DRAFT,
            created_by=user_id,
            created_at=datetime.utcnow()
        )
        
        # Validate before returning
        errors = proposal.validate()
        if errors:
            raise ValueError(f"Generated JE failed validation: {errors}")
        
        return proposal
    
    def _extract_amount(self, source_data: Dict[str, Any], template: JETemplate) -> float:
        """Extract the key amount from source data based on template rules"""
        amount_field = template.calculation_rules.get("amount_field", "amount")
        return float(source_data.get(amount_field, 0.0))
    
    def _calculate_lines(
        self, 
        template: JETemplate, 
        source_data: Dict[str, Any], 
        entity: str,
        amount: float
    ) -> List[JELine]:
        """Calculate debit/credit lines based on template and source data"""
        lines = []
        
        # Get account mappings for this entity
        accounts = self.account_mapping.get_accounts(entity, template.module, template.scenario)
        
        if template.module == "FX" and template.scenario == "translation_adjustment":
            # FX translation adjustment logic
            diff_usd = source_data.get("diff_usd", 0.0)
            account = source_data.get("account", "")
            currency = source_data.get("currency", "USD")
            
            if diff_usd != 0:
                # Asset/Liability adjustment
                if diff_usd > 0:
                    lines.append(JELine(
                        account=account,
                        description=f"FX translation adjustment - {currency}",
                        debit=abs(diff_usd),
                        entity=entity,
                        currency="USD"
                    ))
                    lines.append(JELine(
                        account=accounts.get("fx_gain_loss", "7200"),
                        description=f"FX translation gain - {currency}",
                        credit=abs(diff_usd),
                        entity=entity,
                        currency="USD"
                    ))
                else:
                    lines.append(JELine(
                        account=accounts.get("fx_gain_loss", "7200"),
                        description=f"FX translation loss - {currency}",
                        debit=abs(diff_usd),
                        entity=entity,
                        currency="USD"
                    ))
                    lines.append(JELine(
                        account=account,
                        description=f"FX translation adjustment - {currency}",
                        credit=abs(diff_usd),
                        entity=entity,
                        currency="USD"
                    ))
        
        elif template.module == "Flux" and template.scenario == "accrual_adjustment":
            # Flux variance accrual logic
            var_amount = source_data.get("var_vs_budget", 0.0)
            account = source_data.get("account", "")
            
            if abs(var_amount) > 0:
                expense_account = account
                accrual_account = accounts.get("accrual_payable", "2100")
                
                if var_amount > 0:  # Over budget - additional accrual needed
                    lines.append(JELine(
                        account=expense_account,
                        description="Additional accrual for budget variance",
                        debit=abs(var_amount),
                        entity=entity
                    ))
                    lines.append(JELine(
                        account=accrual_account,
                        description="Accrued liability for budget variance",
                        credit=abs(var_amount),
                        entity=entity
                    ))
        
        return lines
    
    def _format_description(
        self, 
        template: JETemplate, 
        source_data: Dict[str, Any], 
        amount: float
    ) -> str:
        """Format JE description using template and source data"""
        desc_template = template.description_template
        
        # Replace common placeholders
        replacements = {
            "{amount}": f"{abs(amount):,.2f}",
            "{entity}": source_data.get("entity", ""),
            "{account}": source_data.get("account", ""),
            "{currency}": source_data.get("currency", "USD"),
            "{period}": source_data.get("period", "")
        }
        
        description = desc_template
        for placeholder, value in replacements.items():
            description = description.replace(placeholder, str(value))
        
        return description
