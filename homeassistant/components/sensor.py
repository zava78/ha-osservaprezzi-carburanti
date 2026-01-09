from typing import Any


class SensorEntity:
    def __init__(self):
        self._attr_native_unit_of_measurement = None
        self._attr_state_class = None

    @property
    def name(self) -> str:
        return getattr(self, "_name", "")


class SensorEntityDescription:
    def __init__(self, *, key: str | None = None, name: str | None = None, native_unit_of_measurement: Any = None, state_class: Any = None, **kwargs):
        self.key = key
        self.name = name
        self.native_unit_of_measurement = native_unit_of_measurement
        self.state_class = state_class


class SensorStateClass:
    MEASUREMENT = "measurement"
