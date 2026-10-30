"""Telethon client wrapper with session persistence."""
import asyncio
import sys
from pathlib import Path
from typing import Optional, Callable, Any

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import SESSIONS_DIR, SESSION_NAME
from utils.logger import get_logger

log = get_logger("telegram_client")


class TelegramClientWrapper:
    """Wraps Telethon client with lifecycle management."""

    def __init__(self):
        self._client = None
        self._api_id: Optional[int] = None
        self._api_hash: Optional[str] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def _session_path(self) -> str:
        return str(SESSIONS_DIR / SESSION_NAME)

    def _get_client(self):
        """Return the active client or raise."""
        if self._client is None:
            raise RuntimeError("Client not initialised. Call init_client() first.")
        return self._client

    def init_client(self, api_id: int, api_hash: str):
        """Create a new Telethon client (does NOT connect yet)."""
        from telethon import TelegramClient
        if self._client:
            self._client.disconnect()
        self._api_id = api_id
        self._api_hash = api_hash
        self._client = TelegramClient(
            self._session_path(), api_id, api_hash,
            system_version="Windows 10",
        )
        log.info("TelegramClient initialised (session path: %s)", self._session_path())
        return self._client

    async def is_authorised(self) -> bool:
        client = self._get_client()
        if not client.is_connected():
            await client.connect()
        return await client.is_user_authorized()

    async def send_code(self, phone: str):
        client = self._get_client()
        if not client.is_connected():
            await client.connect()
        result = await client.send_code_request(phone)
        return result

    async def sign_in(self, phone: str, code: str, phone_code_hash: str):
        client = self._get_client()
        return await client.sign_in(phone=phone, code=code,
                                    phone_code_hash=phone_code_hash)

    async def sign_in_2fa(self, password: str):
        client = self._get_client()
        from telethon.errors import SessionPasswordNeededError
        return await client.sign_in(password=password)

    async def get_me(self):
        client = self._get_client()
        return await client.get_me()

    async def disconnect(self):
        if self._client and self._client.is_connected():
            await self._client.disconnect()
            log.info("Client disconnected")

    async def logout(self):
        client = self._get_client()
        if client.is_connected():
            await client.log_out()
        # Remove session file
        session_file = Path(self._session_path() + ".session")
        if session_file.exists():
            session_file.unlink()
            log.info("Session file removed")

    def get_raw_client(self):
        return self._get_client()

    @property
    def is_connected(self) -> bool:
        return self._client is not None and self._client.is_connected()


# Singleton
_client_wrapper: Optional[TelegramClientWrapper] = None


def get_client_wrapper() -> TelegramClientWrapper:
    global _client_wrapper
    if _client_wrapper is None:
        _client_wrapper = TelegramClientWrapper()
    return _client_wrapper
