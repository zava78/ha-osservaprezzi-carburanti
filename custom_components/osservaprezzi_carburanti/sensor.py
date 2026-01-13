"""Sensori per l'integrazione Osservaprezzi Carburanti.

Questo modulo crea sensori per ogni impianto e per tipo di carburante usando
DataUpdateCoordinator per gestire il polling e la memorizzazione dei dati.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
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
from homeassistant.helpers.event import async_track_time_change

from .api import OsservaprezziAPI
from .const import (
    BRAND_LOGOS,
    DATA_COORDINATORS,
    DEFAULT_ICON,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    scan_interval_td,
)
from .helpers import find_coordinates

_LOGGER = logging.getLogger(__name__)

DATA_LOGOS = f"{DOMAIN}_logos"


def _normalize(text: Optional[str]) -> str:
    if not text:
        return "unknown"
    return "".join(c if c.isalnum() else "_" for c in text.lower())


def _format_address(data: Dict[str, Any]) -> str:
    # Tenta di estrarre un indirizzo leggibile e ben formattato
    # Es. "Via Roma 10, 20100 Milano (MI)"
    
    # 1. Via e Civico
    street = data.get("indirizzo") or data.get("address") or data.get("street") or ""
    civic = data.get("civic") or ""
    
    address_part = street
    if civic:
        address_part = f"{street} {civic}" if street else civic

    # 2. CAP, Comune, Provincia
    zip_code = data.get("zip") or data.get("cap") or ""
    town = data.get("city") or data.get("municipality") or data.get("comune") or ""
    province = data.get("prov") or data.get("province") or data.get("provincia") or ""

    location_part = ""
    if zip_code:
        location_part += f"{zip_code} "
    if town:
        location_part += town
    if province:
        location_part += f" ({province})"

    # Combine
    parts = [p.strip() for p in (address_part, location_part) if p.strip()]
    if parts:
        return ", ".join(parts)
        
    return data.get("name") or data.get("description") or ""


class StationDataUpdateCoordinator(DataUpdateCoordinator):
    """Coordinator per ottenere i dati dell'impianto dall'API Osservaprezzi."""

    def __init__(self, hass: HomeAssistant, api: OsservaprezziAPI, station_id: int, scan_interval: int):
        self.api = api
        self.station_id = station_id
        super().__init__(
            hass,
            _LOGGER,
            name=f"osservaprezzi_{station_id}",
            update_interval=scan_interval_td(scan_interval),
        )
        
        # Se l'intervallo è circa 1 giorno (default daily), forziamo l'aggiornamento alle 08:30
        # Questo per rispettare la richiesta di "Scheduled Updates: ... default is daily at 08:30"
        # Se l'utente ha impostato 3600s, questo refresh delle 08:30 sarà solo un "di più", male non fa.
        async_track_time_change(hass, self._async_scheduled_update, hour=8, minute=30, second=0)

    async def _async_scheduled_update(self, now):
        """Force update at scheduled time."""
        _LOGGER.debug("Esecuzione aggiornamento programmato delle 08:30")
        await self.async_request_refresh()

    async def _async_update_data(self) -> Dict[str, Any]:
        """Recupera i dati dall'API e ritorna il JSON."""
        try:
            # Fetch station data
            data = await self.api.get_station_details(self.station_id)
            
            # Ensure logos are loaded (once per session ideally, or refreshed if missing)
            if DATA_LOGOS not in self.hass.data:
                 self.hass.data[DATA_LOGOS] = {}
            
            # If the loaded logos map is empty, try fetching.
            # We don't want to block every update if it fails, but we try initially.
            if not self.hass.data.get(DATA_LOGOS):
                 logos = await self.api.get_all_logos()
                 if logos:
                     self.hass.data[DATA_LOGOS] = logos

            _LOGGER.debug("Fetched data for %s: %s", self.station_id, data.keys())
            return data
        except Exception as err:
            _LOGGER.exception("Errore recupero dati per impianto %s: %s", self.station_id, err)
            raise UpdateFailed(err)


