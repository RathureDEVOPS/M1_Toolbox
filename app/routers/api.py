from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse

from app.modules.registry import list_modules
from app.schemas.scan import ModuleSchema, ScanHistoryEntry, ScanRequest, ScanResponse, SessionCreateRequest, SessionResponse
from app.services.auth_audit_service import auth_audit_service
from app.services.artifact_service import artifact_service
from app.services.gobuster_service import gobuster_service
from app.services.hydra_service import hydra_service
from app.services.nikto_service import nikto_service
from app.services.nmap_service import nmap_service
from app.services.sqlmap_service import sqlmap_service
from app.services.sslyze_service import sslyze_service
from app.services.theharvester_service import theharvester_service
from app.services.whatweb_service import whatweb_service
from app.services.wireshark_service import wireshark_service
from app.services.auth_service import auth_service


def require_api_auth(request: Request) -> None:
    if not auth_service.is_enabled():
        return

    if request.session.get("authenticated") is True:
        return

    raise HTTPException(status_code=401, detail="Authentification requise.")


router = APIRouter(prefix="/api", tags=["api"], dependencies=[Depends(require_api_auth)])


@router.get("/modules", response_model=list[ModuleSchema])
async def get_modules() -> list[ModuleSchema]:
    modules = list_modules()
    return [
        ModuleSchema(
            identifier=module.identifier,
            name=module.name,
            description=module.description,
            category=module.category,
            source=module.source,
        )
        for module in modules
    ]


@router.post("/scans/nmap", response_model=ScanResponse)
async def launch_nmap_scan(payload: ScanRequest) -> ScanResponse:
    try:
        return nmap_service.run_scan(payload.target, payload.scripts, payload.options)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@router.post("/scans/nmap/stream")
async def stream_nmap_scan(payload: ScanRequest) -> StreamingResponse:
    return StreamingResponse(
        nmap_service.stream_scan(payload.target, payload.scripts, payload.options, persist_result=False),
        media_type="application/x-ndjson",
    )


@router.post("/scans/hydra", response_model=ScanResponse)
async def launch_hydra_scan(payload: ScanRequest) -> ScanResponse:
    try:
        return hydra_service.run_scan(payload.target, payload.scripts, payload.options)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@router.post("/scans/hydra/stream")
async def stream_hydra_scan(payload: ScanRequest) -> StreamingResponse:
    return StreamingResponse(
        hydra_service.stream_scan(payload.target, payload.scripts, payload.options, persist_result=False),
        media_type="application/x-ndjson",
    )


@router.post("/scans/auth-audit", response_model=ScanResponse)
async def launch_auth_audit(payload: ScanRequest) -> ScanResponse:
    try:
        return auth_audit_service.run_scan(payload.target, payload.scripts, payload.options)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@router.post("/scans/auth-audit/stream")
async def stream_auth_audit(payload: ScanRequest) -> StreamingResponse:
    return StreamingResponse(
        auth_audit_service.stream_scan(payload.target, payload.scripts, payload.options, persist_result=False),
        media_type="application/x-ndjson",
    )


@router.post("/scans/nikto", response_model=ScanResponse)
async def launch_nikto_scan(payload: ScanRequest) -> ScanResponse:
    try:
        return nikto_service.run_scan(payload.target, payload.scripts, payload.options)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@router.post("/scans/nikto/stream")
async def stream_nikto_scan(payload: ScanRequest) -> StreamingResponse:
    return StreamingResponse(
        nikto_service.stream_scan(payload.target, payload.scripts, payload.options, persist_result=False),
        media_type="application/x-ndjson",
    )


@router.post("/scans/whatweb", response_model=ScanResponse)
async def launch_whatweb_scan(payload: ScanRequest) -> ScanResponse:
    try:
        return whatweb_service.run_scan(payload.target, payload.scripts, payload.options)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@router.post("/scans/whatweb/stream")
