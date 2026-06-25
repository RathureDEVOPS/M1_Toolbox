from app.config import get_settings
from app.core.audit import log_audit_event
from app.schemas.scan import ScanResponse
from app.services.scan_streaming import CommandStreamingService


class SSLyzeService(CommandStreamingService):
    def __init__(self) -> None:
        self.settings = get_settings()
        self.module_id = "sslyze"
        self.module_name = "SSLyze"
        self.timeout_seconds = self.settings.sslyze_timeout

    def _build_command(self, target: str, scripts: list[str], options: dict[str, object]) -> list[str]:
        return [self.settings.sslyze_binary, target]

    def _file_not_found_message(self) -> str:
        return "SSLyze n'est pas disponible dans l'environnement d'execution."

    def _timeout_message(self) -> str:
        return "Le scan SSLyze a depasse le temps limite autorise."

    def persist_scan(self, response: ScanResponse) -> ScanResponse:
        super().persist_scan(response)
        log_audit_event(
            "sslyze_scan_executed",
            scan_id=response.scan_id,
            module_id=response.module_id,
            target=response.target,
            exit_code=response.exit_code,
            duration_seconds=response.duration_seconds,
        )
        return response


sslyze_service = SSLyzeService()
