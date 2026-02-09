"""
State definition for tax determination workflow
"""

from typing import List, Annotated, Optional
from typing_dict import TypedDict
import operator


class TaxDeterminationState(TypedDict):
    """State object passed between nodes in the workflow"""
    
    # Input data
    item_description: str
    hsn: int
    supplier_name: str
    supplier_gstin: str
    supplier_country: str
    buyer_gstin: str
    buyer_country: str
    tax: List[tuple]  # [('CGST', '9%'), ('SGST', '9%')]
    erp_type: str  # SAP_ECC, ORACLE, MS_365
    
    # Extracted/computed data
    supplier_state_code: str
    buyer_state_code: str
    is_union_territory: bool
    transaction_type: str  # INTRA or INTER
    total_tax_rate: float
    is_rcm: bool
    is_credit_eligible: bool
    
    # Result
    tax_code: str
    tax_description: str
    confidence: float
    
    # Token usage tracking (accumulated across all LLM calls)
    total_prompt_tokens: int
    total_completion_tokens: int
    total_reasoning_tokens: int
    total_tokens: int
    
    # Metadata
    messages: Annotated[List[str], operator.add]  # Accumulate log messages
    errors: Annotated[List[str], operator.add]  # Accumulate errors
