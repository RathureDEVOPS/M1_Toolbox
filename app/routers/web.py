from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.config import get_settings
from app.modules.nmap import SCRIPT_OPTIONS
from app.modules.registry import list_module_groups, list_modules
from app.services.auth_service import auth_service


settings = get_settings()
templates = Jinja2Templates(directory=str(settings.templates_dir))
router = APIRouter(tags=["web"])


@router.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    if auth_service.is_enabled() and request.session.get("authenticated") is not True:
        return RedirectResponse(url="/login", status_code=303)

    static_version = max(
        int((settings.static_dir / "app.js").stat().st_mtime),
        int((settings.static_dir / "styles.css").stat().st_mtime),
    )
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "app_name": settings.app_name,
            "scripts": SCRIPT_OPTIONS,
            "modules": list_modules(),
            "module_groups": list_module_groups(),
            "static_version": static_version,
            "juice_shop_target": settings.juice_shop_target,
            "hydra_username_list_short": settings.hydra_username_list_short,
            "hydra_username_list_common": settings.hydra_username_list_common,
            "hydra_password_list_small": settings.hydra_password_list_small,
            "hydra_password_list_common": settings.hydra_password_list_common,
            "hydra_password_list_rockyou": settings.hydra_password_list_rockyou,
            "auth_audit_default_endpoint": settings.auth_audit_default_endpoint,
            "auth_audit_default_request_format": settings.auth_audit_default_request_format,
            "auth_audit_default_failure_marker": settings.auth_audit_default_failure_marker,
            "auth_audit_default_attempts": settings.auth_audit_default_attempts,
            "wireshark_default_interface": settings.wireshark_default_interface,
            "auth_enabled": auth_service.is_enabled(),
            "auth_username": settings.toolbox_auth_username,
        },
    )


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request) -> HTMLResponse:
    if not auth_service.is_enabled():
        return RedirectResponse(url="/", status_code=303)

    if request.session.get("authenticated") is True:
        return RedirectResponse(url="/", status_code=303)

    static_version = max(
        int((settings.static_dir / "app.js").stat().st_mtime),
        int((settings.static_dir / "styles.css").stat().st_mtime),
    )
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "app_name": settings.app_name,
            "static_version": static_version,
            "error_message": "",
            "auth_configured": auth_service.is_configured(),
            "totp_enrolled": auth_service.is_totp_enrolled(),
            "auth_totp_issuer": settings.toolbox_auth_totp_issuer,
            "auth_username": settings.toolbox_auth_username,
        },
    )


@router.post("/login", response_class=HTMLResponse)
async def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    if not auth_service.is_enabled():
        return RedirectResponse(url="/", status_code=303)

    allowed, message = auth_service.verify_primary_credentials(username, password)
    if allowed:
        request.session["auth_stage"] = "primary_ok"
        request.session["auth_username"] = settings.toolbox_auth_username
        if auth_service.is_totp_enrolled():
            return RedirectResponse(url="/verify-2fa", status_code=303)
        return RedirectResponse(url="/setup-2fa", status_code=303)

    static_version = max(
        int((settings.static_dir / "app.js").stat().st_mtime),
        int((settings.static_dir / "styles.css").stat().st_mtime),
    )
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "app_name": settings.app_name,
            "static_version": static_version,
            "error_message": message,
            "auth_configured": auth_service.is_configured(),
            "totp_enrolled": auth_service.is_totp_enrolled(),
            "auth_totp_issuer": settings.toolbox_auth_totp_issuer,
            "auth_username": settings.toolbox_auth_username,
        },
        status_code=401,
    )


@router.get("/verify-2fa", response_class=HTMLResponse)
async def verify_totp_page(request: Request) -> HTMLResponse:
    if not auth_service.is_enabled():
        return RedirectResponse(url="/", status_code=303)

    if request.session.get("authenticated") is True:
        return RedirectResponse(url="/", status_code=303)

    if request.session.get("auth_stage") != "primary_ok" or not auth_service.is_totp_enrolled():
        return RedirectResponse(url="/login", status_code=303)

    static_version = max(
        int((settings.static_dir / "app.js").stat().st_mtime),
        int((settings.static_dir / "styles.css").stat().st_mtime),
    )
    return templates.TemplateResponse(
        request=request,
        name="verify_2fa.html",
        context={
            "app_name": settings.app_name,
            "static_version": static_version,
            "error_message": "",
            "auth_totp_issuer": settings.toolbox_auth_totp_issuer,
            "auth_username": settings.toolbox_auth_username,
        },
    )


