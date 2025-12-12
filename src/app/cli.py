import asyncio
import sys
from src.app.bootstrap import MCPContainer
from src.common.logger import setup_logger

logger = setup_logger("cli")

async def _async_main():
    """
    The actual asynchronous logic for the Headless MCP server.
    """
    try:
        mcp = MCPContainer.get_server()
        await mcp.run_stdio_async()
        
    except Exception as e:
        sys.stderr.write(f"Critical Error in Stdio Mode: {e}\n")
        sys.exit(1)

def main():
    """
    Synchronous Entry Point.
    This is what 'mcp-cli' in pyproject.toml calls.
    """
    try:
        asyncio.run(_async_main())
    except KeyboardInterrupt:
        sys.stderr.write("\nStopped by user.\n")
        sys.exit(0)

if __name__ == "__main__":
    main()