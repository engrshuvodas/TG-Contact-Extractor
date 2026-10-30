"""Telethon client wrapper with session persistence and dedicated async loop."""
import asyncio
import concurrent.futures
import sys
import threading
from pathlib import Path
from typing import Optional, Callable, Any

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import SESSIONS_DIR, SESSION_NAME
from utils.logger import get_logger

log = get_logger("telegram_client")


class AsyncLoopManager:
    """Manages a single persistent asyncio event loop on a dedicated background thread."""

    def __init__(self):
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._ready = threading.Event()
        self._start()

    def _start(self):
        def _runner():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._ready.set()
            self._loop.run_forever()

        self._thread = threading.Thread(target=_runner, daemon=True, name="TelegramEventLoopThread")
        self._thread.start()
        self._ready.wait()

    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        return self._loop

    def run_coro(self, coro) -> concurrent.futures.Future:
        """Submit a coroutine to the background loop and return a concurrent.futures.Future."""
        return asyncio.run_coroutine_threadsafe(coro, self._loop)

    def run_coro_sync(self, coro, timeout: Optional[float] = None) -> Any:
        """Run coroutine and wait synchronously for the result."""
        future = self.run_coro(coro)
        return future.result(timeout=timeout)


_loop_manager: Optional[AsyncLoopManager] = None


def get_async_loop_manager() -> AsyncLoopManager:
    global _loop_manager
    if _loop_manager is None:
        _loop_manager = AsyncLoopManager()
    return _loop_manager


class TelegramClientWrapper:
    """Wraps Telethon client with lifecycle management."""

    def __init__(self):
        self._client = None
        self._api_id: Optional[int] = None
        self._api_hash: Optional[str] = None
        self._loop_mgr = get_async_loop_manager()

    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        return self._loop_mgr.loop

    def _session_path(self) -> str:
        return str(SESSIONS_DIR / SESSION_NAME)

    def _get_client(self):
        """Return the active client or raise."""
        if self._client is None:
            raise RuntimeError("Client not initialised. Call init_client() first.")
        return self._client

    def init_client(self, api_id: int, api_hash: str):
        """Create a new Telethon client tied to the persistent event loop."""
        from telethon import TelegramClient
        if self._client:
            try:
                self._loop_mgr.run_coro_sync(self.disconnect(), timeout=3)
            except Exception:
                pass
        self._api_id = api_id
        self._api_hash = api_hash
        self._client = TelegramClient(
            self._session_path(), api_id, api_hash,
            loop=self._loop_mgr.loop,
            system_version="Windows 10",
        )
        log.info("TelegramClient initialised on persistent loop (session path: %s)", self._session_path())
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

