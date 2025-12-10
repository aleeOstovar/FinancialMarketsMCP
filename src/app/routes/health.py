from fastapi import APIRouter
from src.common.settings import get_settings as get_common_settings

router = APIRouter()
common_settings = get_common_settings()

@router.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "online",
        "app": common_settings.APP_NAME,
        "version": "1.0.0"
    }