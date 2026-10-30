"""
TG Contact Extractor - Application Configuration
"""
import os
import sys
from pathlib import Path

APP_NAME = "TG Contact Extractor"
APP_VERSION = "2.0.0"
APP_BUILD = "2.0"
APP_AUTHOR = "TG Contact Extractor"
APP_DESCRIPTION = "Extract and export contacts from your Telegram private chats"

if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent

DATA_DIR    = BASE_DIR / "data"
SESSIONS_DIR = BASE_DIR / "sessions"
EXPORTS_DIR = BASE_DIR / "exports"
LOGS_DIR    = BASE_DIR / "logs"
ASSETS_DIR  = BASE_DIR / "assets"

for _dir in [DATA_DIR, SESSIONS_DIR, EXPORTS_DIR, LOGS_DIR, ASSETS_DIR]:
    _dir.mkdir(parents=True, exist_ok=True)

DB_PATH  = DATA_DIR / "tg_extractor.db"
DB_VERSION = 1

TELEGRAM_API_URL = "https://my.telegram.org/apps"
SESSION_NAME = "tg_extractor_session"

EXCEL_COLUMNS = [
    ("user_id",           "User ID"),
    ("first_name",        "First Name"),
    ("last_name",         "Last Name"),
    ("full_name",         "Full Name"),
    ("username",          "Username"),
    ("phone",             "Phone Number"),
    ("is_contact",        "Is Contact"),
    ("last_message_date", "Last Message Date"),
    ("chat_type",         "Chat Type"),
    ("extraction_date",   "Extraction Date"),
]

EXPORT_FILTERS = [
    ("all",              "All Users"),
    ("with_username",    "Users With Username"),
    ("without_username", "Users Without Username"),
    ("with_phone",       "Users With Phone Number"),
    ("without_phone",    "Users Without Phone Number"),
    ("saved_contacts",   "Saved Contacts"),
    ("non_saved",        "Non-Saved Users"),
]

THEME = {
    "bg_primary":    "#0B0F1A",
    "bg_secondary":  "#111827",
    "bg_card":       "#1A2035",
    "bg_hover":      "#1E2740",
    "bg_input":      "#141D2F",
    "accent_blue":   "#3B82F6",
    "accent_purple": "#8B5CF6",
    "accent_grad_1": "#3B82F6",
    "accent_grad_2": "#8B5CF6",
    "success":       "#10B981",
    "warning":       "#F59E0B",
    "error":         "#EF4444",
    "info":          "#06B6D4",
    "text_primary":  "#F1F5F9",
    "text_secondary":"#94A3B8",
    "text_muted":    "#475569",
    "border":        "#1E293B",
    "border_active": "#3B82F6",
    "sidebar_bg":    "#0D1424",
    "sidebar_width": 220,
    "font_family":   "Segoe UI",
    "font_size_xs":  10,
    "font_size_sm":  11,
    "font_size_md":  13,
    "font_size_lg":  15,
    "font_size_xl":  18,
    "font_size_2xl": 22,
    "font_size_3xl": 28,
    "radius_sm": 6,
    "radius_md": 10,
    "radius_lg": 14,
}

LOG_FILE = LOGS_DIR / "app.log"
LOG_MAX_BYTES = 5 * 1024 * 1024
LOG_BACKUP_COUNT = 3

EXTRACTION_BATCH_SIZE = 100
FLOOD_WAIT_RETRY_THRESHOLD = 60
EXTRACTION_DELAY_MS = 50

WINDOW_WIDTH  = 1200
WINDOW_HEIGHT = 750
WINDOW_MIN_WIDTH  = 900
WINDOW_MIN_HEIGHT = 600
