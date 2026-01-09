"""Integrazione Osservaprezzi Carburanti.

Inizializzazione minima: salva la configurazione YAML (se presente) in
`hass.data` affinché le piattaforme possano leggerla.
"""
from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN, DATA_COORDINATORS


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the osservaprezzi_carburanti component from YAML configuration."""
    hass.data.setdefault(DOMAIN, {})
    hass.data.setdefault(DATA_COORDINATORS, {})

    if DOMAIN in config:
        hass.data[DOMAIN]["yaml_config"] = config[DOMAIN]

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a config entry (forward to platforms)."""
    hass.data.setdefault(DOMAIN, {})
    hass.data.setdefault(DATA_COORDINATORS, {})

    # store entry data for platforms to read
    hass.data[DOMAIN].setdefault("entries", {})
    hass.data[DOMAIN]["entries"][entry.entry_id] = entry.data

    # forward setup to sensor platform
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry and its platforms."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["sensor"])
    # remove coordinators associated with this entry if any
    coordinators = hass.data.get(DATA_COORDINATORS, {})
    to_remove = [k for k in coordinators.keys() if isinstance(k, tuple) and k[0] == entry.entry_id]
    for k in to_remove:
        coordinators.pop(k, None)

    hass.data.get(DOMAIN, {}).get("entries", {}).pop(entry.entry_id, None)
    return unload_ok
