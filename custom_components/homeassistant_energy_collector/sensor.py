from datetime import datetime
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_change
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
import logging

_LOGGER = logging.getLogger(__name__)
DOMAIN = "homeassistant_energy_collector"

async def async_setup_entry(hass, entry, async_add_entities):
    source = entry.data["entity_id"]
    name = entry.data["name"]
    entity = SimpleEnergySensor(hass, name, source)
    entity._async_set_entry_id(entry.entry_id)
    async_add_entities([entity], update_before_add=True)

class SimpleEnergySensor(SensorEntity):
    def __init__(self, hass, name, source_entity_id):
        self._hass = hass
        self._name = name
        self._source_entity_id = source_entity_id
        self._state = 0.0
        self._last_update = None
        self._last_power = None
        self._attr_name = name
        self._attr_unique_id = f"{source_entity_id}_daily_kwh"
        self._attr_native_unit_of_measurement = "kWh"
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        self._attr_device_class = SensorDeviceClass.ENERGY

    async def async_added_to_hass(self):
        self.async_on_remove(
            async_track_state_change_event(
                self._hass, [self._source_entity_id], self._handle_event
            )
        )
        self.async_on_remove(
            async_track_time_change(
                self._hass, self._reset, hour=0, minute=0, second=0
            )
        )

    async def _handle_event(self, event):
        try:
            now = datetime.now()
            new_state = event.data.get("new_state")
            if not new_state or new_state.state in ("unknown", "unavailable"):
                return
            power = float(new_state.state)
            if self._last_update and self._last_power is not None:
                delta = (now - self._last_update).total_seconds()
                if 0 < delta < 3600:
                    avg = (self._last_power + power) / 2
                    self._state += (avg * delta / 3600) / 1000
            self._last_update = now
            self._last_power = power
            self.async_write_ha_state()
        except Exception as e:
            _LOGGER.error(f"[{self._name}] Energy update failed: {e}")

    async def _reset(self, _):
        _LOGGER.info(f"[{self._name}] Daily reset: {round(self._state, 5)} kWh")
        self._state = 0
        self._last_update = None
        self._last_power = None
        self.async_write_ha_state()

    @property
    def native_value(self):
        return round(self._state, 5)
