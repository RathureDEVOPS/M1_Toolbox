from urllib.parse import urlparse

from app.config import get_settings
from app.core.audit import log_audit_event
from app.core.security import normalize_target
from app.schemas.scan import ScanResponse
from app.services.scan_streaming import CommandStreamingService


class WiresharkService(CommandStreamingService):
    def __init__(self) -> None:
        self.settings = get_settings()
        self.module_id = "wireshark"
        self.module_name = "Wireshark"
        self.timeout_seconds = self.settings.wireshark_timeout

    def _normalize_target(self, raw_target: str) -> str:
        value = (raw_target or "").strip()
        if not value:
            raise ValueError("Veuillez saisir une IP, un domaine ou une URL pour le filtre Wireshark.")
        if value.startswith(("http://", "https://")):
            parsed = urlparse(value)
            if not parsed.hostname:
                raise ValueError("URL invalide pour Wireshark.")
            return parsed.hostname
        return normalize_target(value)

    def _normalize_options(self, options: dict[str, object] | None) -> dict[str, object]:
        data = dict(options or {})
        interface = str(data.get("interface", self.settings.wireshark_default_interface)).strip()
        duration_raw = str(data.get("duration", "10")).strip() or "10"

        if not interface:
            raise ValueError("Veuillez renseigner une interface reseau pour Wireshark.")

        if not duration_raw.isdigit():
            raise ValueError("La duree Wireshark doit etre numerique.")

        duration = int(duration_raw)
        if duration < 1 or duration > 300:
            raise ValueError("La duree Wireshark doit etre comprise entre 1 et 300 secondes.")

        return {
            "interface": interface,
            "duration": duration,
        }

    def _build_command(self, target: str, scripts: list[str], options: dict[str, object]) -> list[str]:
        return [
            self.settings.wireshark_binary,
            "-n",
            "-i",
            str(options["interface"]),
            "-a",
            f'duration:{options["duration"]}',
            "-f",
            f"host {target}",
            "-q",
            "-z",
            "io,stat,1",
            "-z",
            "io,phs",
            "-z",
            "endpoints,ip",
        ]

    def _file_not_found_message(self) -> str:
        return "tshark n'est pas disponible dans l'environnement d'execution."

    def _timeout_message(self) -> str:
        return "La capture Wireshark a depasse le temps limite autorise."

    def _get_timeout_seconds(self, options: dict[str, object]) -> int:
        duration = int(options.get("duration", 10))
        return max(self.timeout_seconds, duration + 10)

    def persist_scan(self, response: ScanResponse) -> ScanResponse:
        super().persist_scan(response)
        log_audit_event(
            "wireshark_capture_executed",
            scan_id=response.scan_id,
            module_id=response.module_id,
            target=response.target,
            exit_code=response.exit_code,
            duration_seconds=response.duration_seconds,
        )
        return response


wireshark_service = WiresharkService()
