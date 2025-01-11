# pylint: disable=duplicate-code
"""The Homewizard Vacuum Cleaner integration"""
from __future__ import annotations

import asyncio

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform

from .const import DOMAIN
from .coordinator import HWCleanerCoordinator

PLATFORMS: list[Platform] = [Platform.VACUUM, Platform.SENSOR, Platform.SWITCH]

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up HW Vacuum Cleaner from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    coordinator = HWCleanerCoordinator(hass, config_entry)

    # Fetch initial data so we have data when entities subscribe
    #
    # If the refresh fails, async_config_entry_first_refresh will
    # raise ConfigEntryNotReady and setup will try again later
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][config_entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(config_entry, ["vacuum"])
    await hass.config_entries.async_forward_entry_setups(config_entry, ["sensor"])
    await hass.config_entries.async_forward_entry_setups(config_entry, ["switch"])

    # Return true to denote a successful setup.
    return True

async def async_remove_config_entry_device(
    hass: HomeAssistant, config_entry: ConfigEntry, device_entry: DeviceEntry
) -> bool:
    """Delete device if selected from UI."""
    # Adding this function shows the delete device option in the UI.
    return True

async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # This is called when you remove your integration or shutdown HA.

    # Unload services
    for service in hass.services.async_services_for_domain(DOMAIN):
        hass.services.async_remove(DOMAIN, service)

    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(
        config_entry, PLATFORMS
    )

    # Remove the config entry from the hass data object.
    if unload_ok:
        hass.data[DOMAIN].pop(config_entry.entry_id)

    # Return that unloading was successful.
    return unload_ok