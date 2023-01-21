print("Testing")
import SentioModbus.SentioApi
from SentioModbus import SentioApi
from SentioModbus.SentioApi import SentioApi

api = SentioApi.SentioModbus("hssdfsfsd")
print("Api = {0}".format(api))
print("Modbus Type = {0}".format(SentioApi.ModbusType.MODBUS_TCPIP))


