import time
from datetime import datetime, timezone
from typing import Callable
from urllib.parse import urljoin, urlparse
from uuid import uuid4

import httpx

from app.config import get_settings
from app.core.audit import log_audit_event
from app.schemas.scan import ScanResponse
from app.services.scan_streaming import CommandStreamingService


class AuthAuditService(CommandStreamingService):
    def __init__(self) -> None:
        self.settings = get_settings()
        self.module_id = "auth-audit"
        self.module_name = "Auth Audit"
        self.timeout_seconds = self.settings.auth_audit_timeout

    def _normalize_target(self, raw_target: str) -> str:
        value = (raw_target or "").strip()
        if not value:
            raise ValueError("Veuillez saisir une URL de connexion pour Auth Audit.")
        if "://" not in value:
            value = f"http://{value}"
        parsed = urlparse(value)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError("URL Auth Audit invalide.")
        return value

    def _normalize_options(self, options: dict[str, object] | None) -> dict[str, object]:
        data = dict(options or {})
        endpoint_path = str(data.get("endpoint_path", self.settings.auth_audit_default_endpoint)).strip()
        request_format = (
            str(data.get("request_format", self.settings.auth_audit_default_request_format)).strip().lower()
            or self.settings.auth_audit_default_request_format
        )
        username_field = str(data.get("username_field", "email")).strip() or "email"
        password_field = str(data.get("password_field", "password")).strip() or "password"
        failure_marker = (
            str(data.get("failure_marker", self.settings.auth_audit_default_failure_marker)).strip()
            or self.settings.auth_audit_default_failure_marker
        )
        attempts_raw = str(data.get("attempts", self.settings.auth_audit_default_attempts)).strip()

        if request_format not in {"json", "form"}:
            raise ValueError("Auth Audit supporte uniquement les formats json et form.")
        if not endpoint_path:
            raise ValueError("Veuillez renseigner un endpoint de connexion pour Auth Audit.")
        if not attempts_raw.isdigit():
            raise ValueError("Le nombre de tentatives Auth Audit doit etre numerique.")

        attempts = int(attempts_raw)
        if attempts < 1 or attempts > 5:
            raise ValueError("Auth Audit autorise entre 1 et 5 tentatives controlees.")

        return {
            "endpoint_path": endpoint_path,
            "request_format": request_format,
            "username_field": username_field,
            "password_field": password_field,
            "failure_marker": failure_marker,
            "attempts": attempts,
        }

    def _build_command(self, target: str, scripts: list[str], options: dict[str, object]) -> list[str]:
        endpoint_url = self._build_endpoint_url(target, str(options["endpoint_path"]))
        return [
            "auth-audit",
            target,
            endpoint_url,
            str(options["request_format"]),
            str(options["attempts"]),
        ]

    def _display_command(self, command: list[str], options: dict[str, object]) -> str:
        return (
            f"auth-audit page={command[1]} endpoint={command[2]} "
            f"format={command[3]} tentatives={command[4]}"
        )

    def run_scan(self, raw_target: str, scripts: list[str], options: dict[str, object] | None = None) -> ScanResponse:
        target = self._normalize_target(raw_target)
        selected_scripts = self._validate_scripts(scripts)
        normalized_options = self._normalize_options(options)
        command = self._build_command(target, selected_scripts, normalized_options)
        display_command = self._display_command(command, normalized_options)
        scan_id = str(uuid4())
        created_at = datetime.now(timezone.utc).isoformat()

        stdout, stderr, exit_code, duration_seconds = self._execute_audit(target, normalized_options, None)
        response = self._build_scan_response(
            scan_id=scan_id,
            created_at=created_at,
            target=target,
            scripts=selected_scripts,
            display_command=display_command,
            stdout=stdout,
            stderr=stderr,
            exit_code=exit_code,
            duration_seconds=duration_seconds,
        )
        return self.persist_scan(response)

    def stream_scan(
        self,
        raw_target: str,
        scripts: list[str],
        options: dict[str, object] | None = None,
        persist_result: bool = True,
    ):
        try:
            target = self._normalize_target(raw_target)
            selected_scripts = self._validate_scripts(scripts)
            normalized_options = self._normalize_options(options)
            command = self._build_command(target, selected_scripts, normalized_options)
            display_command = self._display_command(command, normalized_options)
        except ValueError as error:
            yield self._event_bytes(
                "error",
                {"module_id": self.module_id, "module_name": self.module_name, "message": str(error)},
            )
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

        stream_lines: list[tuple[str, str]] = []

        def emit(kind: str, line: str) -> None:
            stream_lines.append((kind, line))

        stdout, stderr, exit_code, duration_seconds = self._execute_audit(target, normalized_options, emit)

        for kind, line in stream_lines:
            yield self._event_bytes(
                kind,
                {
                    "module_id": self.module_id,
                    "module_name": self.module_name,
                    "line": line,
                },
            )

        response = self._build_scan_response(
            scan_id=scan_id,
            created_at=created_at,
            target=target,
            scripts=selected_scripts,
            display_command=display_command,
            stdout=stdout,
            stderr=stderr,
            exit_code=exit_code,
            duration_seconds=duration_seconds,
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

    def persist_scan(self, response: ScanResponse) -> ScanResponse:
        super().persist_scan(response)
        log_audit_event(
            "auth_audit_executed",
            scan_id=response.scan_id,
            module_id=response.module_id,
            target=response.target,
            exit_code=response.exit_code,
            duration_seconds=response.duration_seconds,
        )
        return response

    def _execute_audit(
        self,
        target: str,
        options: dict[str, object],
        emit: Callable[[str, str], None] | None,
    ) -> tuple[str, str, int, float]:
        started_at = time.perf_counter()
        stdout_lines: list[str] = []
        stderr_lines: list[str] = []

        def write_stdout(line: str) -> None:
            stdout_lines.append(line)
            if emit is not None:
                emit("stdout", line)

        def write_stderr(line: str) -> None:
            stderr_lines.append(line)
            if emit is not None:
                emit("stderr", line)

        page_url = target
        endpoint_url = self._build_endpoint_url(target, str(options["endpoint_path"]))
        request_format = str(options["request_format"])
        username_field = str(options["username_field"])
        password_field = str(options["password_field"])
        failure_marker = str(options["failure_marker"])
        attempts = int(options["attempts"])

        parsed_target = urlparse(target)
        write_stdout(f"[page] URL de login analysee : {page_url}")
        write_stdout(f"[auth] Endpoint teste : {endpoint_url}")
        write_stdout(f"[auth] Format de requete : {request_format}")
        if parsed_target.fragment:
            write_stdout("[page] Fragment detecte dans l'URL. Le serveur recoit la page sans la partie apres '#'.")

        page_response: httpx.Response | None = None
        attempt_results: list[dict[str, object]] = []
        try:
            with httpx.Client(follow_redirects=True, timeout=10.0, verify=False) as client:
                try:
                    page_response = client.get(page_url)
                    page_body = page_response.text
                    write_stdout(
                        f"[page] code={page_response.status_code} type={page_response.headers.get('content-type', 'inconnu')}"
                    )
                    self._emit_page_findings(write_stdout, page_response, page_body)
                except httpx.HTTPError as error:
                    write_stderr(f"[page] Impossible de recuperer la page de login: {error}")

                for attempt_index in range(1, attempts + 1):
                    probe_username = f"audit-user-{attempt_index}@example.local"
                    probe_password = f"AuditPass-{attempt_index}-Invalid!"
                    payload = {
                        username_field: probe_username,
                        password_field: probe_password,
                    }
                    request_kwargs = {
                        "headers": {
                            "Accept": "application/json, text/plain, */*",
                        }
                    }
                    if request_format == "json":
                        request_kwargs["json"] = payload
                        request_kwargs["headers"]["Content-Type"] = "application/json"
                    else:
                        request_kwargs["data"] = payload

                    try:
                        response = client.post(endpoint_url, **request_kwargs)
                        response_text = response.text
                        contains_failure_marker = failure_marker.lower() in response_text.lower() if failure_marker else False
                        result = {
                            "status_code": response.status_code,
                            "length": len(response_text),
                            "contains_failure_marker": contains_failure_marker,
                            "retry_after": response.headers.get("retry-after", ""),
                            "body_preview": self._normalize_preview(response_text),
                        }
                        attempt_results.append(result)
                        write_stdout(
                            f"[auth][tentative {attempt_index}] code={response.status_code} "
                            f"taille={result['length']} marker={'oui' if contains_failure_marker else 'non'}"
                        )
                    except httpx.HTTPError as error:
                        write_stderr(f"[auth][tentative {attempt_index}] Erreur HTTP: {error}")
                        attempt_results.append(
                            {
                                "status_code": 0,
                                "length": 0,
                                "contains_failure_marker": False,
                                "retry_after": "",
                                "body_preview": "",
                            }
                        )

        except Exception as error:  # pragma: no cover - garde-fou de presentation
            write_stderr(f"[audit] Echec inattendu pendant l'audit: {error}")

        summary_lines = self._build_summary(page_response, attempt_results)
        for line in summary_lines:
            write_stdout(line)

        exit_code = 0 if page_response is not None or any(result["status_code"] for result in attempt_results) else 1
        duration_seconds = round(time.perf_counter() - started_at, 2)
        return (
            "\n".join(stdout_lines).strip(),
            "\n".join(stderr_lines).strip(),
            exit_code,
            duration_seconds,
        )

    def _emit_page_findings(self, write_stdout: Callable[[str], None], response: httpx.Response, body: str) -> None:
        headers = response.headers
        lower_body = body.lower()
        form_detected = "<form" in lower_body
        csrf_detected = any(token in lower_body for token in ("csrf", "_token", "__requestverificationtoken"))
        mfa_detected = any(token in lower_body for token in ("mfa", "2fa", "otp", "captcha", "recaptcha"))
        security_headers = {
            "csp": "oui" if "content-security-policy" in headers else "non",
            "x-frame-options": "oui" if "x-frame-options" in headers else "non",
            "x-content-type-options": "oui" if "x-content-type-options" in headers else "non",
            "strict-transport-security": "oui" if "strict-transport-security" in headers else "non",
        }
        write_stdout(f"[page] formulaire HTML detecte : {'oui' if form_detected else 'non'}")
        write_stdout(f"[page] token CSRF visible : {'oui' if csrf_detected else 'non'}")
        write_stdout(f"[page] MFA / CAPTCHA detecte : {'oui' if mfa_detected else 'non'}")
        write_stdout(
            "[page] en-tetes securite : "
            + ", ".join(f"{header}={value}" for header, value in security_headers.items())
        )

        cookie_headers = headers.get_list("set-cookie")
        if cookie_headers:
            cookie_summary = self._summarize_cookies(cookie_headers)
            write_stdout(
                "[page] cookies : "
                f"HttpOnly={cookie_summary['httponly']}, Secure={cookie_summary['secure']}, SameSite={cookie_summary['samesite']}"
            )

    def _build_summary(self, page_response: httpx.Response | None, attempt_results: list[dict[str, object]]) -> list[str]:
        status_codes = [int(result["status_code"]) for result in attempt_results if int(result["status_code"]) > 0]
        marker_hits = [bool(result["contains_failure_marker"]) for result in attempt_results]
        previews = [str(result["body_preview"]) for result in attempt_results]
        retry_after_seen = any(str(result["retry_after"]).strip() for result in attempt_results)

        uniform_errors = len({(result["status_code"], result["body_preview"]) for result in attempt_results}) <= 1 if attempt_results else False
        rate_limited = any(code == 429 for code in status_codes) or retry_after_seen
        lockout_suspected = len(status_codes) >= 2 and len(set(status_codes)) > 1 and any(code in {401, 403, 423} for code in status_codes[1:])
        api_reachable = any(code > 0 for code in status_codes)
        failure_marker_seen = any(marker_hits)

        summary = [
            "",
            "[resume] Audit d'authentification",
            f"[resume] page joignable : {'oui' if page_response is not None else 'non'}",
            f"[resume] endpoint joignable : {'oui' if api_reachable else 'non'}",
            f"[resume] message d'echec uniforme : {'oui' if uniform_errors else 'non'}",
            f"[resume] marqueur d'echec observe : {'oui' if failure_marker_seen else 'non'}",
            f"[resume] rate limiting detecte : {'oui' if rate_limited else 'non'}",
            f"[resume] verrouillage suspecte : {'oui' if lockout_suspected else 'non'}",
        ]
        if previews:
            summary.append(f"[resume] apercu reponse auth : {previews[0] or '(vide)'}")
        return summary

    def _build_endpoint_url(self, target: str, endpoint_path: str) -> str:
        if endpoint_path.startswith(("http://", "https://")):
            return endpoint_path

        parsed = urlparse(target)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        normalized_path = endpoint_path if endpoint_path.startswith("/") else f"/{endpoint_path}"
        return urljoin(origin, normalized_path)

    def _normalize_preview(self, value: str) -> str:
        compact = " ".join(value.split())
        return compact[:180]

    def _summarize_cookies(self, cookie_headers: list[str]) -> dict[str, str]:
        lower_headers = " ".join(cookie_headers).lower()
        return {
            "httponly": "oui" if "httponly" in lower_headers else "non",
            "secure": "oui" if "secure" in lower_headers else "non",
            "samesite": "oui" if "samesite" in lower_headers else "non",
        }


auth_audit_service = AuthAuditService()
