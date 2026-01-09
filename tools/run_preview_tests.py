"""Simple runner for preview tests without pytest.

This script imports the test module and runs its functions.

Run with:
    python .\tools\run_preview_tests.py
"""
from importlib import import_module
from pathlib import Path
import sys

# Ensure repo root is on sys.path so the `tests` package is importable
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

mod = import_module("tests.test_helpers_preview")

failed = 0
for name in dir(mod):
    if name.startswith("test_"):
        fn = getattr(mod, name)
        try:
            fn()
            print(f"PASS: {name}")
        except AssertionError as e:
            print(f"FAIL: {name} -> {e}")
            failed += 1

if failed:
    raise SystemExit(1)

print("All tests passed.")
