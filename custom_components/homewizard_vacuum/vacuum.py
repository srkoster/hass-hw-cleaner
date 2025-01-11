import aiohttp
import logging
import voluptuous as vol

from homeassistant.components.vacuum import (
    StateVacuumEntity,
    VacuumActivity,
    VacuumEntityFeature
)
from .base import HWCleanerBaseEntity
from .const import DOMAIN, CONF_IDENTIFIER
from .coordinator import HWCleanerCoordinator

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv, entity_platform

_LOGGER = logging.getLogger(__name__)

FAN_SPEEDS = ["Quiet", "Normal", "Strong"]
API_FAN_SPEEDS = {
    "Quiet": "stop",
    "Normal": "normal",
    "Strong": "strong",
}
REVERSE_API_FAN_SPEEDS = {v: k for k, v in API_FAN_SPEEDS.items()}

CLEANER_STATUS_TO_HA = {
    "working": VacuumActivity.CLEANING,
    "charging": VacuumActivity.DOCKED,
    "finished_charging": VacuumActivity.DOCKED,
    "standby": VacuumActivity.IDLE,
    "stopped": VacuumActivity.IDLE,
    "docking": VacuumActivity.RETURNING,
    "malfunction": VacuumActivity.ERROR,
}

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
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Create vacuum entities from config flow."""
    # This gets the data update coordinator from hass.data as specified in your __init__.py
    coordinator: HWCleanerCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ]

    vacs = []
    vacs.append(HWVacuumCleaner(coordinator, "Vacuum"))

    async_add_entities(vacs, False)

    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service(
        "program_deep_clean",
        {},
        "async_start_program_deep_clean"
    )
    platform.async_register_entity_service(
        "program_edge",
        {},
        "async_start_program_edge"
    )
    platform.async_register_entity_service(
        "program_random",
        {},
        "async_start_program_random"
    )

class HWVacuumCleaner(HWCleanerBaseEntity, StateVacuumEntity):
    """Representation of a Homewizard Vacuum Cleaner."""

    _attr_fan_speed_list = FAN_SPEEDS
    _attr_supported_features = SUPPORT_VACUUM

    @property
    def activity(self) -> VacuumActivity | None:
        return CLEANER_STATUS_TO_HA.get(self.coordinator._attr_device_status, VacuumActivity.IDLE)

    @property
    def battery_level(self):
        return self.coordinator._attr_battery_percentage

    @property
    def device_id(self):
        """Return the device ID from the coordinator's data."""
        return self.coordinator._device_identifier
    
    @property
    def icon(self):
        """Return the icon for the current state."""
        icon = None
        if self.coordinator._attr_device_status in ["malfunction"]:
            icon = "mdi:robot-vacuum-alert"
        else:
            icon = "mdi:robot-vacuum"
        return icon

    @property
    def supported_features(self):
        return self._attr_supported_features

    @property
    def fan_speed_list(self):
        """Return the status of the vacuum."""
        return self._attr_fan_speed_list

    @property
    def fan_speed(self):
        """Return the status of the vacuum."""
        return REVERSE_API_FAN_SPEEDS.get(self.coordinator._attr_fan_mode)

    async def async_start(self):
        await self.coordinator.control_vacuum({"activity": "work"})

    async def async_stop(self):
        await self.coordinator.control_vacuum({"activity": "suspend", "direction": "stop"})

    async def async_return_to_base(self):
        await self.coordinator.control_vacuum({"activity": "charge"})

    async def async_clean_spot(self):
        await self.coordinator.control_vacuum({"activity": "work", "program": "spot"})

    async def async_start_program_deep_clean(self):
        await self.coordinator.control_vacuum({"activity": "work", "program": "deep_clean"})

    async def async_start_program_edge(self):
        await self.coordinator.control_vacuum({"activity": "work", "program": "edge"})

    async def async_start_program_random(self):
        await self.coordinator.control_vacuum({"activity": "work", "program": "random"})

    async def async_set_fan_speed(self, fan_speed, **kwargs):
        """Set the vacuum's fan speed."""

        if fan_speed in FAN_SPEEDS:
            api_fan_speed = API_FAN_SPEEDS[fan_speed]
            await self.coordinator.control_vacuum({"activity": "work", "program": api_fan_speed})

    async def async_send_command(self, payload: str) -> None:
        """Send a command to a vacuum cleaner."""
        await self.coordinator.control_vacuum(payload)