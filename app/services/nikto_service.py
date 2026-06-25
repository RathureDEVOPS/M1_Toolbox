from urllib.parse import urlparse

from app.config import get_settings
from app.core.audit import log_audit_event
from app.core.security import normalize_target
from app.schemas.scan import ScanResponse
from app.services.scan_streaming import CommandStreamingService


class NiktoService(CommandStreamingService):
    def __init__(self) -> None:
        self.settings = get_settings()
        self.module_id = "nikto"
        self.module_name = "Nikto"
        self.timeout_seconds = self.settings.nikto_timeout

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
            self.settings.nikto_binary,
            "-ask",
            "no",
            "-nointeractive",
            "-host",
            target,
        ]

    def _file_not_found_message(self) -> str:
        return "Nikto n'est pas disponible dans l'environnement d'execution."

    def _timeout_message(self) -> str:
        return "Le scan Nikto a depasse le temps limite autorise."

    def persist_scan(self, response: ScanResponse) -> ScanResponse:
        super().persist_scan(response)
        log_audit_event(
            "nikto_scan_executed",
            scan_id=response.scan_id,
            module_id=response.module_id,
            target=response.target,
            exit_code=response.exit_code,
            duration_seconds=response.duration_seconds,
        )
        return response


nikto_service = NiktoService()
