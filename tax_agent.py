"""
Main tax agent entry point
"""

from typing import List, Dict, Any
from pydantic import BaseModel
from logs.log import logger

from .graph import create_tax_determination_graph
from .state import TaxDeterminationState
from .metrics import track_request_metrics, track_node_metrics


class TaggingRequestLineItem(BaseModel):
    """Single line item for tax tagging"""
    item_description: str
    hsn: int
    supplier_name: str
    po_number: str
    quantity: int
    unit_price: float
    total: float
    supplier_gstin: str
    supplier_country: str
    buyer_gstin: str
    buyer_country: str
    tax: List[tuple]  # [('CGST', '9%'), ('SGST', '9%')]


class TaggingRequest(BaseModel):
    """Request with multiple line items"""
    lines: List[TaggingRequestLineItem]
    erp_type: str = "SAP_ECC"  # SAP_ECC, ORACLE, MS_365


class TaxTaggingResult(BaseModel):
    """Result for a single line item"""
    line_index: int
    item_description: str
    tax_code: str
    tax_description: str
    confidence: float
    total_prompt_tokens: int
    total_completion_tokens: int
    total_reasoning_tokens: int
    total_tokens: int
    messages: List[str]
    errors: List[str]


class TaxTaggingResponse(BaseModel):
    """Response with results for all line items"""
    results: List[TaxTaggingResult]
    summary: Dict[str, Any]


class TaxAgent:
    """Main Tax Agent class"""
    
    def __init__(self):
        """Initialize tax agent with workflow graph"""
        self.graph = create_tax_determination_graph()
        logger.info("[TAX_AGENT] Initialized")
    
    @track_request_metrics(erp_type="SAP_ECC")
    async def process_tagging_request(
        self,
        request: TaggingRequest
    ) -> TaxTaggingResponse:
        """
        Process tax tagging request for multiple line items
        
        Args:
            request: TaggingRequest with line items
        
        Returns:
            TaxTaggingResponse with tax codes for each line
        """
        logger.info(f"[TAX_AGENT] Processing {len(request.lines)} line items for ERP: {request.erp_type}")
        
        results = []
        total_confidence = 0.0
        manual_review_count = 0
        error_count = 0
        
        # Aggregate token usage across all lines
        aggregate_prompt_tokens = 0
        aggregate_completion_tokens = 0
        aggregate_reasoning_tokens = 0
        aggregate_total_tokens = 0
        
        for idx, line in enumerate(request.lines):
            logger.info(f"[TAX_AGENT] Processing line {idx + 1}/{len(request.lines)}")
            
            # Build initial state
            initial_state: TaxDeterminationState = {
                "item_description": line.item_description,
                "hsn": line.hsn,
                "supplier_name": line.supplier_name,
                "supplier_gstin": line.supplier_gstin,
                "supplier_country": line.supplier_country,
                "buyer_gstin": line.buyer_gstin,
                "buyer_country": line.buyer_country,
                "tax": line.tax,
                "erp_type": request.erp_type,
                "supplier_state_code": "",
                "buyer_state_code": "",
                "is_union_territory": False,
                "transaction_type": "",
                "total_tax_rate": 0.0,
                "is_rcm": False,
                "is_credit_eligible": True,
                "tax_code": "",
                "tax_description": "",
                "confidence": 0.0,
                "total_prompt_tokens": 0,
                "total_completion_tokens": 0,
                "total_reasoning_tokens": 0,
                "total_tokens": 0,
                "messages": [],
                "errors": []
            }
            
            try:
                # Execute graph
                final_state = await self.graph.ainvoke(initial_state)
                
                # Extract result
                result = TaxTaggingResult(
                    line_index=idx,
                    item_description=line.item_description,
                    tax_code=final_state['tax_code'],
                    tax_description=final_state['tax_description'],
                    confidence=final_state['confidence'],
                    total_prompt_tokens=final_state.get('total_prompt_tokens', 0),
                    total_completion_tokens=final_state.get('total_completion_tokens', 0),
                    total_reasoning_tokens=final_state.get('total_reasoning_tokens', 0),
                    total_tokens=final_state.get('total_tokens', 0),
                    messages=final_state.get('messages', []),
                    errors=final_state.get('errors', [])
                )
                
                results.append(result)
                total_confidence += final_state['confidence']
                
                # Aggregate tokens
                aggregate_prompt_tokens += result.total_prompt_tokens
                aggregate_completion_tokens += result.total_completion_tokens
                aggregate_reasoning_tokens += result.total_reasoning_tokens
                aggregate_total_tokens += result.total_tokens
                
                if final_state['tax_code'] == 'MANUAL_REVIEW_REQUIRED':
                    manual_review_count += 1
                
                if len(final_state.get('errors', [])) > 0:
                    error_count += 1
                
            except Exception as e:
                logger.error(f"[TAX_AGENT] Error processing line {idx}: {str(e)}", exc_info=True)
                
                # Create error result
                result = TaxTaggingResult(
                    line_index=idx,
                    item_description=line.item_description,
                    tax_code="ERROR",
                    tax_description=f"Processing error: {str(e)}",
                    confidence=0.0,
                    total_prompt_tokens=0,
                    total_completion_tokens=0,
                    total_reasoning_tokens=0,
                    total_tokens=0,
                    messages=[],
                    errors=[str(e)]
                )
                
                results.append(result)
                error_count += 1
        
        # Build summary
        avg_confidence = total_confidence / len(request.lines) if len(request.lines) > 0 else 0.0
        
        summary = {
            "total_lines": len(request.lines),
            "successful": len(request.lines) - manual_review_count - error_count,
            "manual_review": manual_review_count,
            "errors": error_count,
            "average_confidence": round(avg_confidence, 3),
            "total_prompt_tokens": aggregate_prompt_tokens,
            "total_completion_tokens": aggregate_completion_tokens,
            "total_reasoning_tokens": aggregate_reasoning_tokens,
            "total_tokens": aggregate_total_tokens,
        }
        
        logger.info(f"[TAX_AGENT] Completed. Summary: {summary}")
        
        return TaxTaggingResponse(
            results=results,
            summary=summary
        )


# Singleton instance
_tax_agent_instance = None


def get_tax_agent() -> TaxAgent:
    """Get singleton tax agent instance"""
    global _tax_agent_instance
    if _tax_agent_instance is None:
        _tax_agent_instance = TaxAgent()
    return _tax_agent_instance
