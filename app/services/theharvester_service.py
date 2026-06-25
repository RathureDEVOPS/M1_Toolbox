import ipaddress
from urllib.parse import urlparse

from app.config import get_settings
from app.core.audit import log_audit_event
from app.schemas.scan import ScanResponse
from app.services.scan_streaming import CommandStreamingService


class TheHarvesterService(CommandStreamingService):
    UNSUPPORTED_SOURCES = {"anubis"}
    FALLBACK_SOURCES = ("crtsh", "rapiddns", "urlscan")

    def __init__(self) -> None:
        self.settings = get_settings()
        self.module_id = "theharvester"
        self.module_name = "theHarvester"
        self.timeout_seconds = self.settings.theharvester_timeout

    def _normalize_target(self, raw_target: str) -> str:
        value = (raw_target or "").strip()
        if not value:
            raise ValueError("Veuillez saisir un domaine ou une URL.")

        candidate = value
        if value.startswith(("http://", "https://")):
            parsed = urlparse(value)
            if not parsed.hostname:
                raise ValueError("URL invalide.")
            candidate = parsed.hostname

        candidate = candidate.split("/", 1)[0].split(":", 1)[0].strip().strip(".").lower()
        if not candidate:
            raise ValueError("Veuillez saisir un domaine valide.")

        try:
            ipaddress.ip_address(candidate)
        except ValueError:
            pass
        else:
            raise ValueError("theHarvester requiert un nom de domaine et non une adresse IP.")

        if "." not in candidate:
            raise ValueError("theHarvester requiert un nom de domaine valide.")

        return candidate

    def _build_command(self, target: str, scripts: list[str], options: dict[str, object]) -> list[str]:
        configured_sources = [
            source.strip()
            for source in self.settings.theharvester_sources.split(",")
            if source.strip()
        ]
        filtered_sources = [
            source for source in configured_sources if source.lower() not in self.UNSUPPORTED_SOURCES
        ]

        if not filtered_sources:
            filtered_sources = list(self.FALLBACK_SOURCES)

        return [
            self.settings.theharvester_binary,
            "-d",
            target,
            "-b",
            ",".join(filtered_sources),
            "-l",
            str(self.settings.theharvester_limit),
        ]

    def _file_not_found_message(self) -> str:
        return "theHarvester n'est pas disponible dans l'environnement d'execution."

    def _timeout_message(self) -> str:
        return "Le scan theHarvester a depasse le temps limite autorise."

    def persist_scan(self, response: ScanResponse) -> ScanResponse:
        super().persist_scan(response)
        log_audit_event(
            "theharvester_scan_executed",
            scan_id=response.scan_id,
            module_id=response.module_id,
            target=response.target,
            exit_code=response.exit_code,
            duration_seconds=response.duration_seconds,
        )
        return response


theharvester_service = TheHarvesterService()
