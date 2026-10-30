import json, re
from pathlib import Path
from typing import Optional

def mask_phone(phone: str) -> str:
    if not phone or len(phone) < 6: return "****"
    return phone[:3] + "****" + phone[-3:]

def mask_api_hash(api_hash: str) -> str:
    if not api_hash or len(api_hash) < 8: return "****"
    return api_hash[:4] + "****" + api_hash[-4:]

def sanitize_log_message(msg: str) -> str:
    msg = re.sub(r"\+?\d{7,15}", "<PHONE>", msg)
    msg = re.sub(r"\b[0-9a-fA-F]{32}\b", "<HASH>", msg)
    return msg

def load_saved_credentials(cred_path: Path) -> dict:
    if cred_path.exists():
        try:
            with open(cred_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {"api_id": data.get("api_id", "")}
        except Exception:
            pass
    return {}

def save_credentials(cred_path: Path, api_id: str) -> None:
    try:
        with open(cred_path, "w", encoding="utf-8") as f:
            json.dump({"api_id": api_id}, f)
    except Exception:
        pass
