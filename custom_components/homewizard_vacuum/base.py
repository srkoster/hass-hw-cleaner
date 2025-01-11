import logging

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.core import callback

from .const import DOMAIN
from .coordinator import HWCleanerCoordinator

_LOGGER = logging.getLogger(__name__)


class HWCleanerBaseEntity(CoordinatorEntity):
    """Base Entity Class.

    This inherits a CoordinatorEntity class to register your entites to be updated
    by your DataUpdateCoordinator when async_update_data is called, either on the scheduled
    interval or by forcing an update.
    """

    coordinator: HWCleanerCoordinator

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: HWCleanerCoordinator, name: str
    ) -> None:
        """Initialise entity."""
        super().__init__(coordinator)
        self._name = name

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            name=self.coordinator._name,
            manufacturer="Princess",
            model="339000 Robot Vacuum Deluxe",
            sw_version=self.coordinator._attr_fw_version,
            identifiers={
                (
                    DOMAIN,
                    self.coordinator._device_identifier,
                )
            }
        )
    
    @callback
    def _handle_coordinator_update(self) -> None:
        """Update sensor with latest data from coordinator."""
        self.async_write_ha_state()

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self._name.title()

    @property
    def unique_id(self) -> str:
        """Return unique id."""
        return f"{DOMAIN}-{self.coordinator._device_identifier}-{self._name}"