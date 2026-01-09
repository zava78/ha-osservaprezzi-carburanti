"""Runner semplice per i test di anteprima senza pytest.

Questo script importa il modulo di test e invoca le sue funzioni.

Esegui con:
    python .\tools\run_preview_tests.py
"""
from importlib import import_module
from pathlib import Path
import sys

# Assicura che la root del repository sia in `sys.path` così il package `tests` è importabile
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

print("Tutti i test sono passati.")
