
"""The Bore integration."""
import asyncio
import logging
from datetime import timedelta

import async_timeout
import socket
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
    DEFAULT_UPDATE_INTERVAL,
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
        hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    )

    return True


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    coordinator: BoreDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    await coordinator._stop_bore_process()

    await asyncio.sleep(5)

    unload_ok = await hass.config_entries.async_forward_entry_unload(entry, ["sensor"])
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
            self.config_data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
        )

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )

        self._bore_process = None
        self._assigned_port = None
        self._healthy = True

    @property
    def config_data(self):
        """Return the config data."""
        return self.entry.options or self.entry.data

    async def _async_update_data(self):
        """Fetch data from the Bore tunnel."""
        # If the last health check failed, restart the process now before this check.
        if not self._healthy:
            _LOGGER.info("Previous health check failed. Restarting bore process now.")
            await self._stop_bore_process()

        # Start process if it's not running (or was just stopped).
        if self._bore_process is None or self._bore_process.returncode is not None:
            _LOGGER.info("Bore process not running. Starting...")
            await self._start_bore_process()
            # Give bore a moment to establish the tunnel before checking.
            await asyncio.sleep(5)

        check_url = self.config_data.get(CONF_CHECK_URL)
        if not check_url and self._assigned_port:
            check_url = f"{self.config_data.get(CONF_TO)}:{self._assigned_port}"

        if not check_url:
            self._healthy = True
            return {"status": "connected"}  # Assume connected if no check url

        if ":" in check_url:
            host, port_str = check_url.split(":")
            port = int(port_str)
        else:
            host = check_url
            port = 443 # Default to HTTPS port

        try:
            with socket.create_connection((host, port), timeout=10):
                _LOGGER.debug("Health check to %s successful.", check_url)
                self._healthy = True  # Mark as healthy for the next run.
                return {"status": "connected"}
        except (socket.timeout, ConnectionRefusedError, socket.gaierror) as ex:
            _LOGGER.warning(
                "Health check to %s failed: %s. The tunnel will be restarted on the next update.",
                check_url,
                ex,
            )
            self._healthy = False  # Mark as unhealthy for the next run.
            # Do not stop the process now; just signal the update failure.
            raise UpdateFailed(f"Health check failed: {ex}") from ex

    async def _stop_bore_process(self):
        """Stop the bore process."""
        if self._bore_process and self._bore_process.returncode is None:
            _LOGGER.info("Stopping bore process...")
            try:
                self._bore_process.terminate()
                await asyncio.wait_for(self._bore_process.wait(), timeout=5.0)
                _LOGGER.info("Bore process terminated.")
            except asyncio.TimeoutError:
                _LOGGER.warning("Bore process did not terminate gracefully, killing it.")
                self._bore_process.kill()
                await self._bore_process.wait()
            finally:
                self._bore_process = None

    async def _start_bore_process(self):
        """Start the bore process."""
        args = [
            "bore",
            "local",
            str(self.config_data.get(CONF_LOCAL_PORT)),
            "--to",
            self.config_data.get(CONF_TO),
            "--local-host",
            self.config_data.get(CONF_LOCAL_HOST),
            "--port",
            str(self.config_data.get(CONF_PORT)),
        ]
        if self.config_data.get(CONF_SECRET):
            args.extend(["--secret", self.config_data.get(CONF_SECRET)])

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
        """Log the output of the bore process from stdout and stderr."""

        async def log_stdout():
            """Read from stdout, log, and parse for the assigned port."""
            while True:
                try:
                    line_bytes = await self._bore_process.stdout.readline()
                except (BrokenPipeError, ConnectionResetError):
                    break
                if not line_bytes:
                    break
                line = line_bytes.decode().strip()
                _LOGGER.info(line)
                if "listening at" in line:
                    parts = line.split("listening at")
                    if len(parts) == 2:
                        address = parts[1].strip()
                        self._assigned_port = int(address.split(":")[-1])

        async def log_stderr():
            """Read from stderr and log as an error."""
            while True:
                try:
                    line_bytes = await self._bore_process.stderr.readline()
                except (BrokenPipeError, ConnectionResetError):
                    break
                if not line_bytes:
                    break
                _LOGGER.error("Bore process stderr: %s", line_bytes.decode().strip())
        
        try:
            # Run both logging tasks concurrently until the process exits
            await asyncio.gather(log_stdout(), log_stderr())
        finally:
            if self._bore_process:
                await self._bore_process.wait()
                _LOGGER.info(
                    "Bore process has terminated with code %s", self._bore_process.returncode
                )
