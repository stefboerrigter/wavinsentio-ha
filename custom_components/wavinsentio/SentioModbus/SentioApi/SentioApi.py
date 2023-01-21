import logging

from pymodbus.client import ModbusTcpClient
from pymodbus.client import ModbusSerialClient
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.constants import Endian

#Api regisers and defaults
#import Defaults
from .Defaults import Defaults
from .SentioRegisterMap import *
from .SentioTypes import *

#sentio types
from .SentioTypes import *

class ModbusType(Enum):
    MODBUS_TCPIP = 0
    MODBUS_RTU = 1


#class SentioApi:

class SentioModbus:
    def __init__(self, 
        _host: str = "",
        _ModbusType:ModbusType = ModbusType.MODBUS_TCPIP,
        _baudrate: int = Defaults.BaudRate,
        _slaveId: int = Defaults.SlaveId,
        _port: int = Defaults.TcpPort,
        _loglevel = logging.ERROR
    ):
        self.host = _host
        self.slaveId = _slaveId
        self.port = _port
        self.modbusType = _ModbusType
        logging.basicConfig(format='%(levelname)s %(asctime)s | %(message)s', level=_loglevel, datefmt='%m/%d/%Y %H:%M:%S')
        pass

    def connectModbusRTU(self):
        try:
            self.client = ModbusSerialClient(self.host, baudrate=self._baudrate)
            logging.debug("Connecting")
            result = self.client.connect()
            if result == True:
                logging.debug("Connected {0}".format(result))
                #super().connect()
                return 0
            else:
                logging.error("Failed to connect")
                return -1
        except:
            logging.exception("Failed to connect")
            return -1
        pass

    def connectModbusTcpIp(self):
        try:
            self.client = ModbusTcpClient(self.host)
            logging.debug("Connecting")
            result = self.client.connect()
            if result == True:
                logging.debug("Connected {0}".format(result))
                #super().connect()
                return 0
            else:
                logging.error("Failed to connect")
                return -1
        except:
            logging.exception("Failed to connect")
            raise NoConnectionPossible("Failed to connect")

    def connect(self):
        if self.modbusType == ModbusType.MODBUS_TCPIP:
           return self.connectModbusTcpIp()
        elif self.modbusType == ModbusType.MODBUS_RTU:
            return self.connectModbusRTU()
        else: 
            logging.exception("Wrong modbus type detected {0}".format(self.modbusType))
            raise AttributeError("Wrong modbus type detected {0}".format(self.modbusType))

    def disconnect(self):
        return self.client.close()

    def initializeDeviceData(self, deviceType:SentioDeviceType = SentioDeviceType.CCU208):
        returnValue = 0
        deviceTypeInt = self.readRegister(SentioRegisterMap.DeviceType)
        try:
            devType = SentioDeviceType(deviceTypeInt)
            if devType  == deviceType and devType == SentioDeviceType.CCU208:
                #check supported FW version.
                self.serialNumberPrefix =  self.readRegister(SentioRegisterMap.DeviceSerialNrPrefix)
                self.serialNumberNumber  = self.readRegister(SentioRegisterMap.DeviceSerialNumber)
                if self.serialNumberPrefix != Defaults.SerialNumberPrefix:
                    logging.error("Invalid Serial Number Prefix")
                    return -1
                self.firmwareVersionMajor = self.readRegister(SentioRegisterMap.DeviceSwVersion)
                self.firmwareVersionMinor = self.readRegister(SentioRegisterMap.DeviceSwVersionMinor)
                # test fw version at least 12
                if self.firmwareVersionMajor < 12:
                    logging.error("Minimum supported FW version is 12.X, please update your sentio")
                    return -1
                self.roomCount = self.detectRooms()

            else:
                logging.error("Device Type is not equal {0} {1}".format(deviceTypeInt == deviceType, SentioDeviceType(deviceTypeInt) == SentioDeviceType.CCU208))
                returnValue = -1
        except Exception as e:
            logging.error("Exception occured ==> {0}".format(e))
            returnValue = -1

        return returnValue

    def detectRooms(self):
        nrRooms = 0
        roomCtr = 0
        self.detectedRooms=[]
        for roomCtr in range(Defaults.MaxNumberOfRooms):
            try:
                value = self.readRegister(SentioRegisterMap.RoomName, _roomCount = roomCtr)
                if value:
                    self.detectedRooms.append(SentioRoom(roomCtr, value.decode('utf-8')))
                #else:
                    #logging.error("Room {0} not found".format(roomCtr))
            except Exception as e:
                logging.exception("Exception reading room {0}".format(e))

        for room in self.detectedRooms:
            logging.debug("Room ID={0} | Name={1}".format(room.index, room.name))
        
        return nrRooms

    def writeRegister(self, registerMapObject, value, _roomCount = 0):
        returnValue = 0
        
        try:
            address = registerMapObject.address
            if(registerMapObject.objectType == RegisterObjectType.ROOM):
                logging.debug("Detected Room Object {0} - {1}".format(address, _roomCount))
                address = (_roomCount * 100) + address
            if(registerMapObject.regType == RegisterType.INPUT_REGISTER):
                logging.error("Not possible to write input reg")
            elif(registerMapObject.regType == RegisterType.DISCRETE_INPUT):
                logging.error("Not possible to write discrete input reg")
            elif(registerMapObject.regType == RegisterType.HOLDING_REGISTER):
                returnValue = self.client.write_register(address, value, slave=self.slaveId)
        except Exception as e:
            logging.exception("error occured ==>  {0}".format(e))
            returnValue = -1
        return returnValue

    def readRegister(self, registerMapObject, _roomCount = 0):
        returnValue = 0
        #logging.("--- Super readRegister called ----{0}".format(registerMapObject.regType))
        #logging.error(registerMapObject)
        try:
            address = registerMapObject.address
            if(registerMapObject.objectType == RegisterObjectType.ROOM):
                #logging.error("Detected Room Object {0} - {1}".format(address, _roomCount))
                address = (_roomCount * 100) + address

            if(registerMapObject.regType == RegisterType.INPUT_REGISTER):
                response = self.client.read_input_registers(address, registerMapObject.count, slave=self.slaveId)
                if not response.isError(): 
                    if(registerMapObject.dataType == RegisterDataType.NUMERIC):
                        if(registerMapObject.count == 1):
                            returnValue = response.registers[0]
                        else:
                            decoder = BinaryPayloadDecoder.fromRegisters(response.registers, wordorder=Endian.Big, byteorder=Endian.Big)
                            if(registerMapObject.count == 2):
                                if(registerMapObject.count == 2):
                                    returnValue = decoder.decode_32bit_uint()
                                elif(registerMapObject.count == 4):
                                    returnValue = decoder.decode_64bit_uint()
                                else:
                                    logging.error("Unsupported decoding format {0}".format(registerMapObject.count))
                    elif(registerMapObject.dataType == RegisterDataType.STRING):
                        decoder = BinaryPayloadDecoder.fromRegisters(response.registers, wordorder=Endian.Big, byteorder=Endian.Big)
                        returnValue = decoder.decode_string(registerMapObject.count)  
                    elif(registerMapObject.dataType == RegisterDataType.VAL_D2FP100):
                        if(registerMapObject.count == 1):
                            fp100value = response.registers[0]
                            returnValue = fp100value / 100
                            logging.info("Found {0} -> /100 = {1}".format(fp100value, returnValue))
                        else:
                            logging.error("Unsupported count for Holding Registers {0} D2_FP100".format(registerMapObject.count))

                    else:
                        logging.error("No support yet for Input Register with {0} type".format(registerMapObject.regType))
                #logging.error("Read InputReg complete {0}".format(returnValue))
            elif(registerMapObject.regType == RegisterType.DISCRETE_INPUT):
                logging.error("Discrete Input type {0} - {1}".format(address, registerMapObject.count))
            
            elif(registerMapObject.regType == RegisterType.HOLDING_REGISTER):
                #logging.error("Holding Register type {0} - {1}".format(registerMapObject.address, registerMapObject.count))
                response = self.client.read_holding_registers(address, registerMapObject.count, slave=self.slaveId)
                if not response.isError(): 
                    if(registerMapObject.dataType == RegisterDataType.NUMERIC):
                        if(registerMapObject.count == 1):
                            returnValue = response.registers[0]
                        else:
                            logging.error("Unsupported count for Holding Registers {0} Numeric".format(registerMapObject.count))
                    elif(registerMapObject.dataType == RegisterDataType.STRING):
                        decoder = BinaryPayloadDecoder.fromRegisters(response.registers, wordorder=Endian.Big, byteorder=Endian.Big)
                        returnValue =  decoder.decode_string(registerMapObject.count)
                    elif(registerMapObject.dataType == RegisterDataType.VAL_D2FP100):
                        if(registerMapObject.count == 1):
                            fp100value = response.registers[0]
                            returnValue = fp100value / 100
                            logging.info("Found {0} -> /100 = {1}".format(fp100value, returnValue))
                        else:
                            logging.error("Unsupported count for Holding Registers {0} D2_FP100".format(registerMapObject.count))

        except Exception as e:
            logging.exception("error occured ==>  {0}".format(e))
            return -1
        return returnValue

    def readDeviceData(self):
        devType = self.readRegister(SentioRegisterMap.DeviceType)
        logging.info("DeviceType           = {0}".format(devType))
        logging.info("SerialNumberPrefix   = {0}".format(self.readRegister(SentioRegisterMap.DeviceSerialNrPrefix)))
        logging.info("SerialNumber         = {0}".format(self.readRegister(SentioRegisterMap.DeviceSerialNumber)))
        logging.info("ModbusMode           = {0}".format(self.readRegister(SentioRegisterMap.ModbusMode)))
    
    def getRooms(self):
        return self.detectedRooms
    
    def setRoomSetpoint(self, roomIndex, setpointdouble):
        for room in self.detectedRooms:
            if room.index == roomIndex:
                mode = self.readRegister(SentioRegisterMap.RoomModeOverride, _roomCount = roomIndex)
                if mode != SentioRoomModeSetting.RM_NONE:
                    self.writeRegister(SentioRegisterMap.RoomModeOverride, SentioRoomModeSetting.RM_NONE.value, _roomCount = roomIndex)

                setpoint_fp100 = int(setpointdouble * 100)
                logging.debug(" ---------- Set room {0} temp setpoint to {1}".format(roomIndex, setpoint_fp100))
                value = self.writeRegister(SentioRegisterMap.RoomTempSetpChange, setpoint_fp100, _roomCount = roomIndex)
                return value
            
        return -1

    def getOutdoorTemperature(self):
        return self.readRegister(SentioRegisterMap.OutdoorTemperature)

    def getRoomSetpoint(self, roomIndex):
        for room in self.detectedRooms:
            if room.index == roomIndex:
                value = self.readRegister(SentioRegisterMap.RoomTempSetpoint, _roomCount = roomIndex) / 100
                return value
        return -1
    
    def getRoomActualTemperature(self, roomIndex):
        for room in self.detectedRooms:
            if room.index == roomIndex:
                value = self.readRegister(SentioRegisterMap.RoomAirTempActual, _roomCount = roomIndex)
                return value / 100
        return -1

    def getRoomRelativeHumidity(self, roomIndex):
        for room in self.detectedRooms:
            if room.index == roomIndex:
                value = self.readRegister(SentioRegisterMap.RoomRelHumidity, _roomCount = roomIndex)
                return value / 100
        return -1

    def getRoomFloorTemperature(self, roomIndex):
        for room in self.detectedRooms:
            if room.index == roomIndex:
                value = self.readRegister(SentioRegisterMap.RoomFloorTempActual, _roomCount = roomIndex)
                return value / 100
        return -1

    def getRoomCalculatedDewPoint(self, roomIndex):
        for room in self.detectedRooms:
            if room.index == roomIndex:
                value = self.readRegister(SentioRegisterMap.RoomCalcDewPoint, _roomCount = roomIndex)
                return value / 100
        return -1

    def getRoomHeatingState(self, roomIndex):
        for room in self.detectedRooms:
            if room.index == roomIndex:
                value = self.readRegister(SentioRegisterMap.RoomHeatingState, _roomCount = roomIndex)
                return SentioHeatingStates(value)
        return -1

    def getRoomMode(self, roomIndex):
        for room in self.detectedRooms:
            if room.index == roomIndex:
                value = self.readRegister(SentioRegisterMap.RoomMode, _roomCount = roomIndex)
                return SentioRoomMode(value)
        return -1

    def setRoomMode(self, roomIndex, roomMode:SentioRoomMode):
        for room in self.detectedRooms:
            if room.index == roomIndex:
                logging.info("Setting Room {0} to set room {1} {2}".format(roomIndex, roomMode, roomMode.value))
                value = self.writeRegister(SentioRegisterMap.RoomMode, roomMode.value, _roomCount = roomIndex)
                return True
        logging.error("Failed to set room mode")
        return False


class NoConnectionPossible(Exception):
    pass