print("Testing")
import WavinSentioModbus
from SentioModbus import SentioApi
from WavinSentioModbus import SentioApi

api = SentioApi.SentioModbus("hssdfsfsd")
print("Api = {0}".format(api))
print("Modbus Type = {0}".format(SentioApi.ModbusType.MODBUS_TCPIP))


