from dataclasses import dataclass


@dataclass
class DeviceInfo:
    identifiers: set = None
    name: str = None
    manufacturer: str = None
