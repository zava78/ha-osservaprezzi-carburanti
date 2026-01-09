"""Sensori per l'integrazione Osservaprezzi Carburanti.

Questo modulo crea sensori per ogni impianto e per tipo di carburante usando
DataUpdateCoordinator per gestire il polling e la memorizzazione dei dati.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ATTRIBUTION, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.config_entries import ConfigEntry

from .const import (
    API_URL_TEMPLATE,
    BRAND_LOGOS,
    DATA_COORDINATORS,
    DEFAULT_ICON,
    DEFAULT_SCAN_INTERVAL,
    REQUEST_TIMEOUT,
    DOMAIN,
    scan_interval_td,
)
from .helpers import find_coordinates

_LOGGER = logging.getLogger(__name__)


def _normalize(text: Optional[str]) -> str:
    if not text:
        return "unknown"
    return "".join(c if c.isalnum() else "_" for c in text.lower())


def _format_address(data: Dict[str, Any]) -> str:
    # Attempt to extract a readable address from known fields, fallback to str(data)
    for key in ("address", "indirizzo", "street"):
        if key in data and data[key]:
            return data[key]

    parts = []
    for k in ("street", "civic", "city", "municipality", "prov", "province", "zip"):
        v = data.get(k) or data.get(k.upper())
        if v:
            parts.append(str(v))
    if parts:
        return ", ".join(parts)
    return data.get("name") or data.get("description") or ""


class StationDataUpdateCoordinator(DataUpdateCoordinator):
    """Coordinator to fetch station data from Osservaprezzi API."""

    def __init__(self, hass: HomeAssistant, station_id: int, scan_interval: int):
        self.station_id = station_id
        super().__init__(
            hass,
            _LOGGER,
            name=f"osservaprezzi_{station_id}",
            update_interval=scan_interval_td(scan_interval),
        )

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch data from the API and return JSON."""
        url = API_URL_TEMPLATE.format(id=self.station_id)
        _LOGGER.debug("Fetching station %s from %s", self.station_id, url)

        session = async_get_clientsession(self.hass)
        try:
            async with session.get(url, timeout=REQUEST_TIMEOUT) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise UpdateFailed(f"HTTP {resp.status}: {text}")

                data = await resp.json()
                if not isinstance(data, dict):
                    raise UpdateFailed("Unexpected JSON structure")

                _LOGGER.debug("Fetched data for %s: %s", self.station_id, data.keys())
                return data
        except Exception as err:  # noqa: BLE001 - we want to log and wrap
            _LOGGER.exception("Error fetching station %s: %s", self.station_id, err)
            raise UpdateFailed(err)