async def stream_whatweb_scan(payload: ScanRequest) -> StreamingResponse:
    return StreamingResponse(
        whatweb_service.stream_scan(payload.target, payload.scripts, payload.options, persist_result=False),
        media_type="application/x-ndjson",
    )


@router.post("/scans/theharvester", response_model=ScanResponse)
async def launch_theharvester_scan(payload: ScanRequest) -> ScanResponse:
    try:
        return theharvester_service.run_scan(payload.target, payload.scripts, payload.options)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@router.post("/scans/theharvester/stream")
async def stream_theharvester_scan(payload: ScanRequest) -> StreamingResponse:
    return StreamingResponse(
        theharvester_service.stream_scan(payload.target, payload.scripts, payload.options, persist_result=False),
        media_type="application/x-ndjson",
    )


@router.post("/scans/wireshark", response_model=ScanResponse)
async def launch_wireshark_scan(payload: ScanRequest) -> ScanResponse:
    try:
        return wireshark_service.run_scan(payload.target, payload.scripts, payload.options)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@router.post("/scans/wireshark/stream")
async def stream_wireshark_scan(payload: ScanRequest) -> StreamingResponse:
    return StreamingResponse(
        wireshark_service.stream_scan(payload.target, payload.scripts, payload.options, persist_result=False),
        media_type="application/x-ndjson",
    )


@router.post("/scans/gobuster", response_model=ScanResponse)
async def launch_gobuster_scan(payload: ScanRequest) -> ScanResponse:
    try:
        return gobuster_service.run_scan(payload.target, payload.scripts, payload.options)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@router.post("/scans/gobuster/stream")
async def stream_gobuster_scan(payload: ScanRequest) -> StreamingResponse:
    return StreamingResponse(
        gobuster_service.stream_scan(payload.target, payload.scripts, payload.options, persist_result=False),
        media_type="application/x-ndjson",
    )


@router.post("/scans/sqlmap", response_model=ScanResponse)
async def launch_sqlmap_scan(payload: ScanRequest) -> ScanResponse:
    try:
        return sqlmap_service.run_scan(payload.target, payload.scripts, payload.options)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@router.post("/scans/sqlmap/stream")
async def stream_sqlmap_scan(payload: ScanRequest) -> StreamingResponse:
    return StreamingResponse(
        sqlmap_service.stream_scan(payload.target, payload.scripts, payload.options, persist_result=False),
        media_type="application/x-ndjson",
    )


@router.post("/scans/sslyze", response_model=ScanResponse)
async def launch_sslyze_scan(payload: ScanRequest) -> ScanResponse:
    try:
        return sslyze_service.run_scan(payload.target, payload.scripts, payload.options)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@router.post("/scans/sslyze/stream")
async def stream_sslyze_scan(payload: ScanRequest) -> StreamingResponse:
    return StreamingResponse(
        sslyze_service.stream_scan(payload.target, payload.scripts, payload.options, persist_result=False),
        media_type="application/x-ndjson",
    )


@router.post("/scans/session", response_model=SessionResponse)
async def create_scan_session(payload: SessionCreateRequest) -> SessionResponse:
    try:
        return artifact_service.persist_session(payload)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/scans/history", response_model=list[ScanHistoryEntry])
async def get_scan_history() -> list[ScanHistoryEntry]:
    return artifact_service.list_history()


@router.get("/scans/{scan_id}/artifacts/{artifact_format}")
async def download_scan_artifact(scan_id: str, artifact_format: str) -> FileResponse:
    artifact_path = artifact_service.get_artifact_path(scan_id, artifact_format)
    if artifact_path is None:
        raise HTTPException(status_code=404, detail="Artefact introuvable.")

    media_types = {
        "json": "application/json",
        "pdf": "application/pdf",
    }
    return FileResponse(
        artifact_path,
        media_type=media_types.get(artifact_format, "application/octet-stream"),
        filename=artifact_path.name,
    )
