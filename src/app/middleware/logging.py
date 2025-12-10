import time
import logging
from starlette.types import ASGIApp, Scope, Receive, Send

# Use our centralized logger configuration
from src.common.logger import setup_logger

logger = setup_logger("http_middleware")

class RequestLoggingMiddleware:
    """
    Pure ASGI Middleware for logging.
    Compatible with SSE/WebSockets where BaseHTTPMiddleware fails.
    """
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        # 1. Only log HTTP requests (skip lifespan/websocket if needed)
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = time.time()
        
        # 2. Capture Status Code
        # We use a mutable list to capture the status code from the inner application
        status_code = [500] # Default to 500 if something crashes hard

        async def wrapped_send(message):
            if message["type"] == "http.response.start":
                status_code[0] = message["status"]
            await send(message)

        # 3. Process Request
        try:
            await self.app(scope, receive, wrapped_send)
        except Exception as e:
            # Log the error but re-raise it so the ExceptionHandler catches it
            logger.error(f"Middleware caught error: {e}")
            raise e
        finally:
            # 4. Log after response is sent (or connection closed)
            process_time = (time.time() - start_time) * 1000
            
            # Extract basic info
            method = scope.get("method", "UNKNOWN")
            path = scope.get("path", "UNKNOWN")
            client = scope.get("client", ["unknown"])
            ip = client[0] if client else "unknown"

            logger.info(
                f"Method={method} Path={path} IP={ip} "
                f"Status={status_code[0]} Duration={process_time:.2f}ms"
            )