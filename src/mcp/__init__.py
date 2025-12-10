from .protocol import create_mcp_server
from .router import register_tools

def create_app():
    """
    Factory function to initialize the MCP server.
    1. Creates the FastMCP instance (Protocol)
    2. Registers all tools (Router)
    3. Returns the runnable server
    """
    server = create_mcp_server()
    register_tools(server)
    return server