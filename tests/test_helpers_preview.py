from pathlib import Path
import sys

# Ensure the integration package directory is importable without importing Home Assistant
ROOT = Path(__file__).resolve().parents[1]
COMP_DIR = ROOT / "custom_components" / "osservaprezzi_carburanti"
sys.path.insert(0, str(COMP_DIR))

import helpers as hc_helpers
from helpers import build_station_preview


def test_build_station_preview_minimal():
    payload = {"id": 14922, "name": "Service Area Esempio", "company": "CompanyX"}
    preview, entry = hc_helpers.build_station_preview(payload, 14922, None)
    assert "14922:" in preview
    assert "Service Area Esempio" in preview
    assert "CompanyX" in preview
    assert entry["id"] == 14922
    assert entry["name"] == "Service Area Esempio"


def test_build_station_preview_full():
    payload = {
        "id": 48524,
        "description": "Distributore Ener Coop Borgo",
        "gestore": "Enercoop",
        "brand": "Enercoop",
        "address": "Via Roma 1",
        "city": "Mantova",
        "latitude": 45.1600,
        "longitude": 10.8000,
    }
    preview, entry = hc_helpers.build_station_preview(payload, 48524, None)
    assert "48524:" in preview
    assert "Distributore Ener Coop Borgo" in preview
    assert "Enercoop" in preview
    assert "addr=Via Roma 1" in preview or "Mantova" in preview
    assert "coord=" in preview
    assert entry["id"] == 48524