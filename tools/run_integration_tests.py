#!/usr/bin/env python3
"""Runner minimalista per i test di integrazione creati in `tests/`.

Questo script esegue i test presenti in `tests/test_integration_sensors.py`
senza dipendere da pytest (usa import + chiamate a funzioni di test).
"""
import importlib.util
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEST_FILE = ROOT / 'tests' / 'test_integration_sensors.py'


def run_tests():
    ns = {}
    print(f"Running integration tests from: {TEST_FILE}")
    try:
        # Ensure project root is importable as top-level for `custom_components` imports
        sys.path.insert(0, str(ROOT))
        code = TEST_FILE.read_text(encoding='utf-8')
        exec(compile(code, str(TEST_FILE), 'exec'), ns)
    except Exception as e:
        print('ERROR executing test file:', e)
        return 2

    # Find functions starting with test_
    tests = [v for k, v in ns.items() if callable(v) and k.startswith('test_')]
    if not tests:
        print('No tests found')
        return 1

    failed = 0
    for t in tests:
        name = t.__name__
        try:
            t()
            print(f'PASS: {name}')
        except AssertionError as e:
            failed += 1
            print(f'FAIL: {name} -> {e}')
        except Exception as e:
            failed += 1
            print(f'ERROR: {name} -> {e}')

    if failed:
        print(f'{failed} test(s) failed')
        return 2
    print('All integration tests passed.')
    return 0


if __name__ == '__main__':
    sys.exit(run_tests())
