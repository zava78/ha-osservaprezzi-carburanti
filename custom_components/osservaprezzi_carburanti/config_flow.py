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
        if user_input is None:
            return self.async_show_form(step_id="user")

        # Minimal: store a global scan_interval or stations list in options
        return self.async_create_entry(title="Osservaprezzi Carburanti", data=user_input)
