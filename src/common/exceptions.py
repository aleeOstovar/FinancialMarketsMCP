import logging
import re
import requests
from typing import Optional
from src.common.logger import setup_logger
# exception handler for massive forex 
from src.common.custom_exceptions import (
    MCPError, 
    DataNotFound, 
    RateLimitExceeded, 
    ProviderConnectionError, 
    ProviderTimeoutError,
    InvalidInputError
)

logger = setup_logger(__name__)

def sanitize_message(message: str, api_key: Optional[str] = None) -> str:
    """
    Redacts API keys from error messages to prevent leaking secrets in logs/LLM context.
    """
    if api_key and api_key in message:
        message = message.replace(api_key, "[REDACTED]")
    message = re.sub(r'\b[a-f0-9]{32,}\b', '[REDACTED]', message, flags=re.IGNORECASE)
    return message

def handle_api_error(error: Exception, api_key: Optional[str] = None) -> str:
    """ Global Exception Translator """
    error_message = str(error)
    sanitized_message = sanitize_message(error_message, api_key)
    
    # Log structured error
    logger.error(
        f"External API Error: {sanitized_message}", 
        extra={"error_type": type(error).__name__},
        exc_info=True
    )

    # HANDLE CUSTOM MCP ERRORS
    
    if isinstance(error, DataNotFound):
        return f"Error: {str(error)}"
        
    if isinstance(error, RateLimitExceeded):
        return "Error: API rate limit exceeded. Please wait a moment before trying again."
        
    if isinstance(error, InvalidInputError):
        return f"Error: Invalid Input - {str(error)}"
        
    if isinstance(error, ProviderTimeoutError):
        return "Error: The data provider timed out. Please try again."

    if isinstance(error, ProviderConnectionError):
        return "Error: Failed to connect to the external data provider."

    if isinstance(error, MCPError):
        return f"Error: {str(error)}"

    # LEGACY 'REQUESTS' ERRORS-->crypto api  
    
    if isinstance(error, requests.exceptions.HTTPError):
        status_code = error.response.status_code if error.response else None
        if status_code == 401:
            return "Error: Invalid API credentials."
        elif status_code == 429:
            return "Error: Rate limit exceeded."
        elif status_code == 400:
            return "Error: Invalid request parameters."
        elif status_code == 404:
            return "Error: Resource not found."
        elif status_code and 500 <= status_code < 600:
            return "Error: External API internal error."
        else:
            return f"Error: API request failed with status code {status_code}."
    
    elif isinstance(error, requests.exceptions.ConnectionError):
        return "Error: Unable to connect to API."
    
    elif isinstance(error, requests.exceptions.Timeout):
        return "Error: Request timed out."
    
    return "Error: An unexpected error occurred. Please try again."