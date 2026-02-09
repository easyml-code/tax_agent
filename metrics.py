"""
Prometheus metrics for tax agent monitoring
"""

from prometheus_client import Counter, Histogram, Gauge
from functools import wraps
import time
from typing import Callable
from logs.log import logger


# Request-level metrics
tax_agent_requests_total = Counter(
    'tax_agent_requests_total',
    'Total number of tax determination requests',
    ['erp_type', 'status']  # status: success, error, manual_review
)

tax_agent_processing_time_seconds = Histogram(
    'tax_agent_processing_time_seconds',
    'Time spent processing tax determination',
    ['erp_type', 'node'],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0)
)

tax_agent_active_requests = Gauge(
    'tax_agent_active_requests',
    'Number of currently active requests',
    ['erp_type']
)

# LLM-specific metrics
tax_agent_llm_calls_total = Counter(
    'tax_agent_llm_calls_total',
    'Total number of LLM API calls',
    ['agent_node', 'erp_type', 'status']  # status: success, error
)

tax_agent_llm_tokens_total = Counter(
    'tax_agent_llm_tokens_total',
    'Total LLM tokens consumed',
    ['erp_type', 'token_type']  # token_type: prompt, completion, reasoning
)

tax_agent_llm_latency_seconds = Histogram(
    'tax_agent_llm_latency_seconds',
    'LLM call latency in seconds',
    ['agent_node', 'erp_type'],
    buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 30.0)
)

# Result quality metrics
tax_agent_confidence_score = Histogram(
    'tax_agent_confidence_score',
    'Confidence score of tax code determination',
    ['erp_type'],
    buckets=(0.0, 0.2, 0.4, 0.6, 0.8, 0.9, 0.95, 1.0)
)

tax_agent_manual_review_total = Counter(
    'tax_agent_manual_review_total',
    'Total number of requests requiring manual review',
    ['erp_type', 'reason']
)

# Error tracking
tax_agent_errors_total = Counter(
    'tax_agent_errors_total',
    'Total number of errors',
    ['erp_type', 'error_type']
)

# Tool-specific metrics
tax_agent_tool_calls_total = Counter(
    'tax_agent_tool_calls_total',
    'Total number of tool function calls',
    ['tool_name', 'status']  # status: success, failure
)

tax_agent_tool_latency_seconds = Histogram(
    'tax_agent_tool_latency_seconds',
    'Tool function latency in seconds',
    ['tool_name'],
    buckets=(0.001, 0.01, 0.05, 0.1, 0.5, 1.0)
)


def track_request_metrics(erp_type: str = "SAP_ECC"):
    """
    Decorator to track overall request metrics
    
    Args:
        erp_type: ERP system type
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            tax_agent_active_requests.labels(erp_type=erp_type).inc()
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                
                # Track success/manual review based on results
                manual_review_count = sum(
                    1 for r in result.results 
                    if r.tax_code == 'MANUAL_REVIEW_REQUIRED'
                )
                error_count = sum(
                    1 for r in result.results 
                    if r.tax_code == 'ERROR' or len(r.errors) > 0
                )
                
                if manual_review_count > 0:
                    tax_agent_requests_total.labels(
                        erp_type=erp_type,
                        status='manual_review'
                    ).inc(manual_review_count)
                
                if error_count > 0:
                    tax_agent_requests_total.labels(
                        erp_type=erp_type,
                        status='error'
                    ).inc(error_count)
                
                success_count = len(result.results) - manual_review_count - error_count
                if success_count > 0:
                    tax_agent_requests_total.labels(
                        erp_type=erp_type,
                        status='success'
                    ).inc(success_count)
                
                # Track confidence scores
                for r in result.results:
                    if r.confidence > 0:
                        tax_agent_confidence_score.labels(
                            erp_type=erp_type
                        ).observe(r.confidence)
                
                return result
                
            except Exception as e:
                tax_agent_requests_total.labels(
                    erp_type=erp_type,
                    status='error'
                ).inc()
                tax_agent_errors_total.labels(
                    erp_type=erp_type,
                    error_type=type(e).__name__
                ).inc()
                logger.error(f"Request failed: {str(e)}", exc_info=True)
                raise
                
            finally:
                duration = time.time() - start_time
                tax_agent_processing_time_seconds.labels(
                    erp_type=erp_type,
                    node='total'
                ).observe(duration)
                tax_agent_active_requests.labels(erp_type=erp_type).dec()
        
        return wrapper
    return decorator


def track_node_metrics(node_name: str, erp_type: str = "SAP_ECC"):
    """
    Decorator to track node-level metrics
    
    Args:
        node_name: Name of the node
        erp_type: ERP system type
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                return result
                
            finally:
                duration = time.time() - start_time
                tax_agent_processing_time_seconds.labels(
                    erp_type=erp_type,
                    node=node_name
                ).observe(duration)
        
        return wrapper
    return decorator


