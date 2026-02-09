"""
Tools for tax code determination
"""

from typing import Dict, Optional, Tuple, List
from pydantic import BaseModel, Field
import re
from logs.log import logger

from .masters import (
    SAP_TAX_CODE_MASTER,
    SAP_TAX_CODE_DESCRIPTIONS,
    SAP_UNION_TERRITORIES,
    ORACLE_TAX_CODE_MASTER,
    ORACLE_TAX_CODE_DESCRIPTIONS,
    ORACLE_UNION_TERRITORIES,
    MS360_TAX_CODE_MASTER,
    MS360_TAX_CODE_DESCRIPTIONS,
    MS360_UNION_TERRITORIES,
)
from .metrics import (
    track_tool_call,
    track_tool_success,
    track_tool_failure,
)


class GSTINExtractResult(BaseModel):
    """Result of GSTIN state code extraction"""
    state_code: str = Field(description="2-digit state code")
    is_valid: bool = Field(description="Whether GSTIN format is valid")
    is_union_territory: bool = Field(description="Whether state is a Union Territory")
    error: Optional[str] = Field(default=None, description="Error message if invalid")


class TransactionTypeResult(BaseModel):
    """Result of transaction type determination"""
    transaction_type: str = Field(description="INTRA or INTER")
    supplier_state: str = Field(description="Supplier state code")
    buyer_state: str = Field(description="Buyer state code")
    is_same_state: bool = Field(description="Whether supplier and buyer in same state")


class TaxCodeLookupResult(BaseModel):
    """Result of tax code lookup"""
    tax_code: str = Field(description="Tax code")
    tax_description: str = Field(description="Tax code description")
    confidence: float = Field(description="Confidence score 0-1")
    found: bool = Field(description="Whether tax code was found in master")


@track_tool_call("extract_state_code_from_gstin")
def extract_state_code_from_gstin(gstin: str, erp_type: str = "SAP_ECC") -> GSTINExtractResult:
    """
    Extract state code from GSTIN and validate format
    
    GSTIN Format: [01-02][03-12][13][14][15]
                  State  PAN    Entity Check
                  Code         Type   Digit
    
    Args:
        gstin: 15-character GSTIN
        erp_type: ERP type for Union Territory lookup
    
    Returns:
        GSTINExtractResult with state code and validation info
    """
    try:
        if not gstin or len(gstin) != 15:
            track_tool_failure("extract_state_code_from_gstin", "invalid_length")
            return GSTINExtractResult(
                state_code="",
                is_valid=False,
                is_union_territory=False,
                error="GSTIN must be 15 characters"
            )
        
        # Validate GSTIN format using regex
        pattern = r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$'
        if not re.match(pattern, gstin):
            track_tool_failure("extract_state_code_from_gstin", "invalid_format")
            return GSTINExtractResult(
                state_code="",
                is_valid=False,
                is_union_territory=False,
                error="Invalid GSTIN format"
            )
        
        state_code = gstin[0:2]
        
        # Get appropriate Union Territory set based on ERP
        if erp_type == "ORACLE":
            ut_set = ORACLE_UNION_TERRITORIES
        elif erp_type == "MS_365":
            ut_set = MS360_UNION_TERRITORIES
        else:
            ut_set = SAP_UNION_TERRITORIES
        
        is_ut = state_code in ut_set
        
        track_tool_success("extract_state_code_from_gstin")
        
        return GSTINExtractResult(
            state_code=state_code,
            is_valid=True,
            is_union_territory=is_ut,
            error=None
        )
    
    except Exception as e:
        track_tool_failure("extract_state_code_from_gstin", "exception")
        logger.error(f"Error extracting state code: {str(e)}", exc_info=True)
        return GSTINExtractResult(
            state_code="",
            is_valid=False,
            is_union_territory=False,
            error=f"Exception: {str(e)}"
        )


@track_tool_call("determine_transaction_type")
def determine_transaction_type(supplier_gstin: str, buyer_gstin: str, erp_type: str = "SAP_ECC") -> TransactionTypeResult:
    """
    Determine if transaction is intrastate or interstate
    
    Args:
        supplier_gstin: Supplier's GSTIN
        buyer_gstin: Buyer's GSTIN
        erp_type: ERP type
    
    Returns:
        TransactionTypeResult with transaction type
    """
    try:
        supplier_result = extract_state_code_from_gstin(supplier_gstin, erp_type)
        buyer_result = extract_state_code_from_gstin(buyer_gstin, erp_type)
        
        if not supplier_result.is_valid or not buyer_result.is_valid:
            track_tool_failure("determine_transaction_type", "invalid_gstin")
            return TransactionTypeResult(
                transaction_type="UNKNOWN",
                supplier_state=supplier_result.state_code,
                buyer_state=buyer_result.state_code,
                is_same_state=False
            )
        
        is_same = supplier_result.state_code == buyer_result.state_code
        txn_type = "INTRA" if is_same else "INTER"
        
        track_tool_success("determine_transaction_type")
        
        return TransactionTypeResult(
            transaction_type=txn_type,
            supplier_state=supplier_result.state_code,
            buyer_state=buyer_result.state_code,
            is_same_state=is_same
        )
    
    except Exception as e:
        track_tool_failure("determine_transaction_type", "exception")
        logger.error(f"Error determining transaction type: {str(e)}", exc_info=True)
        return TransactionTypeResult(
            transaction_type="UNKNOWN",
            supplier_state="",
            buyer_state="",
            is_same_state=False
        )


