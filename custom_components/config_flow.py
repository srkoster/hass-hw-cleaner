# pylint: disable=duplicate-code
"""Config flow for HW Vacuum Cleaner."""
import logging
import requests
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME

from .const import API_URL, CONF_ENDPOINT, CONF_IDENTIFIER, DOMAIN

_LOGGER = logging.getLogger(__name__)

class HWCleanerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HW Vacuum Cleaner."""

    VERSION = 1

    def __init__(self):
        self._conf_username = None
        self._conf_password = None
        self._api_url = API_URL

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Store the credentials from the user
            self._conf_username = user_input.get(CONF_USERNAME)
            self._conf_password = user_input.get(CONF_PASSWORD)

            # Validate the credentials
            try:
                device = await self.hass.async_add_executor_job(
                    self._validate_credentials,
                    self._conf_username,
                    self._conf_password,
                )

                if device:
                    # Create the config entry with necessary details
                    return self.async_create_entry(
                        title=f"Robot Vacuum ({device['identifier']})",
                        data={
                            CONF_USERNAME: self._conf_username,
                            CONF_PASSWORD: self._conf_password,
                            CONF_IDENTIFIER: device["identifier"],
                            CONF_ENDPOINT: device["endpoint"],
                        },
                    )
                else:
                    errors["base"] = "no_cleaner_found"

            except Exception as e:
                _LOGGER.error("Error validating credentials: %s", str(e))
                errors["base"] = "auth_failed"

        data_schema = vol.Schema({
            vol.Required(CONF_USERNAME): str,
            vol.Required(CONF_PASSWORD): str,
        })
        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)

    def _validate_credentials(self, username, password):
        """Validate credentials and find a cleaner device."""
        url = f"{self._api_url}/auth/devices"
        response = requests.get(url, auth=(username, password))

        if response.status_code != 200:
            raise ValueError("Invalid credentials")

        devices = response.json().get("devices", [])

        # Find a device of type "cleaner"
        for device in devices:
            if device.get("type") == "cleaner":
                return {
                    "identifier": device["identifier"],
                    "endpoint": device["endpoint"],
                }

        return None

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return RobotVacuumOptionsFlow(config_entry)

class RobotVacuumOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for the Robot Vacuum integration."""

    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Handle options configuration."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(step_id="init", data_schema=self._get_options_schema())

    def _get_options_schema(self):
        """Return the options schema for the form."""
        return vol.Schema({})
