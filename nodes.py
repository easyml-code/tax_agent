"""
LangGraph nodes for tax code determination workflow
"""

from typing import Dict, Any
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from logs.log import logger
from llm.llm import get_llm_response

from .state import TaxDeterminationState
from .tools import (
    extract_state_code_from_gstin,
    determine_transaction_type,
    calculate_total_tax_rate,
    check_rcm_applicability,
    lookup_tax_code,
)
from .prompt import get_system_prompt
from .metrics import track_node_metrics, track_llm_call, track_llm_tokens


class TaxCodeOutput(BaseModel):
    """LLM output for tax code determination"""
    tax_code: str = Field(description="Tax code for the ERP system")
    reasoning: str = Field(description="Reasoning for tax code selection")
    confidence: float = Field(description="Confidence score 0-1", ge=0, le=1)


@track_node_metrics("preprocessing")
def preprocessing_node(state: TaxDeterminationState) -> Dict[str, Any]:
    """
    Preprocessing node: Extract state codes, determine transaction type, calculate rates
    
    Args:
        state: Current state
    
    Returns:
        Updated state dict
    """
    logger.info(f"[PREPROCESSING] Starting for supplier: {state['supplier_name']}")
    
    updates = {}
    messages = []
    errors = []
    
    try:
        erp_type = state.get('erp_type', 'SAP_ECC')
        
        # Extract supplier state code
        supplier_result = extract_state_code_from_gstin(state['supplier_gstin'], erp_type)
        if not supplier_result.is_valid:
            error_msg = f"Invalid supplier GSTIN: {supplier_result.error}"
            errors.append(error_msg)
            logger.warning(error_msg)
        
        updates['supplier_state_code'] = supplier_result.state_code
        messages.append(f"Supplier state: {supplier_result.state_code}")
        
        # Extract buyer state code
        buyer_result = extract_state_code_from_gstin(state['buyer_gstin'], erp_type)
        if not buyer_result.is_valid:
            error_msg = f"Invalid buyer GSTIN: {buyer_result.error}"
            errors.append(error_msg)
            logger.warning(error_msg)
        
        updates['buyer_state_code'] = buyer_result.state_code
        messages.append(f"Buyer state: {buyer_result.state_code}")
        
        # Determine if Union Territory
        updates['is_union_territory'] = supplier_result.is_union_territory
        if supplier_result.is_union_territory:
            messages.append(f"State {supplier_result.state_code} is a Union Territory")
        
        # Determine transaction type
        txn_result = determine_transaction_type(
            state['supplier_gstin'],
            state['buyer_gstin'],
            erp_type
        )
        updates['transaction_type'] = txn_result.transaction_type
        messages.append(f"Transaction type: {txn_result.transaction_type}state")
        
        # Calculate total tax rate
        total_rate = calculate_total_tax_rate(state['tax'])
        updates['total_tax_rate'] = total_rate
        messages.append(f"Total tax rate: {total_rate}%")
        
        # Check RCM applicability
        is_rcm = check_rcm_applicability(
            state['supplier_gstin'],
            state['supplier_country'],
            state['item_description']
        )
        updates['is_rcm'] = is_rcm
        if is_rcm:
            messages.append("RCM applicable")
        
        # Default ITC eligibility to True (can be enhanced with GL account logic)
        updates['is_credit_eligible'] = True
        
        logger.info(f"[PREPROCESSING] Complete: {txn_result.transaction_type}state, Rate: {total_rate}%")
        
    except Exception as e:
        error_msg = f"Preprocessing error: {str(e)}"
        errors.append(error_msg)
        logger.error(error_msg, exc_info=True)
    
    updates['messages'] = messages
    updates['errors'] = errors
    
    return updates


