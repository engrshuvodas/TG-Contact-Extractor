"""Tests for utility helpers."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.helpers import (
    safe_str, format_phone, build_full_name, format_datetime, now_str
)
import datetime


def test_safe_str_none():
    assert safe_str(None) is None

def test_safe_str_empty():
    assert safe_str("") is None

def test_safe_str_whitespace():
    assert safe_str("  ") is None

def test_safe_str_value():
    assert safe_str("  John  ") == "John"

def test_format_phone_valid():
    assert format_phone("+1234567890") == "+1234567890"

def test_format_phone_none():
    assert format_phone(None) is None

def test_format_phone_empty():
    assert format_phone("") is None

def test_format_phone_strips_spaces():
    assert format_phone("+1 234 567") == "+1234567"

def test_build_full_name_both():
    assert build_full_name("John", "Smith") == "John Smith"

def test_build_full_name_first_only():
    assert build_full_name("John", None) == "John"

def test_build_full_name_last_only():
    assert build_full_name(None, "Smith") == "Smith"

def test_build_full_name_none():
    assert build_full_name(None, None) is None

def test_format_datetime_none():
    assert format_datetime(None) is None

def test_format_datetime_datetime():
    dt = datetime.datetime(2024, 1, 15, 10, 30, 0)
    assert format_datetime(dt) == "2024-01-15 10:30:00"

def test_now_str_format():
    s = now_str()
    assert len(s) == 19  # "YYYY-MM-DD HH:MM:SS"


if __name__ == "__main__":
    import traceback
    tests = [v for k,v in globals().items() if k.startswith("test_")]
    passed = failed = 0
    for fn in tests:
        try:
            fn()
            print(f"  PASS: {fn.__name__}")
            passed += 1
        except Exception as e:
            print(f"  FAIL: {fn.__name__} — {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
