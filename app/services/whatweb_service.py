from urllib.parse import urlparse

from app.config import get_settings
from app.core.audit import log_audit_event
from app.core.security import normalize_target
from app.schemas.scan import ScanResponse
from app.services.scan_streaming import CommandStreamingService


class WhatWebService(CommandStreamingService):
    def __init__(self) -> None:
        self.settings = get_settings()
        self.module_id = "whatweb"
        self.module_name = "WhatWeb"
        self.timeout_seconds = self.settings.whatweb_timeout

    def _normalize_target(self, raw_target: str) -> str:
        value = (raw_target or "").strip()
        if not value:
            raise ValueError("Veuillez saisir une IP, un domaine ou une URL.")
        if value.startswith(("http://", "https://")):
            parsed = urlparse(value)
            if not parsed.hostname:
                raise ValueError("URL invalide.")
            return value
        return normalize_target(value)

    def _build_command(self, target: str, scripts: list[str], options: dict[str, object]) -> list[str]:
        return [
            self.settings.whatweb_binary,
            target,
        ]

    def _file_not_found_message(self) -> str:
        return "WhatWeb n'est pas disponible dans l'environnement d'execution."

    def _timeout_message(self) -> str:
        return "Le scan WhatWeb a depasse le temps limite autorise."

    def persist_scan(self, response: ScanResponse) -> ScanResponse:
        super().persist_scan(response)
        log_audit_event(
            "whatweb_scan_executed",
            scan_id=response.scan_id,
            module_id=response.module_id,
            target=response.target,
            exit_code=response.exit_code,
            duration_seconds=response.duration_seconds,
        )
        return response


whatweb_service = WhatWebService()
