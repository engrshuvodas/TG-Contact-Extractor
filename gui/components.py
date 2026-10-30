"""Reusable UI components."""
import tkinter as tk
import customtkinter as ctk
from typing import Optional, Callable
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import THEME as T


def make_card(parent, **kwargs) -> ctk.CTkFrame:
    defaults = dict(
        fg_color=T["bg_card"],
        corner_radius=T["radius_md"],
        border_width=1,
        border_color=T["border"],
    )
    defaults.update(kwargs)
    return ctk.CTkFrame(parent, **defaults)


def make_label(parent, text: str, style: str = "body", **kwargs) -> ctk.CTkLabel:
    styles = {
        "title":    {"font": (T["font_family"], T["font_size_3xl"], "bold"), "text_color": T["text_primary"]},
        "h1":       {"font": (T["font_family"], T["font_size_2xl"], "bold"), "text_color": T["text_primary"]},
        "h2":       {"font": (T["font_family"], T["font_size_xl"], "bold"), "text_color": T["text_primary"]},
        "h3":       {"font": (T["font_family"], T["font_size_lg"], "bold"), "text_color": T["text_primary"]},
        "body":     {"font": (T["font_family"], T["font_size_md"]),          "text_color": T["text_primary"]},
        "small":    {"font": (T["font_family"], T["font_size_sm"]),          "text_color": T["text_secondary"]},
        "muted":    {"font": (T["font_family"], T["font_size_xs"]),          "text_color": T["text_muted"]},
        "success":  {"font": (T["font_family"], T["font_size_md"]),          "text_color": T["success"]},
        "error":    {"font": (T["font_family"], T["font_size_md"]),          "text_color": T["error"]},
        "warning":  {"font": (T["font_family"], T["font_size_md"]),          "text_color": T["warning"]},
        "info":     {"font": (T["font_family"], T["font_size_md"]),          "text_color": T["info"]},
        "accent":   {"font": (T["font_family"], T["font_size_md"], "bold"),  "text_color": T["accent_blue"]},
    }
    cfg = styles.get(style, styles["body"]).copy()
    cfg.update(kwargs)
    return ctk.CTkLabel(parent, text=text, **cfg)


def make_button(parent, text: str, style: str = "primary", **kwargs) -> ctk.CTkButton:
    styles = {
        "primary": {
            "fg_color": T["accent_blue"], "hover_color": "#2563EB",
            "text_color": "white", "corner_radius": T["radius_md"],
            "font": (T["font_family"], T["font_size_md"], "bold"),
            "height": 40,
        },
        "secondary": {
            "fg_color": T["bg_hover"], "hover_color": T["bg_card"],
            "text_color": T["text_primary"], "corner_radius": T["radius_md"],
            "border_width": 1, "border_color": T["border"],
            "font": (T["font_family"], T["font_size_md"]),
            "height": 40,
        },
        "danger": {
            "fg_color": T["error"], "hover_color": "#DC2626",
            "text_color": "white", "corner_radius": T["radius_md"],
            "font": (T["font_family"], T["font_size_md"], "bold"),
            "height": 40,
        },
        "success": {
            "fg_color": T["success"], "hover_color": "#059669",
            "text_color": "white", "corner_radius": T["radius_md"],
            "font": (T["font_family"], T["font_size_md"], "bold"),
            "height": 40,
        },
        "purple": {
            "fg_color": T["accent_purple"], "hover_color": "#7C3AED",
            "text_color": "white", "corner_radius": T["radius_md"],
            "font": (T["font_family"], T["font_size_md"], "bold"),
            "height": 40,
        },
        "ghost": {
            "fg_color": "transparent", "hover_color": T["bg_hover"],
            "text_color": T["text_secondary"], "corner_radius": T["radius_md"],
            "font": (T["font_family"], T["font_size_md"]),
            "height": 36,
        },
    }
    cfg = styles.get(style, styles["primary"]).copy()
    cfg.update(kwargs)
    return ctk.CTkButton(parent, text=text, **cfg)


