class MCPError(Exception):
    """Base class for all MCP Server errors."""
    pass

class ProviderConnectionError(MCPError):
    """Network/Connection issues with the upstream provider."""
    pass

class ProviderTimeoutError(ProviderConnectionError):
    """Upstream provider took too long to respond."""
    pass

class DataNotFound(MCPError):
    """The requested ticker or resource does not exist."""
    pass

class RateLimitExceeded(MCPError):
    """We have hit the API limit."""
    pass

class InvalidInputError(MCPError):
    """The user provided bad input (that the provider rejected)."""
    pass
