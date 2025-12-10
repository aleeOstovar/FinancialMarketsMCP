import logging
import re
import requests
from typing import Optional

logger = logging.getLogger(__name__)

def sanitize_message(message: str, api_key: Optional[str] = None) -> str:
    """
    Logic from your error_handler.py: Remove API key and regex patterns.
    """
    if api_key and api_key in message:
        message = message.replace(api_key, "[REDACTED]")
    
    # Your exact regex for API keys
    message = re.sub(r'\b[a-f0-9]{32,}\b', '[REDACTED]', message, flags=re.IGNORECASE)
    return message

def handle_api_error(error: Exception, api_key: Optional[str] = None) -> str:
    """
    Logic from your error_handler.py: Transform API errors into user-friendly messages.
    """
    error_message = str(error)
    sanitized_message = sanitize_message(error_message, api_key)
    
    # Log the full error (sanitized)
    logger.error(f"API error occurred: {sanitized_message}", exc_info=True)
    
    if isinstance(error, requests.exceptions.HTTPError):
        status_code = error.response.status_code if error.response else None
        
        # Your exact mapping
        if status_code == 401:
            return "Error: Invalid API credentials. Please check your COINMARKETCAP_API_KEY."
        elif status_code == 429:
            return "Error: Rate limit exceeded. Please wait before making more requests or upgrade your API plan."
        elif status_code == 400:
            return "Error: Invalid request. Please check your input parameters."
        elif status_code == 404:
            return "Error: Cryptocurrency symbol not found."
        elif status_code and 500 <= status_code < 600:
            return "Error: CoinMarketCap API is experiencing issues. Please try again later."
        else:
            return f"Error: API request failed with status code {status_code}."
    
    elif isinstance(error, requests.exceptions.ConnectionError):
        return "Error: Unable to connect to CoinMarketCap API. Please check your internet connection."
    
    elif isinstance(error, requests.exceptions.Timeout):
        return "Error: Request to CoinMarketCap API timed out. Please try again."
    
    elif isinstance(error, requests.exceptions.RequestException):
        return "Error: Failed to communicate with CoinMarketCap API."
    
    return "Error: An unexpected error occurred. Please try again."