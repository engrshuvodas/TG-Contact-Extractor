"""Extraction panel — live progress and control."""
import asyncio
import threading
import sys
from pathlib import Path
import customtkinter as ctk

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import THEME as T
from gui.components import (make_card, make_label, make_button,
                             StatCard, Separator)
from core.extractor import ContactExtractor
from core.telegram_client import get_client_wrapper


class ExtractionPanel(ctk.CTkFrame):

    def __init__(self, parent, db, on_navigate=None, **kwargs):
        super().__init__(parent, fg_color=T["bg_primary"], **kwargs)
        self.db = db
        self._on_navigate = on_navigate
        self._extractor: ContactExtractor = None
        self._thread: threading.Thread = None
        self._stat_cards = {}
        self._log_lines = []
        self._build_ui()

    def _build_ui(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color=T["bg_primary"],
                                         scrollbar_button_color=T["bg_hover"],
                                         scrollbar_button_hover_color=T["accent_blue"])
        scroll.pack(fill="both", expand=True)

        # Header
        hdr = ctk.CTkFrame(scroll, fg_color="transparent")
        hdr.pack(fill="x", padx=30, pady=(28, 0))
        make_label(hdr, "⚡  Extract Contacts", style="h1").pack(side="left")

        make_label(scroll, "Scan your private Telegram conversations for contact data.",
                   style="small").pack(anchor="w", padx=30, pady=(4, 20))

        Separator(scroll).pack(fill="x", padx=30, pady=(0, 20))

        # ── Control buttons ─────────────────────────────────────────────
        ctrl = ctk.CTkFrame(scroll, fg_color="transparent")
        ctrl.pack(fill="x", padx=30, pady=(0, 16))

        self._start_btn = make_button(ctrl, "▶  Start Extraction", style="success",
                                      command=self._start, width=180)
        self._start_btn.pack(side="left", padx=(0,8))

        self._pause_btn = make_button(ctrl, "⏸  Pause", style="secondary",
                                      command=self._pause, width=120, state="disabled")
        self._pause_btn.pack(side="left", padx=(0,8))

        self._resume_btn = make_button(ctrl, "▶  Resume", style="primary",
                                       command=self._resume, width=120, state="disabled")
        self._resume_btn.pack(side="left", padx=(0,8))

        self._stop_btn = make_button(ctrl, "⏹  Stop", style="danger",
                                     command=self._stop, width=120, state="disabled")
        self._stop_btn.pack(side="left")

        # ── Progress ─────────────────────────────────────────────────────
        prog_card = make_card(scroll)
        prog_card.pack(fill="x", padx=30, pady=(0, 16))
        prog_inner = ctk.CTkFrame(prog_card, fg_color="transparent")
        prog_inner.pack(fill="x", padx=20, pady=16)

        status_row = ctk.CTkFrame(prog_inner, fg_color="transparent")
        status_row.pack(fill="x")
        self._status_label = make_label(status_row, "Ready to extract.", style="body")
        self._status_label.pack(side="left")
        self._count_label  = make_label(status_row, "", style="small")
        self._count_label.pack(side="right")

        self._progress = ctk.CTkProgressBar(prog_inner,
                                             fg_color=T["bg_input"],
                                             progress_color=T["accent_blue"],
                                             corner_radius=4, height=8)
        self._progress.pack(fill="x", pady=(10,0))
        self._progress.set(0)

        # ── Live stats grid ───────────────────────────────────────────────
        make_label(scroll, "Live Statistics", style="h2").pack(anchor="w", padx=30, pady=(8,12))

        grid = ctk.CTkFrame(scroll, fg_color="transparent")
        grid.pack(fill="x", padx=30, pady=(0, 16))
        grid.columnconfigure((0,1,2,3), weight=1, uniform="col")

        stat_defs = [
            ("total",            "👥", "Total Found",          T["accent_blue"]),
            ("with_username",    "🔖", "With Username",         T["success"]),
            ("with_phone",       "📞", "With Phone",            T["success"]),
            ("saved_contacts",   "💾", "Saved Contacts",        T["accent_purple"]),
            ("without_username", "🚫", "Without Username",      T["warning"]),
            ("without_phone",    "🔇", "Without Phone",         T["error"]),
            ("non_saved",        "👤", "Non-Saved",             T["info"]),
            ("failed",           "❌", "Failed Records",        T["error"]),
        ]
        for idx, (key, icon, label, color) in enumerate(stat_defs):
            card = StatCard(grid, icon=icon, label=label, color=color)
            card.grid(row=idx//4, column=idx%4, padx=6, pady=6, sticky="nsew")
            self._stat_cards[key] = card

        # ── Activity log ─────────────────────────────────────────────────
        Separator(scroll).pack(fill="x", padx=30, pady=(8, 16))
        make_label(scroll, "Activity Log", style="h2").pack(anchor="w", padx=30, pady=(0,8))

        log_card = make_card(scroll)
        log_card.pack(fill="x", padx=30, pady=(0, 30))

        self._log_box = ctk.CTkTextbox(log_card,
                                        fg_color=T["bg_input"],
                                        text_color=T["text_secondary"],
                                        font=(T["font_family"], T["font_size_sm"]),
                                        height=200,
                                        border_width=0,
                                        wrap="none")
        self._log_box.pack(fill="x", padx=16, pady=16)
        self._log_box.configure(state="disabled")

    # ─── Async bridge ───────────────────────────────────────────────────────
    def _start(self):
        wrapper = get_client_wrapper()
        if not wrapper.is_connected:
            self._set_status("Not connected. Please connect first.", "error")
            return

        self._extractor = ContactExtractor(self.db)
        self._start_btn.configure(state="disabled")
        self._pause_btn.configure(state="normal")
        self._stop_btn.configure(state="normal")
        self._resume_btn.configure(state="disabled")
        self._progress.set(0)
        self._log_lines = []
        self._clear_log()
        self._append_log("Starting extraction…")

        self._thread = threading.Thread(target=self._run_extraction, daemon=True)
        self._thread.start()

    def _run_extraction(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(
                self._extractor.extract(
                    on_progress=self._on_progress,
                    on_user_found=self._on_user_found,
                )
            )
        finally:
            loop.close()
            self.after(0, self._on_extraction_done)

    def _on_progress(self, msg, stats):
        self.after(0, lambda: self._update_ui(msg, stats))

    def _on_user_found(self, user_dict):
        name = user_dict.get("full_name", "User")
        self.after(0, lambda: self._append_log(f"✓ {name}"))

    def _on_extraction_done(self):
        self._start_btn.configure(state="normal")
        self._pause_btn.configure(state="disabled")
        self._resume_btn.configure(state="disabled")
        self._stop_btn.configure(state="disabled")
        if self._extractor:
            stats = self._extractor.stats
            self._append_log(f"\nExtraction complete. Found {stats.total_users} users.")
            self._progress.set(1.0)

    def _update_ui(self, msg: str, stats):
        self._set_status(msg)
        self._count_label.configure(text=f"Processed: {stats.processed}")
        self._append_log(msg)
        self._stat_cards["total"].update_value(stats.total_users)
        self._stat_cards["with_username"].update_value(stats.with_username)
        self._stat_cards["with_phone"].update_value(stats.with_phone)
        self._stat_cards["saved_contacts"].update_value(stats.saved_contacts)
        self._stat_cards["without_username"].update_value(stats.without_username)
        self._stat_cards["without_phone"].update_value(stats.without_phone)
        self._stat_cards["non_saved"].update_value(stats.non_saved)
        self._stat_cards["failed"].update_value(stats.failed)

        # Pulse progress bar (indeterminate style)
        cur = self._progress.get()
        new_val = (cur + 0.01) % 1.0
        self._progress.set(new_val)

    # ─── Controls ───────────────────────────────────────────────────────────
    def _pause(self):
        if self._extractor:
            self._extractor.pause()
            self._pause_btn.configure(state="disabled")
            self._resume_btn.configure(state="normal")
            self._set_status("Paused.")

    def _resume(self):
        if self._extractor:
            self._extractor.resume()
            self._resume_btn.configure(state="disabled")
            self._pause_btn.configure(state="normal")
            self._set_status("Resumed.")

    def _stop(self):
        if self._extractor:
            self._extractor.stop()
            self._set_status("Stopping…")

    # ─── Helpers ────────────────────────────────────────────────────────────
    def _set_status(self, msg: str, level: str = "info"):
        colors = {"info": T["info"], "success": T["success"],
                  "error": T["error"], "warning": T["warning"]}
        self._status_label.configure(text=msg,
                                      text_color=colors.get(level, T["text_secondary"]))

    def _append_log(self, text: str):
        self._log_box.configure(state="normal")
        self._log_lines.append(text)
        if len(self._log_lines) > 200:
            self._log_lines = self._log_lines[-200:]
        self._log_box.delete("1.0", "end")
        self._log_box.insert("end", "\n".join(self._log_lines))
        self._log_box.see("end")
        self._log_box.configure(state="disabled")

    def _clear_log(self):
        self._log_box.configure(state="normal")
        self._log_box.delete("1.0", "end")
        self._log_box.configure(state="disabled")
