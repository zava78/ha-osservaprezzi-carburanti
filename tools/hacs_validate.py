#!/usr/bin/env python3
"""Semplice validatore HACS per controlli formali del repo.

Questo script esegue controlli base:
- `hacs.json` esiste e contiene i campi attesi
- i file frontend dichiarati esistono
- `custom_components/<domain>` esiste e contiene `manifest.json` e `__init__.py`
- `README.md` e `info.md` esistono (info.md opzionale ma consigliato)

Non valida contenuti profondi della `info.md` o restrizioni HACS avanzate,
ma fornisce un rapida verifica formale prima di pubblicare.
"""
import json
import os
import sys

ROOT = os.path.abspath(os.path.dirname(__file__) + os.sep + '..')

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def main():
    errors = 0
    print(f"Root del repository: {ROOT}")

    hacs_path = os.path.join(ROOT, 'hacs.json')
    if not os.path.exists(hacs_path):
        print('ERRORE: file hacs.json non trovato')
        errors += 1
    else:
        try:
            hj = load_json(hacs_path)
            print('hacs.json caricato')
            # basic checks
            for key in ('name','domains','render_readme'):
                if key not in hj:
                    print(f'ERRORE: hacs.json mancante chiave: {key}')
                    errors += 1
            # frontend entries
            frontend = hj.get('frontend') or []
            for entry in frontend:
                path = entry.get('path')
                if not path:
                    print('ERRORE: voce frontend senza path')
                    errors += 1
                    continue
                full = os.path.join(ROOT, path.replace('/', os.sep))
                if not os.path.exists(full):
                    print(f'ERRORE: path frontend dichiarato ma mancante: {full}')
                    errors += 1
                else:
                    print(f'OK: asset frontend esistente: {path}')
        except Exception as e:
            print('ERRORE: parsing di hacs.json non riuscito', e)
            errors += 1

    # validate custom_components structure
    cc_dir = os.path.join(ROOT, 'custom_components')
    if not os.path.isdir(cc_dir):
        print('ERRORE: directory custom_components mancante')
        errors += 1
    else:
        # find integration dir
        found = False
        for name in os.listdir(cc_dir):
            p = os.path.join(cc_dir, name)
            if os.path.isdir(p):
                # check manifest and __init__.py
                m = os.path.join(p, 'manifest.json')
                i = os.path.join(p, '__init__.py')
                if os.path.exists(m) and os.path.exists(i):
                    print(f'OK: cartella integrazione: {name}')
                    found = True
                    # load manifest
                    try:
                        mj = load_json(m)
                        if 'domain' not in mj and 'name' not in mj:
                            print('AVVISO: manifest.json mancante campo `domain` o `name`')
                    except Exception as e:
                        print('ERRORE: impossibile parsare manifest.json', e)
                        errors += 1
        if not found:
            print('ERRORE: nessuna integrazione valida trovata in custom_components')
            errors += 1

    # check README and info.md
    for fname in ('README.md','info.md'):
        p = os.path.join(ROOT, fname)
        if not os.path.exists(p):
            print(f'AVVISO: {fname} non trovato')
        else:
            print(f'OK: {fname} presente')

    if errors:
        print(f'Validazione completata: trovati {errors} problema/i')
        return 2
    print('Validazione completata: nessun problema trovato')
    return 0

if __name__ == '__main__':
    sys.exit(main())
