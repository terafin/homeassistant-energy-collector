from datetime import datetime
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_change
from homeassistant.helpers import device_registry as dr
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    name = entry.data["name"]
    source = entry.data["source"]
    device_registry = dr.async_get(hass)
    device = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.entry_id)},
        name=name,
        manufacturer="Energy Collector",
        model="Daily Power Accumulator",
    )
    entity = EnergyCollectorSensor(hass, name, source, entry.entry_id)
    async_add_entities([entity], update_before_add=True)

class EnergyCollectorSensor(SensorEntity):
    def __init__(self, hass, name, source_entity_id, entry_id):
        self._hass = hass
        self._name = name
        self._source_entity_id = source_entity_id
        self._entry_id = entry_id
        self._state = 0.0
        self._last_update = None
        self._last_power = None
        self._attr_name = name
        self._attr_unique_id = f"{DOMAIN}_{source_entity_id.replace('.', '_')}_daily_kwh"
        self._attr_native_unit_of_measurement = "kWh"
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        self._attr_device_class = SensorDeviceClass.ENERGY
        self._attr_should_poll = False

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._entry_id)},
            "name": self._name,
            "manufacturer": "Energy Collector",
            "model": "Daily Power Accumulator"
        }

    async def async_added_to_hass(self):
        self.async_on_remove(
            async_track_state_change_event(
                self._hass, [self._source_entity_id], self._handle_power_change
            )
        )
        self.async_on_remove(
            async_track_time_change(
                self._hass, self._reset_daily, hour=0, minute=0, second=0
            )
        )

    async def _handle_power_change(self, event):
        now = datetime.now()
        new_state = event.data.get("new_state")
        if not new_state or new_state.state in ("unknown", "unavailable"):
            return
        try:
            power = float(new_state.state)
        except ValueError:
            return

        if self._last_update is not None and self._last_power is not None:
            elapsed = (now - self._last_update).total_seconds()
            if 0 < elapsed < 3600:
                avg_power = (self._last_power + power) / 2
                self._state += (avg_power * elapsed / 3600) / 1000

        self._last_update = now
        self._last_power = power
        self.async_write_ha_state()

    async def _reset_daily(self, now):
        self._state = 0.0
        self._last_update = None
        self._last_power = None
        self.async_write_ha_state()

    @property
    def native_value(self):
        return round(self._state, 5)
