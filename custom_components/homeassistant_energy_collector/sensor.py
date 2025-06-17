from datetime import datetime
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_change
from .const import DOMAIN
import logging

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    source = entry.data["entity_id"]
    name = entry.data["name"]
    async_add_entities([PolishedEnergySensor(hass, name, source, entry.entry_id)])

class PolishedEnergySensor(SensorEntity):
    def __init__(self, hass, name, source_entity_id, config_entry_id):
        self._hass = hass
        self._attr_name = name
        self._source_entity_id = source_entity_id
        self._attr_unique_id = f"{self._source_entity_id}_daily_kwh"
        self._attr_native_unit_of_measurement = "kWh"
        self._attr_unit_of_measurement = "kWh"  # legacy fallback
        self._attr_icon = "mdi:flash"
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        self._attr_device_class = SensorDeviceClass.ENERGY
        self._attr_has_entity_name = True
        self._attr_config_entry_id = config_entry_id
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._source_entity_id)},
            "name": f"{name} Source",
            "entry_type": "service",
        }

        self._state = 0.0
        self._last_reported = None
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

    async def async_will_remove_from_hass(self):
        _LOGGER.info(f"[{self.name}] Entity removed from Home Assistant")

    async def _handle_event(self, event):
        try:
            now = datetime.now()
            new_state = event.data.get("new_state")
            if new_state is None:
                return

            raw = new_state.state
            if raw in ("unknown", "unavailable"):
                _LOGGER.info(f"[{self.name}] Ignored invalid state: {raw}")
                return

            power = float(raw)

            if self._last_update is not None and self._last_power is not None:
                delta_sec = (now - self._last_update).total_seconds()
                if 0 < delta_sec < 3600:
                    delta_hr = delta_sec / 3600.0
                    avg_power = (self._last_power + power) / 2.0
                    added_energy = (avg_power * delta_hr) / 1000.0

                    _LOGGER.info(f"[{self.name}] Δt={delta_hr:.5f} hr, Pavg={avg_power:.2f} W, ΔE={added_energy:.6f} kWh")

                    if added_energy < 0:
                        _LOGGER.error(f"[{self.name}] Invalid negative energy calc: {added_energy:.6f}")
                    else:
                        self._state += added_energy

            self._last_update = now
            self._last_power = power

            new_rounded = round(self._state, 5)
            if self._last_reported is None or new_rounded > self._last_reported:
                self._last_reported = new_rounded
                self.async_write_ha_state()

        except Exception as e:
            _LOGGER.exception(f"[{self.name}] Exception in energy update: {e}")

    async def _reset_daily(self, now):
        _LOGGER.info(f"[{self.name}] Daily reset: total usage = {round(self._state, 5)} kWh")
        self._state = 0.0
        self._last_reported = None
        self._last_update = None
        self._last_power = None
        self.async_write_ha_state()

    @property
    def native_value(self):
        return round(self._state, 5)
