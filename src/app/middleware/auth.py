import secrets
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from src.app.settings import get_app_settings

settings = get_app_settings()
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def validate_api_key(api_key: str = Security(api_key_header)):
    """
    Validates the X-API-Key header.
    """
    # 1. Dev Mode: If no key is configured, allow everything
    if not settings.MCP_SERVER_API_KEY:
        return True

    # 2. Check for missing header
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API Key header (X-API-Key)"
        )

    # 3. Constant-time comparison to prevent timing attacks
    is_valid = secrets.compare_digest(
        api_key.encode("utf8"), 
        settings.MCP_SERVER_API_KEY.encode("utf8")
    )

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key"
        )

    return api_key