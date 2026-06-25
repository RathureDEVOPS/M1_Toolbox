import ipaddress
import re
from urllib.parse import urlparse

from cryptography.fernet import Fernet


HOSTNAME_LABEL_RE = re.compile(r"^[a-zA-Z0-9-]{1,63}$")


def normalize_target(raw_target: str) -> str:
    target = (raw_target or "").strip()
    if not target:
        raise ValueError("Veuillez saisir une IP, un domaine ou une URL.")

    if target.startswith(("http://", "https://")):
        parsed = urlparse(target)
        if not parsed.hostname:
            raise ValueError("URL invalide.")
        candidate = parsed.hostname
    else:
        candidate = target

    candidate = candidate.strip("[]")

    try:
        ipaddress.ip_address(candidate)
        return candidate
    except ValueError:
        pass

    if len(candidate) > 253:
        raise ValueError("La cible est trop longue.")

    labels = candidate.split(".")
    if not labels or any(not label for label in labels):
        raise ValueError("Nom de domaine invalide.")

    if any(label.startswith("-") or label.endswith("-") for label in labels):
        raise ValueError("Nom de domaine invalide.")

    if not all(HOSTNAME_LABEL_RE.match(label) for label in labels):
        raise ValueError("La cible contient des caracteres non autorises.")

    return candidate


def build_fernet(key: str) -> Fernet | None:
    if not key:
        return None
    return Fernet(key.encode("utf-8"))
