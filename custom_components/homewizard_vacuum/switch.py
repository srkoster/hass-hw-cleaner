import aiohttp
import logging

from typing import Any

from .base import HWCleanerBaseEntity
from .const import DOMAIN, CONF_IDENTIFIER
from .coordinator import HWCleanerCoordinator

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.core import HomeAssistant
from homeassistant.components.switch import SwitchEntity

SOUND_OPTIONS = ["Beeps", "English", "No sound"]

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Create vacuum entities from config flow."""
    # This gets the data update coordinator from hass.data as specified in your __init__.py
    coordinator: HWCleanerCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    vacs = []
    vacs.append(HWVacuumSoundSwitch(coordinator, "Sound"))

    async_add_entities(vacs)

class HWVacuumSoundSwitch(HWCleanerBaseEntity, SwitchEntity):
    """Sensor entity for the vacuum's sound type."""
    
    @property
    def available(self):
        """Return if the sensor is available."""
        return self.coordinator.last_update_success

    @property
    def icon(self):
        """Return the icon for the current state."""
        return "mdi:volume-medium"

    @property
    def is_on(self) -> bool | None:
        """Return if the binary sensor is on."""
        # This needs to enumerate to true or false
        return (
            self.coordinator._attr_sound_status == "Beeps"
        )

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        await self.coordinator.configure_sound("beeps")

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        await self.coordinator.configure_sound("off")