import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN


class RandomNumberSensorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Random Number Sensor."""

    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            return self.async_create_entry(
                title="Transport ATM Milano Monitor", data=user_input
            )

        data_schema = vol.Schema(
            {
                vol.Required("Line", default=0): cv.string,
                vol.Required("Bus_Stop_Number", default=0): cv.string,
                vol.Required("Refresh_Time_sec", default=30): int,
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )
