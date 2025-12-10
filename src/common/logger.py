# import logging
# import sys
# from src.common.settings import get_settings

# settings = get_settings()

# def setup_logger(name: str):
#     logger = logging.getLogger(name)
#     logger.setLevel(settings.LOG_LEVEL)
    
#     if not logger.handlers:
#         handler = logging.StreamHandler(sys.stdout)
#         formatter = logging.Formatter(
#             '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
#         )
#         handler.setFormatter(formatter)
#         logger.addHandler(handler)
        
#     return logger
import logging
import sys
from src.common.settings import get_settings

settings = get_settings()

def setup_logger(name: str):
    logger = logging.getLogger(name)
    logger.setLevel(settings.LOG_LEVEL)
    
    # Prevent adding multiple handlers if function is called twice
    if not logger.handlers:
        # --- FIX: Use stderr instead of stdout ---
        # stdout is reserved for MCP protocol messages
        handler = logging.StreamHandler(sys.stderr) 
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
    return logger