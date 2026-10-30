"""Authentication flow coordinator."""
import asyncio
import sys
from pathlib import Path
from typing import Callable, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.telegram_client import get_client_wrapper
from utils.logger import get_logger

log = get_logger("authentication")

# Step constants
STEP_INIT     = "init"
STEP_WAITING_CODE  = "waiting_code"
STEP_WAITING_2FA   = "waiting_2fa"
STEP_DONE     = "done"
STEP_ERROR    = "error"


class AuthManager:
    """Manages the multi-step Telegram authentication flow."""

    def __init__(self):
        self._phone: Optional[str] = None
        self._phone_code_hash: Optional[str] = None
        self._step = STEP_INIT

    @property
    def step(self) -> str:
        return self._step

    async def start_login(self, api_id: str, api_hash: str, phone: str) -> dict:
        """Step 1: Init client and send OTP."""
        try:
            api_id_int = int(api_id.strip())
        except ValueError:
            return {"ok": False, "error": "API ID must be a number."}

        api_hash = api_hash.strip()
        phone = phone.strip()
        if not phone.startswith("+"):
            phone = "+" + phone

        wrapper = get_client_wrapper()
        try:
            wrapper.init_client(api_id_int, api_hash)
            # Check for existing session
            if await wrapper.is_authorised():
                self._step = STEP_DONE
                return {"ok": True, "already_logged_in": True}

            result = await wrapper.send_code(phone)
            self._phone = phone
            self._phone_code_hash = result.phone_code_hash
            self._step = STEP_WAITING_CODE
            log.info("OTP sent to %s", phone[:3] + "****")
            return {"ok": True, "already_logged_in": False}
        except Exception as e:
            self._step = STEP_ERROR
            log.error("start_login error: %s", str(e))
            return {"ok": False, "error": self._friendly_error(e)}

    async def verify_code(self, code: str) -> dict:
        """Step 2: Verify OTP code."""
        if self._step != STEP_WAITING_CODE:
            return {"ok": False, "error": "Not waiting for code."}
        wrapper = get_client_wrapper()
        try:
            await wrapper.sign_in(self._phone, code.strip(), self._phone_code_hash)
            self._step = STEP_DONE
            return {"ok": True, "needs_2fa": False}
        except Exception as e:
            err_str = str(e).lower()
            if "session_password_needed" in err_str or "two-steps verification" in err_str:
                self._step = STEP_WAITING_2FA
                return {"ok": True, "needs_2fa": True}
            if "phone_code_invalid" in err_str:
                return {"ok": False, "error": "Invalid code. Please check and try again."}
            if "phone_code_expired" in err_str:
                self._step = STEP_INIT
                return {"ok": False, "error": "Code expired. Please request a new one."}
            log.error("verify_code error: %s", str(e))
            return {"ok": False, "error": self._friendly_error(e)}

    async def verify_2fa(self, password: str) -> dict:
        """Step 3: Verify 2FA password."""
        if self._step != STEP_WAITING_2FA:
            return {"ok": False, "error": "Not waiting for 2FA password."}
        wrapper = get_client_wrapper()
        try:
            await wrapper.sign_in_2fa(password)
            self._step = STEP_DONE
            return {"ok": True}
        except Exception as e:
            err_str = str(e).lower()
            if "password_hash_invalid" in err_str:
                return {"ok": False, "error": "Incorrect 2FA password. Please try again."}
            log.error("verify_2fa error: %s", str(e))
            return {"ok": False, "error": self._friendly_error(e)}

    @staticmethod
    def _friendly_error(exc: Exception) -> str:
        s = str(exc)
        if "FloodWait" in s:
            secs = "a while"
            try:
                import re
                m = re.search(r"(\d+)", s)
                if m:
                    secs = f"{m.group(1)} seconds"
            except Exception:
                pass
            return f"Telegram requires you to wait {secs} before trying again."
        s_lower = s.lower()
        if any(term in s_lower for term in ["network error", "connection reset", "connection refused", "timeout", "timed out", "cannot connect"]):
            return "Network error. Please check your internet connection."
        if "api_id" in s_lower:
            return "Invalid API ID. Please check your credentials."
        if "api_hash" in s_lower:
            return "Invalid API Hash. Please check your credentials."
        if "phone_number_invalid" in s_lower:
            return "Invalid phone number. Please include country code (+XX...)."
        return f"Error: {s[:200]}"

    def reset(self):
        self._phone = None
        self._phone_code_hash = None
        self._step = STEP_INIT