@track_tool_call("calculate_total_tax_rate")
def calculate_total_tax_rate(tax_list: List[Tuple[str, str]]) -> float:
    """
    Calculate total tax rate from tax list
    
    Args:
        tax_list: List of (tax_type, rate) tuples, e.g., [('CGST', '9%'), ('SGST', '9%')]
    
    Returns:
        Total tax rate as float
    """
    try:
        total = 0.0
        for tax_type, rate_str in tax_list:
            # Remove % and convert to float
            rate = float(rate_str.replace('%', '').strip())
            total += rate
        
        track_tool_success("calculate_total_tax_rate")
        return total
    
    except Exception as e:
        track_tool_failure("calculate_total_tax_rate", "exception")
        logger.error(f"Error calculating tax rate: {str(e)}", exc_info=True)
        return 0.0


@track_tool_call("check_rcm_applicability")
def check_rcm_applicability(
    supplier_gstin: Optional[str],
    supplier_country: str,
    item_description: str
) -> bool:
    """
    Check if Reverse Charge Mechanism (RCM) is applicable
    
    RCM scenarios:
    - Unregistered vendor (no GSTIN)
    - Foreign vendor
    - Specific notified services (GTA, Legal, etc.) - TODO: Implement detailed checks
    
    Args:
        supplier_gstin: Supplier's GSTIN (None if unregistered)
        supplier_country: Supplier's country code
        item_description: Item description for service type detection
    
    Returns:
        Boolean indicating RCM applicability
    """
    try:
        # Foreign vendor
        if supplier_country != "IN":
            track_tool_success("check_rcm_applicability")
            return True
        
        # Unregistered vendor (no valid GSTIN)
        if not supplier_gstin or supplier_gstin.upper() in ['URP', 'UNREGISTERED', 'NA']:
            track_tool_success("check_rcm_applicability")
            return True
        
        # TODO: Add logic for notified services (GTA, Legal, Advocate, etc.)
        # This would require SAC code or keyword matching
        rcm_keywords = ['reverse charge', 'rcm', 'gta', 'legal', 'advocate', 'arbitration']
        description_lower = item_description.lower()
        if any(keyword in description_lower for keyword in rcm_keywords):
            track_tool_success("check_rcm_applicability")
            return True
        
        track_tool_success("check_rcm_applicability")
        return False
    
    except Exception as e:
        track_tool_failure("check_rcm_applicability", "exception")
        logger.error(f"Error checking RCM applicability: {str(e)}", exc_info=True)
        return False


@track_tool_call("lookup_tax_code")
def lookup_tax_code(
    tax_rate: float,
    transaction_type: str,
    charge_type: str,
    credit_type: str,
    state_type: str,
    erp_type: str = "SAP_ECC"
) -> TaxCodeLookupResult:
    """
    Lookup tax code from master mapping
    
    Args:
        tax_rate: Total tax rate (0, 0.25, 3, 5, 12, 18, 28)
        transaction_type: INTRA or INTER
        charge_type: REGULAR or RCM
        credit_type: CREDIT or NON_CREDIT
        state_type: STATE or UT (Union Territory)
        erp_type: ERP system type
    
    Returns:
        TaxCodeLookupResult with tax code and metadata
    """
    try:
        # Normalize tax rate to string
        rate_str = str(tax_rate).rstrip('0').rstrip('.')
        
        # Build lookup key
        lookup_key = (rate_str, transaction_type, charge_type, credit_type, state_type)
        
        # Select appropriate master based on ERP type
        if erp_type == "ORACLE":
            tax_master = ORACLE_TAX_CODE_MASTER
            desc_master = ORACLE_TAX_CODE_DESCRIPTIONS
        elif erp_type == "MS_365":
            tax_master = MS360_TAX_CODE_MASTER
            desc_master = MS360_TAX_CODE_DESCRIPTIONS
        else:  # SAP_ECC
            tax_master = SAP_TAX_CODE_MASTER
            desc_master = SAP_TAX_CODE_DESCRIPTIONS
        
        # Lookup in master
        tax_code = tax_master.get(lookup_key)
        
        if tax_code:
            # Get description from master or build it
            tax_description = desc_master.get(
                tax_code,
                f"Tax Code {tax_code} - {rate_str}%"
            )
            
            track_tool_success("lookup_tax_code")
            
            return TaxCodeLookupResult(
                tax_code=tax_code,
                tax_description=tax_description,
                confidence=0.95,
                found=True
            )
        else:
            track_tool_failure("lookup_tax_code", "not_found")
            
            return TaxCodeLookupResult(
                tax_code="MANUAL_REVIEW",
                tax_description=f"No mapping found: rate={rate_str}%, type={transaction_type}, charge={charge_type}",
                confidence=0.0,
                found=False
            )
    
    except Exception as e:
        track_tool_failure("lookup_tax_code", "exception")
        logger.error(f"Error looking up tax code: {str(e)}", exc_info=True)
        
        return TaxCodeLookupResult(
            tax_code="ERROR",
            tax_description=f"Lookup error: {str(e)}",
            confidence=0.0,
            found=False
        )
