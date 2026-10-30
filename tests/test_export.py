"""Tests for Excel and CSV export."""
import sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.export_manager import ExportManager
from utils.helpers import now_str

SAMPLE_USERS = [
    {"user_id": 1, "first_name": "Alice", "last_name": "Smith",
     "full_name": "Alice Smith", "username": "alice", "phone": "+1234567890",
     "is_contact": 1, "last_message_date": "2024-01-01 12:00:00",
     "chat_type": "private", "extraction_date": now_str()},
    {"user_id": 2, "first_name": "Bob", "last_name": None,
     "full_name": "Bob", "username": None, "phone": None,
     "is_contact": 0, "last_message_date": None,
     "chat_type": "private", "extraction_date": now_str()},
]


def test_excel_export_creates_file():
    tmp = Path(tempfile.mkdtemp())
    mgr = ExportManager(tmp)
    path = mgr.export_excel(SAMPLE_USERS)
    assert path.exists()
    assert path.suffix == ".xlsx"

def test_excel_export_row_count():
    import openpyxl
    tmp = Path(tempfile.mkdtemp())
    mgr = ExportManager(tmp)
    path = mgr.export_excel(SAMPLE_USERS)
    wb = openpyxl.load_workbook(str(path))
    ws = wb.active
    # Row 1 = header, remaining = data
    assert ws.max_row == len(SAMPLE_USERS) + 1

def test_csv_export_creates_file():
    tmp = Path(tempfile.mkdtemp())
    mgr = ExportManager(tmp)
    path = mgr.export_csv(SAMPLE_USERS)
    assert path.exists()
    assert path.suffix == ".csv"

def test_csv_export_row_count():
    import csv
    tmp = Path(tempfile.mkdtemp())
    mgr = ExportManager(tmp)
    path = mgr.export_csv(SAMPLE_USERS)
    with open(path, encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))
    # 1 header + 2 data rows
    assert len(rows) == len(SAMPLE_USERS) + 1

def test_csv_export_handles_null():
    import csv
    tmp = Path(tempfile.mkdtemp())
    mgr = ExportManager(tmp)
    path = mgr.export_csv(SAMPLE_USERS)
    with open(path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    # Bob has no phone — should be empty string not "None"
    bob_row = [r for r in rows if r["Username"] == ""][0]
    assert bob_row["Phone Number"] == ""


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
