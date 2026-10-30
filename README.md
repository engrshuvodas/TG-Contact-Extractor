# ✈ TG Contact Extractor

> **A professional Windows desktop application to extract and export contact information from your Telegram private conversations.**

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)
![License](https://img.shields.io/badge/license-MIT-green)

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Screenshots](#screenshots)
- [Requirements](#requirements)
- [Installation](#installation)
- [Getting Your Telegram API Credentials](#getting-your-telegram-api-credentials)
- [How to Use](#how-to-use)
- [Project Structure](#project-structure)
- [Running Tests](#running-tests)
- [Building the Executable](#building-the-executable)
- [Security & Privacy](#security--privacy)
- [Important Limitations](#important-limitations)
- [Error Handling](#error-handling)
- [FAQ](#faq)
- [License](#license)

---

## Overview

**TG Contact Extractor** is a fully functional Windows desktop application that lets you connect your own Telegram account, scan your private conversation history, collect available user information, and export it to Excel (`.xlsx`) or CSV files.

All processing is **100% local** — no external server, no cloud database, no data upload of any kind.

---

## Features

- **Secure Telegram Login** — Full MTProto authentication with OTP and optional 2FA support
- **Session Persistence** — Logs in once; re-uses session on next launch
- **Private Chat Extraction** — Scans all accessible one-to-one private dialogs
- **Archived Chat Support** — Includes archived private conversations
- **Saved Contacts** — Fetches your saved Telegram contacts
- **Rich Export Options**:
  - Export All Users
  - Export Users With / Without Username
  - Export Users With / Without Phone Number
  - Export Saved Contacts / Non-Saved Users
- **Excel Export** — Professionally formatted `.xlsx` with bold headers, auto-filter, frozen row, and auto column widths
- **CSV Export** — UTF-8 BOM CSV compatible with Excel
- **Live Extraction Dashboard** — Real-time stats, progress bar, activity log
- **Pause / Resume / Stop** — Full extraction control
- **SQLite Database** — Local persistence with upsert (no duplicates)
- **Extraction History** — Records of all past extraction sessions
- **Settings Page** — DB management, export folder, account info, logout
- **Premium Dark UI** — Navy dark theme with blue/purple accents, modern cards, smooth layout

---

## Requirements

| Requirement | Version |
|-------------|---------|
| Windows     | 10 or 11 |
| Python      | 3.11+  |
| Telethon    | 1.36+  |
| CustomTkinter | 5.2+ |
| Pillow      | 10.0+  |
| OpenPyXL    | 3.1+   |
| PyInstaller | 6.0+ (for EXE build) |

---

## Installation

### Option 1 — Quick Launch (Windows)

Double-click `run.bat` or run from terminal:
```cmd
run.bat
```
This script automatically checks for Python, installs any missing dependencies, and starts the application.

### Option 2 — Run from Source (Manual)

```bash
# 1. Clone the repository
git clone https://github.com/youruser/TG-Contact-Extractor.git
cd "TG Contact Extractor"

# 2. Create a virtual environment (recommended)
python -m venv .venv
.venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application
python main.py
```

### Option 3 — Use Pre-Built Executable

Download `TGContactExtractor.exe` from the Releases page and run it directly.  
No Python installation required.

---

## Getting Your Telegram API Credentials

To use TG Contact Extractor, you need your **own** Telegram API credentials:

1. Visit **https://my.telegram.org/apps**
2. Log in with your Telegram account
3. Click **"Create New Application"**
4. Fill in the form (App name, platform = Desktop, etc.)
5. You will receive:
   - **API ID** — a number (e.g., `12345678`)
   - **API Hash** — a 32-character hex string

> ⚠️ Never share your API credentials or session files with anyone.

---

## How to Use

### Step 1 — Connect Telegram

1. Open the app and go to **Connect Telegram** in the sidebar
2. Enter your **API ID**, **API Hash**, and **Phone Number** (with country code, e.g., `+8801234567890`)
3. Click **Send Login Code**
4. Enter the OTP received via Telegram or SMS
5. If your account has 2FA enabled, enter your password
6. You are now connected!

### Step 2 — Extract Contacts

1. Navigate to **Extract Contacts**
2. Click **▶ Start Extraction**
3. Monitor the live progress, stats, and activity log
4. Use **Pause / Resume / Stop** as needed
5. When finished, results are saved to the local SQLite database

### Step 3 — Export Data

1. Navigate to **Export Data**
2. Choose your **export filter** (e.g., "Users With Phone Number")
3. Select your **destination folder** (defaults to `exports/`)
4. Click **Export as Excel** or **Export as CSV**
5. Your file is saved as `TG_Contacts_YYYY-MM-DD_HH-MM-SS.xlsx/csv`

---

## Project Structure

```
TG Contact Extractor/
│
├── main.py                  # Application entry point
├── config.py                # All constants, paths, theme, settings
├── requirements.txt         # Python dependencies
├── build.bat                # Windows build script (PyInstaller)
├── README.md                # This file
│
├── core/
│   ├── telegram_client.py   # Telethon client wrapper & session management
│   ├── authentication.py    # Multi-step auth flow (OTP, 2FA)
│   ├── extractor.py         # Private chat contact extraction engine
│   ├── database.py          # SQLite database manager
│   └── export_manager.py    # Excel & CSV export with formatting
│
├── gui/
│   ├── components.py        # Reusable UI widgets (StatCard, SidebarButton, etc.)
│   ├── login.py             # Telegram login panel (3-step flow)
│   ├── dashboard.py         # KPI dashboard with stat cards
│   ├── extraction.py        # Live extraction panel with controls
│   ├── export.py            # Export panel with filter selection
│   ├── settings.py          # Settings panel
│   ├── history.py           # Extraction history panel
│   └── about.py             # About panel
│
├── utils/
│   ├── logger.py            # Rotating file logger
│   ├── helpers.py           # String, datetime, phone utilities
│   └── security.py         # Credential masking, safe log sanitiser
│
├── tests/
│   ├── test_helpers.py      # Tests for utility helpers
│   ├── test_database.py     # Tests for the database layer
│   ├── test_extractor_logic.py  # Tests for extraction filtering (mock data)
│   └── test_export.py       # Tests for Excel & CSV export
│
├── assets/
│   └── icons/               # Application icons
│
├── data/                    # SQLite database (auto-created)
├── sessions/                # Telegram session files (auto-created)
├── exports/                 # Exported files (auto-created)
└── logs/                    # Application logs (auto-created)
```

---

## Running Tests

All tests work without a real Telegram connection (mock data is used):

```bash
# Run all test suites
python tests/test_helpers.py
python tests/test_database.py
python tests/test_extractor_logic.py
python tests/test_export.py
```

Expected output: all tests should report `PASS`.

**Test coverage includes:**
- Utility helper functions (string, phone, datetime)
- SQLite database CRUD and deduplication
- Extraction filtering (bots, self, deleted, duplicates)
- Excel export formatting and row counts
- CSV export with NULL field handling

---

## Building the Executable

### Quick Build

```batch
build.bat
```

This will:
1. Install all dependencies
2. Clean previous builds
3. Run PyInstaller to create `dist\TGContactExtractor\TGContactExtractor.exe`
4. Copy assets and create required folders

### Manual Build Command

```bash
pyinstaller \
  --name "TGContactExtractor" \
  --onedir \
  --windowed \
  --add-data "assets;assets" \
  --add-data "config.py;." \
  --hidden-import "customtkinter" \
  --hidden-import "PIL._tkinter_finder" \
  --hidden-import "telethon" \
  --hidden-import "openpyxl" \
  --collect-data "customtkinter" \
  --noconfirm \
  main.py
```

### After Building

The `dist/TGContactExtractor/` folder is self-contained.  
The `data/`, `sessions/`, `exports/`, and `logs/` folders are created automatically on first launch.

---

## Data Fields Extracted

| Column | Field | Notes |
|--------|-------|-------|
| A | User ID | Telegram numeric user ID |
| B | First Name | May be empty |
| C | Last Name | May be empty |
| D | Full Name | Combined name |
| E | Username | `@username` or empty if not set |
| F | Phone Number | Only if shared with you |
| G | Is Contact | Yes / No |
| H | Last Message Date | Date of last private message |
| I | Chat Type | `private` or `contact` |
| J | Extraction Date | When the record was extracted |

---

## Security & Privacy

| Aspect | Implementation |
|--------|---------------|
| Local only | All data stays on your machine |
| No external server | No API calls outside Telegram's official servers |
| Session security | Sessions stored in `sessions/` — never uploaded |
| Credential storage | Only `api_id` hint is saved; API hash and passwords are never persisted |
| Log sanitisation | Phone numbers and hashes are masked in log files |
| 2FA passwords | Never logged or stored |
| OTP codes | Never logged or stored |
| Delete confirmation | Destructive actions require explicit confirmation |

---

## Important Limitations

1. **Phone numbers** are only visible if the contact explicitly shared their number with you (Telegram privacy setting)
2. **Username visibility** depends on the user's privacy settings
3. **Only private chats** are scanned — no group member extraction
4. **No hidden data recovery** — the app never attempts to bypass Telegram privacy restrictions
5. **FloodWait** — if Telegram rate-limits the session, the extractor waits the required time
6. **Deleted accounts** — gracefully skipped
7. **API compliance** — all operations use official Telegram MTProto API via Telethon

---

## Error Handling

| Error | Handling |
|-------|---------|
| No internet | Friendly message displayed |
| Invalid API ID/Hash | Validated before connection attempt |
| Incorrect OTP | Error message, retry allowed |
| Incorrect 2FA | Error message, retry allowed |
| FloodWaitError | Waits requested duration, notifies user |
| Expired session | Prompts for re-login |
| Deleted account | Skipped silently during extraction |
| DB error | Logged and skipped, extraction continues |
| Export failure | Error dialog with details |
| Network timeout | Friendly error message |

---

## FAQ

**Q: Is this safe to use?**  
A: Yes. The app uses only the official Telegram API. It never accesses data you don't have permission to see.

**Q: Do I need to enter my credentials every time?**  
A: No. Your session is saved after the first login. You only need to log in again if the session expires or you manually log out.

**Q: Why can't I see phone numbers for some contacts?**  
A: Telegram shows phone numbers only if the user has set their privacy to allow it, or if they are in your phone contacts and have mutual contact enabled.

**Q: Where are my exported files saved?**  
A: By default in the `exports/` folder inside the application directory. You can change this in Settings.

**Q: How do I update the app?**  
A: Pull the latest code from the repository and run `python main.py` again, or rebuild the executable with `build.bat`.

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

*Built with Python 3.11+, Telethon, CustomTkinter, OpenPyXL, and SQLite.*
