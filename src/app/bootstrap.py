from src.mcp import create_app as create_mcp_core
from fastmcp import FastMCP

class MCPContainer:
    _instance: FastMCP | None = None

    @classmethod
    def get_server(cls) -> FastMCP:
        if cls._instance is None:
            # Initialize the Core MCP Logic
            cls._instance = create_mcp_core()
            
        return cls._instance