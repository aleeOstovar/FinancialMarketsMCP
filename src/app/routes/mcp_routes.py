from fastapi import APIRouter, Request, Depends
from starlette.responses import JSONResponse, Response
from src.app.bootstrap import MCPContainer
from src.app.middleware.auth import validate_api_key

# We use a router to group these endpoints
router = APIRouter(dependencies=[Depends(validate_api_key)])

# Get the initialized MCP Core
mcp_server = MCPContainer.get_server()

@router.get("/sse")
async def handle_sse(request: Request):
    """
    Connect to the MCP Server via SSE.
    This endpoint is protected by the API Key.
    """
    # FastMCP exposes the underlying Starlette app handling SSE
    # We delegate the request to the MCP core
    # Note: We are calling the internal SSE handler of FastMCP
    return await mcp_server._sse_handler(request)

@router.post("/messages")
async def handle_messages(request: Request):
    """
    Send JSON-RPC messages to the MCP Server.
    Protected by API Key.
    """
    return await mcp_server._messages_handler(request)