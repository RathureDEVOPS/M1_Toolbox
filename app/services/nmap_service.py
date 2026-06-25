from app.config import get_settings
from app.core.audit import log_audit_event
from app.modules.nmap import ALLOWED_SCRIPT_KEYS
from app.schemas.scan import ScanResponse
from app.services.scan_streaming import CommandStreamingService


class NmapService(CommandStreamingService):
    def __init__(self) -> None:
        self.settings = get_settings()
        self.module_id = "nmap"
        self.module_name = "Nmap"
        self.base_args = ("-Pn", "-sV")
        self.timeout_seconds = self.settings.nmap_timeout

    def _validate_scripts(self, scripts: list[str]) -> list[str]:
        unknown_scripts = sorted({script for script in scripts if script not in ALLOWED_SCRIPT_KEYS})
        if unknown_scripts:
            raise ValueError(f"Scripts non autorises: {', '.join(unknown_scripts)}")
        return list(dict.fromkeys(scripts))

    def _build_command(self, target: str, scripts: list[str], options: dict[str, object]) -> list[str]:
        command = [self.settings.nmap_binary, *self.base_args]
        if scripts:
            command.extend(["--script", ",".join(scripts)])
        command.append(target)
        return command

    def persist_scan(self, response: ScanResponse) -> ScanResponse:
        super().persist_scan(response)
        log_audit_event(
            "nmap_scan_executed",
            scan_id=response.scan_id,
            module_id=response.module_id,
            target=response.target,
            scripts=response.scripts,
            exit_code=response.exit_code,
            duration_seconds=response.duration_seconds,
        )
        return response


nmap_service = NmapService()
