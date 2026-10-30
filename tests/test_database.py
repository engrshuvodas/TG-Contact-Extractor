"""Tests for the database layer."""
import sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.database import Database
from utils.helpers import now_str


def _make_db() -> Database:
    tmp = tempfile.mktemp(suffix=".db")
    return Database(Path(tmp))


def test_db_creates():
    db = _make_db()
    assert db.db_path.exists()

def test_settings_roundtrip():
    db = _make_db()
    db.set_setting("test_key", "hello")
    assert db.get_setting("test_key") == "hello"

def test_settings_default():
    db = _make_db()
    assert db.get_setting("missing", "default") == "default"

def test_upsert_user():
    db = _make_db()
    user = {
        "user_id": 111, "first_name": "Alice", "last_name": "Smith",
        "full_name": "Alice Smith", "username": "alice123", "phone": "+1234567",
        "is_contact": 1, "last_message_date": None,
        "chat_type": "private", "extraction_date": now_str(), "updated_at": now_str(),
    }
    db.upsert_user(user)
    assert db.get_user_count() == 1

def test_upsert_user_dedup():
    db = _make_db()
    base = {
        "user_id": 222, "first_name": "Bob", "last_name": None,
        "full_name": "Bob", "username": None, "phone": None,
        "is_contact": 0, "last_message_date": None,
        "chat_type": "private", "extraction_date": now_str(), "updated_at": now_str(),
    }
    db.upsert_user(base)
    db.upsert_user(base)   # insert same user again
    assert db.get_user_count() == 1

def test_get_all_users_filter():
    db = _make_db()
    users = [
        {"user_id": 1, "first_name": "A", "last_name": None, "full_name": "A",
         "username": "alpha", "phone": "+1111", "is_contact": 1,
         "last_message_date": None, "chat_type": "private",
         "extraction_date": now_str(), "updated_at": now_str()},
        {"user_id": 2, "first_name": "B", "last_name": None, "full_name": "B",
         "username": None, "phone": None, "is_contact": 0,
         "last_message_date": None, "chat_type": "private",
         "extraction_date": now_str(), "updated_at": now_str()},
    ]
    for u in users:
        db.upsert_user(u)

    all_users = db.get_all_users("all")
    assert len(all_users) == 2

    with_username = db.get_all_users("with_username")
    assert len(with_username) == 1
    assert with_username[0]["username"] == "alpha"

    without_username = db.get_all_users("without_username")
    assert len(without_username) == 1

    with_phone = db.get_all_users("with_phone")
    assert len(with_phone) == 1

    saved = db.get_all_users("saved_contacts")
    assert len(saved) == 1
    assert saved[0]["is_contact"] == 1

def test_stats():
    db = _make_db()
    db.upsert_user({"user_id":10,"first_name":"X","last_name":None,"full_name":"X",
                    "username":"xyz","phone":None,"is_contact":1,
                    "last_message_date":None,"chat_type":"private",
                    "extraction_date":now_str(),"updated_at":now_str()})
    stats = db.get_stats()
    assert stats["total"] == 1
    assert stats["with_username"] == 1
    assert stats["without_username"] == 0
    assert stats["without_phone"] == 1
    assert stats["saved_contacts"] == 1

def test_clear_users():
    db = _make_db()
    db.upsert_user({"user_id":99,"first_name":"X","last_name":None,"full_name":"X",
                    "username":None,"phone":None,"is_contact":0,
                    "last_message_date":None,"chat_type":"private",
                    "extraction_date":now_str(),"updated_at":now_str()})
    db.clear_users()
    assert db.get_user_count() == 0

def test_extraction_history():
    db = _make_db()
    hid = db.start_extraction_history("+1234567890")
    db.finish_extraction_history(hid, total_found=42)
    history = db.get_history()
    assert len(history) >= 1
    assert history[0]["total_found"] == 42
    assert history[0]["status"] == "completed"


if __name__ == "__main__":
    tests = [v for k,v in globals().items() if k.startswith("test_")]
    passed = failed = 0
    for fn in tests:
        try:
            fn()
            print(f"  PASS: {fn.__name__}")
            passed += 1
        except Exception as e:
            print(f"  FAIL: {fn.__name__} — {e}")
            import traceback; traceback.print_exc()
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
