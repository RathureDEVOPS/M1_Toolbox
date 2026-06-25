from __future__ import annotations

import base64
import hashlib
import hmac
import io
import json
import struct
import time
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote

import qrcode
import qrcode.image.svg

from app.config import get_settings


class AuthService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.settings.auth_dir.mkdir(parents=True, exist_ok=True)

    def is_enabled(self) -> bool:
        return self.settings.toolbox_auth_enabled

    def is_configured(self) -> bool:
        return bool(
            self.settings.toolbox_auth_username
            and self.settings.toolbox_auth_password
            and self.settings.toolbox_auth_totp_secret
            and self.settings.auth_session_secret
        )

    def is_totp_enrolled(self) -> bool:
        state = self.load_state()
        return bool(state.get("totp_enabled"))

    def load_state(self) -> dict[str, Any]:
        if self.settings.auth_state_path.exists():
            try:
                payload = json.loads(self.settings.auth_state_path.read_text(encoding="utf-8"))
                if isinstance(payload, dict):
                    return {
                        "username": str(payload.get("username", self.settings.toolbox_auth_username)),
                        "totp_enabled": bool(payload.get("totp_enabled", False)),
                        "activated_at": str(payload.get("activated_at", "")).strip(),
                    }
            except Exception:
                pass
        return self._default_state()

    def verify_primary_credentials(self, username: str, password: str) -> tuple[bool, str]:
        if not self.is_enabled():
            return True, ""

        if not self.is_configured():
            return False, (
                "Authentification active mais incomplete. "
                "Verifie TOOLBOX_AUTH_USERNAME, TOOLBOX_AUTH_PASSWORD, "
                "TOOLBOX_AUTH_TOTP_SECRET et AUTH_SESSION_SECRET."
            )

        expected_username = self.settings.toolbox_auth_username
        expected_password = self.settings.toolbox_auth_password

        if not hmac.compare_digest(username.strip(), expected_username):
            return False, "Identifiant ou mot de passe invalide."

        if not hmac.compare_digest(password, expected_password):
            return False, "Identifiant ou mot de passe invalide."

        return True, ""

    def verify_full_login(self, username: str, password: str, otp_code: str) -> tuple[bool, str]:
        primary_ok, primary_message = self.verify_primary_credentials(username, password)
        if not primary_ok:
            return False, primary_message

        if not self.verify_totp_code(otp_code):
            return False, "Code A2F invalide ou expire."

        return True, ""

    def activate_totp(self, otp_code: str) -> tuple[bool, str]:
        if not self.verify_totp_code(otp_code):
            return False, "Code A2F invalide ou expire."

        payload = {
            "username": self.settings.toolbox_auth_username,
            "totp_enabled": True,
            "activated_at": datetime.now(timezone.utc).isoformat(),
        }
        self.settings.auth_state_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return True, ""

    def verify_totp_code(self, otp_code: str) -> bool:
        normalized_code = "".join(character for character in otp_code if character.isdigit())
        if len(normalized_code) != 6:
            return False

        time_step = 30
        current_counter = int(time.time() // time_step)

        for offset in (-1, 0, 1):
            expected_code = self._generate_totp(counter=current_counter + offset)
            if hmac.compare_digest(normalized_code, expected_code):
                return True

        return False

    def provisioning_uri(self) -> str:
        secret = self._normalized_secret()
        issuer = quote(self.settings.toolbox_auth_totp_issuer)
        account_name = quote(self.settings.toolbox_auth_username or "toolbox")
        return f"otpauth://totp/{issuer}:{account_name}?secret={secret}&issuer={issuer}&digits=6&period=30"

    def provisioning_qr_data_uri(self) -> str:
        qr_image = qrcode.make(
            self.provisioning_uri(),
            image_factory=qrcode.image.svg.SvgImage,
            box_size=8,
            border=2,
        )
        output = io.BytesIO()
        qr_image.save(output)
        encoded = base64.b64encode(output.getvalue()).decode("ascii")
        return f"data:image/svg+xml;base64,{encoded}"

    def current_secret(self) -> str:
        return self._normalized_secret()

    def _normalized_secret(self) -> str:
        return self.settings.toolbox_auth_totp_secret.replace(" ", "").strip().upper()

    def _default_state(self) -> dict[str, Any]:
        return {
            "username": self.settings.toolbox_auth_username,
            "totp_enabled": False,
            "activated_at": "",
        }

    def _generate_totp(self, counter: int) -> str:
        secret = self._normalized_secret()
        padded_secret = secret + "=" * ((8 - len(secret) % 8) % 8)
        secret_bytes = base64.b32decode(padded_secret, casefold=True)
        counter_bytes = struct.pack(">Q", counter)
        digest = hmac.new(secret_bytes, counter_bytes, hashlib.sha1).digest()
        offset = digest[-1] & 0x0F
        binary = struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7FFFFFFF
        return str(binary % 1_000_000).zfill(6)


auth_service = AuthService()
