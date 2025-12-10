# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from contextlib import asynccontextmanager

# # Local Imports
# from src.app.settings import get_app_settings
# from src.app.middleware.logging import request_logging_middleware
# from src.app.exceptions.handlers import register_exception_handlers
# from src.app.bootstrap import MCPContainer
# from src.app.routes import health

# settings = get_app_settings()

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     mcp = MCPContainer.get_server()
#     print(f"🚀 MCP Core '{mcp.name}' initialized.")
#     yield
#     print("🛑 Shutting down.")

# def create_fastapi_app() -> FastAPI:
#     app = FastAPI(
#         title="Financial Market MCP",
#         version="1.0.0",
#         lifespan=lifespan,
#         docs_url="/docs",
#         redoc_url="/redoc"
#     )

#     # 1. Middleware
#     app.add_middleware(
#         CORSMiddleware,
#         allow_origins=settings.CORS_ORIGINS,
#         allow_credentials=True,
#         allow_methods=["*"],
#         allow_headers=["*"],
#     )
#     app.middleware("http")(request_logging_middleware)

#     # 2. Exception Handlers
#     register_exception_handlers(app)

#     # 3. Standard Routes
#     app.include_router(health.router, prefix="/api/v1")
    
#     # 4. MCP Integration
#     mcp_core = MCPContainer.get_server()
    
#     # We call .sse_app() to get the ASGI app that handles /sse and /messages
#     try:
#         mcp_asgi_app = mcp_core.sse_app()
        
#         # Mount it at /mcp
#         # Resulting Routes:
#         # - GET  /mcp/sse      (Protected by auth injected in bootstrap)
#         # - POST /mcp/messages (Protected by auth injected in bootstrap)
#         app.mount("/mcp", mcp_asgi_app)
#         print("✅ Mounted MCP SSE Transport at /mcp")
        
#     except Exception as e:
#         print(f"❌ Failed to mount MCP app: {e}")

#     return app

# app = create_fastapi_app()

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(
#         "src.app.main:app", 
#         host=settings.HOST, 
#         port=settings.PORT, 
#         reload=settings.DEBUG
#     )

import secrets
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Local Imports
from src.app.settings import get_app_settings
from src.app.exceptions.handlers import register_exception_handlers
from src.app.bootstrap import MCPContainer
from src.app.routes import health
from src.app.middleware.logging import RequestLoggingMiddleware 

settings = get_app_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    mcp = MCPContainer.get_server()
    print(f"🚀 MCP Core '{mcp.name}' initialized.")
    yield
    print("🛑 Shutting down.")

class SecureMCPWrapper:
    """
    Wraps an ASGI app (the MCP server) to enforce API Key authentication.
    """
    def __init__(self, app, api_key: str | None):
        self.app = app
        self.api_key = api_key

    async def __call__(self, scope, receive, send):
        # Only check HTTP requests (allow lifespan/other protocols if needed)
        if scope["type"] == "http" and self.api_key:
            # Extract headers manually from ASGI scope
            headers = dict(scope.get("headers", []))
            # Headers are bytes in ASGI
            client_key = headers.get(b"x-api-key", b"").decode("utf-8")
            
            if not secrets.compare_digest(client_key, self.api_key):
                # Return 403 Forbidden manually
                response = Response(content="Invalid API Key", status_code=403)
                await response(scope, receive, send)
                return

        # Pass through to the MCP app
        await self.app(scope, receive, send)

def create_fastapi_app() -> FastAPI:
    app = FastAPI(
        title="Financial Market MCP",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc"
    )

    # 1. Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestLoggingMiddleware)

    # 2. Exception Handlers
    register_exception_handlers(app)

    # 3. Standard Routes
    app.include_router(health.router, prefix="/api/v1")
    
    # 4. MCP Integration (Secured)
    mcp_core = MCPContainer.get_server()
    
    try:
        # Get the raw ASGI app from FastMCP
        mcp_asgi_app = mcp_core.sse_app()
        # Wrap it with our Security Layer
        secured_mcp_app = SecureMCPWrapper(mcp_asgi_app, settings.MCP_SERVER_API_KEY)
        
        # Mount the secured app
        app.mount("/mcp", secured_mcp_app)
        print("✅ Mounted Secured MCP SSE Transport at /mcp")
        
    except Exception as e:
        print(f"❌ Failed to mount MCP app: {e}")

    return app

app = create_fastapi_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.app.main:app", 
        host=settings.HOST, 
        port=settings.PORT, 
        reload=settings.DEBUG
    )