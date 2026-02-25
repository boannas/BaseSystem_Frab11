import protocol as proto
from pymodbus.client import ModbusSerialClient
import time

protocol = proto.Protocol()
protocol.slave_address = 21

while True:
    time.sleep(.2)
    (protocol.routine())
    protocol.write_stop_process("Stop")

# protocol.write_base_system_status("sss")


