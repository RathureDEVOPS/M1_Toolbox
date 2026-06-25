from urllib.parse import urlparse

from app.config import get_settings
from app.core.audit import log_audit_event
from app.core.security import normalize_target
from app.schemas.scan import ScanResponse
from app.services.scan_streaming import CommandStreamingService


class HydraService(CommandStreamingService):
    def __init__(self) -> None:
        self.settings = get_settings()
        self.module_id = "hydra"
        self.module_name = "Hydra"
        self.timeout_seconds = self.settings.hydra_timeout

    def _normalize_target(self, raw_target: str) -> str:
        value = (raw_target or "").strip()
        if not value:
            raise ValueError("Veuillez saisir une IP ou un domaine pour Hydra.")
        if "://" in value:
            parsed = urlparse(value)
            if not parsed.hostname:
                raise ValueError("Cible Hydra invalide.")
            return parsed.hostname
        return normalize_target(value)

    def _normalize_options(self, options: dict[str, object] | None) -> dict[str, object]:
        data = dict(options or {})
        username = str(data.get("username", "")).strip()
        username_mode = str(data.get("username_mode", "shortlist")).strip().lower() or "shortlist"
        username_list_path = str(data.get("username_list_path", "")).strip()
        password = str(data.get("password", ""))
        password_mode = str(data.get("password_mode", "manual")).strip().lower() or "manual"
        password_list_path = str(data.get("password_list_path", "")).strip()
        port_raw = str(data.get("port", "22")).strip() or "22"
        if not port_raw.isdigit():
            raise ValueError("Le port Hydra doit etre numerique.")

        port = int(port_raw)
        if port < 1 or port > 65535:
            raise ValueError("Le port Hydra doit etre compris entre 1 et 65535.")

        if username_mode == "manual":
            if not username:
                raise ValueError("Veuillez renseigner un identifiant SSH pour Hydra.")
        elif username_mode in {"shortlist", "names"}:
            if not username_list_path:
                raise ValueError("La wordlist utilisateurs Hydra selectionnee est introuvable.")
            username = ""
        else:
            raise ValueError("Mode d'utilisateur Hydra non pris en charge.")

        if password_mode == "manual":
            if password == "":
                raise ValueError("Veuillez renseigner un mot de passe SSH pour Hydra.")
        elif password_mode in {"small", "common", "rockyou"}:
            if not password_list_path:
                raise ValueError("La wordlist Hydra selectionnee est introuvable.")
            password = ""
        else:
            raise ValueError("Mode de mot de passe Hydra non pris en charge.")

        return {
            "username": username,
            "username_mode": username_mode,
            "username_list_path": username_list_path,
            "password": password,
            "password_mode": password_mode,
            "password_list_path": password_list_path,
            "port": port,
        }

    def _build_command(self, target: str, scripts: list[str], options: dict[str, object]) -> list[str]:
        command = [
            self.settings.hydra_binary,
            "-s",
            str(options["port"]),
            "-t",
            str(self.settings.hydra_threads),
        ]

        if options["username_mode"] == "manual":
            command.extend(["-l", str(options["username"])])
        else:
            command.extend(["-L", str(options["username_list_path"])])

        if options["password_mode"] == "manual":
            command.extend(["-p", str(options["password"])])
        else:
            command.extend(["-P", str(options["password_list_path"])])

        command.extend([target, "ssh"])
        return command

    def _display_command(self, command: list[str], options: dict[str, object]) -> str:
        masked = list(command)
        if "-p" in masked:
            password_index = masked.index("-p") + 1
            if password_index < len(masked):
                masked[password_index] = "********"
        return " ".join(masked)

    def _file_not_found_message(self) -> str:
        return "Hydra n'est pas disponible dans l'environnement d'execution."

    def _timeout_message(self) -> str:
        return "Le scan Hydra a depasse le temps limite autorise."

    def persist_scan(self, response: ScanResponse) -> ScanResponse:
        super().persist_scan(response)
        log_audit_event(
            "hydra_scan_executed",
            scan_id=response.scan_id,
            module_id=response.module_id,
            target=response.target,
            exit_code=response.exit_code,
            duration_seconds=response.duration_seconds,
        )
        return response


hydra_service = HydraService()
