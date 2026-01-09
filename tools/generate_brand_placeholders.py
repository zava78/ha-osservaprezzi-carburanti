"""Genera loghi PNG placeholder per ha-osservaprezzi-carburanti.

Questo script scrive piccoli file PNG trasparenti 1x1 per una lista di
nomi file brand nella cartella `custom_components/osservaprezzi_carburanti/assets/brands/`.

Esegui dalla root del progetto (esempio PowerShell):

    python .\tools\generate_brand_placeholders.py

"""
from __future__ import annotations

import base64
import os
from pathlib import Path

BRAND_FILES = [
    "eni.png",
    "eni_station.png",
    "ip.png",
    "q8.png",
    "esso.png",
    "tamoil.png",
    "api.png",
    "erg.png",
    "repsol.png",
    "enercoop.png",
    "default.png",
]

# 1x1 transparent PNG (base64)
TRANSPARENT_PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMAAWgmWQ0AAAAASUVORK5CYII="
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BRANDS_DIR = PROJECT_ROOT / "custom_components" / "osservaprezzi_carburanti" / "assets" / "brands"


def main() -> None:
    BRANDS_DIR.mkdir(parents=True, exist_ok=True)
    png_bytes = base64.b64decode(TRANSPARENT_PNG_B64)

    for fname in BRAND_FILES:
        path = BRANDS_DIR / fname
        with open(path, "wb") as f:
            f.write(png_bytes)
        print(f"Creato placeholder: {path}")

    print("Fatto. Sostituisci questi file con loghi PNG reali quando necessario.")


if __name__ == "__main__":
    main()
