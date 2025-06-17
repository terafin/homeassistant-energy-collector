from datetime import datetime
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.helpers.event import async_track_state_change, async_track_time_change
from .const import DOMAIN
import logging

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    source = entry.data["entity_id"]
    name = entry.data["name"]
    async_add_entities([EnergyCollectorSensor(hass, name, source)])

class EnergyCollectorSensor(SensorEntity):
    def __init__(self, hass, name, source_entity_id):
        self._hass = hass
        self._attr_name = name
        self._source_entity_id = source_entity_id
        self._attr_native_unit_of_measurement = "kWh"
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        self._attr_device_class = SensorDeviceClass.ENERGY
        self._state = 0.0
        self._last_update = None
        self._last_power = 0.0

    async def async_added_to_hass(self):
        self.async_on_remove(
            async_track_state_change(
                self._hass, self._source_entity_id, self._handle_source_update
            )
        )
        self.async_on_remove(
            async_track_time_change(
                self._hass, self._reset_daily, hour=0, minute=0, second=0
            )
        )

    async def _handle_source_update(self, entity_id, old_state, new_state):
        try:
            now = datetime.now()
            power_str = new_state.state
            if power_str in ("unknown", "unavailable"):
                return

            power = max(float(power_str), 0.0)

            if self._last_update is not None:
                delta_hours = (now - self._last_update).total_seconds() / 3600.0

                if 0 < delta_hours < 3600:
                    avg_power = (self._last_power + power) / 2
                    added_energy = (avg_power * delta_hours) / 1000.0
                    if added_energy >= 0:
                        self._state += added_energy
                    else:
                        _LOGGER.warning(f"[{self.name}] Negative energy calc skipped: {added_energy} kWh")

            self._last_update = now
            self._last_power = power
            self.async_write_ha_state()
        except Exception as e:
            _LOGGER.error(f"[{self.name}] Error updating: {e}")

    async def _reset_daily(self, now):
        self._state = 0.0
        self._last_update = None
        self._last_power = 0.0
        self.async_write_ha_state()

    @property
    def native_value(self):
        return round(self._state, 3)
