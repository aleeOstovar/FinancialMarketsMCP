from fastapi import Request, FastAPI
from fastapi.responses import JSONResponse
from src.common.logger import setup_logger

logger = setup_logger("exception_handler")

def register_exception_handlers(app: FastAPI):
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled error: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error", "error": str(exc)}
        )