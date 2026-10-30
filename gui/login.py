"""Telegram login panel — 3-step auth flow."""
import asyncio
import threading
import sys
from pathlib import Path
import customtkinter as ctk

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import THEME as T, TELEGRAM_API_URL, DATA_DIR
from gui.components import (make_card, make_label, make_button,
                             make_entry, Separator)
from core.authentication import AuthManager
from utils.security import load_saved_credentials, save_credentials

import webbrowser

_CRED_FILE = DATA_DIR / ".creds.json"


class LoginPanel(ctk.CTkFrame):
    """Handles the full 3-step Telegram login flow."""

    def __init__(self, parent, on_login_success=None, **kwargs):
        super().__init__(parent, fg_color=T["bg_primary"], **kwargs)
        self._on_success = on_login_success
        self._auth = AuthManager()
        self._loop = None
        self._build_ui()

    def _build_ui(self):
        # Centered container
        container = make_card(self, width=480)
        container.place(relx=0.5, rely=0.5, anchor="center")
        container.pack_propagate(False)
        container.configure(height=620)

        inner = ctk.CTkFrame(container, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=36, pady=32)

        # Logo / Title
        make_label(inner, "✈", style="title").pack(anchor="center")
        make_label(inner, "TG Contact Extractor", style="h1").pack(anchor="center", pady=(2,4))
        make_label(inner, "Connect your Telegram account to begin",
                   style="small").pack(anchor="center", pady=(0,20))

        Separator(inner).pack(fill="x", pady=(0, 20))

        # ── Step 1 frame ──────────────────────────────────────────────────
        self._step1_frame = ctk.CTkFrame(inner, fg_color="transparent")
        self._step1_frame.pack(fill="x")

        make_label(self._step1_frame, "Step 1 — Enter Credentials", style="h3").pack(anchor="w", pady=(0,12))

        # API link
        link_row = ctk.CTkFrame(self._step1_frame, fg_color="transparent")
        link_row.pack(fill="x", pady=(0,8))
        make_label(link_row, "Get your API ID & Hash:", style="small").pack(side="left")
        ctk.CTkButton(link_row, text="my.telegram.org/apps →",
                      fg_color="transparent", hover_color=T["bg_hover"],
                      text_color=T["accent_blue"],
                      font=(T["font_family"], T["font_size_sm"], "bold"),
                      height=24, width=180,
                      command=lambda: webbrowser.open(TELEGRAM_API_URL)
                      ).pack(side="left", padx=4)

        make_label(self._step1_frame, "API ID", style="small").pack(anchor="w", pady=(4,2))
        self._api_id_entry = make_entry(self._step1_frame, placeholder="e.g. 12345678")
        self._api_id_entry.pack(fill="x", pady=(0,8))

        make_label(self._step1_frame, "API Hash", style="small").pack(anchor="w", pady=(0,2))
        self._api_hash_entry = make_entry(self._step1_frame, placeholder="32-character hex string")
        self._api_hash_entry.pack(fill="x", pady=(0,8))

        make_label(self._step1_frame, "Phone Number (with country code)", style="small").pack(anchor="w", pady=(0,2))
        self._phone_entry = make_entry(self._step1_frame, placeholder="+1 234 567 8901")
        self._phone_entry.pack(fill="x", pady=(0,16))

        self._send_code_btn = make_button(self._step1_frame, "Send Login Code",
                                          style="primary", command=self._on_send_code)
        self._send_code_btn.pack(fill="x")

        # Load saved api_id hint
        saved = load_saved_credentials(_CRED_FILE)
        if saved.get("api_id"):
            self._api_id_entry.insert(0, saved["api_id"])

        # ── Step 2 frame ──────────────────────────────────────────────────
        self._step2_frame = ctk.CTkFrame(inner, fg_color="transparent")

        make_label(self._step2_frame, "Step 2 — Enter Verification Code", style="h3").pack(anchor="w", pady=(0,8))
        make_label(self._step2_frame,
                   "A code was sent via Telegram or SMS to your phone.",
                   style="small").pack(anchor="w", pady=(0,12))

        make_label(self._step2_frame, "Verification Code", style="small").pack(anchor="w", pady=(0,2))
        self._code_entry = make_entry(self._step2_frame, placeholder="Enter 5-digit code")
        self._code_entry.pack(fill="x", pady=(0,12))

        self._verify_btn = make_button(self._step2_frame, "Verify Code",
                                       style="primary", command=self._on_verify_code)
        self._verify_btn.pack(fill="x", pady=(0,8))

        make_button(self._step2_frame, "← Back", style="ghost",
                    command=self._go_to_step1).pack(fill="x")

        # ── Step 3 frame (2FA) ────────────────────────────────────────────
        self._step3_frame = ctk.CTkFrame(inner, fg_color="transparent")

        make_label(self._step3_frame, "Step 3 — Two-Step Verification", style="h3").pack(anchor="w", pady=(0,8))
        make_label(self._step3_frame,
                   "Your account has 2FA enabled. Enter your password.",
                   style="small").pack(anchor="w", pady=(0,12))

        make_label(self._step3_frame, "2FA Password", style="small").pack(anchor="w", pady=(0,2))
        self._password_entry = make_entry(self._step3_frame,
                                          placeholder="Your 2FA password",
                                          show="●")
        self._password_entry.pack(fill="x", pady=(0,12))

        self._twofa_btn = make_button(self._step3_frame, "Verify Password",
                                      style="primary", command=self._on_verify_2fa)
        self._twofa_btn.pack(fill="x")

        # ── Status / error ────────────────────────────────────────────────
        self._status_label = make_label(inner, "", style="small")
        self._status_label.pack(pady=(16, 0))

    # ─── Navigation ─────────────────────────────────────────────────────────
    def _go_to_step1(self):
        self._step2_frame.pack_forget()
        self._step3_frame.pack_forget()
        self._step1_frame.pack(fill="x")
        self._set_status("", "info")

    def _go_to_step2(self):
        self._step1_frame.pack_forget()
        self._step3_frame.pack_forget()
        self._step2_frame.pack(fill="x")
        self._set_status("Code sent! Check Telegram or SMS.", "success")

    def _go_to_step3(self):
        self._step1_frame.pack_forget()
        self._step2_frame.pack_forget()
        self._step3_frame.pack(fill="x")
        self._set_status("Please enter your 2FA password.", "info")

    # ─── Actions ────────────────────────────────────────────────────────────
    def _run_async(self, coro, callback):
        """Run a coroutine on the persistent Telegram event loop and invoke callback with result."""
        from core.telegram_client import get_async_loop_manager
        future = get_async_loop_manager().run_coro(coro)

        def _on_future_done(fut):
            try:
                res = fut.result()
            except Exception as exc:
                res = {"ok": False, "error": str(exc)}
            self.after(0, lambda: callback(res))

        future.add_done_callback(_on_future_done)

    def _on_send_code(self):
        api_id   = self._api_id_entry.get().strip()
        api_hash = self._api_hash_entry.get().strip()
        phone    = self._phone_entry.get().strip()

        if not all([api_id, api_hash, phone]):
            self._set_status("Please fill in all fields.", "error")
            return

        self._send_code_btn.configure(state="disabled", text="Sending…")
        self._set_status("Connecting to Telegram…", "info")

        self._run_async(
            self._auth.start_login(api_id, api_hash, phone),
            self._on_code_sent
        )

    def _on_code_sent(self, result: dict):
        self._send_code_btn.configure(state="normal", text="Send Login Code")
        if not result["ok"]:
            self._set_status(result["error"], "error")
            return

        # Save api_id hint (NOT api_hash)
        save_credentials(_CRED_FILE, self._api_id_entry.get().strip())

        if result.get("already_logged_in"):
            self._set_status("Already logged in!", "success")
            self.after(800, lambda: self._finalize_login())
        else:
            self._go_to_step2()

    def _on_verify_code(self):
        code = self._code_entry.get().strip()
        if not code:
            self._set_status("Please enter the code.", "error")
            return
        self._verify_btn.configure(state="disabled", text="Verifying…")
        self._set_status("Verifying code…", "info")
        self._run_async(self._auth.verify_code(code), self._on_code_verified)

    def _on_code_verified(self, result: dict):
        self._verify_btn.configure(state="normal", text="Verify Code")
        if not result["ok"]:
            self._set_status(result["error"], "error")
            return
        if result.get("needs_2fa"):
            self._go_to_step3()
        else:
            self._finalize_login()

    def _on_verify_2fa(self):
        pwd = self._password_entry.get()
        if not pwd:
            self._set_status("Please enter your 2FA password.", "error")
            return
        self._twofa_btn.configure(state="disabled", text="Verifying…")
        self._run_async(self._auth.verify_2fa(pwd), self._on_2fa_verified)

    def _on_2fa_verified(self, result: dict):
        self._twofa_btn.configure(state="normal", text="Verify Password")
        if not result["ok"]:
            self._set_status(result["error"], "error")
            return
        self._finalize_login()

    def _finalize_login(self):
        self._set_status("Login successful! Loading dashboard…", "success")
        if self._on_success:
            self.after(600, self._on_success)

    def _set_status(self, msg: str, level: str = "info"):
        colors = {
            "info":    T["info"],
            "success": T["success"],
            "error":   T["error"],
            "warning": T["warning"],
        }
        self._status_label.configure(
            text=msg,
            text_color=colors.get(level, T["text_secondary"])
        )
