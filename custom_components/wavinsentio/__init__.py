import logging

from homeassistant import config_entries, core

from homeassistant.exceptions import ConfigEntryAuthFailed, Unauthorized

from .const import DOMAIN

from homeassistant.const import CONF_HOST, CONF_PORT, CONF_TYPE, CONF_SLAVE

from .SentioModbus.SentioApi.SentioApi import SentioModbus, NoConnectionPossible, ModbusType

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: core.HomeAssistant, entry: config_entries.ConfigEntry
) -> bool:
    """Set up platform from a ConfigEntry."""
    hass.data.setdefault(DOMAIN, {})
    hass_data = dict(entry.data)
    _LOGGER.error("Setting up with data --> {0}".format(entry.data))
    # @TODO: Add setup code.
    # Registers update listener to update config entry when options are updated.
    # unsub_options_update_listener = entry.add_update_listener(options_update_listener)
    # Store a reference to the unsubscribe function to cleanup if an entry is unloaded.
    # hass_data["unsub_options_update_listener"] = unsub_options_update_listener
    hass.data[DOMAIN][entry.entry_id] = hass_data

    # Forward the setup to the sensor platform.
    if entry.data[CONF_TYPE] == "Network":
        modbusType = ModbusType.MODBUS_TCPIP
        baud = 0
    elif entry.data[CONF_TYPE] == "Serial":
        modbusType = ModbusType.MODBUS_RTU
        baud = 0 #TODO
    else:
        raise ConfigEntryAuthFailed("Failed to detect connection type")

    try:      
        api = await hass.async_add_executor_job(
            SentioModbus, modbusType, entry.data[CONF_HOST], entry.data[CONF_PORT], entry.data[CONF_SLAVE], baud, logging.DEBUG
        )
        
        status = await hass.async_add_executor_job(api.connect)

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
