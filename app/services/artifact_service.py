import json
import textwrap
from pathlib import Path

from app.config import get_settings
from datetime import datetime, timezone
from uuid import uuid4

from app.schemas.scan import ModuleExecutionResult, ScanHistoryEntry, ScanResponse, SessionCreateRequest, SessionResponse


class ArtifactService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.settings.reports_dir.mkdir(parents=True, exist_ok=True)

    def _json_path(self, scan_id: str) -> Path:
        return self.settings.reports_dir / f"{scan_id}.json"

    def _pdf_path(self, scan_id: str) -> Path:
        return self.settings.reports_dir / f"{scan_id}.pdf"

    def json_artifact_url(self, scan_id: str) -> str:
        return f"/api/scans/{scan_id}/artifacts/json"

    def pdf_artifact_url(self, scan_id: str) -> str:
        return f"/api/scans/{scan_id}/artifacts/pdf"

    def persist_scan(self, result: ScanResponse) -> None:
        json_path = self._json_path(result.scan_id)
        pdf_path = self._pdf_path(result.scan_id)

        json_path.write_text(result.model_dump_json(indent=2), encoding="utf-8")
        self._write_pdf(result, pdf_path)

    def persist_session(self, session_request: SessionCreateRequest) -> SessionResponse:
        if not session_request.results:
            raise ValueError("Aucun module n'a ete execute pour cette session.")

        scan_id = str(uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        module_names = [result.module_name for result in session_request.results]
        joined_names = " + ".join(module_names) if module_names else "Session"
        command_lines = [result.command for result in session_request.results if result.command]
        stdout_blocks = []
        stderr_blocks = []
        exit_code = 0
        total_duration = 0.0
        ok = True

        for result in session_request.results:
            total_duration += result.duration_seconds
            if not result.ok:
                ok = False
                if exit_code == 0:
                    exit_code = result.exit_code

            if result.stdout:
                stdout_blocks.append(f"[{result.module_name}]\n{result.stdout}")
            if result.stderr:
                stderr_blocks.append(f"[{result.module_name}]\n{result.stderr}")

        summary = SessionResponse(
            scan_id=scan_id,
            module_id="batch",
            module_name=joined_names,
            created_at=created_at,
            target=session_request.target,
            scripts=[],
            command="\n".join(command_lines),
            stdout="\n\n".join(stdout_blocks).strip(),
            stderr="\n\n".join(stderr_blocks).strip(),
            exit_code=exit_code,
            duration_seconds=round(total_duration, 2),
            ok=ok,
            json_artifact_url=self.json_artifact_url(scan_id),
            pdf_artifact_url=self.pdf_artifact_url(scan_id),
        )

        payload = summary.model_dump()
        payload["modules"] = session_request.modules
        payload["results"] = [result.model_dump() for result in session_request.results]

        json_path = self._json_path(scan_id)
        pdf_path = self._pdf_path(scan_id)
        json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        self._write_session_pdf(summary, session_request.results, pdf_path)
        return summary

    def get_artifact_path(self, scan_id: str, artifact_format: str) -> Path | None:
        mapping = {
            "json": self._json_path(scan_id),
            "pdf": self._pdf_path(scan_id),
        }
        candidate = mapping.get(artifact_format)
        if candidate is None or not candidate.exists():
            return None
        return candidate

    def list_history(self, limit: int = 25) -> list[ScanHistoryEntry]:
        entries: list[ScanHistoryEntry] = []
        files = sorted(self.settings.reports_dir.glob("*.json"), key=lambda path: path.stat().st_mtime, reverse=True)

        for file_path in files[:limit]:
            payload = json.loads(file_path.read_text(encoding="utf-8"))
            entries.append(
                ScanHistoryEntry(
                    scan_id=payload["scan_id"],
                    module_id=payload.get("module_id", "unknown"),
                    module_name=payload.get("module_name", payload.get("module_id", "Unknown")),
                    created_at=payload["created_at"],
                    target=payload["target"],
                    scripts=payload.get("scripts", []),
                    command=payload["command"],
                    exit_code=payload["exit_code"],
                    duration_seconds=payload["duration_seconds"],
                    ok=payload["ok"],
                    json_artifact_url=payload["json_artifact_url"],
                    pdf_artifact_url=payload["pdf_artifact_url"],
                )
            )

        return entries

    def _write_pdf(self, result: ScanResponse, destination: Path) -> None:
        lines = [
            "Reconforge - Resultat de scan",
            f"Scan ID: {result.scan_id}",
            f"Date: {result.created_at}",
            f"Cible: {result.target}",
            f"Commande: {result.command}",
            f"Scripts: {', '.join(result.scripts) if result.scripts else 'aucun'}",
            f"Code retour: {result.exit_code}",
            f"Duree: {result.duration_seconds}s",
            "",
            "Sortie standard:",
        ]

        if result.stdout:
            for raw_line in result.stdout.splitlines():
                wrapped = textwrap.wrap(raw_line, width=100) or [""]
                lines.extend(wrapped)
        else:
            lines.append("(vide)")

        lines.extend(["", "Erreurs:"])
        if result.stderr:
            for raw_line in result.stderr.splitlines():
                wrapped = textwrap.wrap(raw_line, width=100) or [""]
                lines.extend(wrapped)
        else:
            lines.append("(aucune)")

        self._render_basic_pdf(lines, destination)

    def _write_session_pdf(
        self,
        summary: SessionResponse,
        results: list[ModuleExecutionResult],
        destination: Path,
    ) -> None:
        lines = [
            "Reconforge - Resultat de session",
            f"Session ID: {summary.scan_id}",
            f"Date: {summary.created_at}",
            f"Cible: {summary.target}",
            f"Outils: {summary.module_name}",
            f"Code retour global: {summary.exit_code}",
            f"Duree totale: {summary.duration_seconds}s",
            "",
        ]

        for result in results:
            lines.extend(
                [
                    f"Module: {result.module_name}",
                    f"Commande: {result.command}",
                    f"Code retour: {result.exit_code}",
                    f"Duree: {result.duration_seconds}s",
                    "Sortie standard:",
                ]
            )

            if result.stdout:
                for raw_line in result.stdout.splitlines():
                    lines.extend(textwrap.wrap(raw_line, width=100) or [""])
            else:
                lines.append("(vide)")

            lines.append("Erreurs:")
            if result.stderr:
                for raw_line in result.stderr.splitlines():
                    lines.extend(textwrap.wrap(raw_line, width=100) or [""])
            else:
                lines.append("(aucune)")
            lines.append("")

        self._render_basic_pdf(lines, destination)

    def _render_basic_pdf(self, lines: list[str], destination: Path) -> None:
        lines_per_page = 48
        pages = [lines[index:index + lines_per_page] for index in range(0, len(lines), lines_per_page)] or [[]]
        objects: list[bytes] = []

        def add_object(content: str | bytes) -> int:
            data = content if isinstance(content, bytes) else content.encode("latin-1", errors="replace")
            objects.append(data)
            return len(objects)

        font_id = add_object("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
        page_ids: list[int] = []
        content_ids: list[int] = []

        for page_lines in pages:
            stream_text = ["BT", "/F1 10 Tf", "40 800 Td", "14 TL"]
            for line in page_lines:
                safe_line = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
                stream_text.append(f"({safe_line}) Tj")
                stream_text.append("T*")
            stream_text.append("ET")
            stream_body = "\n".join(stream_text).encode("latin-1", errors="replace")
            content_id = add_object(
                b"<< /Length " + str(len(stream_body)).encode("ascii") + b" >>\nstream\n" + stream_body + b"\nendstream"
            )
            content_ids.append(content_id)
            page_ids.append(0)

        pages_id = add_object("")

        for index, content_id in enumerate(content_ids):
            page_object = (
                f"<< /Type /Page /Parent {pages_id} 0 R /MediaBox [0 0 595 842] "
                f"/Resources << /Font << /F1 {font_id} 0 R >> >> /Contents {content_id} 0 R >>"
            )
            page_ids[index] = add_object(page_object)

        kids_refs = " ".join(f"{page_id} 0 R" for page_id in page_ids)
        objects[pages_id - 1] = f"<< /Type /Pages /Kids [{kids_refs}] /Count {len(page_ids)} >>".encode("latin-1")
        catalog_id = add_object(f"<< /Type /Catalog /Pages {pages_id} 0 R >>")

        pdf = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        offsets = [0]
        for object_id, data in enumerate(objects, start=1):
            offsets.append(len(pdf))
            pdf.extend(f"{object_id} 0 obj\n".encode("ascii"))
            pdf.extend(data)
            pdf.extend(b"\nendobj\n")

        xref_offset = len(pdf)
        pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
        pdf.extend(b"0000000000 65535 f \n")
        for offset in offsets[1:]:
            pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
        pdf.extend(
            (
                f"trailer\n<< /Size {len(objects) + 1} /Root {catalog_id} 0 R >>\n"
                f"startxref\n{xref_offset}\n%%EOF\n"
            ).encode("ascii")
        )
        destination.write_bytes(pdf)


artifact_service = ArtifactService()
