import logging

from homeassistant import config_entries, core

from homeassistant.exceptions import ConfigEntryAuthFailed, Unauthorized

from .const import DOMAIN

from homeassistant.const import CONF_IP_ADDRESS

from .SentioModbus.SentioApi.SentioApi import SentioModbus, NoConnectionPossible 

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: core.HomeAssistant, entry: config_entries.ConfigEntry
) -> bool:
    """Set up platform from a ConfigEntry."""
    hass.data.setdefault(DOMAIN, {})
    hass_data = dict(entry.data)
    # @TODO: Add setup code.
    # Registers update listener to update config entry when options are updated.
    # unsub_options_update_listener = entry.add_update_listener(options_update_listener)
    # Store a reference to the unsubscribe function to cleanup if an entry is unloaded.
    # hass_data["unsub_options_update_listener"] = unsub_options_update_listener
    hass.data[DOMAIN][entry.entry_id] = hass_data

    # Forward the setup to the sensor platform.
    try:
        _LOGGER.error("---------- SB ------------- Async Setup Entry ")
        api = await hass.async_add_executor_job(
            SentioModbus, entry.data[CONF_IP_ADDRESS]
        )
        _LOGGER.error("---------- SB ------------- Async Setup Entry - Start Connect ")
        status = await hass.async_add_executor_job(api.connect)

        _LOGGER.error("---------- SB ------------- Async Setup Entry -  Connect {0} ".format(status))
        if status != 0:
            raise ConfigEntryAuthFailed("Failed to connect")

    except NoConnectionPossible as err:
        raise ConfigEntryAuthFailed(err) from err

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "climate")
    )
    return True


async def async_setup(hass: core.HomeAssistant, config: dict) -> bool:
    """Set up the Wavin Sentio component."""
    # @TODO: Add setup code.
    return True
