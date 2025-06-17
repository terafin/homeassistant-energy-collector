from datetime import datetime
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_change
import logging

_LOGGER = logging.getLogger(__name__)
DOMAIN = "homeassistant_energy_collector"

async def async_setup_entry(hass, entry, async_add_entities):
    name = entry.data["name"]
    source = entry.data["entity_id"]
    async_add_entities([FinalSensor(hass, name, source, entry.entry_id)], update_before_add=True)

class FinalSensor(SensorEntity):
    def __init__(self, hass, name, source_entity_id, entry_id):
        self._hass = hass
        self._name = name
        self._source = source_entity_id
        self._state = 0.0
        self._last_power = None
        self._last_update = None
        self._attr_name = name
        self._attr_unique_id = f"{source_entity_id.replace('.', '_')}_daily_kwh"
        self._attr_native_unit_of_measurement = "kWh"
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        self._attr_device_class = SensorDeviceClass.ENERGY
        self._attr_should_poll = False
        self._attr_config_entry_id = entry_id

    async def async_added_to_hass(self):
        self.async_on_remove(
            async_track_state_change_event(
                self._hass, [self._source], self._handle_power
            )
        )
        self.async_on_remove(
            async_track_time_change(self._hass, self._reset, hour=0, minute=0, second=0)
        )

    async def _handle_power(self, event):
        now = datetime.now()
        state = event.data.get("new_state")
        if not state or state.state in ("unknown", "unavailable"):
            return
        try:
            power = float(state.state)
        except ValueError:
            return

        if self._last_update and self._last_power is not None:
            delta = (now - self._last_update).total_seconds()
            if 0 < delta < 3600:
                avg = (self._last_power + power) / 2
                self._state += (avg * delta / 3600) / 1000

        self._last_update = now
        self._last_power = power
        self.async_write_ha_state()

    async def _reset(self, now):
        _LOGGER.info(f"[{self._name}] Daily reset at midnight: {round(self._state, 5)} kWh")
        self._state = 0.0
        self._last_update = None
        self._last_power = None
        self.async_write_ha_state()

    @property
    def native_value(self):
        return round(self._state, 5)