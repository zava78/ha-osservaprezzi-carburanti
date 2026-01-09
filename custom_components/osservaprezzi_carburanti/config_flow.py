"""Config flow for osservaprezzi_carburanti (skeleton).

This is optional; providing minimal skeleton to be extended later.
"""
from __future__ import annotations

import logging
from typing import Any

from homeassistant import config_entries
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class OsservaPrezziConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Osservaprezzi Carburanti."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle the initial step for adding a station.

        This minimal flow lets the user add a single station per entry (station id
        and optional name). Users can add multiple entries to monitor multiple stations.
        """
        errors = {}
        if user_input is None:
            schema = {
                "station_id": str,
                "name": str,
                "scan_interval": int,
            }
            # Show a simple form (Home Assistant will render types)
            return self.async_show_form(step_id="user", data_schema=schema)

        # validate station_id
        station_id = user_input.get("station_id")
        try:
            int(station_id)
        except Exception:
            errors["station_id"] = "invalid_station_id"

        if errors:
            return self.async_show_form(step_id="user", data_schema=None, errors=errors)

        data = {
            "station_id": int(station_id),
            "name": user_input.get("name") or "",
            "scan_interval": user_input.get("scan_interval") or None,
        }

        title = f"Osservaprezzi {station_id}"
        return self.async_create_entry(title=title, data=data)
