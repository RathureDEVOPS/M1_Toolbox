import json
import logging
from typing import Any


audit_logger = logging.getLogger("audit")


def log_audit_event(event: str, **payload: Any) -> None:
    audit_logger.info("%s", json.dumps({"event": event, **payload}, ensure_ascii=True))