@router.post("/verify-2fa", response_class=HTMLResponse)
async def verify_totp_submit(request: Request, otp_code: str = Form(...)):
    if not auth_service.is_enabled():
        return RedirectResponse(url="/", status_code=303)

    if request.session.get("auth_stage") != "primary_ok" or not auth_service.is_totp_enrolled():
        return RedirectResponse(url="/login", status_code=303)

    if auth_service.verify_totp_code(otp_code):
        request.session["authenticated"] = True
        request.session["auth_stage"] = "complete"
        request.session["auth_username"] = settings.toolbox_auth_username
        return RedirectResponse(url="/", status_code=303)

    static_version = max(
        int((settings.static_dir / "app.js").stat().st_mtime),
        int((settings.static_dir / "styles.css").stat().st_mtime),
    )
    return templates.TemplateResponse(
        request=request,
        name="verify_2fa.html",
        context={
            "app_name": settings.app_name,
            "static_version": static_version,
            "error_message": "Code A2F invalide ou expire.",
            "auth_totp_issuer": settings.toolbox_auth_totp_issuer,
            "auth_username": settings.toolbox_auth_username,
        },
        status_code=401,
    )


@router.get("/setup-2fa", response_class=HTMLResponse)
async def setup_totp_page(request: Request) -> HTMLResponse:
    if not auth_service.is_enabled():
        return RedirectResponse(url="/", status_code=303)

    if request.session.get("authenticated") is True:
        return RedirectResponse(url="/", status_code=303)

    if request.session.get("auth_stage") != "primary_ok":
        return RedirectResponse(url="/login", status_code=303)

    if auth_service.is_totp_enrolled():
        return RedirectResponse(url="/verify-2fa", status_code=303)

    static_version = max(
        int((settings.static_dir / "app.js").stat().st_mtime),
        int((settings.static_dir / "styles.css").stat().st_mtime),
    )
    return templates.TemplateResponse(
        request=request,
        name="setup_2fa.html",
        context={
            "app_name": settings.app_name,
            "static_version": static_version,
            "error_message": "",
            "auth_totp_issuer": settings.toolbox_auth_totp_issuer,
            "auth_username": settings.toolbox_auth_username,
            "totp_secret": auth_service.current_secret(),
            "provisioning_uri": auth_service.provisioning_uri(),
            "qr_code_data_uri": auth_service.provisioning_qr_data_uri(),
        },
    )


@router.post("/setup-2fa", response_class=HTMLResponse)
async def setup_totp_submit(request: Request, otp_code: str = Form(...)):
    if not auth_service.is_enabled():
        return RedirectResponse(url="/", status_code=303)

    if request.session.get("auth_stage") != "primary_ok":
        return RedirectResponse(url="/login", status_code=303)

    activated, message = auth_service.activate_totp(otp_code)
    if activated:
        request.session["authenticated"] = True
        request.session["auth_stage"] = "complete"
        request.session["auth_username"] = settings.toolbox_auth_username
        return RedirectResponse(url="/", status_code=303)

    static_version = max(
        int((settings.static_dir / "app.js").stat().st_mtime),
        int((settings.static_dir / "styles.css").stat().st_mtime),
    )
    return templates.TemplateResponse(
        request=request,
        name="setup_2fa.html",
        context={
            "app_name": settings.app_name,
            "static_version": static_version,
            "error_message": message,
            "auth_totp_issuer": settings.toolbox_auth_totp_issuer,
            "auth_username": settings.toolbox_auth_username,
            "totp_secret": auth_service.current_secret(),
            "provisioning_uri": auth_service.provisioning_uri(),
            "qr_code_data_uri": auth_service.provisioning_qr_data_uri(),
        },
        status_code=401,
    )


@router.get("/logout")
async def logout(request: Request) -> RedirectResponse:
    request.session.clear()
    if auth_service.is_enabled():
        return RedirectResponse(url="/login", status_code=303)
    return RedirectResponse(url="/", status_code=303)


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
