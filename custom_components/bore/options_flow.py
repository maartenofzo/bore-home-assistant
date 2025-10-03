
"""Options flow for Bore."""
import voluptuous as vol
from homeassistant.config_entries import OptionsFlow
from homeassistant.const import CONF_PORT, CONF_SECRET
from .const import (
    DOMAIN,
    CONF_LOCAL_HOST,
    CONF_LOCAL_PORT,
    CONF_TO,
    CONF_CHECK_URL,
    CONF_UPDATE_INTERVAL,
    DEFAULT_LOCAL_HOST,
    DEFAULT_PORT,
    DEFAULT_UPDATE_INTERVAL,
    UPDATE_INTERVALS,
)

class BoreOptionsFlow(OptionsFlow):
    """Bore options flow."""

    def __init__(self, config_entry):
        """Initialize the options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Handle a flow initialized by the user."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_TO, default=self.config_entry.options.get(CONF_TO)
                    ): str,
                    vol.Required(
                        CONF_LOCAL_PORT,
                        default=self.config_entry.options.get(CONF_LOCAL_PORT),
                    ): int,
                    vol.Optional(
                        CONF_LOCAL_HOST,
                        default=self.config_entry.options.get(
                            CONF_LOCAL_HOST, DEFAULT_LOCAL_HOST
                        ),
                    ): str,
                    vol.Optional(
                        CONF_PORT,
                        default=self.config_entry.options.get(CONF_PORT, DEFAULT_PORT),
                    ): int,
                    vol.Optional(
                        CONF_SECRET,
                        default=self.config_entry.options.get(CONF_SECRET),
                    ): str,
                    vol.Optional(
                        CONF_CHECK_URL,
                        default=self.config_entry.options.get(CONF_CHECK_URL),
                    ): str,
                    vol.Optional(
                        CONF_UPDATE_INTERVAL,
                        default=self.config_entry.options.get(
                            CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
                        ),
                    ): vol.In(UPDATE_INTERVALS),
                }
            ),
        )
