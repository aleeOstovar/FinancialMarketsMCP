import functools
import time
from src.common.logger import setup_logger

logger = setup_logger("mcp.tracer")

def monitor_tool(func):
    """
    Decorator to log tool execution time, inputs, and success/failure status.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        tool_name = func.__name__
        start_time = time.time()
        
        # Log Start
        safe_inputs = {k: str(v) for k, v in kwargs.items()}
        logger.info(
            f"Tool Execution Started: {tool_name}", 
            extra={"tool_name": tool_name, "event": "start", "inputs": safe_inputs}
        )
        
        try:
            result = func(*args, **kwargs)
            
            duration = (time.time() - start_time) * 1000
            
            is_error = isinstance(result, str) and result.strip().startswith("Error:")
            status = "failure" if is_error else "success"
            
            logger.info(
                f"Tool Execution Finished: {tool_name}", 
                extra={
                    "tool_name": tool_name, 
                    "event": "finish", 
                    "duration_ms": round(duration, 2),
                    "status": status
                }
            )
            return result
            
        except Exception as e:
            # This catches crashes NOT handled by the tool's internal try/except
            duration = (time.time() - start_time) * 1000
            logger.error(
                f"Tool Crashed: {tool_name}", 
                extra={
                    "tool_name": tool_name, 
                    "event": "crash", 
                    "duration_ms": round(duration, 2),
                    "status": "crash",
                    "error": str(e)
                },
                exc_info=True
            )
            raise e
            
    return wrapper