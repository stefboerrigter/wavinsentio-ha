import logging

from homeassistant import config_entries, core

from homeassistant.exceptions import ConfigEntryAuthFailed, Unauthorized

from .const import DOMAIN

from homeassistant.const import CONF_HOST, CONF_PORT, CONF_TYPE, CONF_SLAVE, Platform
from homeassistant.core import HomeAssistant

from .SentioModbus.SentioApi.SentioApi import SentioModbus, NoConnectionPossible, ModbusType

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: config_entries.ConfigEntry
) -> bool:
    """Set up platform from a ConfigEntry."""
    hass.data.setdefault(DOMAIN, {})
    #hass_data = dict(entry.data)
    _LOGGER.error("__INIT__ Setting up with data --> {0}".format(entry.data))
    
    hass.data[DOMAIN] = SentioApiHandler(entry.data[CONF_TYPE], entry.data[CONF_HOST], entry.data[CONF_PORT], entry.data[CONF_SLAVE], logging.DEBUG, hass)
    #try:      
    #    api = await hass.async_add_executor_job(
    #        SentioModbus, entry.data[CONF_TYPE], entry.data[CONF_HOST], entry.data[CONF_PORT], entry.data[CONF_SLAVE], entry.data[CONF_PORT], logging.DEBUG
    #    )
    #    
    #    status = await hass.async_add_executor_job(api.connect)
    #
    #    if status != 0:
    #        raise ConfigEntryAuthFailed("Failed to connect")
    #
    #except NoConnectionPossible as err:
    #    raise ConfigEntryAuthFailed(err) from err

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "climate")
    )

    return True


class SentioApiHandler:

    def __init__(self, type, host, port, slave, loglevel, hass: HomeAssistant):
        self._data = {}
        self._connected = False
        self._initialized = False
        self._value = 0
        self._hass = hass
        self._api = SentioModbus(type, host, port, slave, port, loglevel)
        _LOGGER.error("Sentio API class {0}".format(self._value))

    async def connect(self):
        if self._connected:
            _LOGGER.error("Sentio connection already established")
            return
        else:
            status = await self._hass.async_add_executor_job(self._api.connect)
            if status == 0:
                self._connected = True
            else:
                _LOGGER.error("Sentio connection failed")
        return self._connected

    async def initialize(self):
        if self._initialized:
            _LOGGER.error("Sentio data already initialized")
            return
        else:
            status = await self._hass.async_add_executor_job(self._api.initialize)
            if status == 0:
                self._initialized = True
        return self._initialized

    async def update(self):
        _LOGGER.error("Calling Update")
        if self._connected == False or self._initialized == False:
            _LOGGER.error("Connect and initialize first!")
        else:
            await self._hass.async_add_executor_job(self._api.updateData)
    
    async def setRoomTemperature(self, roomIndex, temperature):
        room = self.getRoom(self, roomIndex)
        await self._hass.async_add_executor_job(room.setRoomSetpoint, temperature)

    @property
    def sentioData(self):
        return self._api.sentioData

    def getAvailableRooms(self):
        return self._api.availableRooms
    
    def getRoom(self, index):
        for room in self._api.availableRooms:
            if room.index == index:
                return room
        return None


async def async_setup(hass: core.HomeAssistant, config: dict) -> bool:
    """Set up the Wavin Sentio component."""
    # @TODO: Add setup code.
    _LOGGER.error("__INIT__ : Calling async setup for INIT file ")
    return True
