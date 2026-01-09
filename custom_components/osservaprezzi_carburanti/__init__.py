"""Osservaprezzi Carburanti integration.

Minimal init: store YAML config (if present) in hass.data for platforms to consume.
"""
from __future__ import annotations

from homeassistant.core import HomeAssistant

from .const import DOMAIN


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the osservaprezzi_carburanti component from YAML configuration."""
    hass.data.setdefault(DOMAIN, {})

    if DOMAIN in config:
        hass.data[DOMAIN]["yaml_config"] = config[DOMAIN]

    return True


async def async_setup_entry(hass: HomeAssistant, entry) -> bool:  # pragma: no cover - optional
    """Set up from a config entry (not implemented yet)."""
    return True


async def async_unload_entry(hass: HomeAssistant, entry) -> bool:  # pragma: no cover - optional
    """Unload a config entry (not implemented yet)."""
    return True