def make_entry(parent, placeholder: str = "", show: str = "", **kwargs) -> ctk.CTkEntry:
    defaults = dict(
        fg_color=T["bg_input"],
        border_color=T["border"],
        text_color=T["text_primary"],
        placeholder_text_color=T["text_muted"],
        corner_radius=T["radius_sm"],
        font=(T["font_family"], T["font_size_md"]),
        height=44,
        placeholder_text=placeholder,
    )
    if show:
        defaults["show"] = show
    defaults.update(kwargs)
    return ctk.CTkEntry(parent, **defaults)


def make_scrollable(parent, **kwargs) -> ctk.CTkScrollableFrame:
    defaults = dict(
        fg_color=T["bg_primary"],
        scrollbar_button_color=T["bg_hover"],
        scrollbar_button_hover_color=T["accent_blue"],
    )
    defaults.update(kwargs)
    return ctk.CTkScrollableFrame(parent, **defaults)


class StatCard(ctk.CTkFrame):
    """A KPI stat card with icon, value and label."""

    def __init__(self, parent, icon: str, label: str, value: str = "0",
                 color: str = None, **kwargs):
        super().__init__(parent,
                         fg_color=T["bg_card"],
                         corner_radius=T["radius_md"],
                         border_width=1,
                         border_color=T["border"],
                         **kwargs)
        self._color = color or T["accent_blue"]

        # Accent bar on top
        accent = ctk.CTkFrame(self, height=3, fg_color=self._color, corner_radius=2)
        accent.pack(fill="x", padx=0, pady=(0, 0))

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=14, pady=12)

        ctk.CTkLabel(inner, text=icon,
                     font=(T["font_family"], 22),
                     text_color=self._color).pack(anchor="w")

        self._val_label = ctk.CTkLabel(inner, text=value,
                                       font=(T["font_family"], T["font_size_2xl"], "bold"),
                                       text_color=T["text_primary"])
        self._val_label.pack(anchor="w", pady=(2, 0))

        ctk.CTkLabel(inner, text=label,
                     font=(T["font_family"], T["font_size_sm"]),
                     text_color=T["text_secondary"]).pack(anchor="w")

    def update_value(self, value: str):
        self._val_label.configure(text=str(value))


class StatusBadge(ctk.CTkFrame):
    """Coloured status badge."""

    def __init__(self, parent, text: str = "Disconnected", **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._dot = ctk.CTkLabel(self, text="●",
                                 font=(T["font_family"], 12),
                                 text_color=T["error"])
        self._dot.pack(side="left", padx=(0, 4))
        self._label = ctk.CTkLabel(self, text=text,
                                   font=(T["font_family"], T["font_size_sm"]),
                                   text_color=T["text_secondary"])
        self._label.pack(side="left")

    def set_connected(self, name: str = ""):
        self._dot.configure(text_color=T["success"])
        self._label.configure(text=f"Connected{': ' + name if name else ''}")

    def set_disconnected(self):
        self._dot.configure(text_color=T["error"])
        self._label.configure(text="Disconnected")


class SidebarButton(ctk.CTkButton):
    """Sidebar navigation button."""

    def __init__(self, parent, text: str, icon: str = "",
                 command=None, **kwargs):
        super().__init__(parent,
                         text=f"  {icon}  {text}" if icon else text,
                         fg_color="transparent",
                         hover_color=T["bg_hover"],
                         text_color=T["text_secondary"],
                         anchor="w",
                         corner_radius=T["radius_sm"],
                         font=(T["font_family"], T["font_size_md"]),
                         height=44,
                         command=command,
                         **kwargs)

    def set_active(self, active: bool):
        if active:
            self.configure(fg_color=T["bg_hover"],
                           text_color=T["text_primary"],
                           font=(T["font_family"], T["font_size_md"], "bold"))
        else:
            self.configure(fg_color="transparent",
                           text_color=T["text_secondary"],
                           font=(T["font_family"], T["font_size_md"]))


class GradientLabel(ctk.CTkLabel):
    """Label with accent colour (CTk doesn't support gradients natively)."""
    def __init__(self, parent, text: str, **kwargs):
        super().__init__(parent, text=text,
                         text_color=T["accent_blue"],
                         font=(T["font_family"], T["font_size_3xl"], "bold"),
                         **kwargs)


class Separator(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, height=1,
                         fg_color=T["border"],
                         **kwargs)
