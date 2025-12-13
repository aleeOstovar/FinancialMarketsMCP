from src.common.logger import setup_logger
from src.common.settings import PROJECT_ROOT

print(f"📂 Project Root detected as: {PROJECT_ROOT}")
print(f"📝 Logs will be written to: {PROJECT_ROOT / 'logs'}")

logger = setup_logger("debug_test")

print("--- Sending Log Message ---")
logger.info("This is a test log message", extra={"status": "success", "duration_ms": 100})
print("--- Check your terminal output above and the logs/ folder ---")