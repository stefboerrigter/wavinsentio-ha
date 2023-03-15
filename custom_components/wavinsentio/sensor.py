from datetime import timedelta
import logging
from typing import Any, Final
from enum import Enum
from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.core import callback
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_TYPE, CONF_SLAVE

from homeassistant.const import (
    CONF_HOST, 
    CONF_PORT, 
    CONF_TYPE, 
    CONF_SLAVE, 
    PERCENTAGE, 
    TEMP_CELSIUS,
    UnitOfTemperature
)

from homeassistant.exceptions import ConfigEntryAuthFailed

from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from homeassistant.components.sensor import (
    SensorEntity, 
    SensorDeviceClass,
    SensorEntityDescription,
    SensorStateClass
)

from .const import (
    DOMAIN as SENTIO_CLIMATE_DOMAIN,
    _LOGGER,
)

#from WavinSentioInterface.SentioApi import SentioApi, NoConnectionPossible
from WavinSentioModbus.SentioApi import SentioModbus, NoConnectionPossible, ModbusType, SentioSensors

class SentioSensorTypes(Enum):
    OUTDOOR_TEMPERATURE_SENSOR = 0
    ITC_STATE = 10
    ITC_PUMPSTATE = 11
    ITC_INLETTEMP = 12
    ITC_INLETDESIRED = 13
    ITC_RETURNTEMP = 14
    ITC_SUPPLIERTEMP = 15

SENSORTYPE_TO_STRING: Final[dict[SentioSensorTypes, Any]] = {
    SentioSensorTypes.OUTDOOR_TEMPERATURE_SENSOR: "Temperature",
    SentioSensorTypes.ITC_STATE: "ITC State",
    SentioSensorTypes.ITC_PUMPSTATE: "ITC Pump State",
    SentioSensorTypes.ITC_INLETTEMP: "ITC InletTemperature",
    SentioSensorTypes.ITC_INLETDESIRED: "ITC Desired InletTemperature",
    SentioSensorTypes.ITC_RETURNTEMP: "ITC Return Temperature",
    SentioSensorTypes.ITC_SUPPLIERTEMP: "ITC Supplier Temperature",
}

SENSORTYPE_TO_DEVICECLASS: Final[dict[SentioSensorTypes, Any]] = {
    SentioSensorTypes.OUTDOOR_TEMPERATURE_SENSOR: SensorDeviceClass.TEMPERATURE,
    SentioSensorTypes.ITC_STATE: None,
    SentioSensorTypes.ITC_PUMPSTATE: None,
    SentioSensorTypes.ITC_INLETTEMP: SensorDeviceClass.TEMPERATURE,
    SentioSensorTypes.ITC_INLETDESIRED:SensorDeviceClass.TEMPERATURE,
    SentioSensorTypes.ITC_RETURNTEMP: SensorDeviceClass.TEMPERATURE,
    SentioSensorTypes.ITC_SUPPLIERTEMP: SensorDeviceClass.TEMPERATURE,
}

SENSORTYPE_TO_NATIVETYPE: Final[dict[SentioSensorTypes, Any]] = {
    SentioSensorTypes.OUTDOOR_TEMPERATURE_SENSOR: float,
    SentioSensorTypes.ITC_STATE: int,
    SentioSensorTypes.ITC_PUMPSTATE: int,
    SentioSensorTypes.ITC_INLETTEMP: float,
    SentioSensorTypes.ITC_INLETDESIRED: float,
    SentioSensorTypes.ITC_RETURNTEMP: float,
    SentioSensorTypes.ITC_SUPPLIERTEMP: float,
}

SENSORTYPE_TO_SENSORUNIT: Final[dict[SentioSensorTypes, Any]] = {
    SentioSensorTypes.OUTDOOR_TEMPERATURE_SENSOR: UnitOfTemperature.CELSIUS,
    SentioSensorTypes.ITC_STATE: int,
    SentioSensorTypes.ITC_PUMPSTATE: int,
    SentioSensorTypes.ITC_INLETTEMP: UnitOfTemperature.CELSIUS,
    SentioSensorTypes.ITC_INLETDESIRED: UnitOfTemperature.CELSIUS,
    SentioSensorTypes.ITC_RETURNTEMP: UnitOfTemperature.CELSIUS,
    SentioSensorTypes.ITC_SUPPLIERTEMP: UnitOfTemperature.CELSIUS,
}

'''
@dataclass
class SentioSensorDescriptionMixin:
    """Mixin for required keys."""

    value_fn: Callable[[SentioModbus], Any]


@dataclass
class SentioSensorEntityDescription(
        SensorEntityDescription, SentioSensorDescriptionMixin
):
    """Describes a Aseko binary sensor entity."""


UNIT_SENSORS: tuple[SentioSensorEntityDescription, ...] = (
    SentioSensorEntityDescription(
        key="outsideTemp",
        name="Outside Temperature",
        icon="mdi:waves-arrow-right",
        value_fn=lambda sensorObject: sensorObject.getOutdoorTemp,
    ),
    #SentioSensorEntityDescription(
    #    key="has_alarm",
    #    name="Alarm",
    #    value_fn=lambda unit: unit.has_alarm,
    #    device_class=BinarySensorDeviceClass.SAFETY,
    #),
    #SentioSensorEntityDescription(
    #    key="has_error",
    #    name="Error",
    #    value_fn=lambda unit: unit.has_error,
    #    device_class=BinarySensorDeviceClass.PROBLEM,
    #),
)
'''
UPDATE_DELAY = timedelta(seconds=30)

