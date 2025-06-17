from homeassistant import config_entries
import voluptuous as vol
from .const import DOMAIN

class EnergyCollectorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            return self.async_create_entry(title=user_input["name"], data=user_input)
        sensor_entities = [
            e.entity_id for e in self.hass.states.async_all()
            if e.domain == "sensor"
        ]
        schema = vol.Schema({
            vol.Required("name"): str,
            vol.Required("source"): vol.In(sensor_entities)
        })
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
