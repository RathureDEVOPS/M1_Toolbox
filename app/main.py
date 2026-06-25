from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.config import get_settings
from app.logging_conf import configure_logging
from app.routers.api import router as api_router
from app.routers.web import router as web_router


settings = get_settings()


def create_app() -> FastAPI:
    configure_logging(settings)
    settings.storage_dir.mkdir(parents=True, exist_ok=True)
    settings.reports_dir.mkdir(parents=True, exist_ok=True)
    settings.logs_dir.mkdir(parents=True, exist_ok=True)
    settings.auth_dir.mkdir(parents=True, exist_ok=True)

    application = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Reconforge, plateforme de pentest modulaire avec interface web locale et API Swagger.",
    )
    application.add_middleware(
        SessionMiddleware,
        secret_key=settings.auth_session_secret or settings.fernet_key or "toolbox-session-secret-change-me",
        same_site="lax",
        https_only=False,
    )

    application.include_router(web_router)
    application.include_router(api_router)
    application.mount("/static", StaticFiles(directory=str(settings.static_dir)), name="static")
    return application


app = create_app()
