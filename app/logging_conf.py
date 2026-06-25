import logging
from logging.handlers import RotatingFileHandler

from app.config import Settings


def configure_logging(settings: Settings) -> None:
    settings.logs_dir.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    if not root_logger.handlers:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        )

    audit_logger = logging.getLogger("audit")
    audit_logger.setLevel(logging.INFO)

    already_configured = any(
        isinstance(handler, RotatingFileHandler) and getattr(handler, "baseFilename", "") == str(settings.audit_log_path)
        for handler in audit_logger.handlers
    )
    if already_configured:
        return

    file_handler = RotatingFileHandler(settings.audit_log_path, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    file_handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
    audit_logger.addHandler(file_handler)
