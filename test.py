#/usr/bin/python

import obd2

handle = obd2.ObdFunctions(obd2.ObdConnection('/dev/ttyUSB0'))

pids_available = handle.get_supported_pids_mode_1()
print(pids_available)


dtc_stored = handle.get_dtc_mode_3()