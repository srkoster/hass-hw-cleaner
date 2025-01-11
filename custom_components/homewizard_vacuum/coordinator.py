import aiohttp
import logging

from datetime import timedelta

from .const import DOMAIN, API_URL, CONF_IDENTIFIER, CONF_ENDPOINT, DEFAULT_SCAN_INTERVAL

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, CONF_NAME
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed


_LOGGER = logging.getLogger(__name__)

class HWCleanerCoordinator(DataUpdateCoordinator):
    """Representation of a Homewizard Vacuum Cleaner."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize coordinator."""

        # Set variables from values entered in config flow setup
        self._username = config_entry.data[CONF_USERNAME]
        self._password = config_entry.data[CONF_PASSWORD]
        self._device_identifier = config_entry.data[CONF_IDENTIFIER]
        self._device_endpoint = config_entry.data[CONF_ENDPOINT]
        self._name = config_entry.data[CONF_NAME]

        self._api_url = API_URL
        self._token = None
        self._poll_interval = 30

        self._attr_device_status = None
        self._attr_fw_version = None
        self._attr_brush_type = None
        self._attr_faults = None
        self._attr_sound_status = None
        self._attr_battery_percentage = None
        self._attr_fan_mode = None

        # Initialise DataUpdateCoordinator
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN} ({config_entry.unique_id})",
            # Method to call on every update interval.
            update_method=self._async_update_data,
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta(seconds=self._poll_interval),
        )

    async def _async_setup(self) -> None:
        """Set up the coordinator.

        Can be overwritten by integrations to load data or resources
        only once during the first refresh.
        """
        await self._get_token()
        await self._get_version()


    async def _get_token(self):
        """Fetch and store the bearer token."""
        _LOGGER.debug("Fetch and store token")
        url = f"{self._api_url}/auth/token"
        auth = aiohttp.BasicAuth(self._username, self._password)
        payload = {"device": self._device_identifier}

        async with aiohttp.ClientSession() as session:
            async with session.post(url, auth=auth, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    self._token = data.get("token")
                else:
                    raise UpdateFailed(f"Authentication failed: {response.status}")
                
    async def _get_version(self):
        """Fetch the firmware version."""
        _LOGGER.debug("Update firmware version")
        data = await self._send_api_command("version", None)

        # Parse response into attributes
        self._attr_fw_version = data.get("version")

    async def _async_update_data(self):
        """Fetch the latest state from the API."""
        _LOGGER.debug("Update status")
        data = await self._send_api_command(None, None)

        # Parse response into attributes
        self._attr_device_status = data.get("status").replace("_", " ").title()
        self._attr_brush_type = data.get("brush").title()
        self._attr_sound_status = data.get("sound").title()
        self._attr_battery_percentage = data.get("battery_percentage")
        self._attr_fan_mode = data.get("fan_mode")

        # Handle faults list
        faults = data.get("faults", [])
        if faults:
            self._attr_faults = ", ".join(f.title() for f in faults)
        else:
            self._attr_faults = "None"
    
    async def configure_sound(self, sound_type): 
        await self._send_api_command("configure", {"sound": sound_type})

    async def control_vacuum(self, payload): 
        await self._send_api_command("control", payload)

    async def _send_api_command(self, command, payload):
        # Determine the HTTP method based on the command
        if command in (None, "version"):
            http_method = "GET"
        elif command in ("control", "configure"):
            http_method = "POST"
        else:
            raise ValueError(f"Command '{command}' is not supported.")

        # Create the URL and headers
        url = f"{self._device_endpoint}/{command}" if command else f"{self._device_endpoint}"
        headers = {"Authorization": f"Bearer {self._token}"}

        async with aiohttp.ClientSession() as session:
            if http_method == "GET":
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        _LOGGER.debug("Command successful: %s", command)
                        return await response.json() 
                    elif response.status == 401:
                        _LOGGER.debug("Token expired during command, refreshing.")
                        await self._get_token()
                        return await self._send_api_command(command, payload)
                    else:
                        _LOGGER.error("Command failed: %s", command)
                        raise UpdateFailed(f"Command failed: {command}")
            elif http_method == "POST":
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        _LOGGER.debug("Command successful: %s", command)
                        await self.async_request_refresh()
                    elif response.status == 401:
                        _LOGGER.debug("Token expired during command, refreshing.")
                        await self._get_token()
                        await self._send_api_command(command, payload)
                    else:
                        _LOGGER.error("Command failed: %s", command)
                        raise UpdateFailed(f"Command failed: {command}")