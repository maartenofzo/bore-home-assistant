
"""Bore sensor platform."""
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the Bore tunnel."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([BoreTunnel(coordinator, entry)])


class BoreTunnel(CoordinatorEntity, SensorEntity):
    """Bore tunnel."""

    def __init__(self, coordinator, entry):
        """Initialize the tunnel."""
        super().__init__(coordinator)
        self._entry = entry

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._entry.entry_id

    @property
    def name(self):
        """Return the name of the tunnel."""
        return self._entry.title

    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": "Bore Tunnel",
            "manufacturer": "https://github.com/ekzhang",
        }

    @property
    def state(self):
        """Return the state of the sensor."""
        return self.coordinator.data.get("status")

    @property
    def icon(self):
        """Return the icon of the sensor."""
        if self.coordinator.data.get("status") == "connected":
            return "mdi:check-circle"
        return "mdi:close-circle"
