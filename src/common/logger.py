import logging
import sys
import json
import datetime
import os
from logging.handlers import TimedRotatingFileHandler 
from src.common.settings import get_settings, ENV_PATH

settings = get_settings()

log_dir_path = ENV_PATH.parent / settings.LOG_DIR
os.makedirs(log_dir_path, exist_ok=True)
log_file_path = log_dir_path / settings.LOG_FILENAME

class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": datetime.datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Include structured extra fields
        for key in ["tool_name", "duration_ms", "status", "inputs", "error_type"]:
            if hasattr(record, key):
                log_record[key] = getattr(record, key)

        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_record)

class HumanReadableFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        ts = datetime.datetime.fromtimestamp(record.created).strftime('%H:%M:%S')
        msg = f"[{ts}] [{record.levelname}] {record.getMessage()}"
        
        if hasattr(record, "status"):
            status_icon = "✅" if record.status == "success" else "❌"
            duration = getattr(record, "duration_ms", 0)
            msg += f" ({status_icon} {record.status.upper()} | {duration}ms)"
        return msg

def setup_logger(name: str):
    logger = logging.getLogger(name)
    logger.setLevel(settings.LOG_LEVEL)
    
    if not logger.handlers:
        logger.propagate = False

        # FILE HANDLER
        # Rotates every midnight.
        # Keeps last 7 days (backupCount=7).
        file_handler = TimedRotatingFileHandler(
            log_file_path,
            when="midnight",
            interval=1,
            backupCount=7, 
            encoding='utf-8'
        )
        file_handler.suffix = "%Y-%m-%d"
        file_handler.setFormatter(JSONFormatter())
        file_handler.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)

        # CONSOLE HANDLER ---
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setFormatter(HumanReadableFormatter())
        console_handler.setLevel(settings.LOG_LEVEL)
        logger.addHandler(console_handler)
        
    return logger