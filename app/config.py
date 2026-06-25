from dataclasses import dataclass
from pathlib import Path
import os


@dataclass(frozen=True)
class Settings:
    app_name: str
    host: str
    port: int
    base_dir: Path
    templates_dir: Path
    static_dir: Path
    storage_dir: Path
    reports_dir: Path
    logs_dir: Path
    auth_dir: Path
    auth_state_path: Path
    audit_log_path: Path
    toolbox_auth_enabled: bool
    toolbox_auth_username: str
    toolbox_auth_password: str
    toolbox_auth_totp_secret: str
    toolbox_auth_totp_issuer: str
    auth_session_secret: str
    execution_mode: str
    kali_ssh_host: str
    kali_ssh_port: int
    kali_ssh_username: str
    kali_ssh_password: str
    kali_ssh_key_path: str
    kali_ssh_allow_unknown_host: bool
    nmap_binary: str
    nmap_timeout: int
    nikto_binary: str
    nikto_timeout: int
    sqlmap_binary: str
    sqlmap_timeout: int
    sslyze_binary: str
    sslyze_timeout: int
    whatweb_binary: str
    whatweb_timeout: int
    theharvester_binary: str
    theharvester_timeout: int
    theharvester_sources: str
    theharvester_limit: int
    gobuster_binary: str
    gobuster_timeout: int
    gobuster_wordlist: str
    gobuster_threads: int
    gobuster_extensions: str
    gobuster_delay: str
    gobuster_request_timeout: str
    hydra_binary: str
    hydra_timeout: int
    hydra_threads: int
    hydra_username_list_short: str
    hydra_username_list_common: str
    hydra_password_list_small: str
    hydra_password_list_common: str
    hydra_password_list_rockyou: str
    auth_audit_timeout: int
    auth_audit_default_endpoint: str
    auth_audit_default_request_format: str
    auth_audit_default_failure_marker: str
    auth_audit_default_attempts: int
    wireshark_binary: str
    wireshark_timeout: int
    wireshark_default_interface: str
    juice_shop_target: str
    postgres_dsn: str
    redis_url: str
    minio_endpoint: str
    minio_access_key: str
    minio_secret_key: str
    minio_secure: bool
    fernet_key: str
    github_token: str


