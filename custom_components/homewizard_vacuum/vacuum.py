import aiohttp
import logging

from homeassistant.components.vacuum import (
    STATE_CLEANING,
    STATE_DOCKED,
    STATE_ERROR,
    STATE_IDLE,
    STATE_RETURNING,
    StateVacuumEntity,
    VacuumEntityFeature
)
from .const import DOMAIN, API_URL, CONF_IDENTIFIER, CONF_ENDPOINT

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.const import STATE_UNKNOWN, CONF_PASSWORD, CONF_USERNAME, CONF_NAME


_LOGGER = logging.getLogger(__name__)

FAN_SPEEDS = ["Quiet", "Normal", "Strong"]
API_FAN_SPEEDS = {
    "Quiet": "stop",
    "Normal": "normal",
    "Strong": "strong",
}
REVERSE_API_FAN_SPEEDS = {v: k for k, v in API_FAN_SPEEDS.items()}

SUPPORT_VACUUM = (
    VacuumEntityFeature.BATTERY
    | VacuumEntityFeature.CLEAN_SPOT
    | VacuumEntityFeature.FAN_SPEED
    | VacuumEntityFeature.RETURN_HOME
    | VacuumEntityFeature.SEND_COMMAND
    | VacuumEntityFeature.START
    | VacuumEntityFeature.STATE
    | VacuumEntityFeature.STOP
)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Create vacuum entities from config flow."""
    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]
    identifier = entry.data[CONF_IDENTIFIER]
    endpoint = entry.data[CONF_ENDPOINT]
    devicename = entry.data[CONF_NAME]

    vacs = []
    vacs.append(HWVacuumCleaner(identifier, endpoint, username, password, devicename))

    async_add_entities(vacs, False)

class HWVacuumCleaner(StateVacuumEntity):
    """Representation of a Homewizard Vacuum Cleaner."""

    def __init__(self, identifier, endpoint, username, password, devicename):
        self._username = username
        self._password = password
        self._device_identifier = identifier
        self._device_endpoint = endpoint
        self._name = devicename
        self._state = STATE_UNKNOWN
        self._battery = None
        self._status = None
        self._token = None
        self._fan_speed = "stop"
        self._api_url = API_URL

    async def async_added_to_hass(self):
        """Run when the entity is added to Home Assistant."""
        await self._get_token()

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
                raise HomeAssistantError(f"Authentication failed: {response.status}")

    async def async_send_command(self, activity, direction=None, program=None):
        """Send a command to the vacuum with the required syntax."""
        _LOGGER.debug("Process command")
        url = f"{self._device_endpoint}/control"
        headers = {"Authorization": f"Bearer {self._token}"}
        
        # Construct the payload with optional parameters
        payload = {"activity": activity}
        if direction:
            payload["direction"] = direction
        if program:
            payload["program"] = program

        # Send the command
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                elif response.status == 401:  # Unauthorized, token likely expired
                    _LOGGER.warning("Bearer token expired, refreshing token.")
                    await self._get_token()

                raise HomeAssistantError(f"Command failed: {response.status}")

    async def async_clean_spot(self):
        await self.async_send_command(program="spot", activity="work")  

    async def async_set_fan_speed(self, fan_speed, **kwargs):
        """Set the vacuum's fan speed."""

        if fan_speed in FAN_SPEEDS:
            self._fan_speed = fan_speed
            if self._fan_speed == "Quiet":
                new_program = "silent"
            elif self._fan_speed == "Normal":
                new_program = "auto"
            elif self._fan_speed == "Strong":
                new_program = "max"
            await self.async_send_command(program=new_program, activity="work")

    async def async_update(self):
        """Fetch the latest state from the API."""
        _LOGGER.debug("Update status")
        url = f"{self._device_endpoint}"
        headers = {"Authorization": f"Bearer {self._token}"}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
            
                    # Parse the response payload
                    
                    self._battery = data.get("battery_percentage")  # Battery level as a percentage
                    self._status = {
                        "program": data.get("program"),  # Example: "deep_clean", or null
                        "fan_mode": data.get("fan_mode"),  # Example: "stop", "normal", "strong"
                        "direction": data.get("direction"),  # Example: "forward", "backward", or null
                        "brush": data.get("brush"),  # Example: "suction", "sweeping"
                        "sound": data.get("sound"),  # Example: "beeps", or other feedback
                        "faults": data.get("faults"),  # List of current faults, empty if none
                    }
                    self._fan_speed = REVERSE_API_FAN_SPEEDS.get(data.get("fan_mode"))

                    # Get vacuum mode
                    if data.get("status") in ["working"]:
                        self._state = STATE_CLEANING
                    elif data.get("status") in ["finished_charging", "charging"]:
                        self._state = STATE_DOCKED
                    elif data.get("status") in ["stopped", "standby"]:
                        self._state = STATE_IDLE
                    elif data.get("status") in ["docking"]:
                        self._state = STATE_RETURNING
                    else:
                        self._state = data.get("status")
                    return data
                
                elif response.status == 401:  # Unauthorized, token likely expired
                    _LOGGER.warning("Bearer token expired, refreshing token.")
                    await self._get_token()

                else:
                    error_message = await response.text()
                    raise Exception(f"Failed to fetch device status: {error_message}")

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, self._device_identifier)
            },
            name=self._name,
            manufacturer="Princess",
            model="339000 Robot Vacuum Deluxe",
        )

    @property
    def name(self):
        return self._name
    
    @property
    def unique_id(self):
        """Return unique ID for this device."""
        return self._device_identifier

    @property
    def state(self):
        return self._state

    @property
    def battery_level(self):
        return self._battery

    @property
    def device_id(self):
        return self._get_device()["id"]

    @property
    def supported_features(self):
        return SUPPORT_VACUUM

    @property
    def fan_speed_list(self):
        """Return the status of the vacuum."""
        return FAN_SPEEDS

    @property
    def fan_speed(self):
        """Return the status of the vacuum."""
        return self._fan_speed

    async def async_start(self):
        await self.async_send_command(activity="work")

    async def async_stop(self):
        await self.async_send_command(activity="suspend", direction="stop")

    async def async_return_to_base(self):
        await self.async_send_command(activity="charge")