async def async_setup_platform(
        hass: HomeAssistant,
        config: Dict[str, Any],
        async_add_entities,
        discovery_info=None,
) -> None:
        """Configurazione via YAML: crea sensori per le stazioni elencate in config.

        Schema YAML supportato (vedi README):
            osservaprezzi_carburanti:
                scan_interval: 7200
                stations:
                    - id: 48524
                        name: "Distributore Ener Coop"
        """
    yaml = hass.data.get(DOMAIN, {}).get("yaml_config", {}) or {}
    stations = yaml.get("stations", [])
    scan_interval = yaml.get("scan_interval", DEFAULT_SCAN_INTERVAL)

    hass.data.setdefault(DATA_COORDINATORS, {})

    entities: List[SensorEntity] = []

    for station in stations:
        station_id = station.get("id")
        if station_id is None:
            _LOGGER.warning("Skipping station without id in YAML: %s", station)
            continue
        try:
            station_id_int = int(station_id)
        except (TypeError, ValueError):
            _LOGGER.warning("Invalid station id '%s', skipping", station_id)
            continue

        coordinator = StationDataUpdateCoordinator(hass, station_id_int, scan_interval)
        # store coordinator for later reference
        hass.data[DATA_COORDINATORS][station_id_int] = coordinator

        # Do an initial refresh (non-blocking pattern: refresh now to populate entities)
        await coordinator.async_request_refresh()

        data = coordinator.data or {}

        # Create meta sensor (one per station)
        entities.append(StationMetaSensor(coordinator, station))

        # Extract fuels list robustly
        fuels = data.get("fuels") or data.get("carburanti") or []
        if not isinstance(fuels, list):
            fuels = []

        if fuels:
            for fuel in fuels:
                name = fuel.get("name") or fuel.get("fuel") or fuel.get("description")
                is_self = bool(fuel.get("isSelf") or fuel.get("is_self") or False)
                entities.append(FuelPriceSensor(coordinator, station, name, is_self))
        else:
            # No fuels returned yet: create a generic sensor to surface unavailability
            entities.append(FuelPriceSensor(coordinator, station, None, True))

    if entities:
        async_add_entities(entities, True)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    """Set up sensors for a config entry.

    A config entry may contain multiple stations in `entry.data['stations']`.
    """
    data = entry.data or {}
    stations = data.get("stations")
    scan_interval = data.get("scan_interval") or DEFAULT_SCAN_INTERVAL

    if not stations:
        # Backwards compatibility: support single station entries
        station_id = data.get("station_id") or data.get("id")
        if station_id is None:
            _LOGGER.error("Config entry %s missing station_id(s)", entry.entry_id)
            return
        stations = [{"id": int(station_id), "name": data.get("name") or ""}]

    hass.data.setdefault(DATA_COORDINATORS, {})

    entities: List[SensorEntity] = []

    for st in stations:
        try:
            station_id_int = int(st.get("id"))
        except (TypeError, ValueError):
            _LOGGER.warning("Skipping invalid station id in entry %s: %s", entry.entry_id, st)
            continue

        coordinator = StationDataUpdateCoordinator(hass, station_id_int, scan_interval)
        # key coordinators by (entry_id, station_id) to allow multiple stations per entry
        hass.data[DATA_COORDINATORS][(entry.entry_id, station_id_int)] = coordinator

        # refresh immediately (per-entry initial refresh)
        try:
            await coordinator.async_config_entry_first_refresh()
        except Exception as err:
            _LOGGER.warning("Initial refresh failed for station %s: %s", station_id_int, err)

        entities.append(StationMetaSensor(coordinator, {"id": station_id_int, "name": st.get("name")}, entry.entry_id))

        fuels = coordinator.data.get("fuels") or coordinator.data.get("carburanti") or []
        if isinstance(fuels, list) and fuels:
            for fuel in fuels:
                fname = fuel.get("name") or fuel.get("fuel") or fuel.get("description")
                is_self = bool(fuel.get("isSelf") or fuel.get("is_self") or False)
                entities.append(FuelPriceSensor(coordinator, {"id": station_id_int, "name": st.get("name")}, fname, is_self, entry.entry_id))
        else:
            entities.append(FuelPriceSensor(coordinator, {"id": station_id_int, "name": st.get("name")}, None, True, entry.entry_id))

    if entities:
        async_add_entities(entities, True)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload sensors for a config entry."""
    # remove coordinators for this entry
    coordinators = hass.data.get(DATA_COORDINATORS, {})
    to_remove = [k for k in coordinators.keys() if isinstance(k, tuple) and k[0] == entry.entry_id]
    for k in to_remove:
        coordinators.pop(k, None)
    return True


class StationMetaSensor(SensorEntity):
    """Sensore che espone i metadati dell'impianto come attributi."""

    _attr_icon = DEFAULT_ICON

    def __init__(self, coordinator: StationDataUpdateCoordinator, station_cfg: Dict[str, Any], entry_id: str | None = None):
        self.coordinator = coordinator
        self.station_cfg = station_cfg
        self.entry_id = entry_id
        self.station_id = int(station_cfg.get("id"))
        configured_name = station_cfg.get("name")
        self._name = configured_name or f"Osservaprezzi {self.station_id}"
        # Include entry id in unique_id when available to avoid collisions across entries
        if self.entry_id:
            self._unique_id = f"{DOMAIN}_{self.entry_id}_{self.station_id}_meta"
        else:
            self._unique_id = f"{DOMAIN}_{self.station_id}_meta"

    @property
    def name(self) -> str:
        return self._name

    @property
    def unique_id(self) -> str:
        return self._unique_id

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success

    @property
    def native_value(self) -> StateType:
        # Meta sensor has no numeric state; use station id
        return str(self.station_id)

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        data = self.coordinator.data or {}
        attrs: Dict[str, Any] = {}
        attrs["company"] = data.get("company") or data.get("gestore")
        attrs["name"] = data.get("name") or data.get("description") or self._name
        attrs["address"] = _format_address(data)
        attrs["brand"] = data.get("brand")
        attrs["raw"] = data
        # Se disponibili, aggiungi latitudine/longitudine come attributi separati
        coords = find_coordinates(data)
        if coords:
            attrs["latitude"] = coords[0]
            attrs["longitude"] = coords[1]

        if not self.available:
            attrs["error"] = "unavailable"
        return attrs

    @property
    def device_info(self) -> DeviceInfo:
        # Use entry-scoped identifier when available so each configured entry
        # gets its own device instance for the same real-world station.
        identifier = f"{self.entry_id}_{self.station_id}" if self.entry_id else str(self.station_id)
        return DeviceInfo(
            identifiers={(DOMAIN, identifier)},
            name=self._name,
            manufacturer="Osservaprezzi / MIMIT",
        )


