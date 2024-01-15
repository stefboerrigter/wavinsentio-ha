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
    UnitOfTemperature,
    STATE_ON,
    STATE_OFF,
)

from homeassistant.exceptions import ConfigEntryAuthFailed

from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass
)

from homeassistant.components.sensor import (
    SensorEntity, 
    SensorDeviceClass,
    SensorEntityDescription,
    SensorStateClass
)

from homeassistant.components.climate import HVACMode
from homeassistant.helpers.typing import StateType

from .const import (
    DOMAIN as SENTIO_CLIMATE_DOMAIN,
    _LOGGER,
)

#from WavinSentioInterface.SentioApi import SentioApi, NoConnectionPossible
from WavinSentioModbus.SentioApi import SentioModbus, NoConnectionPossible, ModbusType, SentioSensors, ITC_PumpState
from WavinSentioModbus.SentioTypes import SentioHeatingStates

class SentioSensorTypes(Enum):
    ROOM_HUMIDITY = 0
    ROOM_FLOORTEMP = 1
    ROOM_CALCULATED_DEWPOINT = 2
    OUTDOOR_TEMPERATURE_SENSOR = 10
    ITC_STATE = 20
    ITC_PUMPSTATE = 21
    ITC_INLETTEMP = 22
    ITC_INLETDESIRED = 23
    ITC_RETURNTEMP = 24
    ITC_SUPPLIERTEMP = 25
    MAIN_HC_SOURCE = 30

SENSORTYPE_TO_STRING: Final[dict[SentioSensorTypes, Any]] = {
    SentioSensorTypes.ROOM_HUMIDITY: "Humidity",
    SentioSensorTypes.ROOM_FLOORTEMP: "FloorTemp",
    SentioSensorTypes.ROOM_CALCULATED_DEWPOINT: "CalculatedDewpoint",
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
    SentioSensorTypes.ITC_STATE: BinarySensorDeviceClass.HEAT,
    SentioSensorTypes.ITC_PUMPSTATE: BinarySensorDeviceClass.HEAT,
    SentioSensorTypes.ITC_INLETTEMP: SensorDeviceClass.TEMPERATURE,
    SentioSensorTypes.ITC_INLETDESIRED:SensorDeviceClass.TEMPERATURE,
    SentioSensorTypes.ITC_RETURNTEMP: SensorDeviceClass.TEMPERATURE,
    SentioSensorTypes.ITC_SUPPLIERTEMP: SensorDeviceClass.TEMPERATURE,
}

SENSORTYPE_TO_NATIVETYPE: Final[dict[SentioSensorTypes, Any]] = {
    SentioSensorTypes.ROOM_HUMIDITY: float,
    SentioSensorTypes.ROOM_FLOORTEMP: float,
    SentioSensorTypes.ROOM_CALCULATED_DEWPOINT: float,
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
    SentioSensorTypes.ITC_STATE: None,
    SentioSensorTypes.ITC_PUMPSTATE: None,
    SentioSensorTypes.ITC_INLETTEMP: UnitOfTemperature.CELSIUS,
    SentioSensorTypes.ITC_INLETDESIRED: UnitOfTemperature.CELSIUS,
    SentioSensorTypes.ITC_RETURNTEMP: UnitOfTemperature.CELSIUS,
    SentioSensorTypes.ITC_SUPPLIERTEMP: UnitOfTemperature.CELSIUS,
}


