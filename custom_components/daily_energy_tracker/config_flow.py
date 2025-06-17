import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector
from homeassistant.const import CONF_NAME, CONF_ENTITY_ID
from .const import DOMAIN

class DailyEnergyTrackerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_NAME): str,
                vol.Required(CONF_ENTITY_ID): selector.selector({
                    "entity": {
                        "domain": "sensor"
                    }
                })
            })
        )