def _to_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def get_settings() -> Settings:
    base_dir = Path(__file__).resolve().parent
    storage_dir = base_dir.parent / "storage"

    return Settings(
        app_name=os.getenv("APP_NAME", "Reconforge"),
        host=os.getenv("APP_HOST", "0.0.0.0"),
        port=int(os.getenv("APP_PORT", "8000")),
        base_dir=base_dir,
        templates_dir=base_dir / "templates",
        static_dir=base_dir / "static",
        storage_dir=storage_dir,
        reports_dir=storage_dir / "reports",
        logs_dir=storage_dir / "logs",
        auth_dir=storage_dir / "auth",
        auth_state_path=storage_dir / "auth" / "auth_state.json",
        audit_log_path=storage_dir / "logs" / "audit.log",
        toolbox_auth_enabled=_to_bool(os.getenv("TOOLBOX_AUTH_ENABLED", "false")),
        toolbox_auth_username=os.getenv("TOOLBOX_AUTH_USERNAME", "admin").strip(),
        toolbox_auth_password=os.getenv("TOOLBOX_AUTH_PASSWORD", "").strip(),
        toolbox_auth_totp_secret=os.getenv("TOOLBOX_AUTH_TOTP_SECRET", "").strip(),
        toolbox_auth_totp_issuer=os.getenv("TOOLBOX_AUTH_TOTP_ISSUER", "Reconforge").strip(),
        auth_session_secret=os.getenv("AUTH_SESSION_SECRET", "").strip(),
        execution_mode=os.getenv("EXECUTION_MODE", "local").strip().lower(),
        kali_ssh_host=os.getenv("KALI_SSH_HOST", "").strip(),
        kali_ssh_port=int(os.getenv("KALI_SSH_PORT", "22")),
        kali_ssh_username=os.getenv("KALI_SSH_USERNAME", "kali").strip(),
        kali_ssh_password=os.getenv("KALI_SSH_PASSWORD", ""),
        kali_ssh_key_path=os.getenv("KALI_SSH_KEY_PATH", "").strip(),
        kali_ssh_allow_unknown_host=_to_bool(os.getenv("KALI_SSH_ALLOW_UNKNOWN_HOST", "true")),
        nmap_binary=os.getenv("NMAP_BINARY", "nmap"),
        nmap_timeout=int(os.getenv("NMAP_TIMEOUT", "120")),
        nikto_binary=os.getenv("NIKTO_BINARY", "/opt/nikto/program/nikto.pl"),
        nikto_timeout=int(os.getenv("NIKTO_TIMEOUT", "300")),
        sqlmap_binary=os.getenv("SQLMAP_BINARY", "/opt/sqlmap/sqlmap.py"),
        sqlmap_timeout=int(os.getenv("SQLMAP_TIMEOUT", "300")),
        sslyze_binary=os.getenv("SSLYZE_BINARY", "sslyze"),
        sslyze_timeout=int(os.getenv("SSLYZE_TIMEOUT", "180")),
        whatweb_binary=os.getenv("WHATWEB_BINARY", "whatweb"),
        whatweb_timeout=int(os.getenv("WHATWEB_TIMEOUT", "180")),
        theharvester_binary=os.getenv("THEHARVESTER_BINARY", "theHarvester"),
        theharvester_timeout=int(os.getenv("THEHARVESTER_TIMEOUT", "180")),
        theharvester_sources=os.getenv("THEHARVESTER_SOURCES", "crtsh,rapiddns,urlscan").strip(),
        theharvester_limit=int(os.getenv("THEHARVESTER_LIMIT", "200")),
        gobuster_binary=os.getenv("GOBUSTER_BINARY", "gobuster"),
        gobuster_timeout=int(os.getenv("GOBUSTER_TIMEOUT", "240")),
        gobuster_wordlist=os.getenv("GOBUSTER_WORDLIST", "/usr/share/wordlists/dirb/common.txt").strip(),
        gobuster_threads=int(os.getenv("GOBUSTER_THREADS", "4")),
        gobuster_extensions=os.getenv("GOBUSTER_EXTENSIONS", "").strip(),
        gobuster_delay=os.getenv("GOBUSTER_DELAY", "150ms").strip(),
        gobuster_request_timeout=os.getenv("GOBUSTER_REQUEST_TIMEOUT", "5s").strip(),
        hydra_binary=os.getenv("HYDRA_BINARY", "hydra"),
        hydra_timeout=int(os.getenv("HYDRA_TIMEOUT", "120")),
        hydra_threads=int(os.getenv("HYDRA_THREADS", "4")),
        hydra_username_list_short=os.getenv(
            "HYDRA_USERNAME_LIST_SHORT",
            "/usr/share/seclists/Usernames/top-usernames-shortlist.txt",
        ).strip(),
        hydra_username_list_common=os.getenv(
            "HYDRA_USERNAME_LIST_COMMON",
            "/usr/share/seclists/Usernames/Names/names.txt",
        ).strip(),
        hydra_password_list_small=os.getenv(
            "HYDRA_PASSWORD_LIST_SMALL",
            "/usr/share/seclists/Passwords/Common-Credentials/500-worst-passwords.txt",
        ).strip(),
        hydra_password_list_common=os.getenv(
            "HYDRA_PASSWORD_LIST_COMMON",
            "/usr/share/seclists/Passwords/Common-Credentials/10k-most-common.txt",
        ).strip(),
        hydra_password_list_rockyou=os.getenv(
            "HYDRA_PASSWORD_LIST_ROCKYOU",
            "/usr/share/wordlists/rockyou.txt",
        ).strip(),
        auth_audit_timeout=int(os.getenv("AUTH_AUDIT_TIMEOUT", "45")),
        auth_audit_default_endpoint=os.getenv("AUTH_AUDIT_DEFAULT_ENDPOINT", "/rest/user/login").strip(),
        auth_audit_default_request_format=os.getenv("AUTH_AUDIT_DEFAULT_REQUEST_FORMAT", "json").strip().lower(),
        auth_audit_default_failure_marker=os.getenv(
            "AUTH_AUDIT_DEFAULT_FAILURE_MARKER",
            "Invalid email or password.",
        ).strip(),
        auth_audit_default_attempts=int(os.getenv("AUTH_AUDIT_DEFAULT_ATTEMPTS", "3")),
        wireshark_binary=os.getenv("WIRESHARK_BINARY", "tshark"),
        wireshark_timeout=int(os.getenv("WIRESHARK_TIMEOUT", "30")),
        wireshark_default_interface=os.getenv("WIRESHARK_DEFAULT_INTERFACE", "eth0").strip(),
        juice_shop_target=os.getenv("JUICE_SHOP_TARGET", "").strip(),
        postgres_dsn=os.getenv("POSTGRES_DSN", "postgresql+psycopg://toolbox:toolbox@postgres:5432/toolbox"),
        redis_url=os.getenv("REDIS_URL", "redis://redis:6379/0"),
        minio_endpoint=os.getenv("MINIO_ENDPOINT", "minio:9000"),
        minio_access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
        minio_secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
        minio_secure=_to_bool(os.getenv("MINIO_SECURE", "false")),
        fernet_key=os.getenv("FERNET_KEY", ""),
        github_token=os.getenv("GITHUB_TOKEN", ""),
    )
