from datetime import datetime
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_change
from .const import DOMAIN
import logging

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    source = entry.data["entity_id"]
    name = entry.data["name"]
    async_add_entities([AccurateEnergySensor(hass, name, source)])

class AccurateEnergySensor(SensorEntity):
    def __init__(self, hass, name, source_entity_id):
        self._hass = hass
        self._attr_name = name
        self._source_entity_id = source_entity_id
        self._attr_native_unit_of_measurement = "kWh"
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        self._attr_device_class = SensorDeviceClass.ENERGY
        self._state = 0.0
        self._last_update = None
        self._last_power = None

    async def async_added_to_hass(self):
        self.async_on_remove(
            async_track_state_change_event(
                self._hass, [self._source_entity_id], self._handle_event
            )
        )
        self.async_on_remove(
            async_track_time_change(
                self._hass, self._reset_daily, hour=0, minute=0, second=0
            )
        )

    async def _handle_event(self, event):
        try:
            now = datetime.now()
            new_state = event.data.get("new_state")
            if new_state is None:
                return

            raw = new_state.state
            if raw in ("unknown", "unavailable"):
                return

            power = float(raw)
            if self._last_update is not None and self._last_power is not None:
                delta_sec = (now - self._last_update).total_seconds()
                if 0 < delta_sec < 3600:
                    delta_hr = delta_sec / 3600.0
                    avg_power = (self._last_power + power) / 2.0
                    self._state += (avg_power * delta_hr) / 1000.0  # W to kWh

            self._last_update = now
            self._last_power = power
            self.async_write_ha_state()

        except Exception as e:
            _LOGGER.error(f"[{self.name}] Trapezoidal update error: {e}")

    async def _reset_daily(self, now):
        self._state = 0.0
        self._last_update = None
        self._last_power = None
        self.async_write_ha_state()

    @property
    def native_value(self):
        return round(self._state, 5)
