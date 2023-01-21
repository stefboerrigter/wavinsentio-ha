import logging

from typing import Any, Dict, Optional

from homeassistant import config_entries
import homeassistant.helpers.config_validation as cv

from homeassistant import config_entries, core, exceptions
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_TYPE
from homeassistant.data_entry_flow import FlowResult

import voluptuous as vol

from .SentioModbus.SentioApi.SentioApi import SentioModbus, NoConnectionPossible 

from .const import DOMAIN, CONF_LOCATION_ID

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
            if user_selection == "Serial":
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
            data = await self.async_validate_wavin_sentio_connection(user_input, errors)
            if not errors:
                return self.async_create_entry(
                    title=f"{data[CONF_HOST]}:{data[CONF_PORT]}", data=data
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_PORT): int,
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


    async def async_validate_wavin_sentio_connection(
        self, input_data: dict[str, Any], errors: dict[str, str]
    ) -> dict[str, Any]:
        """Validate Sentio connection and create data."""
        self.data = input_data

        try:
            api = await self.hass.async_add_executor_job(
                SentioModbus, self.data[CONF_HOST]
            )

            status = await self.hass.async_add_executor_job(api.connect)
            if status == 0:
                info = {
                    "WavinSentio": self.data[CONF_HOST],
                }
                data = {**self.data, **info}
            else:
                errors["base"] = "connect_error"
        except NoConnectionPossible:
            errors["base"] = "connect_error"

        return data

    #async def async_step_location(self, user_input: Optional[Dict[str, Any]] = None):
    #    """Second step in config flow to choose the location"""
    #    errors = {}
    #    _LOGGER.error("---------- SB ------------- Choose location 2nd step ")
    #    try:
    #        self.data = user_input
    #        api = await self.hass.async_add_executor_job(
    #            SentioModbus, self.data[CONF_IP_ADDRESS]
    #        )
#
    #        status = await self.hass.async_add_executor_job(api.connect)
    #        _LOGGER.error("---------- SB ------------- Choose location 2nd step --- {0} ".format(status))
    #        if status != 0:
    #            errors["base"] = "connect_error"
    #            _LOGGER.error("---------- SB -------------Status not null, connect error --- {0} ".format(status))
    #            return self.async_show_form( step_id="user", data_schema=AUTH_SCHEMA, errors=errors)
    #        else:
    #            _LOGGER.error("---------- SB ------------- Choose location 2nd step --- Status is 0, seems complete ".format(status))
    #    except NoConnectionPossible as err:
    #        _LOGGER.error("---------- SB ------------- Error exception caught --- {0} ".format(err))
    #        errors["base"] = "connect_error"
    #        return self.async_show_form(
    #            step_id="user", data_schema=AUTH_SCHEMA, errors=errors
    #        )
        
        #outdoorTemp = await self.hass.async_add_executor_job(api.getOutdoorTemperature)
        #_LOGGER.error("Get locations (outdoor) returned {0}".format(locations))
    
        #all_locations = {l["ulc"]: l["name"] for l in locations}
        #
        #if user_input is not None:
            #self.data[CONF_LOCATION_ID] = user_input[CONF_LOCATION_ID]
            #return await self.async_create_entry(title="Wavin Sentio", data=self.data)
        #
        #LOCATION_SCHEMA = vol.Schema(
        #    {vol.Optional(CONF_LOCATION_ID): vol.In(all_locations)}
        #)
        #
        #_LOGGER.error("---------- SB ------------- async show form complete --> ")
        #return self.async_show_form(
        #    step_id="location", data_schema=LOCATION_SCHEMA, errors=errors
        #)
        #return self.async_create_entry(
        #    title="Wavin Sentio", 
        #    data={
        #        CONF_IP_ADDRESS: self.data[CONF_IP_ADDRESS]
        #    }
        #)
        

    #async def async_step_reauth(self, user_input=None):
    #    _LOGGER.error("---------- SB ------------- Initialize 3 --- NO REAUTH")
        #return await self.async_step_user()

    #async def async_create_entry(self, title: str, data: dict) -> dict:
    #    _LOGGER.error("---------- SB ------------- Initialize 4 -- DUMMY")
        #"""Create an oauth config entry or update existing entry for reauth."""
        # TODO: This example supports only a single config entry. Consider
        # any special handling needed for multiple config entries.
        #existing_entry = await self.async_set_unique_id(data[CONF_LOCATION_ID])
        #if existing_entry:
        #    self.hass.config_entries.async_update_entry(existing_entry, data=data)
        #    await self.hass.config_entries.async_reload(existing_entry.entry_id)
        #    return self.async_abort(reason="reauth_successful")
        #return super().async_create_entry(title=title, data=data)

