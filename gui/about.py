"""About panel."""
import sys, webbrowser
from pathlib import Path
import customtkinter as ctk

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import THEME as T, APP_VERSION, APP_BUILD, TELEGRAM_API_URL
from gui.components import make_card, make_label, make_button, Separator


class AboutPanel(ctk.CTkFrame):

    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color=T["bg_primary"], **kwargs)
        self._build_ui()

    def _build_ui(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color=T["bg_primary"],
                                         scrollbar_button_color=T["bg_hover"],
                                         scrollbar_button_hover_color=T["accent_blue"])
        scroll.pack(fill="both", expand=True)

        # Header
        make_label(scroll, "ℹ  About", style="h1").pack(anchor="w", padx=30, pady=(28,0))
        Separator(scroll).pack(fill="x", padx=30, pady=(12,24))

        # App info card
        card = make_card(scroll)
        card.pack(fill="x", padx=30, pady=(0,16))
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=30, pady=28)

        make_label(inner, "✈  TG Contact Extractor", style="h1").pack(anchor="center")
        make_label(inner, f"Version {APP_VERSION}  •  Build {APP_BUILD}",
                   style="small").pack(anchor="center", pady=(4,20))

        Separator(inner).pack(fill="x", pady=(0,20))

        info_items = [
            ("What it does",
             "Extracts available user information from your Telegram private conversations "
             "using the official Telegram MTProto API (Telethon library)."),
            ("Privacy",
             "All data is processed and stored locally on your computer.\n"
             "No data is uploaded to any external server. "
             "Session files are stored in the 'sessions/' folder."),
            ("Limitations",
             "Only extracts data that Telegram makes available to the authenticated account.\n"
             "Phone numbers are only visible if the contact shared them with you.\n"
             "Hidden information is never recovered or guessed."),
            ("API Requirements",
             "You need your own Telegram API credentials from my.telegram.org/apps."),
        ]

        for title, body in info_items:
            make_label(inner, f"  {title}", style="h3").pack(anchor="w", pady=(12,4))
            make_label(inner, body, style="small",
                       wraplength=680, justify="left").pack(anchor="w", padx=16)

        Separator(inner).pack(fill="x", pady=(20,12))

        make_button(inner, "🔗  Get Telegram API Credentials",
                    style="primary",
                    command=lambda: webbrowser.open(TELEGRAM_API_URL),
                    height=42, width=280).pack(anchor="center")