def track_llm_call(agent_node: str, erp_type: str = "SAP_ECC"):
    """
    Decorator to track LLM calls
    
    Args:
        agent_node: Node making the LLM call
        erp_type: ERP system type
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                
                # Track success
                tax_agent_llm_calls_total.labels(
                    agent_node=agent_node,
                    erp_type=erp_type,
                    status='success'
                ).inc()
                
                # Track latency
                duration = time.time() - start_time
                tax_agent_llm_latency_seconds.labels(
                    agent_node=agent_node,
                    erp_type=erp_type
                ).observe(duration)
                
                return result
                
            except Exception as e:
                # Track failure
                tax_agent_llm_calls_total.labels(
                    agent_node=agent_node,
                    erp_type=erp_type,
                    status='error'
                ).inc()
                
                duration = time.time() - start_time
                tax_agent_llm_latency_seconds.labels(
                    agent_node=agent_node,
                    erp_type=erp_type
                ).observe(duration)
                
                raise
        
        return wrapper
    return decorator


def track_llm_tokens(erp_type: str, prompt_tokens: int, completion_tokens: int, reasoning_tokens: int = 0):
    """
    Track LLM token usage
    
    Args:
        erp_type: ERP system type
        prompt_tokens: Number of prompt tokens
        completion_tokens: Number of completion tokens
        reasoning_tokens: Number of reasoning tokens
    """
    if prompt_tokens > 0:
        tax_agent_llm_tokens_total.labels(
            erp_type=erp_type,
            token_type='prompt'
        ).inc(prompt_tokens)
    
    if completion_tokens > 0:
        tax_agent_llm_tokens_total.labels(
            erp_type=erp_type,
            token_type='completion'
        ).inc(completion_tokens)
    
    if reasoning_tokens > 0:
        tax_agent_llm_tokens_total.labels(
            erp_type=erp_type,
            token_type='reasoning'
        ).inc(reasoning_tokens)


def track_tool_call(tool_name: str):
    """
    Decorator to track tool function calls
    
    Args:
        tool_name: Name of the tool function
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                return result
                
            finally:
                duration = time.time() - start_time
                tax_agent_tool_latency_seconds.labels(
                    tool_name=tool_name
                ).observe(duration)
        
        return wrapper
    return decorator


def track_tool_success(tool_name: str):
    """
    Track successful tool execution
    
    Args:
        tool_name: Name of the tool function
    """
    tax_agent_tool_calls_total.labels(
        tool_name=tool_name,
        status='success'
    ).inc()


def track_tool_failure(tool_name: str, error_type: str):
    """
    Track failed tool execution
    
    Args:
        tool_name: Name of the tool function
        error_type: Type of error
    """
    tax_agent_tool_calls_total.labels(
        tool_name=tool_name,
        status='failure'
    ).inc()
    
    logger.warning(f"Tool {tool_name} failed with error type: {error_type}")