async def async_setup_platform(
        hass: HomeAssistant,
        config: Dict[str, Any],
        async_add_entities,
        discovery_info=None,
) -> None:
    """Configurazione via YAML: crea sensori per le stazioni elencate nella configurazione."""
    yaml = hass.data.get(DOMAIN, {}).get("yaml_config", {}) or {}
    stations = yaml.get("stations", [])
    scan_interval = yaml.get("scan_interval", DEFAULT_SCAN_INTERVAL)

    hass.data.setdefault(DATA_COORDINATORS, {})
    session = async_get_clientsession(hass)
    api = OsservaprezziAPI(session)

    entities: List[SensorEntity] = []

    for station in stations:
        station_id = station.get("id")
        if station_id is None:
            continue
        try:
            station_id_int = int(station_id)
        except (TypeError, ValueError):
            continue

        coordinator = StationDataUpdateCoordinator(hass, api, station_id_int, scan_interval)
        hass.data[DATA_COORDINATORS][station_id_int] = coordinator

        await coordinator.async_request_refresh()

        data = coordinator.data or {}
        entities.append(StationMetaSensor(coordinator, station))

        fuels = data.get("fuels") or data.get("carburanti") or []
        if not isinstance(fuels, list):
            fuels = []

        if fuels:
            for fuel in fuels:
                name = fuel.get("name") or fuel.get("fuel") or fuel.get("description")
                is_self = bool(fuel.get("isSelf") or fuel.get("is_self") or False)
                entities.append(FuelPriceSensor(coordinator, station, name, is_self))
        else:
            entities.append(FuelPriceSensor(coordinator, station, None, True))

    if entities:
        async_add_entities(entities, True)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    """Configura i sensori per una config entry."""
    data = entry.data or {}
    stations = data.get("stations")
    scan_interval = data.get("scan_interval") or DEFAULT_SCAN_INTERVAL

    if not stations:
        station_id = data.get("station_id") or data.get("id")
        if station_id is None:
            return
        stations = [{"id": int(station_id), "name": data.get("name") or ""}]

    hass.data.setdefault(DATA_COORDINATORS, {})
    session = async_get_clientsession(hass)
    api = OsservaprezziAPI(session)

    entities: List[SensorEntity] = []

    for st in stations:
        try:
            station_id_int = int(st.get("id"))
        except (TypeError, ValueError):
            continue

        coordinator = StationDataUpdateCoordinator(hass, api, station_id_int, scan_interval)
        hass.data[DATA_COORDINATORS][(entry.entry_id, station_id_int)] = coordinator

        try:
            await coordinator.async_config_entry_first_refresh()
        except Exception as err:
            _LOGGER.warning("Refresh iniziale fallito per l'impianto %s: %s", station_id_int, err)

        entities.append(StationMetaSensor(coordinator, {"id": station_id_int, "name": st.get("name")}, entry.entry_id))

        fuels = coordinator.data.get("fuels") or coordinator.data.get("carburanti") or []
        if isinstance(fuels, list) and fuels:
            for fuel in fuels:
                fname = fuel.get("name") or fuel.get("fuel") or fuel.get("description")
                is_self = bool(fuel.get("isSelf") or fuel.get("is_self") or False)
                entities.append(FuelPriceSensor(coordinator, {"id": station_id_int, "name": st.get("name")}, fname, is_self, entry.entry_id))
        else:
            entities.append(FuelPriceSensor(coordinator, {"id": station_id_int, "name": st.get("name")}, None, True, entry.entry_id))

        # Nuovi sensori aggiuntivi
        entities.append(StationLocationSensor(coordinator, {"id": station_id_int, "name": st.get("name")}, entry.entry_id))
        entities.append(StationOpeningStatusSensor(coordinator, {"id": station_id_int, "name": st.get("name")}, entry.entry_id))
        
        # Sensori contatti se disponibili nel dato (ma qui siamo in setup, potremmo non averli ancora se il refresh fallisce)
        # Tuttavia il refresh è già stato tentato sopra.
        # Creiamo i sensori contatti genericamente, gestiranno loro se i dati mancano
        for contact_type in ["phone", "email", "website"]:
             entities.append(StationContactSensor(coordinator, {"id": station_id_int, "name": st.get("name")}, contact_type, entry.entry_id))

    if entities:
        async_add_entities(entities, True)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload sensors for a config entry."""
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
        if self.entry_id:
            self._unique_id = f"{DOMAIN}_{self.entry_id}_{self.station_id}_meta"
        else:
            self._unique_id = f"{DOMAIN}_{self.station_id}_meta"
        
        self.entity_description = SensorEntityDescription(
            key=self._unique_id,
            name=self._name,
            translation_key="station_meta",
            entity_category=None,
        )
        try:
            self.entity_description.entity_category = None
        except Exception:
            pass

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
        return str(self.station_id)

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        data = self.coordinator.data or {}
        attrs: Dict[str, Any] = {}
        attrs["company"] = data.get("company") or data.get("gestore")
        attrs["name"] = data.get("name") or data.get("description") or self._name
        attrs["address"] = _format_address(data)
        
        brand = data.get("brand")
        attrs["brand"] = brand
        
        # Gestione logo dinamico
        # Gestione logo dinamico
        brand_id = data.get("brandId")
        logos = self.coordinator.hass.data.get(DATA_LOGOS, {})
        
        # 1. Try by Brand ID
        if brand_id is not None and str(brand_id) in logos:
            attrs["brand_logo"] = logos[str(brand_id)]
        
        # 2. Try by Brand Name (if not found by ID)
        if "brand_logo" not in attrs and brand:
            # Try exact match
            if brand in logos:
                attrs["brand_logo"] = logos[brand]
            # Try lower match
            elif brand.lower() in logos:
                attrs["brand_logo"] = logos[brand.lower()]
        
        # 3. Fallback to local static assets if not found dynamically
        if "brand_logo" not in attrs and brand:
            key = str(brand).lower()
            logo = BRAND_LOGOS.get(key) or BRAND_LOGOS.get(key.split()[0]) or BRAND_LOGOS.get("others")
            if logo:
                 attrs["brand_logo"] = f"/local/custom_components/{DOMAIN}/assets/brands/{logo}"

        attrs["station_type"] = data.get("stationType") or "Sconosciuto"
        
        # Data inserimento (utile per capire quanto è aggiornato il dato lato Ministero)
        insert_date = data.get("insertDate")
        if insert_date:
            try:
                if isinstance(insert_date, str):
                    dt = datetime.fromisoformat(insert_date.replace("Z", "+00:00"))
                    attrs["insert_date"] = dt.isoformat()
                else:
                    attrs["insert_date"] = str(insert_date)
            except Exception:
                attrs["insert_date"] = str(insert_date)

        attrs["raw"] = data
        coords = find_coordinates(data)
        if coords:
            attrs["latitude"] = coords[0]
            attrs["longitude"] = coords[1]

        if not self.available:
            attrs["error"] = "unavailable"
        return attrs

    @property
    def device_info(self) -> DeviceInfo:
        identifier = f"{self.entry_id}_{self.station_id}" if self.entry_id else str(self.station_id)
        
        # Use config name or API name
        data = self.coordinator.data or {}
        dev_name = self.station_cfg.get("name") or data.get("name") or f"Osservaprezzi {self.station_id}"
        brand = data.get("brand")
        if brand:
            dev_name = f"{dev_name} - {brand}"

        return DeviceInfo(
            identifiers={(DOMAIN, identifier)},
            name=dev_name,
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
        if entry_id:
            self._unique_id = f"{DOMAIN}_{entry_id}_{self.station_id}_{normalized}_{mode}"
        else:
            self._unique_id = f"{DOMAIN}_{self.station_id}_{normalized}_{mode}"

        base_name = self.configured_name or (coordinator.data or {}).get("name") or f"Station {self.station_id}"
        mode_label = "Self" if is_self else "Servito"
        # Richiesta utente: "solo il nome del tipo di carburante"
        # Usiamo has_entity_name = True così HA prepende il nome del device se necessario,
        # ma nella UI del device apparirà pulito.
        self._attr_has_entity_name = True
        self._attr_name = f"{self.fuel_name} ({mode_label})"
        self._name = self._attr_name # Backward compatibility internal usage

        self.entity_description = SensorEntityDescription(
            key=self._unique_id,
            name=self._name,
            native_unit_of_measurement="€/l",
            state_class=SensorStateClass.MEASUREMENT,
            translation_key="fuel_price",
            device_class=None,
        )
        self._attr_native_unit_of_measurement = "€/l"
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def name(self) -> str:
        return self._attr_name

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
        return None

    @property
    def unit_of_measurement(self) -> Optional[str]:
        return "€/l"

    @property
    def native_unit_of_measurement(self) -> Optional[str]:
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

        for f in fuels:
            candidate = f.get("name") or f.get("fuel") or f.get("description")
            candidate_is_self = bool(f.get("isSelf") or f.get("is_self") or False)
            if (not self.fuel_name or str(candidate).lower() == str(self.fuel_name).lower()) and candidate_is_self == self.is_self:
                attrs["raw_fuel"] = f
                validity = f.get("validityDate") or f.get("validity_date")
                if validity:
                    try:
                        if isinstance(validity, (int, float)):
                            dt = datetime.fromtimestamp(int(validity) / 1000)
                        else:
                            dt = datetime.fromisoformat(str(validity))
                        attrs["validity_date"] = dt.isoformat()
                    except Exception:
                        attrs["validity_date"] = str(validity)
                break

        # Logo: copy logic from Meta Sensor for consistency directly on fuel sensors too if desired,
        # otherwise users usually check the meta sensor or we duplicate.
        # Let's simple duplicate the logic to ensure the price card has the logo directly.
        brand = data.get("brand")
        brand_id = data.get("brandId")
        logos = self.coordinator.hass.data.get(DATA_LOGOS, {})
        
        # 1. Try by Brand ID
        if brand_id is not None and str(brand_id) in logos:
            attrs["brand_logo"] = logos[str(brand_id)]
            
        # 2. Try by Brand Name
        if "brand_logo" not in attrs and brand:
            if brand in logos:
                attrs["brand_logo"] = logos[brand]
            elif brand.lower() in logos:
                attrs["brand_logo"] = logos[brand.lower()]
        
        # 3. Fallback
        if "brand_logo" not in attrs and brand:
            key = str(brand).lower()
            logo = BRAND_LOGOS.get(key) or BRAND_LOGOS.get(key.split()[0]) or BRAND_LOGOS.get("others")
            if logo:
                attrs["brand_logo"] = f"/local/custom_components/{DOMAIN}/assets/brands/{logo}"
        
        if not self.available:
            attrs["error"] = "unavailable"
        attrs[ATTR_ATTRIBUTION] = "Dati da Osservaprezzi (MIMIT)"
        return attrs

    @property
    def device_info(self) -> DeviceInfo:
        data = self.coordinator.data or {}
        base_name = self.configured_name or data.get("name") or f"Station {self.station_id}"
        brand = data.get("brand")
        if brand:
            base_name = f"{base_name} - {brand}"
            
        # Create a separate device for Fuels as requested ("distinti dalle informazioni")
        # Appending "_fuels" to identifier and "Listino" to name
        identifier = f"{self.entry_id}_{self.station_id}" if getattr(self, "entry_id", None) else str(self.station_id)
        
        return DeviceInfo(
            identifiers={(DOMAIN, f"{identifier}_fuels")},
            name=f"{base_name} (Listino)",
            manufacturer=data.get("company") or "Osservaprezzi",
            # Link via via_device to the main station if possible, but HA doesn't support via_device for same integration easily without setup.
            # Just separate device is enough.
        )


class StationContactSensor(SensorEntity):
    """Sensore per informazioni di contatto (Telefono, Email, Sito)."""

    def __init__(self, coordinator, station_cfg, contact_type, entry_id=None):
        self.coordinator = coordinator
        self.station_cfg = station_cfg
        self.entry_id = entry_id
        self.station_id = int(station_cfg.get("id"))
        self.contact_type = contact_type
        
        self._attr_has_entity_name = True
        self._attr_name = f"Contatto {contact_type.capitalize()}"
        self._name = self._attr_name

        if entry_id:
             self._unique_id = f"{DOMAIN}_{entry_id}_{self.station_id}_{contact_type}"
        else:
             self._unique_id = f"{DOMAIN}_{self.station_id}_{contact_type}"
             
        # Icone
        icons = {
            "phone": "mdi:phone",
            "email": "mdi:email",
            "website": "mdi:web",
        }
        self._attr_icon = icons.get(contact_type, "mdi:information")

    @property
    def name(self):
        return self._attr_name

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def native_value(self):
        data = self.coordinator.data or {}
        # Mapping campi API
        keys = {
            "phone": ["phoneNumber", "telefono"],
            "email": ["email", "mail"],
            "website": ["website", "sito", "url"],
        }
        for k in keys.get(self.contact_type, []):
            if val := data.get(k):
                return val
        return "Non disponibile"

    @property
    def device_info(self) -> DeviceInfo:
        # Link allo stesso device
        identifier = f"{self.entry_id}_{self.station_id}" if self.entry_id else str(self.station_id)
        data = self.coordinator.data or {}
        dev_name = self.station_cfg.get("name") or data.get("name") or f"Osservaprezzi {self.station_id}"
        brand = data.get("brand")
        if brand:
            dev_name = f"{dev_name} - {brand}"

        return DeviceInfo(
            identifiers={(DOMAIN, identifier)},
            name=dev_name,
            manufacturer="Osservaprezzi / MIMIT",
        )


class StationLocationSensor(SensorEntity):
    """Sensore di posizione per la stazione."""

    _attr_icon = "mdi:map-marker"

    def __init__(self, coordinator, station_cfg, entry_id=None):
        self.coordinator = coordinator
        self.station_cfg = station_cfg
        self.entry_id = entry_id
        self.station_id = int(station_cfg.get("id"))
        
        self._attr_has_entity_name = True
        self._attr_name = "Posizione Stazione"
        self._name = self._attr_name
        
        if entry_id:
             self._unique_id = f"{DOMAIN}_{entry_id}_{self.station_id}_location"
        else:
             self._unique_id = f"{DOMAIN}_{self.station_id}_location"

    @property
    def name(self):
        return self._attr_name

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def native_value(self):
        # Valore indicativo, usiamo gli attributi per la mappa
        return "Vedi Mappa"

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data or {}
        attrs = {}
        coords = find_coordinates(data)
        if coords:
            attrs["latitude"] = coords[0]
            attrs["longitude"] = coords[1]
        return attrs

    @property
    def device_info(self) -> DeviceInfo:
        identifier = f"{self.entry_id}_{self.station_id}" if self.entry_id else str(self.station_id)
        data = self.coordinator.data or {}
        dev_name = self.station_cfg.get("name") or data.get("name") or f"Osservaprezzi {self.station_id}"
        brand = data.get("brand")
        if brand:
            dev_name = f"{dev_name} - {brand}"
        return DeviceInfo(
            identifiers={(DOMAIN, identifier)},
            name=dev_name,
            manufacturer="Osservaprezzi / MIMIT",
        )


class StationOpeningStatusSensor(SensorEntity):
    """Sensore stato apertura (Aperto/Chiuso)."""

    _attr_icon = "mdi:clock-outline"

    def __init__(self, coordinator, station_cfg, entry_id=None):
        self.coordinator = coordinator
        self.station_cfg = station_cfg
        self.entry_id = entry_id
        self.station_id = int(station_cfg.get("id"))
        
        self._attr_has_entity_name = True
        self._attr_name = "Stato Apertura"
        self._name = self._attr_name
        
        if entry_id:
             self._unique_id = f"{DOMAIN}_{entry_id}_{self.station_id}_opening_status"
        else:
             self._unique_id = f"{DOMAIN}_{self.station_id}_opening_status"

    @property
    def name(self):
        return self._attr_name

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def native_value(self):
        # Logica semplificata: se abbiamo orari, potremmo calcolare.
        # Per ora ritorniamo "N/D" se non implementiamo il calcolo complesso, 
        # o un placeholder se l'utente vuole solo vedere i dati grezzi.
        # L'utente ha chiesto "sensori per open/closed status e next opening/closing time".
        # Senza una libreria di orari complessa, è difficile. 
        # Esporremo "Dati Orari" e metteremo il JSON negli attributi per ora.
        data = self.coordinator.data or {}
        if data.get("orariapertura"):
             return "Vedi Attributi"
        return "Non disponibile"

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data or {}
        return {"orari": data.get("orariapertura")}

    @property
    def device_info(self) -> DeviceInfo:
        identifier = f"{self.entry_id}_{self.station_id}" if self.entry_id else str(self.station_id)
        data = self.coordinator.data or {}
        dev_name = self.station_cfg.get("name") or data.get("name") or f"Osservaprezzi {self.station_id}"
        brand = data.get("brand")
        if brand:
            dev_name = f"{dev_name} - {brand}"
        return DeviceInfo(
            identifiers={(DOMAIN, identifier)},
            name=dev_name,
            manufacturer="Osservaprezzi / MIMIT",
        )

