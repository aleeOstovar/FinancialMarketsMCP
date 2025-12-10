from fastmcp import FastMCP
from src.common.settings import get_settings

settings = get_settings()

def create_mcp_server() -> FastMCP:
    """Factory function to create the MCP server instance."""
    return FastMCP(
        name=settings.APP_NAME,
        log_level=settings.LOG_LEVEL
    )