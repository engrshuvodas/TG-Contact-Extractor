"""
Unit tests for extractor filtering logic using mock Telegram objects.
No real Telegram connection required.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.helpers import build_full_name, safe_str, format_phone
from utils.helpers import now_str


class MockUser:
    """Simulated Telethon User object."""
    def __init__(self, uid, first=None, last=None, username=None,
                 phone=None, bot=False, is_self=False, deleted=False,
                 contact=False):
        self.id = uid
        self.first_name = first
        self.last_name = last
        self.username = username
        self.phone = phone
        self.bot = bot
        self.is_self = is_self
        self.deleted = deleted
        self.contact = contact
        self.mutual_contact = False


def _should_extract(user: MockUser) -> bool:
    """Mirrors extractor logic."""
    if user.bot:      return False
    if user.is_self:  return False
    if user.deleted:  return False
    return True


def test_bot_excluded():
    u = MockUser(1, bot=True)
    assert not _should_extract(u)

def test_self_excluded():
    u = MockUser(2, is_self=True)
    assert not _should_extract(u)

def test_deleted_excluded():
    u = MockUser(3, deleted=True)
    assert not _should_extract(u)

def test_normal_user_included():
    u = MockUser(4, first="John", last="Doe")
    assert _should_extract(u)

def test_no_username_returns_none():
    u = MockUser(5, username=None)
    assert safe_str(u.username) is None

def test_no_phone_returns_none():
    u = MockUser(6, phone=None)
    assert format_phone(u.phone) is None

def test_full_name_both():
    u = MockUser(7, first="Alice", last="Brown")
    assert build_full_name(u.first_name, u.last_name) == "Alice Brown"

def test_full_name_first_only():
    u = MockUser(8, first="Alice")
    assert build_full_name(u.first_name, u.last_name) == "Alice"

def test_full_name_no_name():
    u = MockUser(9)
    result = build_full_name(u.first_name, u.last_name)
    assert result is None

def test_dedup_via_set():
    seen = set()
    u1 = MockUser(10)
    u2 = MockUser(10)   # same id
    def try_add(u):
        if u.id in seen: return False
        seen.add(u.id)
        return True
    assert try_add(u1) is True
    assert try_add(u2) is False   # duplicate rejected


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
