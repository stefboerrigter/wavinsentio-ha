import logging

from typing import Any, Dict, Optional

from homeassistant import config_entries
import homeassistant.helpers.config_validation as cv

from homeassistant import config_entries, core, exceptions
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_TYPE, CONF_SLAVE
from homeassistant.data_entry_flow import FlowResult

import voluptuous as vol

from .SentioModbus.SentioApi.SentioApi import SentioModbus, NoConnectionPossible, ModbusType

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

AUTH_SCHEMA = vol.Schema(
    {vol.Required(CONF_HOST): cv.string}
)


class WavinSentioConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Wavin Sentio config flow."""
    data: Optional[Dict[str, Any]]

    #async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None):
        
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Step when user initializes a integration."""
        if user_input is not None:
            user_selection = user_input[CONF_TYPE]
            if user_selection == "Serial": #Network
                return await self.async_step_setup_serial()

            return await self.async_step_setup_network()

        list_of_types = ["Serial", "Network"]

        schema = vol.Schema({vol.Required(CONF_TYPE): vol.In(list_of_types)})
        return self.async_show_form(step_id="user", data_schema=schema)

    async def async_step_setup_network(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Step when setting up network configuration."""
        errors: dict[str, str] = {}
        if user_input is not None:
            data = await self.async_validate_wavin_sentio_network_connection(user_input, errors)
            if not errors:
                _LOGGER.info("Creating entry with: {0}".format(data))
                _LOGGER.error("Creating entry with: {0}".format(data))
                
                return self.async_create_entry(
                    title=f"{data[CONF_HOST]}:{data[CONF_PORT]}", data=data
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST, default="192.168.188.14", description="Host"): str,
                vol.Required(CONF_PORT, default=512, description="Port"): int,
                vol.Required(CONF_SLAVE, default=1, description="Slave ID"): int,
            }
        )

        return self.async_show_form(
            step_id="setup_network",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_setup_serial(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        self.data = user_input
        self.data[CONF_TYPE] = "Serial"
        _LOGGER.error("------------------ ERROR Not implemented yet")

        #"""Invoked when a user initiates a flow via the user interface."""
        #_LOGGER.error("---------- SB ------------- Initialize Config async_step_user")
        #errors: Dict[str, str] = {}
        #if user_input is not None:
        #    #self.data = user_input
        #    _LOGGER.error("---------- SB ------------- Initialize {0}".format(user_input))
        #    # Return the form of the next step.
        #    return await self.async_step_location(user_input)
        #_LOGGER.error("---------- SB ------------- Wait for async show form ")
        #return self.async_show_form(
        #    step_id="user", data_schema=AUTH_SCHEMA, errors=errors
        #)


    async def async_validate_wavin_sentio_network_connection(
        self, input_data: dict[str, Any], errors: dict[str, str]
    ) -> dict[str, Any]:
        """Validate Sentio connection and create data."""
        self.data = input_data
        _LOGGER.error("Got here with data {0}".format(input_data))
        try:
            self.data[CONF_TYPE] = "Network"
            api = await self.hass.async_add_executor_job(
                #SentioModbus, self.data[CONF_HOST]
                SentioModbus, ModbusType.MODBUS_TCPIP, self.data[CONF_HOST], self.data[CONF_PORT], self.data[CONF_SLAVE], 0, logging.DEBUG
            )

            status = await self.hass.async_add_executor_job(api.connect)
            if status == 0:
                info = {
                    "WavinSentio": self.data[CONF_HOST],
                }
                data = {**self.data, **info}
                _LOGGER.error("Filled data {0}".format(data))
                _LOGGER.error("Initialized Wavin Sentio Done")
            else:
                errors["base"] = "connect_error"
        except NoConnectionPossible:
            errors["base"] = "connect_error"

        return data

