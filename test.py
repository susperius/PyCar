#/usr/bin/python
#
#import obd2
#
#handle = obd2.ObdFunctions(obd2.ObdConnection('/dev/ttyUSB0'))
#
#pids_available = handle.get_supported_pids()
#print(pids_available)
#
#
#dtc_stored = handle.get_dtc()

import os
import pycar
from pycar import obd2

handle = obd2.ObdFunctions(obd2.ObdConnection('/dev/ttyUSB0', timeout=0.8))

while True:
    speed = handle.get_vehicle_speed()
    rpm = handle.get_engine_rpm()
    print('Speed -> '+rpm+' km/h\nRPM -> '+rpm)
    os.system('clear')
