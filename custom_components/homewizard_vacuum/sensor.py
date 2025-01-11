import aiohttp
import logging

from .base import HWCleanerBaseEntity
from .const import DOMAIN, CONF_IDENTIFIER
from .coordinator import HWCleanerCoordinator

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.core import HomeAssistant
from homeassistant.components.sensor import (
    SensorEntity,
)

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
    vacs.append(HWVacuumBrushSensor(coordinator, "Brush"))
    vacs.append(HWVacuumStatusSensor(coordinator, "Status"))
    vacs.append(HWVacuumFaultsSensor(coordinator, "Faults"))

    async_add_entities(vacs)

class HWVacuumBrushSensor(HWCleanerBaseEntity, SensorEntity):
    """Sensor entity for the vacuum's brush type."""

    @property
    def state(self):
        """Return the current brush type."""
        return self.coordinator._attr_brush_type

    @property
    def available(self):
        """Return if the sensor is available."""
        return self.coordinator.last_update_success

    @property
    def icon(self):
        """Return the icon for the current state."""
        return "mdi:hvac"

class HWVacuumStatusSensor(HWCleanerBaseEntity, SensorEntity):
    """Sensor entity for the vacuum's status type."""

    @property
    def state(self):
        """Return the current status type."""
        return self.coordinator._attr_device_status

    @property
    def available(self):
        """Return if the sensor is available."""
        return self.coordinator.last_update_success

    @property
    def icon(self):
        """Return the icon for the current state."""
        return "mdi:list-status"

class HWVacuumFaultsSensor(HWCleanerBaseEntity, SensorEntity):
    """Sensor entity for the vacuum's faults type."""

    @property
    def state(self):
        """Return the current faults type."""
        return self.coordinator._attr_faults

    @property
    def available(self):
        """Return if the sensor is available."""
        return self.coordinator.last_update_success

    @property
    def icon(self):
        """Return the icon for the current state."""
        return "mdi:alert-circle"