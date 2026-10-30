"""
TG Contact Extractor
====================
Entry point — builds the main window and wires all panels together.
"""
import sys
import asyncio
import threading
from pathlib import Path

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).parent))

import customtkinter as ctk
from config import (
    THEME as T, APP_NAME, APP_VERSION,
    WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT,
)
from core.database import Database
from core.telegram_client import get_client_wrapper
from gui.components import SidebarButton, StatusBadge, make_label, Separator
from gui.login import LoginPanel
from gui.dashboard import DashboardPanel
from gui.extraction import ExtractionPanel
from gui.export import ExportPanel
from gui.settings import SettingsPanel
from gui.history import HistoryPanel
from gui.about import AboutPanel
from utils.logger import get_logger

log = get_logger("main")

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


NAV_ITEMS = [
    ("dashboard",   "📊", "Dashboard"),
    ("connect",     "🔑", "Connect Telegram"),
    ("extraction",  "⚡", "Extract Contacts"),
    ("export",      "📤", "Export Data"),
    ("history",     "📋", "History"),
    ("settings",    "⚙", "Settings"),
    ("about",       "ℹ", "About"),
]


class App(ctk.CTk):

    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME}  v{APP_VERSION}")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        self.configure(fg_color=T["bg_primary"])

        # Set window icon if available
        icon_path = Path(__file__).parent / "assets" / "icons" / "app.ico"
        if icon_path.exists():
            try:
                self.iconbitmap(str(icon_path))
            except Exception:
                pass

        self._db = Database()
        self._panels: dict = {}
        self._sidebar_btns: dict = {}
        self._current_page = None

        self._build_window()
        self._check_existing_session()

    # ─── Window layout ───────────────────────────────────────────────────────
    def _build_window(self):
        # Outer container
        self._outer = ctk.CTkFrame(self, fg_color=T["bg_primary"])
        self._outer.pack(fill="both", expand=True)

        # Sidebar
        self._sidebar = ctk.CTkFrame(self._outer,
                                      fg_color=T["sidebar_bg"],
                                      width=T["sidebar_width"],
                                      corner_radius=0)
        self._sidebar.pack(side="left", fill="y")
        self._sidebar.pack_propagate(False)

        # Main content area
        self._content = ctk.CTkFrame(self._outer,
                                      fg_color=T["bg_primary"],
                                      corner_radius=0)
        self._content.pack(side="left", fill="both", expand=True)

        self._build_sidebar()
        self._build_panels()

    def _build_sidebar(self):
        # Logo area
        logo_frame = ctk.CTkFrame(self._sidebar, fg_color="transparent", height=80)
        logo_frame.pack(fill="x", padx=0)
        logo_frame.pack_propagate(False)

        ctk.CTkLabel(logo_frame,
                     text="✈  TG Extractor",
                     font=(T["font_family"], 15, "bold"),
                     text_color=T["text_primary"]).place(relx=0.5, rely=0.5, anchor="center")

        Separator(self._sidebar).pack(fill="x", padx=12, pady=(0,8))

        # Navigation buttons
        nav_frame = ctk.CTkFrame(self._sidebar, fg_color="transparent")
        nav_frame.pack(fill="x", padx=10)

        for page_key, icon, label in NAV_ITEMS:
            btn = SidebarButton(nav_frame, text=label, icon=icon,
                                command=lambda k=page_key: self.navigate(k))
            btn.pack(fill="x", pady=2)
            self._sidebar_btns[page_key] = btn

        # Bottom status
        Separator(self._sidebar).pack(fill="x", padx=12, side="bottom", pady=(0,8))
        self._status_badge = StatusBadge(self._sidebar)
        self._status_badge.pack(side="bottom", padx=14, pady=(0,12), anchor="w")

        ctk.CTkLabel(self._sidebar,
                     text=f"v{APP_VERSION}",
                     font=(T["font_family"], T["font_size_xs"]),
                     text_color=T["text_muted"]).pack(side="bottom", pady=(0,4))

    def _build_panels(self):
        """Lazily create all panels and stack them in _content."""

        def _make(panel_cls, *args, **kwargs):
            p = panel_cls(self._content, *args, **kwargs)
            p.place(relx=0, rely=0, relwidth=1, relheight=1)
            return p

        self._panels["connect"] = _make(
            LoginPanel,
            on_login_success=self._on_login_success,
        )
        self._panels["dashboard"] = _make(
            DashboardPanel, db=self._db,
            on_navigate=self.navigate,
        )
        self._panels["extraction"] = _make(
            ExtractionPanel, db=self._db,
            on_navigate=self.navigate,
        )
        self._panels["export"] = _make(
            ExportPanel, db=self._db,
        )
        self._panels["history"] = _make(
            HistoryPanel, db=self._db,
        )
        self._panels["settings"] = _make(
            SettingsPanel, db=self._db,
            on_logout=self._on_logout,
        )
        self._panels["about"] = _make(AboutPanel)

    # ─── Navigation ──────────────────────────────────────────────────────────
    def navigate(self, page_key: str):
        if self._current_page == page_key:
            return

        # Hide all
        for panel in self._panels.values():
            panel.place_forget()

        # Show selected
        panel = self._panels.get(page_key)
        if panel:
            panel.place(relx=0, rely=0, relwidth=1, relheight=1)
            panel.lift()
            self._current_page = page_key

        # Update sidebar active state
        for k, btn in self._sidebar_btns.items():
            btn.set_active(k == page_key)

        # Refresh on navigate
        if page_key == "history":
            self._panels["history"].refresh()
        elif page_key == "dashboard":
            self._panels["dashboard"].refresh()
        elif page_key == "export":
            if hasattr(self._panels.get("export"), "refresh"):
                self._panels["export"].refresh()

    # ─── Session check ───────────────────────────────────────────────────────
    def _check_existing_session(self):
        """Check if a valid Telegram session already exists."""
        acct = self._db.get_active_account()
        if acct and acct.get("api_id"):
            # Try to restore session silently
            def _try_restore():
                try:
                    api_id = int(acct["api_id"])
                    from config import DATA_DIR
                    import json
                    cred_file = DATA_DIR / ".creds.json"
                    # We only have api_id stored (not hash for security)
                    # Session file may still be valid; let LoginPanel handle it
                except Exception:
                    pass
                self.after(0, lambda: self.navigate("connect"))
            threading.Thread(target=_try_restore, daemon=True).start()
        else:
            self.navigate("connect")

    def _on_login_success(self):
        """Called after successful Telegram authentication."""
        def _fetch_and_save():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                wrapper = get_client_wrapper()
                me = loop.run_until_complete(wrapper.get_me())
                if me:
                    phone = getattr(me, "phone", "") or ""
                    from utils.helpers import safe_str
                    self._db.save_account(
                        phone=f"+{phone}" if phone and not phone.startswith("+") else (phone or "unknown"),
                        first_name=safe_str(getattr(me, "first_name", "")),
                        last_name=safe_str(getattr(me, "last_name", "")),
                        username=safe_str(getattr(me, "username", "")),
                        user_id=me.id,
                        api_id=str(getattr(wrapper, "_api_id", "")),
                    )
                    name = (getattr(me, "first_name", "") or "").strip()
                    self.after(0, lambda: self._status_badge.set_connected(name))
            except Exception as e:
                log.error("Could not fetch self info: %s", e)
            finally:
                loop.close()
        threading.Thread(target=_fetch_and_save, daemon=True).start()
        self.navigate("dashboard")

    def _on_logout(self):
        self._status_badge.set_disconnected()
        self.navigate("connect")


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
