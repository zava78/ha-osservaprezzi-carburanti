from datetime import datetime

from custom_components.osservaprezzi_carburanti.sensor import (
    StationMetaSensor,
    FuelPriceSensor,
)
from homeassistant.components.sensor import SensorStateClass


class FakeCoordinator:
    def __init__(self, data, last_ok=True):
        self.data = data
        self.last_update_success = last_ok

    async def async_request_refresh(self):
        return True


def test_meta_and_fuel_sensor_basic():
    data = {
        "company": "ACME Srl",
        "name": "Stazione Test",
        "brand": "eni",
        "address": "Via Roma 1",
        "fuels": [
            {"name": "Benzina", "isSelf": True, "price": "1.659", "validityDate": "2025-01-09T12:00:00"}
        ],
    }

    coord = FakeCoordinator(data, last_ok=True)
    meta = StationMetaSensor(coord, {"id": 123, "name": "Test Stazione"}, entry_id="entry1")
    fuel = FuelPriceSensor(coord, {"id": 123, "name": "Test Stazione"}, "Benzina", True, entry_id="entry1")

    # Meta sensor attributes
    attrs = meta.extra_state_attributes
    assert attrs.get("company") == "ACME Srl"
    assert "address" in attrs

    # Fuel sensor value
    val = fuel.native_value
    assert isinstance(val, float) and abs(val - 1.659) < 0.0001

    # Device info identifiers include entry id
    assert any(str(123) in s for s in list(meta.device_info.identifiers)[0])


def test_unavailable_behavior():
    data = {"company": "ACME", "name": "Stazione Down", "fuels": []}
    coord = FakeCoordinator(data, last_ok=False)
    meta = StationMetaSensor(coord, {"id": 999, "name": "Down"}, entry_id=None)
    fuel = FuelPriceSensor(coord, {"id": 999, "name": "Down"}, None, True, entry_id=None)

    assert not meta.available
    assert meta.extra_state_attributes.get("error") == "unavailable"
    assert not fuel.available
    attrs = fuel.extra_state_attributes
    assert attrs.get("error") == "unavailable"


def test_sensor_description_and_state_class():
    data = {
        "name": "Stazione Desc",
        "fuels": [{"name": "Gasolio", "isSelf": False, "price": "1.899"}],
    }
    coord = FakeCoordinator(data, last_ok=True)
    fuel = FuelPriceSensor(coord, {"id": 7, "name": "Desc"}, "Gasolio", False, entry_id="e7")

    # Check the description presence and state class assigned
    desc = getattr(fuel, "entity_description", None)
    assert desc is not None
    # also check internal attr used for HA 2025.12 compatibility
    assert getattr(fuel, "_attr_state_class", None) == SensorStateClass.MEASUREMENT
