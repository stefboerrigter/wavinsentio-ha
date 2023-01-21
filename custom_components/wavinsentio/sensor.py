from datetime import timedelta
import logging

from homeassistant.core import callback
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_TYPE, CONF_SLAVE

from homeassistant.const import TEMP_CELSIUS

from homeassistant.exceptions import ConfigEntryAuthFailed

from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import DOMAIN, CONF_LOCATION_ID

#from WavinSentioInterface.SentioApi import SentioApi, NoConnectionPossible
from .SentioModbus.SentioApi.SentioApi import SentioModbus, NoConnectionPossible, ModbusType

_LOGGER = logging.getLogger(__name__)

UPDATE_DELAY = timedelta(seconds=30)


async def async_setup_entry(hass, entry, async_add_entities):
    _LOGGER.error("Printing HASS Object Start")
    _LOGGER.error(hass)
    _LOGGER.error("Printing HASS Object Done")
    
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


    outdoor_temp = await hass.async_add_executor_job(
        api.getOutdoorTemperature
    )

    _LOGGER.error("Initial Reading outdoor Temp {0}".format(outdoor_temp))
    dataservice = WavinSentioSensorDataService(
        hass, api, outdoor_temp
    )
    dataservice.async_setup()

    #await dataservice.coordinator.async_refresh()

    outdoorTemperatureSensor = WavinSentioOutdoorTemperatureSensor(dataservice)

    entities = []
    entities.append(outdoorTemperatureSensor)

    async_add_entities(entities)


class WavinSentioSensorDataService:
    """Get and update the latest data."""

    def __init__(self, hass, api, outdoor_temp):
        """Initialize the data object."""
        self.api = api

        self.outdoor_temp = outdoor_temp

        self.hass = hass
        self.coordinator = None

    @callback
    def async_setup(self):
        """Coordinator creation."""
        self.coordinator = DataUpdateCoordinator(
            self.hass,
            _LOGGER,
            name="WavinSentioDataService",
            update_method=self.async_update_data,
            update_interval=self.update_interval,
        )

    @property
    def update_interval(self):
        return UPDATE_DELAY

    async def async_update_data(self):
        try:
            self.outdoor_temp = await self.hass.async_add_executor_job(
                self.api.getOutdoorTemperature
            )
            _LOGGER.error("Reading outdoor Temp {0}".format(self.outdoor_temp))
        except KeyError as ex:
            raise UpdateFailed("Missing overview data, skipping update") from ex

    def get_outdoorTemp(self):
        return self.outdoor_temp


class WavinSentioOutdoorTemperatureSensor(CoordinatorEntity, SensorEntity):
    """Representation of an Outdoor Temperature Sensor."""

    def __init__(self, dataservice):
        """Initialize the sensor."""
        super().__init__(dataservice.coordinator)
        self._state = None
        self._dataservice = dataservice

    @property
    def should_poll(self):
        """Return the polling state."""
        return True

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "Outdoor Temperature" 
        #self._dataservice.outdoor_temp()["name"]

    @property
    def state(self):
        """Return the state of the sensor."""
    #    #return self._dataservice.outdoor_temp()

        #return int(self._dataservice.get_outdoorTemp())
        self._state = self._dataservice.get_outdoorTemp()
        return self._state

    @property
    def native_value(self):
        """Return the state."""
        return self._dataservice.get_outdoorTemp()

    @property
    def unit_of_measurement(self) -> str:
        """Return the unit of measurement."""
        return TEMP_CELSIUS

    @property
    def device_class(self):
        return "temperature"

    @property
    def unique_id(self):
        """Return the ID of this device."""
        return "Invalid Serial"
        #self._dataservice.get_outdoorTemp()["serialNumber"]

    @property
    def device_info(self):
        temp_location = self._dataservice.get_outdoorTemp()
        if temp_location is not None:
            return {
                "identifiers": {
                    # Serial numbers are unique identifiers within a specific domain
                    (DOMAIN, self.unique_id)
                },
                "name": self.name,
                "manufacturer": "Wavin",
                "model": "Sentio",
            }
        return
