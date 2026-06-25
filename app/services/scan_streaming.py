import json
from datetime import datetime, timezone
from typing import Generator
from uuid import uuid4

from app.core.security import normalize_target
from app.schemas.scan import ScanResponse
from app.services.artifact_service import artifact_service
from app.services.command_execution_service import CommandExecutionResult, command_execution_service


class CommandStreamingService:
    module_id: str
    module_name: str
    timeout_seconds: int

    def _build_command(self, target: str, scripts: list[str], options: dict[str, object]) -> list[str]:
        raise NotImplementedError

    def _validate_scripts(self, scripts: list[str]) -> list[str]:
        return list(dict.fromkeys(scripts))

    def _normalize_options(self, options: dict[str, object] | None) -> dict[str, object]:
        return dict(options or {})

    def _normalize_target(self, raw_target: str) -> str:
        return normalize_target(raw_target)

    def _file_not_found_message(self) -> str:
        return f"Le binaire {self.module_name} est introuvable dans l'environnement d'execution."

    def _timeout_message(self) -> str:
        return f"Le scan {self.module_name} a depasse le temps limite autorise."

    def _display_command(self, command: list[str], options: dict[str, object]) -> str:
        return " ".join(command)

    def _get_timeout_seconds(self, options: dict[str, object]) -> int:
        return self.timeout_seconds

    def _build_scan_response(
        self,
        scan_id: str,
        created_at: str,
        target: str,
        scripts: list[str],
        display_command: str,
        stdout: str,
        stderr: str,
        exit_code: int,
        duration_seconds: float,
    ) -> ScanResponse:
        return ScanResponse(
            scan_id=scan_id,
            module_id=self.module_id,
            module_name=self.module_name,
            created_at=created_at,
            target=target,
            scripts=scripts,
            command=display_command,
            stdout=stdout,
            stderr=stderr,
            exit_code=exit_code,
            duration_seconds=duration_seconds,
            ok=exit_code == 0,
            json_artifact_url=artifact_service.json_artifact_url(scan_id),
            pdf_artifact_url=artifact_service.pdf_artifact_url(scan_id),
        )

    def persist_scan(self, response: ScanResponse) -> ScanResponse:
        artifact_service.persist_scan(response)
        return response

    def run_scan(self, raw_target: str, scripts: list[str], options: dict[str, object] | None = None) -> ScanResponse:
        target = self._normalize_target(raw_target)
        selected_scripts = self._validate_scripts(scripts)
        normalized_options = self._normalize_options(options)
        command = self._build_command(target, selected_scripts, normalized_options)
        display_command = self._display_command(command, normalized_options)
        timeout_seconds = self._get_timeout_seconds(normalized_options)
        scan_id = str(uuid4())
        created_at = datetime.now(timezone.utc).isoformat()

        result = command_execution_service.run_command(
            command,
            timeout_seconds,
            self._file_not_found_message(),
            self._timeout_message(),
        )
        response = self._build_scan_response(
            scan_id=scan_id,
            created_at=created_at,
            target=target,
            scripts=selected_scripts,
            display_command=display_command,
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.exit_code,
            duration_seconds=result.duration_seconds,
        )
        return self.persist_scan(response)

    def stream_scan(
        self,
        raw_target: str,
        scripts: list[str],
        options: dict[str, object] | None = None,
        persist_result: bool = True,
    ) -> Generator[bytes, None, None]:
        try:
            target = self._normalize_target(raw_target)
            selected_scripts = self._validate_scripts(scripts)
            normalized_options = self._normalize_options(options)
            command = self._build_command(target, selected_scripts, normalized_options)
            display_command = self._display_command(command, normalized_options)
            timeout_seconds = self._get_timeout_seconds(normalized_options)
        except ValueError as error:
            yield self._event_bytes("error", {"module_id": self.module_id, "module_name": self.module_name, "message": str(error)})
            return

        scan_id = str(uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        yield self._event_bytes(
            "start",
            {
                "scan_id": scan_id,
                "module_id": self.module_id,
                "module_name": self.module_name,
                "created_at": created_at,
                "target": target,
                "scripts": selected_scripts,
                "command": display_command,
            },
        )

        execution_result: CommandExecutionResult | None = None
        try:
            for event in command_execution_service.stream_command(
                command,
                timeout_seconds,
                self._file_not_found_message(),
                self._timeout_message(),
            ):
                if event["type"] in {"stdout", "stderr"}:
                    yield self._event_bytes(
                        str(event["type"]),
                        {
                            "module_id": self.module_id,
                            "module_name": self.module_name,
                            "line": str(event["line"]),
                        },
                    )
                elif event["type"] == "result":
                    execution_result = event["result"]  # type: ignore[assignment]
        except RuntimeError as error:
            yield self._event_bytes(
                "error",
                {"module_id": self.module_id, "module_name": self.module_name, "message": str(error)},
            )
            return

        if execution_result is None:
            yield self._event_bytes(
                "error",
                {"module_id": self.module_id, "module_name": self.module_name, "message": "Aucun resultat recupere pour cette commande."},
            )
            return

        response = self._build_scan_response(
            scan_id=scan_id,
            created_at=created_at,
            target=target,
            scripts=selected_scripts,
            display_command=display_command,
            stdout=execution_result.stdout,
            stderr=execution_result.stderr,
            exit_code=execution_result.exit_code,
            duration_seconds=execution_result.duration_seconds,
        )
        if persist_result:
            response = self.persist_scan(response)
        yield self._event_bytes(
            "finish",
            {
                "scan_id": response.scan_id,
                "module_id": response.module_id,
                "module_name": response.module_name,
                "created_at": response.created_at,
                "target": response.target,
                "scripts": response.scripts,
                "command": response.command,
                "stdout": response.stdout,
                "stderr": response.stderr,
                "exit_code": response.exit_code,
                "duration_seconds": response.duration_seconds,
                "ok": response.ok,
                "json_artifact_url": response.json_artifact_url,
                "pdf_artifact_url": response.pdf_artifact_url,
            },
        )

    def _event_bytes(self, event_name: str, payload: dict[str, object]) -> bytes:
        body = {"event": event_name, **payload}
        return (json.dumps(body, ensure_ascii=True) + "\n").encode("utf-8")
