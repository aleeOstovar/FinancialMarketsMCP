import asyncio
import sys
import os

# Ensure we can find the src module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from src.app.bootstrap import MCPContainer
from src.common.logger import setup_logger

# We use a separate logger for CLI to avoid polluting stdout (which breaks MCP)
logger = setup_logger("cli")

async def main():
    """
    Entry point for Claude Desktop (Stdio Mode).
    """
    try:
        # 1. Get the exact same server instance used by FastAPI
        mcp = MCPContainer.get_server()
        
        # 2. Run in Stdio mode
        # This allows Claude to talk to the server directly via pipe
        await mcp.run_stdio_async()
        
    except Exception as e:
        # Log to stderr so we don't break the JSON protocol on stdout
        sys.stderr.write(f"Critical Error: {e}\n")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())