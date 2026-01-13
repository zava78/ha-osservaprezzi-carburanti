"""Sensori binari per i servizi della stazione."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DATA_COORDINATORS, DOMAIN

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Configura i sensori binari da una config entry."""
    coordinators = hass.data.get(DATA_COORDINATORS, {})
    
    # Trova i coordinator associati a questa entry
    entry_coordinators = [
        c for k, c in coordinators.items() 
        if isinstance(k, tuple) and k[0] == entry.entry_id
    ]

    entities = []
    for coordinator in entry_coordinators:
        # Recupera dati stazione
        data = coordinator.data or {}
        # I servizi potrebbero essere una lista di stringhe o oggetti
        services = data.get("services") or []
        
        # Se servizi è una lista di dict/objects con 'description', adattalo
        # Assumiamo per ora sia una lista di nomi o oggetti semplici
        if services:
             for service in services:
                 # Gestione fallback se service è dict o str
                 svc_name = service if isinstance(service, str) else service.get("name") or service.get("description")
                 if svc_name:
                     entities.append(StationServiceSensor(coordinator, svc_name, entry.entry_id))

    if entities:
        async_add_entities(entities)


class StationServiceSensor(CoordinatorEntity, BinarySensorEntity):
    """Sensore binario che indica la presenza di un servizio."""

    def __init__(self, coordinator, service_name, entry_id):
        super().__init__(coordinator)
        self.service_name = service_name
        self.entry_id = entry_id
        self.station_id = coordinator.station_id
        
        # Normalizza nome per ID
        friendly_id = "".join(c if c.isalnum() else "_" for c in service_name.lower())
        
        self._unique_id = f"{DOMAIN}_{entry_id}_{self.station_id}_service_{friendly_id}"
        self._attr_name = f"Servizio {service_name}"
        self._attr_is_on = True # Se è nella lista, è attivo
        
    @property
    def unique_id(self) -> str:
        return self._unique_id

    @property
    def device_info(self) -> DeviceInfo:
        # Link allo stesso device della stazione
        identifier = f"{self.entry_id}_{self.station_id}"
        data = self.coordinator.data or {}
        dev_name = data.get("name") or f"Stazione {self.station_id}"
        brand = data.get("brand")
        if brand:
            dev_name = f"{dev_name} - {brand}"

        return DeviceInfo(
            identifiers={(DOMAIN, identifier)},
            name=dev_name,
            manufacturer="Osservaprezzi / MIMIT",
        )
