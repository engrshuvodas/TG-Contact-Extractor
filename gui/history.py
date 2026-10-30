"""History panel — past extraction records."""
import sys
from pathlib import Path
import customtkinter as ctk

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import THEME as T
from gui.components import make_card, make_label, make_button, Separator


class HistoryPanel(ctk.CTkFrame):

    def __init__(self, parent, db, **kwargs):
        super().__init__(parent, fg_color=T["bg_primary"], **kwargs)
        self.db = db
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=30, pady=(28,0))
        make_label(hdr, "📋  Extraction History", style="h1").pack(side="left")
        make_button(hdr, "🔄 Refresh", style="secondary",
                    command=self.refresh, height=36, width=110).pack(side="right")

        make_label(self, "Past extraction sessions and their results.",
                   style="small").pack(anchor="w", padx=30, pady=(4,16))
        Separator(self).pack(fill="x", padx=30, pady=(0,16))

        self._scroll = ctk.CTkScrollableFrame(self, fg_color=T["bg_primary"],
                                               scrollbar_button_color=T["bg_hover"],
                                               scrollbar_button_hover_color=T["accent_blue"])
        self._scroll.pack(fill="both", expand=True, padx=30, pady=(0,20))

    def refresh(self):
        for w in self._scroll.winfo_children():
            w.destroy()

        history = self.db.get_history()
        if not history:
            make_label(self._scroll, "No extraction history yet.",
                       style="muted").pack(pady=40)
            return

        for record in history:
            card = make_card(self._scroll)
            card.pack(fill="x", pady=(0,8))
            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="x", padx=16, pady=12)

            left = ctk.CTkFrame(inner, fg_color="transparent")
            left.pack(side="left", fill="x", expand=True)

            status = record.get("status","?")
            status_color = {"completed": T["success"], "running": T["warning"],
                            "stopped": T["error"]}.get(status, T["text_muted"])

            row1 = ctk.CTkFrame(left, fg_color="transparent")
            row1.pack(fill="x")
            make_label(row1, f"Session #{record['id']}", style="h3").pack(side="left")
            ctk.CTkLabel(row1, text=status.upper(),
                         font=(T["font_family"], T["font_size_xs"], "bold"),
                         text_color=status_color,
                         fg_color=T["bg_input"],
                         corner_radius=4, width=80, height=20).pack(side="right")

            make_label(left, f"Account: {record.get('account_phone','?')}",
                       style="small").pack(anchor="w", pady=(2,0))
            make_label(left, f"Started: {record.get('started_at','?')}  |  "
                             f"Finished: {record.get('finished_at','N/A')}  |  "
                             f"Found: {record.get('total_found',0)} users",
                       style="muted").pack(anchor="w")
