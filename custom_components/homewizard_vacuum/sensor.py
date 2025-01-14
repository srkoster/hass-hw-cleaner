import aiohttp
import logging

from .base import HWCleanerBaseEntity
from .const import DOMAIN, CONF_IDENTIFIER
from .coordinator import HWCleanerCoordinator

from homeassistant.const import PERCENTAGE
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.core import HomeAssistant
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
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
    vacs.append(HWVacuumBatterySensor(coordinator, "Battery"))

    async_add_entities(vacs)

class HWVacuumBrushSensor(HWCleanerBaseEntity, SensorEntity):
    """Sensor entity for the vacuum's brush type."""

    entity_description = SensorEntityDescription(
        key="brush",
        icon="mdi:hvac"
    )

    @property
    def state(self):
        """Return the current brush type."""
        return self.coordinator._attr_brush_type

    @property
    def available(self):
        """Return if the sensor is available."""
        return self.coordinator.last_update_success

class HWVacuumStatusSensor(HWCleanerBaseEntity, SensorEntity):
    """Sensor entity for the vacuum's status type."""

    entity_description = SensorEntityDescription(
        key="status",
        icon="mdi:list-status"
    )

    @property
    def state(self):
        """Return the current status type."""
        return self.coordinator._attr_device_status

    @property
    def available(self):
        """Return if the sensor is available."""
        return self.coordinator.last_update_success

class HWVacuumFaultsSensor(HWCleanerBaseEntity, SensorEntity):
    """Sensor entity for the vacuum's faults type."""

    entity_description = SensorEntityDescription(
        key="faults",
        icon="mdi:alert-circle"
    )

    @property
    def state(self):
        """Return the current faults type."""
        return self.coordinator._attr_faults

    @property
    def available(self):
        """Return if the sensor is available."""
        return self.coordinator.last_update_success

class HWVacuumBatterySensor(HWCleanerBaseEntity, SensorEntity):
    """Sensor entity for the vacuum's battery percentage."""

    entity_description = SensorEntityDescription(
        key="battery",
        icon="mdi:battery",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY
    )

    @property
    def available(self):
        """Return if the sensor is available."""
        return self.coordinator.last_update_success

    @property
    def native_value(self) -> int | None:
        return self.coordinator._attr_battery_percentage