HVAC_MODE_HASS_TO_SENTIO: Final[dict[HVACMode, SentioHeatingStates]] = {
    HVACMode.COOL: SentioHeatingStates.COOLING,
    HVACMode.HEAT: SentioHeatingStates.HEATING,
    HVACMode.OFF: SentioHeatingStates.IDLE,
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
    _LOGGER.debug("Printing HASS Object Start")
    _LOGGER.debug(hass)
    _LOGGER.debug("Printing HASS Object Done")
    
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

    hcSource = sentioApi.hcSourceState

    rooms = sentioApi.getAvailableRooms()

    dataservice = WavinSentioSensorDataService(
        hass, sentioApi
    )
    dataservice.async_setup()
    
    entities = []

    if itcs != None:
        for itc in itcs:
            _LOGGER.debug("We have ITC Circuits {0}".format(itc))
            entities.append(WavinItcSensor(hass, itc, dataservice, SentioSensorTypes.ITC_STATE))
            entities.append(WavinItcSensor(hass, itc, dataservice, SentioSensorTypes.ITC_PUMPSTATE))
            entities.append(WavinItcSensor(hass, itc, dataservice, SentioSensorTypes.ITC_INLETTEMP))
            entities.append(WavinItcSensor(hass, itc, dataservice, SentioSensorTypes.ITC_INLETDESIRED))
            entities.append(WavinItcSensor(hass, itc, dataservice, SentioSensorTypes.ITC_RETURNTEMP))
            entities.append(WavinItcSensor(hass, itc, dataservice, SentioSensorTypes.ITC_SUPPLIERTEMP))
    else:
        _LOGGER.debug("We have NO ITC Circuits")
    
    if rooms != None:
        for room in rooms:
            _LOGGER.debug("We found a Room {0}".format(room))
            if room.getRoomRelativeHumidity() != None:
                entities.append(WavinSentioRoomSensor(room, dataservice, SentioSensorTypes.ROOM_HUMIDITY))
            if room.GetFloorTemp() != None:
                entities.append(WavinSentioRoomSensor(room, dataservice, SentioSensorTypes.ROOM_FLOORTEMP))
            if room.getRoomCalculatedDewPoint() != None:
                entities.append(WavinSentioRoomSensor(room, dataservice, SentioSensorTypes.ROOM_CALCULATED_DEWPOINT))

    if hcSource != None:
        entities.append(WavinHCSourceTemperatureSensor(dataservice))

    if outdoor_temp != None:
        _LOGGER.debug("We have an outdoor temperature sensor {0}".format(outdoor_temp))
        entities.append(WavinSentioOutdoorTemperatureSensor(dataservice))
    else:
        _LOGGER.debug("We have NO outdoor temperature sensor {0}".format(outdoor_temp))

    async_add_entities(entities)

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
        _LOGGER.debug("Auto update self called from Sensors")
        try:
            await self._api.update()
            
            self._outdoorTemp = self._api.outdoorTemperature

            self._itcData = self._api.getItcData()

            self._hcsourceData = self._api.hcSourceState

        except KeyError as ex:
            raise UpdateFailed("Missing overview data, skipping update") from ex

    def get_room(self, roomIndex):
        return self._api.getRoom(roomIndex)
        
    def get_outdoorTemp(self):
        return self._outdoorTemp
    
    def get_itcData(self):
        return self._itcData
    
    def get_itcCircuit(self, itcIndex):
        return self._api.getItcCircuit(itcIndex)
    
    def get_HCSourceData(self):
        return self._hcsourceData

    def get_serialNumber(self):
        return self._api.sentioData.serial_number

class WavinItcSensor(SensorEntity):
    #Representation of a generic Sensor. TODO; make classes and even more generic (ergo, remove the dirty tables)

    def __init__(self, hass, itc, dataservice, sensorType:SentioSensorTypes):
        #Initialize the sensor.
        self._state = None
        self._dataservice = dataservice
        self._itcIndex = itc.index
        self._hass = hass
        self._sensorType = sensorType
        self._name = "{0} {1}".format(itc.name, SENSORTYPE_TO_STRING[self._sensorType])
        self._attr_name = self._name
        self._attr_unique_id = "{0}_{1}".format(self._itcIndex, self._name.replace(" ", "_"))
        self._attr_native_unit_of_measurement = SENSORTYPE_TO_SENSORUNIT[self._sensorType]
        self._attr_device_class = SENSORTYPE_TO_DEVICECLASS[self._sensorType]

        self._native_value = None
        self._attr_native_value = None
        if self._sensorType != SentioSensorTypes.ITC_STATE:           
            self._attr_precision = 0.1
            self._attr_temperature_unit = TEMP_CELSIUS
        
        #self._attr_state_class = SensorStateClass.MEASUREMENT
        self.update()


    def update(self) -> None:
        #Retrieve latest state.
        local_itc = self._dataservice.get_itcCircuit(self._itcIndex)
        if local_itc is not None:
            if self._sensorType == SentioSensorTypes.ITC_STATE:
                itcState = local_itc._state
                if itcState == SentioHeatingStates.IDLE:
                    self._attr_native_value = HVACMode.OFF
                elif itcState == SentioHeatingStates.HEATING:
                    self._attr_native_value = HVACMode.HEAT
                elif itcState == SentioHeatingStates.COOLING:
                     self._attr_native_value = HVACMode.COOL  
            elif self._sensorType == SentioSensorTypes.ITC_PUMPSTATE:
                pumpState = local_itc.getPumpState
                if pumpState == ITC_PumpState.PUMP_IDLE:
                    self._attr_native_value = "IDLE"
                else:
                    self._attr_native_value = "ON"
            elif self._sensorType == SentioSensorTypes.ITC_INLETTEMP:
                self._attr_native_value = local_itc.getInletMeasured
            elif self._sensorType == SentioSensorTypes.ITC_INLETDESIRED:
                self._attr_native_value = local_itc.getInletDesired
            elif self._sensorType == SentioSensorTypes.ITC_RETURNTEMP:
                self._attr_native_value = local_itc.getReturnTemp
            elif self._sensorType == SentioSensorTypes.ITC_SUPPLIERTEMP:
                self._attr_native_value = local_itc.getSupplierTemp
            else:
                _LOGGER.debug("Unsupported sensortype {0}".format(self._sensorType))
        self._native_value = self._attr_native_value
        _LOGGER.debug("Updating {0} {1}".format(self._attr_unique_id, self._attr_native_value))


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
    
class WavinHCSourceTemperatureSensor(SensorEntity):

    def __init__(self, dataservice):
        #Initialize the sensor.
        self._state = None
        self._dataservice = dataservice
        self._name = "HC Source"
        self._attr_name = self._name
        self._attr_unique_id = "Sentio-HCSource"

        self._native_value = None
        self._attr_native_value = None

        #self._attr_state_class = SensorStateClass.MEASUREMENT
        self.update()
    
    def update(self) -> None:       
        state = self._dataservice.get_HCSourceData()
        if state != None:
            if state == SentioHeatingStates.IDLE:
                self._attr_native_value = HVACMode.OFF
            elif state == SentioHeatingStates.HEATING:
                self._attr_native_value = HVACMode.HEAT
            elif state == SentioHeatingStates.COOLING:
                self._attr_native_value = HVACMode.COOL
            elif state == SentioHeatingStates.BLOCKED_HEATING:
                self._attr_native_value = "Blocked Heat"
            elif state == SentioHeatingStates.BLOCKED_COOLING:
                self._attr_native_value = "Blocked Cooling" 
            else:
                _LOGGER.error("MAIN HC Source state unknown? {0} ".format(state))
            self._native_value = self._attr_native_value
            _LOGGER.debug("MAIN HC Source Updating {0} {1}".format(self._attr_unique_id, self._attr_native_value))
    
    @property
    def native_value(self) -> StateType:
        """Return the state."""
        return self._attr_native_value
    

class WavinSentioRoomSensor(SensorEntity):
    """Representation of an Outdoor Temperature Sensor."""

    def __init__(self, room, dataservice, sensorType:SentioSensorTypes):
        """Initialize the sensor."""
        #super().__init__(dataservice.coordinator)
        #self._state = None
        self._dataservice = dataservice
        self._roomcode = room.index
        self._sensorType = sensorType
        self._name = "{0} {1}".format(room.name, SENSORTYPE_TO_STRING[self._sensorType])
        self._attr_name = self._name
        self._attr_unique_id = "{0}_{1}".format(self._roomcode, self._name.replace(" ", "_"))
        self._native_value = None
        self._attr_native_value = None

        if self._sensorType == SentioSensorTypes.ROOM_HUMIDITY:
            self._attr_native_unit_of_measurement = PERCENTAGE
            self._attr_precision = 0
            self._attr_device_class = SensorDeviceClass.HUMIDITY
        else:
            self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
            self._attr_precision = 0.1
            self._attr_temperature_unit = TEMP_CELSIUS
            self._attr_device_class = SensorDeviceClass.TEMPERATURE
        
        self._attr_state_class = SensorStateClass.MEASUREMENT
        #self.update()

    @callback
    #def _handle_coordinator_update(self) -> None:
    #    """Update attributes when the coordinator updates."""
    #    _LOGGER.debug("Calling coordinator update from roomsensor class ")
    #    self.update()
    #    super()._handle_coordinator_update()

    def update(self) -> None:
        """Retrieve latest state."""
        temp_room = self._dataservice.get_room(self._roomcode)
        if temp_room is not None:
            if self._sensorType == SentioSensorTypes.ROOM_HUMIDITY:
                self._attr_native_value = round(float(temp_room.getRoomRelativeHumidity()), 1)
            elif self._sensorType == SentioSensorTypes.ROOM_FLOORTEMP:
                self._attr_native_value = round(temp_room.GetFloorTemp(), 1)
            elif self._sensorType == SentioSensorTypes.ROOM_CALCULATED_DEWPOINT:
                self._attr_native_value = round(temp_room.getRoomCalculatedDewPoint(), 1)
            else:
                _LOGGER.debug("Unsupported sensortype {0}".format(self._sensorType))
        self._native_value = self._attr_native_value
        _LOGGER.debug("Updating {0} {1}".format(self._attr_unique_id, self._attr_native_value))
    
    @property
    def native_value(self) -> StateType:
        """Return the state."""
        return self._attr_native_value