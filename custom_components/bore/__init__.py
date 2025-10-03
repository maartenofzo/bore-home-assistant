
"""The Bore integration."""
import asyncio
import logging
from datetime import timedelta

import async_timeout
import httpx
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    CONF_LOCAL_PORT,
    CONF_LOCAL_HOST,
    CONF_TO,
    CONF_PORT,
    CONF_SECRET,
    CONF_CHECK_URL,
    CONF_UPDATE_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Bore from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    coordinator = BoreDataUpdateCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    entry.async_on_unload(entry.add_update_listener(update_listener))

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "sensor")
    )

    return True


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_forward_entry_unload(entry, "sensor")
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


def get_update_interval(update_interval: str) -> timedelta:
    """Return the update interval as a timedelta."""
    parts = update_interval.split()
    if len(parts) != 2:
        raise ValueError(f"Invalid update interval: {update_interval}")

    value = int(parts[0])
    unit = parts[1]

    if unit in ["second", "seconds"]:
        return timedelta(seconds=value)
    if unit in ["minute", "minutes"]:
        return timedelta(minutes=value)
    if unit in ["hour", "hours"]:
        return timedelta(hours=value)

    raise ValueError(f"Invalid update interval unit: {unit}")


class BoreDataUpdateCoordinator(DataUpdateCoordinator):
    """Bore data update coordinator."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self.entry = entry
        self.hass = hass
        update_interval = get_update_interval(
            self.entry.options.get(CONF_UPDATE_INTERVAL, self.entry.data[CONF_UPDATE_INTERVAL])
        )

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )

        self._bore_process = None
        self._assigned_port = None

    @property
    def config_data(self):
        """Return the config data."""
        return self.entry.options or self.entry.data

    async def _async_update_data(self):
        """Fetch data from the Bore tunnel."""
        if not self._bore_process:
            await self._start_bore_process()

        check_url = self.entry.data.get(CONF_CHECK_URL)
        if not check_url and self._assigned_port:
            check_url = f"http://{self.entry.data[CONF_TO]}:{self._assigned_port}"

        if not check_url:
            return {"status": "connected"}  # Assume connected if no check url

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(check_url)
                response.raise_for_status()
            return {"status": "connected"}
        except httpx.HTTPStatusError as ex:
            _LOGGER.error("HTTP status error on %s: %s", check_url, ex)
            raise UpdateFailed(f"HTTP status error: {ex.response.status_code}") from ex
        except httpx.RequestError as ex:
            _LOGGER.error("Request error on %s: %s", check_url, ex)
            raise UpdateFailed(f"Request error: {ex}") from ex

    async def _start_bore_process(self):
        """Start the bore process."""
        args = [
            "bore",
            "local",
            str(self.entry.data[CONF_LOCAL_PORT]),
            "--to",
            self.entry.data[CONF_TO],
            "--local-host",
            self.entry.data[CONF_LOCAL_HOST],
            "--port",
            str(self.entry.data[CONF_PORT]),
        ]
        if self.entry.data.get(CONF_SECRET):
            args.extend(["--secret", self.entry.data[CONF_SECRET]])

        try:
            self._bore_process = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except FileNotFoundError as ex:
            _LOGGER.error(
                "The 'bore' command was not found. Please make sure it is installed and in your PATH. See https://github.com/ekzhang/bore for installation instructions."
            )
            raise UpdateFailed("Bore command not found") from ex

        # Read output to find the assigned port and log everything
        self.hass.async_create_task(self._log_output())

    async def _log_output(self):
        """Log the output of the bore process."""
        while self._bore_process.returncode is None:
            try:
                async with async_timeout.timeout(1):
                    line = await self._bore_process.stdout.readline()
                    if not line:
                        break
                    line = line.decode().strip()
                    _LOGGER.info(line)
                    if "listening at" in line:
                        parts = line.split("listening at")
                        if len(parts) == 2:
                            address = parts[1].strip()
                            self._assigned_port = int(address.split(":")[-1])
            except asyncio.TimeoutError:
                pass

        _LOGGER.info("Bore process terminated with code %s", self._bore_process.returncode)
        self._bore_process = None
