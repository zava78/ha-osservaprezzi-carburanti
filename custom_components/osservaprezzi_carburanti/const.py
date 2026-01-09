"""Constants for osservaprezzi_carburanti integration."""
from __future__ import annotations

from datetime import timedelta

DOMAIN = "osservaprezzi_carburanti"
DEFAULT_SCAN_INTERVAL = 3600  # seconds
API_URL_TEMPLATE = "https://carburanti.mise.gov.it/ospzApi/registry/servicearea/{id}"

# Map brand names (as they may appear in API) to asset filenames in assets/brands/
BRAND_LOGOS = {
    "eni": "eni.png",
    "eni station": "eni_station.png",
    "ip": "ip.png",
    "q8": "q8.png",
    "esso": "esso.png",
    "tamoil": "tamoil.png",
    "api": "api.png",
    "erg": "erg.png",
    "repsol": "repsol.png",
    "enercoop": "enercoop.png",
    "others": "default.png",
}

# Default request timeout
REQUEST_TIMEOUT = 10

# Data keys stored in hass.data
DATA_COORDINATORS = f"{DOMAIN}_coordinators"

# Default device class/icon
DEFAULT_ICON = "mdi:gas-station"

# Helper: scan interval as timedelta
def scan_interval_td(seconds: int) -> timedelta:
    return timedelta(seconds=seconds)
