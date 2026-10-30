import re, datetime
from typing import Optional

def safe_str(value) -> Optional[str]:
    if value is None: return None
    s = str(value).strip()
    return s if s else None

def format_phone(phone) -> Optional[str]:
    if not phone: return None
    digits = re.sub(r"[^\d+]", "", str(phone))
    return digits if digits else None

def format_datetime(dt) -> Optional[str]:
    if dt is None: return None
    if isinstance(dt, datetime.datetime):
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    return str(dt)

def now_str() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

def build_full_name(first, last) -> Optional[str]:
    parts = [p for p in [first, last] if p]
    return " ".join(parts) if parts else None

def human_readable_size(size_bytes: int) -> str:
    for unit in ["B","KB","MB","GB"]:
        if size_bytes < 1024: return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"
