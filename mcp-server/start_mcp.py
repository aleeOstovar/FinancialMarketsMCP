import sys
import os

# --- FIX: Look in the Parent Directory ---
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Use stderr for debug prints so we don't break the MCP protocol
sys.stderr.write(f"🔍 Debug: Running from: {current_dir}\n")

try:
    from src.mcp import create_app
    from src.common.logger import setup_logger
except ImportError as e:
    sys.stderr.write(f"❌ Import Failed: {e}\n")
    sys.exit(1)

logger = setup_logger("main")

if __name__ == "__main__":
    # Log to stderr (handled by logger config)
    logger.info("Initializing MCP Server...")
    try:
        mcp = create_app()
        # The .run() method takes over stdout for the protocol
        mcp.run() 
    except Exception as e:
        logger.critical(f"Server failed to start: {e}", exc_info=True)