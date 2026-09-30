import logging
from pathlib import Path
from app.services.notifications import notification_service

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "app.log"),
        logging.StreamHandler()
    ],
)

logger = logging.getLogger("cropcapture")


def log_error(message: str, critical: bool = False):
    if critical:
        logger.critical(message)

        notification_service.send_critical_alert(
            subject="HarvestDB Critical Error",
            message=message,
        )
    else:
        logger.error(message)