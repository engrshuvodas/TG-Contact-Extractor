"""Dashboard page — KPI stats overview."""
import sys
from pathlib import Path
import customtkinter as ctk

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import THEME as T
from gui.components import make_card, make_label, make_button, StatCard, Separator


class DashboardPanel(ctk.CTkFrame):
    """Main dashboard showing extraction statistics."""

    def __init__(self, parent, db, on_navigate=None, **kwargs):
        super().__init__(parent, fg_color=T["bg_primary"], **kwargs)
        self.db = db
        self._on_navigate = on_navigate
        self._stat_cards = {}
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        # Scrollable container
        scroll = ctk.CTkScrollableFrame(self, fg_color=T["bg_primary"],
                                         scrollbar_button_color=T["bg_hover"],
                                         scrollbar_button_hover_color=T["accent_blue"])
        scroll.pack(fill="both", expand=True)

        # ── Header ──────────────────────────────────────────────────────────
        header = ctk.CTkFrame(scroll, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(28, 0))

        make_label(header, "📊  Dashboard", style="h1").pack(side="left")

        btn_row = ctk.CTkFrame(header, fg_color="transparent")
        btn_row.pack(side="right")
        make_button(btn_row, "🔄  Refresh", style="secondary",
                    command=self.refresh, height=36, width=110).pack(side="left", padx=4)
        make_button(btn_row, "⚡  Start Extraction", style="primary",
                    command=lambda: self._on_navigate("extraction") if self._on_navigate else None,
                    height=36, width=160).pack(side="left")

        make_label(scroll,
                   "Overview of your Telegram contact extraction",
                   style="small").pack(anchor="w", padx=30, pady=(4, 20))

        Separator(scroll).pack(fill="x", padx=30, pady=(0, 24))

        # ── Account info card ────────────────────────────────────────────
        acct_card = make_card(scroll)
        acct_card.pack(fill="x", padx=30, pady=(0, 20))

        acct_inner = ctk.CTkFrame(acct_card, fg_color="transparent")
        acct_inner.pack(fill="x", padx=20, pady=16)

        make_label(acct_inner, "Connected Account", style="h3").pack(anchor="w")
        self._acct_label = make_label(acct_inner, "Not connected", style="small")
        self._acct_label.pack(anchor="w", pady=(4, 0))

        # ── Stat grid ────────────────────────────────────────────────────
        make_label(scroll, "Extraction Statistics", style="h2").pack(
            anchor="w", padx=30, pady=(0, 12))

        grid = ctk.CTkFrame(scroll, fg_color="transparent")
        grid.pack(fill="x", padx=30, pady=(0, 20))
        grid.columnconfigure((0,1,2,3), weight=1, uniform="col")

        stat_defs = [
            ("total",            "👥",  "Total Users Found",      T["accent_blue"]),
            ("with_username",    "🔖",  "With Username",           T["success"]),
            ("without_username", "🚫",  "Without Username",        T["warning"]),
            ("with_phone",       "📞",  "With Phone Number",       T["success"]),
            ("without_phone",    "🔇",  "Without Phone",           T["error"]),
            ("saved_contacts",   "💾",  "Saved Contacts",          T["accent_purple"]),
            ("non_saved",        "👤",  "Non-Saved Users",         T["info"]),
            ("archived",         "🗂",  "Archived Chats Scanned",  T["text_secondary"]),
        ]

        for idx, (key, icon, label, color) in enumerate(stat_defs):
            card = StatCard(grid, icon=icon, label=label, color=color)
            card.grid(row=idx//4, column=idx%4, padx=6, pady=6, sticky="nsew")
            self._stat_cards[key] = card

        # ── Quick actions ────────────────────────────────────────────────
        Separator(scroll).pack(fill="x", padx=30, pady=(8, 20))
        make_label(scroll, "Quick Actions", style="h2").pack(anchor="w", padx=30, pady=(0,12))

        actions_row = ctk.CTkFrame(scroll, fg_color="transparent")
        actions_row.pack(fill="x", padx=30, pady=(0, 20))

        actions = [
            ("⚡ Start Extraction",  "primary",   "extraction"),
            ("📤 Export Data",       "purple",    "export"),
            ("📋 View History",      "secondary", "history"),
            ("⚙ Settings",          "secondary", "settings"),
        ]
        for text, style, page in actions:
            make_button(actions_row, text, style=style,
                        command=lambda p=page: self._on_navigate(p) if self._on_navigate else None,
                        width=160, height=42).pack(side="left", padx=(0,10))

        # ── Last extraction info ─────────────────────────────────────────
        info_card = make_card(scroll)
        info_card.pack(fill="x", padx=30, pady=(0, 30))
        info_inner = ctk.CTkFrame(info_card, fg_color="transparent")
        info_inner.pack(fill="x", padx=20, pady=16)
        make_label(info_inner, "ℹ  Important Note", style="h3").pack(anchor="w")
        make_label(info_inner,
                   "TG Contact Extractor only extracts users from your private one-to-one "
                   "conversations using the official Telegram API.\n"
                   "It respects Telegram's privacy settings and never attempts to bypass restrictions.\n"
                   "All data is stored locally on your computer.",
                   style="small",
                   wraplength=700,
                   justify="left").pack(anchor="w", pady=(8,0))

    def refresh(self):
        """Pull latest stats from DB and update cards."""
        try:
            stats = self.db.get_stats()
            self._stat_cards["total"].update_value(stats["total"])
            self._stat_cards["with_username"].update_value(stats["with_username"])
            self._stat_cards["without_username"].update_value(stats["without_username"])
            self._stat_cards["with_phone"].update_value(stats["with_phone"])
            self._stat_cards["without_phone"].update_value(stats["without_phone"])
            self._stat_cards["saved_contacts"].update_value(stats["saved_contacts"])
            self._stat_cards["non_saved"].update_value(stats["non_saved"])
            # Archived not tracked in stats — use history
            history = self.db.get_history()
            if history:
                last = history[0]
                self._stat_cards["archived"].update_value(last.get("total_found", 0))
                acct = last.get("account_phone", "Unknown")
                self._acct_label.configure(text=f"Phone: {acct}")
        except Exception as e:
            pass
