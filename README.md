# Wavin Sentio for Home Assistant

## Requirements
Wavin Sentio CCU-208 controller running a recent firmware (tested with FW18)

## Installation
Open https://portal.wavinsentio.com/devices and add your system there. Use the new (FW18+) remote management feature to enable modbus. (Older versions can use the dedicated control box or the older desktop software to connect).

Go to system --> Installer settings --> Modbus configuration --> Sentio Modbus TCP
TCP Mode: Slave Read/Write
Note the IP and port number (often 502)

Add this module to your Home Assistant setup (use of HACS recommended) and restart Home Assistant. Go to integrations and Add Integration, Wavin Sentio Modbus.
Enter your IP number of the CCU and port number (often 502). Slave 1 works fine.

The addon should show a new device with all the subdevices (rooms). It's read/write so you should be able to set the modes/temperatures.