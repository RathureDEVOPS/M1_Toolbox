from urllib.parse import urlparse, urlunparse
from uuid import uuid4

from app.config import get_settings
from app.core.audit import log_audit_event
from app.core.security import normalize_target
from app.schemas.scan import ScanResponse
from app.services.command_execution_service import command_execution_service
from app.services.scan_streaming import CommandStreamingService


class GobusterService(CommandStreamingService):
    def __init__(self) -> None:
        self.settings = get_settings()
        self.module_id = "gobuster"
        self.module_name = "Gobuster"
        self.timeout_seconds = self.settings.gobuster_timeout

    def _normalize_target(self, raw_target: str) -> str:
        value = (raw_target or "").strip()
        if not value:
            raise ValueError("Veuillez saisir une IP, un domaine ou une URL.")
        if value.startswith(("http://", "https://")):
            parsed = urlparse(value)
            if not parsed.hostname:
                raise ValueError("URL invalide.")
            return value
        return f"http://{normalize_target(value)}"

    def _build_command(self, target: str, scripts: list[str], options: dict[str, object]) -> list[str]:
        if not self.settings.gobuster_wordlist:
            raise ValueError("La wordlist Gobuster n'est pas configuree.")

        command = [
            self.settings.gobuster_binary,
            "dir",
            "-u",
            target,
            "-w",
            self.settings.gobuster_wordlist,
            "-t",
            str(self.settings.gobuster_threads),
            "--no-error",
            "--no-progress",
        ]

        if self.settings.gobuster_extensions:
            command.extend(["-x", self.settings.gobuster_extensions])

        if self.settings.gobuster_delay:
            command.extend(["--delay", self.settings.gobuster_delay])

        if self.settings.gobuster_request_timeout:
            command.extend(["--timeout", self.settings.gobuster_request_timeout])

        exclude_length = self._detect_wildcard_response_length(target)
        if exclude_length is not None:
            command.extend(["--exclude-length", str(exclude_length)])

        return command

    def _detect_wildcard_response_length(self, target: str) -> int | None:
        parsed = urlparse(target)
        random_path = f"{parsed.path.rstrip('/')}/{uuid4()}" if parsed.path else f"/{uuid4()}"
        probe_url = urlunparse(
            (
                parsed.scheme,
                parsed.netloc,
                random_path,
                "",
                "",
                "",
            )
        )

        try:
            result = command_execution_service.run_command(
                [
                    "curl",
                    "-ksS",
                    "-o",
                    "/dev/null",
                    "-w",
                    "%{http_code}:%{size_download}",
                    probe_url,
                ],
                timeout_seconds=min(self.timeout_seconds, 15),
                file_not_found_message="curl n'est pas disponible dans l'environnement d'execution.",
                timeout_message="La detection automatique Gobuster a depasse le temps limite autorise.",
            )
        except RuntimeError:
            return None

        if result.exit_code != 0:
            return None

        status_code, _, payload_length = result.stdout.strip().partition(":")
        if not status_code.isdigit() or not payload_length.isdigit():
            return None

        if int(status_code) == 404:
            return None

        detected_length = int(payload_length)
        return detected_length if detected_length > 0 else None

    def _file_not_found_message(self) -> str:
        return "Gobuster n'est pas disponible dans l'environnement d'execution."

    def _timeout_message(self) -> str:
        return "Le scan Gobuster a depasse le temps limite autorise."

    def persist_scan(self, response: ScanResponse) -> ScanResponse:
        super().persist_scan(response)
        log_audit_event(
            "gobuster_scan_executed",
            scan_id=response.scan_id,
            module_id=response.module_id,
            target=response.target,
            exit_code=response.exit_code,
            duration_seconds=response.duration_seconds,
        )
        return response


gobuster_service = GobusterService()
