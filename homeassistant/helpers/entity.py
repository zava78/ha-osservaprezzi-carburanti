from dataclasses import dataclass


@dataclass
"""RIMOSSO: placeholder per helper `entity` dello shim locale.

Usare la vera `homeassistant.helpers.entity.DeviceInfo` o un mock per i test.
"""

# Stub minimale per `DeviceInfo` (solo placeholder; non usare in produzione)
class DeviceInfo:
    identifiers: set = None
    name: str = None
    manufacturer: str = None