async def async_setup_entry(hass, entry, async_add_entities):
    _LOGGER.error("Printing HASS Object Start")
    _LOGGER.error(hass)
    _LOGGER.error("Printing HASS Object Done")
    
    outdoor_temp=None

    try:      
        sentioApi = hass.data[SENTIO_CLIMATE_DOMAIN]

        status = await sentioApi.connect()
        if status != True: 
            raise ConfigEntryAuthFailed("Failed to connect")
        status = await sentioApi.initialize()
        if status != True:
            raise ConfigEntryAuthFailed("Failed to initialize")
        await sentioApi.update()

    except NoConnectionPossible as err:
        raise ConfigEntryAuthFailed(err) from err

    outdoor_temp = sentioApi.outdoorTemperature

    itcs =  sentioApi.getItcData()

    dataservice = WavinSentioSensorDataService(
        hass, sentioApi
    )
    dataservice.async_setup()
    
    entities = []

    if itcs != None:
        for itc in itcs:
            _LOGGER.error("We have ITC Circuits {0}".format(itc))
    else:
        _LOGGER.error("We have NO ITC Circuits")
    
    if outdoor_temp != None:
        _LOGGER.error("We have an outdoor temperature sensor {0}".format(outdoor_temp))
        entities.append(WavinSentioOutdoorTemperatureSensor(dataservice))
    else:
        _LOGGER.error("We have NO outdoor temperature sensor {0}".format(outdoor_temp))

    async_add_entities(entities)
    """
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
    """


class WavinSentioSensorDataService:
    """Get and update the latest data."""

    def __init__(self, hass, api):
        """Initialize the data object."""
        self._api = api

        self._outdoorTemp = None
        self._itcData = None
        self._hcsourceData = None
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
        _LOGGER.error("Auto update self called from Sensors")
        try:
            await self._api.update()
            
            self._outdoorTemp = self._api.outdoorTemperature

            self._itcData = self._api.getItcData()

            self._hcsourceData = self._api.hcSourceState

        except KeyError as ex:
            raise UpdateFailed("Missing overview data, skipping update") from ex

    def get_outdoorTemp(self):
        return self._outdoorTemp
    
    def get_itcData(self):
        return self._itcData
    
    """
    def showItcCircuit(self, itcCircuit):
        logging.info("-- {0}".format(itcCircuit.name))
        logging.info("-- Index      {0}".format(itcCircuit.index))
        logging.info("-- State      {0}".format(itcCircuit._state))
        logging.info("-- PumpState  {0}".format(itcCircuit._pumpState))
        if itcCircuit._inletMeasured:
            logging.info("-- InletTemp  {0}%".format(itcCircuit._inletMeasured))
        if itcCircuit._inletDesired:
            logging.info("-- InletDes   {0}°C".format(itcCircuit._inletDesired))
        if itcCircuit._returnTemp:
            logging.info("-- ReturnTemp {0} °C".format(itcCircuit._returnTemp))
        if itcCircuit._supplierTemp:
            logging.info("-- SupplierTmp{0} °C".format(itcCircuit._supplierTemp))
    """
    def get_HCSourceData(self):
        return self._hcsourceData

"""
class WavinSentioSensor(SensorEntity):
    #Representation of a generic Sensor.

    def __init__(self, hass, room, dataservice, sensorType:SentioSensorTypes):
        #Initialize the sensor.
        self._state = None
        self._dataservice = dataservice
        self._roomcode = room.index
        self._hass = hass
        self._sensorType = sensorType
        self._name = "{0} {1}".format(room.name, SENSORTYPE_TO_STRING[self._sensorType])
        self._attr_name = self._name
        self._attr_unique_id = "{0}_{1}".format(self._roomcode, self._name.replace(" ", "_"))
        self._native_value = float(0.0)
        self._attr_native_value = float(0.0)
        self._attr_native_unit_of_measurement = SENSORTYPE_TO_SENSORUNIT[self._sensorType]
        self._attr_precision = 0.1
        self._attr_temperature_unit = TEMP_CELSIUS
        self._attr_device_class = SENSORTYPE_TO_DEVICECLASS[self._sensorType]
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self.update()

    def update(self) -> None:
        #Retrieve latest state.
        temp_room = self._dataservice.get_room(self._roomcode)
        if temp_room is not None:
            if self._sensorType == SentioSensorTypes.ROOM_HUMIDITY:
                self._attr_native_value = float(temp_room.getRoomRelativeHumidity())
            elif self._sensorType == SentioSensorTypes.ROOM_FLOORTEMP:
                self._attr_native_value = temp_room.GetFloorTemp()
            elif self._sensorType == SentioSensorTypes.ROOM_CALCULATED_DEWPOINT:
                self._attr_native_value = temp_room.getRoomCalculatedDewPoint()
            else:
                _LOGGER.error("Unsupported sensortype {0}".format(self._sensorType))
        self._native_value = self._attr_native_value
        _LOGGER.error("Updating {0} {1}".format(self._attr_unique_id, self._attr_native_value))
"""

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
                    (SENTIO_CLIMATE_DOMAIN, self._dataservice.get_serialNumber())
                },
                "name": self._name,
                "manufacturer": "Wavin",
                "model": "Sentio",
                "sw_version": self._dataservice.get_firmwareRevision(),
            }
        return
