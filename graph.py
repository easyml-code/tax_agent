"""
LangGraph workflow definition for tax code determination
"""

from langgraph.graph import StateGraph, END
from logs.log import logger

from .state import TaxDeterminationState
from .nodes import (
    preprocessing_node,
    tax_determination_node,
    validation_node,
)


def create_tax_determination_graph():
    """
    Create the LangGraph workflow for tax code determination
    
    Workflow:
    1. Preprocessing: Extract state codes, determine transaction type
    2. Tax Determination: Lookup or LLM-based determination
    3. Validation: Validate and apply business rules
    
    Returns:
        Compiled LangGraph
    """
    logger.info("[GRAPH] Building tax determination workflow")
    
    # Create graph
    workflow = StateGraph(TaxDeterminationState)
    
    # Add nodes
    workflow.add_node("preprocessing", preprocessing_node)
    workflow.add_node("tax_determination", tax_determination_node)
    workflow.add_node("validation", validation_node)
    
    # Define edges
    workflow.set_entry_point("preprocessing")
    workflow.add_edge("preprocessing", "tax_determination")
    workflow.add_edge("tax_determination", "validation")
    workflow.add_edge("validation", END)
    
    # Compile graph
    graph = workflow.compile()
    
    logger.info("[GRAPH] Workflow compiled successfully")
    
    return graph
