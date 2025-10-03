
"""Config flow for Bore."""
import voluptuous as vol
from homeassistant.config_entries import ConfigFlow
from homeassistant.const import CONF_PORT
from .const import (
    DOMAIN,
    CONF_LOCAL_HOST,
    CONF_LOCAL_PORT,
    CONF_TO,
    CONF_SECRET,
    CONF_CHECK_URL,
    CONF_UPDATE_INTERVAL,
    DEFAULT_LOCAL_HOST,
    DEFAULT_PORT,
    DEFAULT_UPDATE_INTERVAL,
    UPDATE_INTERVALS,
)

from .options_flow import BoreOptionsFlow

import logging

_LOGGER = logging.getLogger(__name__)

class BoreConfigFlow(ConfigFlow, domain=DOMAIN):
    """Bore config flow."""

    VERSION = 1

    @staticmethod
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return BoreOptionsFlow(config_entry)

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        _LOGGER.debug("Bore config flow started")
        errors = {}

        if user_input is not None:
            return self.async_create_entry(title=user_input[CONF_TO], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_TO): str,
                    vol.Required(CONF_LOCAL_PORT): int,
                    vol.Optional(CONF_LOCAL_HOST, default=DEFAULT_LOCAL_HOST): str,
                    vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
                    vol.Optional(CONF_SECRET): str,
                    vol.Optional(CONF_CHECK_URL): str,
                    vol.Optional(
                        CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL
                    ): vol.In(UPDATE_INTERVALS),
                }
            ),
            errors=errors,
        )
