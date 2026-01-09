#!/usr/bin/env python3
"""Runner minimalista per i test di integrazione creati in `tests/`.

Questo script esegue i test presenti in `tests/test_integration_sensors.py`
senza dipendere da pytest (usa import + chiamate a funzioni di test).

Nota: questo repository in precedenza includeva uno shim locale `homeassistant/`
per permettere l'esecuzione dei test in ambiente di sviluppo. Lo shim è stato
rimosso. Per eseguire i test di integrazione è necessario installare Home
Assistant nell'ambiente di esecuzione oppure convertire i test per usare
`pytest` con opportune librerie di mocking.
"""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEST_FILE = ROOT / 'tests' / 'test_integration_sensors.py'


def run_tests():
    # Se Home Assistant non è importabile, stampiamo indicazioni in italiano
    # e usciamo senza eseguire i test di integrazione.
    if importlib.util.find_spec("homeassistant") is None:
        print("ATTENZIONE: il pacchetto 'homeassistant' non è disponibile. I test di integrazione richiedono Home Assistant o un ambiente di test con mock adeguati.")
        print("Opzioni:")
        print("  1) Installare le dipendenze di sviluppo di Home Assistant in questo ambiente.")
        print("  2) Convertire i test di integrazione per usare pytest con mock (consigliato per CI).")
        print("  3) Eseguire i test in un ambiente di sviluppo dove Home Assistant è disponibile.")
        return 0

    ns = {}
    print(f"Eseguo i test di integrazione da: {TEST_FILE}")
    try:
        # Assicura che la root del progetto sia importabile come top-level per gli import di `custom_components`
        sys.path.insert(0, str(ROOT))
        code = TEST_FILE.read_text(encoding='utf-8')
        exec(compile(code, str(TEST_FILE), 'exec'), ns)
    except Exception as e:
            print('ERRORE durante l\'esecuzione del file di test:', e)
        return 2

    # Find functions starting with test_
    tests = [v for k, v in ns.items() if callable(v) and k.startswith('test_')]
    if not tests:
        print('Nessun test trovato')
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
                print(f'ERRORE: {name} -> {e}')

    if failed:
        print(f'{failed} test falliti')
        return 2
    print('Tutti i test di integrazione sono passati.')
    return 0


if __name__ == '__main__':
    sys.exit(run_tests())
