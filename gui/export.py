"""Export panel — Excel/CSV export with filter options."""
import sys
import threading
from pathlib import Path
import customtkinter as ctk
from tkinter import filedialog, messagebox

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import THEME as T, EXPORT_FILTERS, EXPORTS_DIR
from gui.components import make_card, make_label, make_button, Separator
from core.export_manager import ExportManager


class ExportPanel(ctk.CTkFrame):

    def __init__(self, parent, db, **kwargs):
        super().__init__(parent, fg_color=T["bg_primary"], **kwargs)
        self.db = db
        self._export_mgr = ExportManager()
        self._selected_filter = "all"
        self._dest_dir = Path(EXPORTS_DIR)
        self._filter_btns = {}
        self._count_label = None
        self._status_label = None
        self._dest_entry = None
        self._build_ui()

    def _build_ui(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color=T["bg_primary"],
                                         scrollbar_button_color=T["bg_hover"],
                                         scrollbar_button_hover_color=T["accent_blue"])
        scroll.pack(fill="both", expand=True)

        # Header
        hdr = ctk.CTkFrame(scroll, fg_color="transparent")
        hdr.pack(fill="x", padx=30, pady=(28,0))
        make_label(hdr, "📤  Export Data", style="h1").pack(side="left")

        make_label(scroll, "Export extracted contacts to Excel or CSV.",
                   style="small").pack(anchor="w", padx=30, pady=(4,20))

        Separator(scroll).pack(fill="x", padx=30, pady=(0,20))

        # ── Export destination ────────────────────────────────────────────
        dest_card = make_card(scroll)
        dest_card.pack(fill="x", padx=30, pady=(0,16))
        dest_inner = ctk.CTkFrame(dest_card, fg_color="transparent")
        dest_inner.pack(fill="x", padx=20, pady=16)

        make_label(dest_inner, "Export Destination Folder", style="h3").pack(anchor="w", pady=(0,8))
        dest_row = ctk.CTkFrame(dest_inner, fg_color="transparent")
        dest_row.pack(fill="x")
        self._dest_entry = ctk.CTkEntry(dest_row,
                                         fg_color=T["bg_input"], border_color=T["border"],
                                         text_color=T["text_primary"],
                                         font=(T["font_family"], T["font_size_sm"]),
                                         height=38)
        self._dest_entry.pack(side="left", fill="x", expand=True, padx=(0,8))
        self._dest_entry.insert(0, str(self._dest_dir))
        make_button(dest_row, "Browse…", style="secondary",
                    command=self._browse_dest, height=38, width=100).pack(side="right")

        # ── Filter selection ──────────────────────────────────────────────
        filter_card = make_card(scroll)
        filter_card.pack(fill="x", padx=30, pady=(0,16))
        filter_inner = ctk.CTkFrame(filter_card, fg_color="transparent")
        filter_inner.pack(fill="x", padx=20, pady=16)

        make_label(filter_inner, "Select Export Filter", style="h3").pack(anchor="w", pady=(0,12))

        grid = ctk.CTkFrame(filter_inner, fg_color="transparent")
        grid.pack(fill="x")

        for idx, (key, label) in enumerate(EXPORT_FILTERS):
            btn = make_button(grid, label, style="secondary",
                              height=38, width=220,
                              command=lambda k=key: self._select_filter(k))
            btn.grid(row=idx//2, column=idx%2, padx=6, pady=4, sticky="w")
            self._filter_btns[key] = btn

        # ── Record count ──────────────────────────────────────────────────
        count_card = make_card(scroll)
        count_card.pack(fill="x", padx=30, pady=(0,16))
        count_inner = ctk.CTkFrame(count_card, fg_color="transparent")
        count_inner.pack(fill="x", padx=20, pady=16)
        make_label(count_inner, "Records to Export", style="h3").pack(anchor="w", pady=(0,4))
        self._count_label = make_label(count_inner, "0 records selected", style="small")
        self._count_label.pack(anchor="w")

        # Initialize filter selection and record count
        self._select_filter("all")

        # ── Export buttons ────────────────────────────────────────────────
        Separator(scroll).pack(fill="x", padx=30, pady=(8,16))
        make_label(scroll, "Choose Export Format", style="h2").pack(anchor="w", padx=30, pady=(0,12))

        btn_row = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_row.pack(fill="x", padx=30, pady=(0,16))

        make_button(btn_row, "📊  Export as Excel (.xlsx)", style="success",
                    command=lambda: self._export("xlsx"),
                    height=48, width=240).pack(side="left", padx=(0,12))
        make_button(btn_row, "📄  Export as CSV (.csv)", style="primary",
                    command=lambda: self._export("csv"),
                    height=48, width=220).pack(side="left")

        # ── Status ────────────────────────────────────────────────────────
        self._status_label = make_label(scroll, "", style="small")
        self._status_label.pack(anchor="w", padx=30, pady=(4,30))

    # ─── Helpers ────────────────────────────────────────────────────────────
    def refresh(self):
        self._update_count()

    def _browse_dest(self):
        path = filedialog.askdirectory(title="Select export folder",
                                        initialdir=str(self._dest_dir))
        if path:
            self._dest_dir = Path(path)
            self._dest_entry.delete(0, "end")
            self._dest_entry.insert(0, str(self._dest_dir))

    def _select_filter(self, key: str):
        self._selected_filter = key
        for k, btn in self._filter_btns.items():
            if k == key:
                btn.configure(fg_color=T["accent_blue"], text_color="white")
            else:
                btn.configure(fg_color=T["bg_hover"], text_color=T["text_secondary"])
        self._update_count()

    def _update_count(self):
        if not getattr(self, "_count_label", None):
            return
        try:
            users = self.db.get_all_users(self._selected_filter)
            self._count_label.configure(text=f"{len(users)} records selected")
        except Exception:
            if getattr(self, "_count_label", None):
                self._count_label.configure(text="0 records selected")

    def _export(self, fmt: str):
        users = self.db.get_all_users(self._selected_filter)
        if not users:
            self._set_status("No records to export for the selected filter.", "warning")
            return

        dest_dir = Path(self._dest_entry.get().strip())
        dest_dir.mkdir(parents=True, exist_ok=True)
        self._export_mgr.export_dir = dest_dir

        def _do_export():
            try:
                if fmt == "xlsx":
                    path = self._export_mgr.export_excel(users)
                else:
                    path = self._export_mgr.export_csv(users)
                self.after(0, lambda: self._set_status(
                    f"Exported {len(users)} records → {path.name}", "success"))
                self.after(0, lambda: messagebox.showinfo(
                    "Export Complete",
                    f"Successfully exported {len(users)} records.\n\nFile: {path}"))
            except Exception as e:
                self.after(0, lambda: self._set_status(f"Export failed: {e}", "error"))

        threading.Thread(target=_do_export, daemon=True).start()
        self._set_status(f"Exporting {len(users)} records…", "info")

    def _set_status(self, msg: str, level: str = "info"):
        if not getattr(self, "_status_label", None):
            return
        colors = {"info": T["info"], "success": T["success"],
                  "error": T["error"], "warning": T["warning"]}
        self._status_label.configure(text=msg,
                                      text_color=colors.get(level, T["text_secondary"]))