class FuelPriceSensor(SensorEntity):
    """Sensor exposing price for a fuel at a station in self/servito mode."""

    _attr_icon = DEFAULT_ICON

    def __init__(
        self,
        coordinator: StationDataUpdateCoordinator,
        station_cfg: Dict[str, Any],
        fuel_name: Optional[str],
        is_self: bool,
        entry_id: str | None = None,
    ) -> None:
        self.coordinator = coordinator
        self.station_cfg = station_cfg
        self.entry_id = entry_id
        self.station_id = int(station_cfg.get("id"))
        self.configured_name = station_cfg.get("name")
        self.fuel_name = fuel_name or "unknown"
        self.is_self = is_self
        mode = "self" if is_self else "attended"
        normalized = _normalize(self.fuel_name)
        # Unique id includes entry id when available to prevent collisions
        if entry_id:
            self._unique_id = f"{DOMAIN}_{entry_id}_{self.station_id}_{normalized}_{mode}"
        else:
            self._unique_id = f"{DOMAIN}_{self.station_id}_{normalized}_{mode}"

        base_name = self.configured_name or (coordinator.data or {}).get("name") or f"Station {self.station_id}"
        # Produce a clearer, user-friendly entity name
        mode_label = "Self" if is_self else "Servito"
        self._name = f"{base_name} — {self.fuel_name} ({mode_label})"

    @property
    def name(self) -> str:
        return self._name

    @property
    def unique_id(self) -> str:
        return self._unique_id

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success

    @property
    def native_value(self) -> StateType:
        data = self.coordinator.data or {}
        fuels = data.get("fuels") or data.get("carburanti") or []
        if not fuels:
            return None
        for f in fuels:
            candidate = f.get("name") or f.get("fuel") or f.get("description")
            candidate_is_self = bool(f.get("isSelf") or f.get("is_self") or False)
            if str(candidate).lower() == str(self.fuel_name).lower() and candidate_is_self == self.is_self:
                price = f.get("price") or f.get("prezzo")
                try:
                    return float(price) if price is not None else None
                except (TypeError, ValueError):
                    return None
        # Fallback: try matching by name only
        for f in fuels:
            candidate = f.get("name") or f.get("fuel") or f.get("description")
            if str(candidate).lower() == str(self.fuel_name).lower():
                price = f.get("price") or f.get("prezzo")
                try:
                    return float(price) if price is not None else None
                except (TypeError, ValueError):
                    return None
        return None

    @property
    def unit_of_measurement(self) -> Optional[str]:
        # We assume €/l for liquid fuels; for kg (metano) the API usually specifies units.
        return "€/l"

    @property
    def native_unit_of_measurement(self) -> Optional[str]:
        # Home Assistant 2025.12 prefers `native_unit_of_measurement` for SensorEntity.
        # Keep `unit_of_measurement` for backward compatibility but provide the
        # modern property to ensure proper compatibility with newer HA releases.
        return "€/l"

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        data = self.coordinator.data or {}
        fuels = data.get("fuels") or data.get("carburanti") or []
        attrs: Dict[str, Any] = {}
        attrs["station_id"] = self.station_id
        attrs["fuel_name"] = self.fuel_name
        attrs["is_self"] = self.is_self
        attrs["company"] = data.get("company") or data.get("gestore")
        attrs["name"] = data.get("name") or data.get("description")
        attrs["address"] = _format_address(data)

        # find matching fuel entry to expose validityDate and raw data
        for f in fuels:
            candidate = f.get("name") or f.get("fuel") or f.get("description")
            candidate_is_self = bool(f.get("isSelf") or f.get("is_self") or False)
            if (not self.fuel_name or str(candidate).lower() == str(self.fuel_name).lower()) and candidate_is_self == self.is_self:
                attrs["raw_fuel"] = f
                validity = f.get("validityDate") or f.get("validity_date")
                if validity:
                    try:
                        # Expecting epoch ms or ISO string. Try parsing robustly.
                        if isinstance(validity, (int, float)):
                            dt = datetime.fromtimestamp(int(validity) / 1000)
                        else:
                            dt = datetime.fromisoformat(str(validity))
                        attrs["validity_date"] = dt.isoformat()
                    except Exception:
                        attrs["validity_date"] = str(validity)
                break

        # Brand logo (if mapped)
        brand = data.get("brand")
        if brand:
            key = str(brand).lower()
            logo = BRAND_LOGOS.get(key) or BRAND_LOGOS.get(key.split()[0]) or BRAND_LOGOS.get("others")
            if logo:
                attrs["brand_logo"] = f"/local/custom_components/{DOMAIN}/assets/brands/{logo}"
        if not self.available:
            attrs["error"] = "unavailable"
        attrs[ATTR_ATTRIBUTION] = "Data from Osservaprezzi (MIMIT)"
        return attrs

    @property
    def device_info(self) -> DeviceInfo:
        base_name = self.configured_name or (self.coordinator.data or {}).get("name") or f"Station {self.station_id}"
        identifier = f"{self.entry_id}_{self.station_id}" if getattr(self, "entry_id", None) else str(self.station_id)
        return DeviceInfo(
            identifiers={(DOMAIN, identifier)},
            name=base_name,
            manufacturer=(self.coordinator.data or {}).get("company") or "Osservaprezzi",
        )
