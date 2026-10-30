"""Private-chat contact extractor."""
import asyncio
import sys
from pathlib import Path
from typing import Callable, Optional, Dict, Any
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.telegram_client import get_client_wrapper
from core.database import Database
from utils.logger import get_logger
from utils.helpers import safe_str, format_phone, format_datetime, now_str, build_full_name

log = get_logger("extractor")


class ExtractionStats:
    def __init__(self):
        self.total_dialogs = 0
        self.total_users = 0
        self.with_username = 0
        self.without_username = 0
        self.with_phone = 0
        self.without_phone = 0
        self.saved_contacts = 0
        self.non_saved = 0
        self.archived_scanned = 0
        self.failed = 0
        self.processed = 0

    def to_dict(self) -> Dict[str, int]:
        return {
            "total_dialogs":    self.total_dialogs,
            "total_users":      self.total_users,
            "with_username":    self.with_username,
            "without_username": self.without_username,
            "with_phone":       self.with_phone,
            "without_phone":    self.without_phone,
            "saved_contacts":   self.saved_contacts,
            "non_saved":        self.non_saved,
            "archived_scanned": self.archived_scanned,
            "failed":           self.failed,
            "processed":        self.processed,
        }


class ContactExtractor:
    """Extracts private-chat contacts using the Telethon API."""

    def __init__(self, db: Database):
        self.db = db
        self._running = False
        self._paused = False
        self._stop_requested = False
        self.stats = ExtractionStats()

    # ─── Control ────────────────────────────────────────────────────────────
    def stop(self):    self._stop_requested = True
    def pause(self):   self._paused = True
    def resume(self):  self._paused = False

    @property
    def is_running(self) -> bool: return self._running

    # ─── Main extraction ────────────────────────────────────────────────────
    async def extract(
        self,
        on_progress: Optional[Callable[[str, ExtractionStats], None]] = None,
        on_user_found: Optional[Callable[[Dict], None]] = None,
    ) -> ExtractionStats:
        """
        Scan all accessible private dialogs and save user data.

        Callbacks:
            on_progress(status_msg, stats) — called frequently
            on_user_found(user_dict)        — called for each new user
        """
        self._running = True
        self._paused = False
        self._stop_requested = False
        self.stats = ExtractionStats()
        seen_ids: set = set()

        wrapper = get_client_wrapper()
        client = wrapper.get_raw_client()

        def _notify(msg: str):
            if on_progress:
                on_progress(msg, self.stats)

        try:
            _notify("Connecting to Telegram…")
            if not client.is_connected():
                await client.connect()

            # Scan dialogs (regular + archived)
            for archived in [False, True]:
                if self._stop_requested:
                    break
                folder = "archived" if archived else "regular"
                _notify(f"Scanning {folder} dialogs…")

                async for dialog in client.iter_dialogs(archived=archived):
                    if self._stop_requested:
                        break

                    # Pause support
                    while self._paused and not self._stop_requested:
                        await asyncio.sleep(0.5)

                    self.stats.total_dialogs += 1
                    if archived:
                        self.stats.archived_scanned += 1

                    entity = dialog.entity
                    from telethon.tl.types import User
                    if not isinstance(entity, User):
                        continue        # skip groups & channels

                    user: User = entity
                    if user.bot:       continue   # skip bots
                    if user.is_self:   continue   # skip self
                    if user.deleted:   continue   # skip deleted accounts

                    uid = user.id
                    if uid in seen_ids:
                        continue
                    seen_ids.add(uid)

                    # Build record
                    phone_raw = getattr(user, "phone", None)
                    username_raw = getattr(user, "username", None)
                    first  = safe_str(getattr(user, "first_name", None))
                    last   = safe_str(getattr(user, "last_name", None))
                    full   = build_full_name(first, last) or f"User {uid}"
                    phone  = format_phone(phone_raw)
                    uname  = safe_str(username_raw)

                    last_msg_date = None
                    try:
                        if dialog.message and dialog.message.date:
                            last_msg_date = format_datetime(dialog.message.date)
                    except Exception:
                        pass

                    is_contact = int(getattr(user, "contact", False) or
                                     getattr(user, "mutual_contact", False))

                    user_dict = {
                        "user_id":           uid,
                        "first_name":        first,
                        "last_name":         last,
                        "full_name":         full,
                        "username":          uname,
                        "phone":             phone,
                        "is_contact":        is_contact,
                        "last_message_date": last_msg_date,
                        "chat_type":         "private",
                        "extraction_date":   now_str(),
                        "updated_at":        now_str(),
                    }

                    try:
                        self.db.upsert_user(user_dict)
                    except Exception as db_err:
                        log.error("DB error for uid %s: %s", uid, db_err)
                        self.stats.failed += 1
                        continue

                    # Update stats
                    self.stats.total_users += 1
                    self.stats.processed += 1
                    if uname:
                        self.stats.with_username += 1
                    else:
                        self.stats.without_username += 1
                    if phone:
                        self.stats.with_phone += 1
                    else:
                        self.stats.without_phone += 1
                    if is_contact:
                        self.stats.saved_contacts += 1
                    else:
                        self.stats.non_saved += 1

                    if on_user_found:
                        on_user_found(user_dict)

                    _notify(f"Found: {full}")
                    await asyncio.sleep(0.03)   # be polite

            # Also fetch saved contacts (may include users not in dialogs)
            if not self._stop_requested:
                _notify("Fetching saved contacts…")
                try:
                    from telethon.tl.functions.contacts import GetContactsRequest
                    result = await client(GetContactsRequest(hash=0))
                    for user in result.users:
                        if self._stop_requested: break
                        from telethon.tl.types import User
                        if not isinstance(user, User): continue
                        if user.bot or user.is_self or user.deleted: continue
                        uid = user.id
                        if uid in seen_ids: continue
                        seen_ids.add(uid)

                        phone_raw = getattr(user, "phone", None)
                        username_raw = getattr(user, "username", None)
                        first = safe_str(getattr(user, "first_name", None))
                        last  = safe_str(getattr(user, "last_name", None))
                        full  = build_full_name(first, last) or f"User {uid}"

                        user_dict = {
                            "user_id":           uid,
                            "first_name":        first,
                            "last_name":         last,
                            "full_name":         full,
                            "username":          safe_str(username_raw),
                            "phone":             format_phone(phone_raw),
                            "is_contact":        1,
                            "last_message_date": None,
                            "chat_type":         "contact",
                            "extraction_date":   now_str(),
                            "updated_at":        now_str(),
                        }
                        try:
                            self.db.upsert_user(user_dict)
                            self.stats.total_users += 1
                            self.stats.processed += 1
                            self.stats.saved_contacts += 1
                            if user_dict["username"]: self.stats.with_username += 1
                            else: self.stats.without_username += 1
                            if user_dict["phone"]: self.stats.with_phone += 1
                            else: self.stats.without_phone += 1
                            if on_user_found: on_user_found(user_dict)
                        except Exception as e:
                            log.error("Contact upsert error: %s", e)
                            self.stats.failed += 1
                except Exception as e:
                    log.warning("Could not fetch contacts list: %s", e)

            _notify("Extraction complete!")
        except Exception as exc:
            log.exception("Extraction failed: %s", exc)
            _notify(f"Error: {exc}")
        finally:
            self._running = False

        return self.stats
