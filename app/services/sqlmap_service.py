from urllib.parse import urlparse

from app.config import get_settings
from app.core.audit import log_audit_event
from app.schemas.scan import ScanResponse
from app.services.scan_streaming import CommandStreamingService


class SQLmapService(CommandStreamingService):
    def __init__(self) -> None:
        self.settings = get_settings()
        self.module_id = "sqlmap"
        self.module_name = "SQLmap"
        self.timeout_seconds = self.settings.sqlmap_timeout

    def _normalize_target(self, raw_target: str) -> str:
        value = (raw_target or "").strip()
        if not value:
            raise ValueError("Veuillez saisir une URL complete pour SQLmap.")
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("SQLmap requiert une URL complete de type http(s)://...")
        return value

    def _build_command(self, target: str, scripts: list[str], options: dict[str, object]) -> list[str]:
        return [
            self.settings.sqlmap_binary,
            "-u",
            target,
            "--batch",
            "--smart",
            "--random-agent",
            "--level",
            "1",
            "--risk",
            "1",
            "--threads",
            "2",
        ]

    def _file_not_found_message(self) -> str:
        return "SQLmap n'est pas disponible dans l'environnement d'execution."

    def _timeout_message(self) -> str:
        return "Le scan SQLmap a depasse le temps limite autorise."

    def persist_scan(self, response: ScanResponse) -> ScanResponse:
        super().persist_scan(response)
        log_audit_event(
            "sqlmap_scan_executed",
            scan_id=response.scan_id,
            module_id=response.module_id,
            target=response.target,
            exit_code=response.exit_code,
            duration_seconds=response.duration_seconds,
        )
        return response


sqlmap_service = SQLmapService()
