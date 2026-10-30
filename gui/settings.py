"""Settings panel."""
import asyncio
import threading
import sys
from pathlib import Path
import customtkinter as ctk
from tkinter import messagebox, filedialog

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import THEME as T, DB_PATH, EXPORTS_DIR, APP_VERSION, APP_BUILD
from gui.components import make_card, make_label, make_button, Separator
from core.telegram_client import get_client_wrapper


class SettingsPanel(ctk.CTkFrame):

    def __init__(self, parent, db, on_logout=None, **kwargs):
        super().__init__(parent, fg_color=T["bg_primary"], **kwargs)
        self.db = db
        self._on_logout = on_logout
        self._build_ui()

    def _build_ui(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color=T["bg_primary"],
                                         scrollbar_button_color=T["bg_hover"],
                                         scrollbar_button_hover_color=T["accent_blue"])
        scroll.pack(fill="both", expand=True)

        make_label(scroll, "⚙  Settings", style="h1").pack(anchor="w", padx=30, pady=(28,0))
        make_label(scroll, "Manage your application preferences and account.",
                   style="small").pack(anchor="w", padx=30, pady=(4,20))
        Separator(scroll).pack(fill="x", padx=30, pady=(0,20))

        # ── Account ──────────────────────────────────────────────────────
        self._section(scroll, "👤 Account")
        acct_card = make_card(scroll)
        acct_card.pack(fill="x", padx=30, pady=(0,16))
        acct_inner = ctk.CTkFrame(acct_card, fg_color="transparent")
        acct_inner.pack(fill="x", padx=20, pady=16)

        self._acct_info = make_label(acct_inner, self._get_account_info(), style="small")
        self._acct_info.pack(anchor="w", pady=(0,12))

        btn_row = ctk.CTkFrame(acct_inner, fg_color="transparent")
        btn_row.pack(fill="x")
        make_button(btn_row, "🔓 Disconnect Account", style="secondary",
                    command=self._disconnect, width=200, height=38).pack(side="left", padx=(0,8))
        make_button(btn_row, "🚪 Logout & Delete Session", style="danger",
                    command=self._logout, width=220, height=38).pack(side="left")

        # ── Database ─────────────────────────────────────────────────────
        self._section(scroll, "🗄 Database")
        db_card = make_card(scroll)
        db_card.pack(fill="x", padx=30, pady=(0,16))
        db_inner = ctk.CTkFrame(db_card, fg_color="transparent")
        db_inner.pack(fill="x", padx=20, pady=16)

        make_label(db_inner, f"Database path:  {DB_PATH}", style="small").pack(anchor="w", pady=(0,8))
        make_label(db_inner, f"Records:  {self.db.get_user_count()}", style="small").pack(anchor="w", pady=(0,12))

        db_btn_row = ctk.CTkFrame(db_inner, fg_color="transparent")
        db_btn_row.pack(fill="x")
        make_button(db_btn_row, "🗑 Clear All Data", style="danger",
                    command=self._clear_db, width=180, height=38).pack(side="left")

        # ── Export ───────────────────────────────────────────────────────
        self._section(scroll, "📁 Export Folder")
        exp_card = make_card(scroll)
        exp_card.pack(fill="x", padx=30, pady=(0,16))
        exp_inner = ctk.CTkFrame(exp_card, fg_color="transparent")
        exp_inner.pack(fill="x", padx=20, pady=16)

        saved_dir = self.db.get_setting("export_dir", str(EXPORTS_DIR))
        self._export_dir_label = make_label(exp_inner, f"Current: {saved_dir}", style="small")
        self._export_dir_label.pack(anchor="w", pady=(0,8))
        make_button(exp_inner, "📂 Change Folder", style="secondary",
                    command=self._change_export_dir, width=180, height=38).pack(anchor="w")

        # ── About ─────────────────────────────────────────────────────────
        self._section(scroll, "ℹ About")
        about_card = make_card(scroll)
        about_card.pack(fill="x", padx=30, pady=(0,30))
        about_inner = ctk.CTkFrame(about_card, fg_color="transparent")
        about_inner.pack(fill="x", padx=20, pady=16)

        make_label(about_inner, "TG Contact Extractor", style="h3").pack(anchor="w")
        make_label(about_inner, f"Version: {APP_VERSION}  |  Build: {APP_BUILD}", style="small").pack(anchor="w", pady=(4,0))
        make_label(about_inner,
                   "A professional tool to extract and export contact information from\n"
                   "your Telegram private conversations. Uses official Telegram API only.",
                   style="small", wraplength=600, justify="left").pack(anchor="w", pady=(8,0))

        # Status label
        self._status = make_label(scroll, "", style="small")
        self._status.pack(anchor="w", padx=30, pady=(0,12))

    def _section(self, parent, title):
        make_label(parent, title, style="h2").pack(anchor="w", padx=30, pady=(8,8))

    def _get_account_info(self) -> str:
        acct = self.db.get_active_account()
        if acct:
            name = " ".join(filter(None, [acct.get("first_name"), acct.get("last_name")])) or "Unknown"
            phone = acct.get("phone", "Unknown")
            return f"Connected as: {name}  |  Phone: {phone}"
        return "Not connected."

    def _disconnect(self):
        if not messagebox.askyesno("Disconnect",
                "Disconnect your account?\nYour session will remain valid for future use."):
            return
        def _do():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(get_client_wrapper().disconnect())
            finally:
                loop.close()
        threading.Thread(target=_do, daemon=True).start()
        self._set_status("Disconnected.", "success")

    def _logout(self):
        if not messagebox.askyesno("Logout",
                "Logout and delete your session file?\nYou will need to log in again next time.",
                icon="warning"):
            return
        def _do():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(get_client_wrapper().logout())
            finally:
                loop.close()
            acct = self.db.get_active_account()
            if acct:
                self.db.deactivate_account(acct["phone"])
            self.after(0, lambda: self._on_logout() if self._on_logout else None)
        threading.Thread(target=_do, daemon=True).start()
        self._set_status("Logging out…", "info")

    def _clear_db(self):
        count = self.db.get_user_count()
        if not messagebox.askyesno("Clear Database",
                f"This will permanently delete all {count} extracted users.\nAre you sure?",
                icon="warning"):
            return
        self.db.clear_users()
        self._set_status(f"Cleared {count} records.", "success")

    def _change_export_dir(self):
        current = self.db.get_setting("export_dir", str(EXPORTS_DIR))
        path = filedialog.askdirectory(title="Select export folder", initialdir=current)
        if path:
            self.db.set_setting("export_dir", path)
            self._export_dir_label.configure(text=f"Current: {path}")
            self._set_status("Export folder updated.", "success")

    def _set_status(self, msg, level="info"):
        colors = {"info":T["info"],"success":T["success"],"error":T["error"],"warning":T["warning"]}
        self._status.configure(text=msg, text_color=colors.get(level, T["text_secondary"]))
