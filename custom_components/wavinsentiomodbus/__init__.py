import logging

from homeassistant import config_entries, core

from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady, Unauthorized

from .const import DOMAIN

from homeassistant.const import CONF_HOST, CONF_PORT, CONF_TYPE, CONF_SLAVE, Platform
from homeassistant.core import HomeAssistant

from WavinSentioModbus.SentioApi import SentioModbus, NoConnectionPossible, ModbusType

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: config_entries.ConfigEntry
) -> bool:
    """Set up platform from a ConfigEntry."""
    hass.data.setdefault(DOMAIN, {})
    _LOGGER.debug("__INIT__ Setting up with data --> {0}".format(entry.data))

    handler = SentioApiHandler(
        entry.data[CONF_TYPE], entry.data[CONF_HOST],
        entry.data[CONF_PORT], entry.data[CONF_SLAVE], logging.DEBUG, hass
    )
    hass.data[DOMAIN][entry.entry_id] = handler

    try:
        connected = await handler.connect()
        if not connected:
            raise ConfigEntryNotReady("Failed to connect to Wavin Sentio")
        initialized = await handler.initialize()
        if not initialized:
            raise ConfigEntryNotReady("Failed to initialize Wavin Sentio")
    except (AttributeError, NoConnectionPossible) as err:
        raise ConfigEntryNotReady(str(err)) from err

    await hass.config_entries.async_forward_entry_setups(entry, ["climate"])

    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: config_entries.ConfigEntry
) -> bool:
    """Unload a config entry and close the Modbus connection."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["climate", "sensor"])
    if unload_ok:
        handler: SentioApiHandler = hass.data[DOMAIN].pop(entry.entry_id)
        await hass.async_add_executor_job(handler._api.disconnect)
    return unload_ok


class SentioApiHandler:

    def __init__(self, type, host, port, slave, loglevel, hass: HomeAssistant):
        self._data = {}
        self._connected = False
        self._initialized = False
        self._value = 0
        self._hass = hass
        self._api = SentioModbus(ModbusType(type), host, port, slave, 0, loglevel)
        self.coordinator = None
        _LOGGER.debug("Sentio API class {0}".format(self._value))

    async def connect(self):
        if self._connected:
            _LOGGER.info("Sentio connection already established")
            return self._connected
        else:
            status = await self._hass.async_add_executor_job(self._api.connect)
            if status == 0:
                self._connected = True
            else:
                _LOGGER.debug("Sentio connection failed")
        return self._connected

    async def initialize(self):
        if self._initialized:
            _LOGGER.info("Sentio data already initialized")
            return self._initialized
        else:
            status = await self._hass.async_add_executor_job(self._api.initialize)
            if status == 0:
                self._initialized = True
        return self._initialized

    async def update(self):
        _LOGGER.debug("Calling Update")
        if self._connected == False or self._initialized == False:
            _LOGGER.debug("Connect and initialize first!")
        else:
            await self._hass.async_add_executor_job(self._api.updateData)
    
    async def setRoomTemperature(self, roomIndex, temperature):
        room = self.getRoom(roomIndex)
        await self._hass.async_add_executor_job(room.setRoomSetpoint, temperature)

    @property
    def sentioData(self):
        return self._api.sentioData

    def getAvailableRooms(self):
        return self._api.availableRooms
    
    def getItcData(self):
        return self._api.availableItcs
    
    def getHccData(self):
        return self._api.availableHccs
    
    def getBoilerTanks(self):
        return self._api.boilerTanks
    @property
    def outdoorTemperature(self):
        return self._api.sentioData.outdoor_temperature

    @property 
    def hcSourceState(self):
        return self._api.sentioData.hc_source_state

    def getTemperatureSensors(self, index):
        return self._api.sentioData.temperature_sensors(index)

    def getRoom(self, index):
        for room in self._api.availableRooms:
            if room.index == index:
                return room
        return None
    
    def getItcCircuit(self, index):
        for itc in self._api.availableItcs:
            if itc.index == index:
                return itc
        return None
    
    def getHccCircuit(self, index):
        for hcc in self._api.availableHccs:
            if hcc.index == index:
                return hcc
        return None

    def getBoilerTankByIndex(self, index):
        for tank in self._api.boilerTanks:
            if tank.index == index:
                return tank
        return None
    
async def async_setup(hass: core.HomeAssistant, config: dict) -> bool:
    """Set up the Wavin Sentio component."""
    # @TODO: Add setup code.
    _LOGGER.debug("__INIT__ : Calling async setup for INIT file ")
    return True
