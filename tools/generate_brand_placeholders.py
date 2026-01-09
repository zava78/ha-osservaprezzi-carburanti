"""Generate placeholder PNG logos for ha-osservaprezzi-carburanti.

This script writes small 1x1 transparent PNG files for a list of brand
filenames into `custom_components/osservaprezzi_carburanti/assets/brands/`.

Run from project root (PowerShell example):

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
        print(f"Wrote placeholder: {path}")

    print("Done. Replace these files with real PNG logos as needed.")


if __name__ == "__main__":
    main()