@track_node_metrics("tax_determination")
async def tax_determination_node(state: TaxDeterminationState) -> Dict[str, Any]:
    """
    Tax determination node: Lookup tax code from master or use LLM for complex cases
    
    Args:
        state: Current state
    
    Returns:
        Updated state dict
    """
    logger.info(f"[TAX_DETERMINATION] Starting for rate: {state['total_tax_rate']}%")
    
    updates = {}
    messages = []
    errors = []
    
    # Initialize token counters
    prompt_tokens = 0
    completion_tokens = 0
    reasoning_tokens = 0
    
    try:
        erp_type = state.get('erp_type', 'SAP_ECC')
        
        # Determine state type (UT or STATE)
        state_type = "UT" if state['is_union_territory'] else "STATE"
        
        # Determine charge type
        charge_type = "RCM" if state['is_rcm'] else "REGULAR"
        
        # Determine credit type
        credit_type = "CREDIT" if state['is_credit_eligible'] else "NON_CREDIT"
        
        # Attempt direct lookup first
        lookup_result = lookup_tax_code(
            tax_rate=state['total_tax_rate'],
            transaction_type=state['transaction_type'],
            charge_type=charge_type,
            credit_type=credit_type,
            state_type=state_type,
            erp_type=erp_type
        )
        
        if lookup_result.found:
            # Direct match found
            updates['tax_code'] = lookup_result.tax_code
            updates['tax_description'] = lookup_result.tax_description
            updates['confidence'] = lookup_result.confidence
            messages.append(f"Tax code found in master: {lookup_result.tax_code}")
            logger.info(f"[TAX_DETERMINATION] Direct lookup: {lookup_result.tax_code}")
        
        else:
            # No direct match - use LLM for complex case
            messages.append("No direct match - using LLM for determination")
            logger.info("[TAX_DETERMINATION] Using LLM for complex case")
            
            # Prepare context for LLM
            context = f"""
Item Description: {state['item_description']}
HSN Code: {state['hsn']}
Supplier: {state['supplier_name']} (GSTIN: {state['supplier_gstin']})
Supplier State: {state['supplier_state_code']}
Buyer State: {state['buyer_state_code']}
Transaction Type: {state['transaction_type']}state
Tax Breakdown: {state['tax']}
Total Tax Rate: {state['total_tax_rate']}%
Is Union Territory: {state['is_union_territory']}
RCM Applicable: {state['is_rcm']}
ITC Eligible: {state['is_credit_eligible']}

Determine the appropriate {erp_type} tax code for this transaction.
"""
            
            # Get system prompt
            system_prompt = get_system_prompt(erp_type)
            
            # Call LLM with tracking
            parser = PydanticOutputParser(pydantic_object=TaxCodeOutput)
            
            @track_llm_call("tax_determination", erp_type)
            async def call_llm():
                return await get_llm_response(
                    content=context,
                    parser=parser,
                    system_prompt=system_prompt
                )
            
            try:
                llm_response, llm_output = await call_llm()
                
                # Extract token usage from LangChain AIMessage format
                if llm_output and 'token_usage' in llm_output:
                    token_usage = llm_output['token_usage']
                    prompt_tokens = token_usage.get('prompt_tokens', 0)
                    completion_tokens = token_usage.get('completion_tokens', 0)
                    
                    # Handle completion_tokens_details for reasoning tokens
                    if 'completion_tokens_details' in token_usage:
                        details = token_usage['completion_tokens_details']
                        reasoning_tokens = details.get('reasoning_tokens', 0)
                
                # Track tokens in metrics
                track_llm_tokens(erp_type, prompt_tokens, completion_tokens, reasoning_tokens)
                
                updates['tax_code'] = llm_response.tax_code
                updates['tax_description'] = llm_response.reasoning
                updates['confidence'] = llm_response.confidence
                messages.append(f"LLM determined tax code: {llm_response.tax_code}")
                logger.info(f"[TAX_DETERMINATION] LLM result: {llm_response.tax_code}")
                
            except Exception as llm_error:
                error_msg = f"LLM error: {str(llm_error)}"
                errors.append(error_msg)
                logger.error(error_msg, exc_info=True)
                
                # Fallback
                updates['tax_code'] = "MANUAL_REVIEW_REQUIRED"
                updates['tax_description'] = "Error in automated determination"
                updates['confidence'] = 0.0
        
    except Exception as e:
        error_msg = f"Tax determination error: {str(e)}"
        errors.append(error_msg)
        logger.error(error_msg, exc_info=True)
        
        updates['tax_code'] = "ERROR"
        updates['tax_description'] = str(e)
        updates['confidence'] = 0.0
    
    # Accumulate token usage in state
    current_prompt = state.get('total_prompt_tokens', 0)
    current_completion = state.get('total_completion_tokens', 0)
    current_reasoning = state.get('total_reasoning_tokens', 0)
    
    updates['total_prompt_tokens'] = current_prompt + prompt_tokens
    updates['total_completion_tokens'] = current_completion + completion_tokens
    updates['total_reasoning_tokens'] = current_reasoning + reasoning_tokens
    updates['total_tokens'] = (current_prompt + prompt_tokens + 
                                current_completion + completion_tokens + 
                                current_reasoning + reasoning_tokens)
    
    updates['messages'] = messages
    updates['errors'] = errors
    
    return updates


@track_node_metrics("validation")
def validation_node(state: TaxDeterminationState) -> Dict[str, Any]:
    """
    Validation node: Validate tax code and apply business rules
    
    Args:
        state: Current state
    
    Returns:
        Updated state dict
    """
    logger.info(f"[VALIDATION] Validating tax code: {state['tax_code']}")
    
    updates = {}
    messages = []
    errors = []
    
    try:
        # Validation checks
        
        # 1. Check confidence threshold
        if state['confidence'] < 0.6:
            messages.append(f"Low confidence: {state['confidence']}")
            errors.append("Confidence below threshold (0.6)")
        
        # 2. Validate tax code format
        tax_code = state['tax_code']
        if tax_code in ['MANUAL_REVIEW_REQUIRED', 'ERROR', '']:
            messages.append("Tax code requires manual review")
            errors.append("Tax code not automatically determined")
        
        # 3. Cross-check rate consistency
        # For interstate, IGST rate should match total tax rate
        if state['transaction_type'] == 'INTER' and tax_code.startswith('1'):
            messages.append("IGST tax code matches interstate transaction")
        
        # For intrastate, CGST+SGST should sum to total tax rate
        elif state['transaction_type'] == 'INTRA' and (tax_code.startswith('3') or tax_code.startswith('R')):
            messages.append("CGST-SGST tax code matches intrastate transaction")
        
        # 4. TODO: Additional validations
        # - HSN code validation against tax rate
        # - Supplier type validation
        # - Industry-specific rules
        
        if len(errors) == 0:
            messages.append("All validations passed")
            logger.info(f"[VALIDATION] Success: {tax_code}")
        else:
            logger.warning(f"[VALIDATION] Warnings: {errors}")
        
    except Exception as e:
        error_msg = f"Validation error: {str(e)}"
        errors.append(error_msg)
        logger.error(error_msg, exc_info=True)
    
    updates['messages'] = messages
    updates['errors'] = errors
    
    return updates
