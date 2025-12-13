import logging
import re
import requests
from typing import Optional
from src.common.logger import setup_logger

logger = setup_logger(__name__)

def sanitize_message(message: str, api_key: Optional[str] = None) -> str:
    if api_key and api_key in message:
        message = message.replace(api_key, "[REDACTED]")
    message = re.sub(r'\b[a-f0-9]{32,}\b', '[REDACTED]', message, flags=re.IGNORECASE)
    return message

def handle_api_error(error: Exception, api_key: Optional[str] = None) -> str:
    error_message = str(error)
    sanitized_message = sanitize_message(error_message, api_key)
    
    # Log structured error
    # We don't have tool_name here easily unless passed, but we log the raw error
    logger.error(
        f"External API Error: {sanitized_message}", 
        extra={"error_type": type(error).__name__},
        exc_info=True
    )
    
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
    
    return "Error: An unexpected error occurred."