import obd2

ser = obd2.ObdConnection('/dev/ttyUSB0',wait_time=0)

print(ser.communicate('AT H1 \r'))

x = 0

for a in range(0x7):
    y = 0
    for b in range(0xF):
        z = 0
        for c in range(0xF):
            print('--------------------------------------------------')
            print('Address -> ',ser.communicate('AT SH '+hex(x)[2:4]+hex(y)[2:4]+hex(z)[2:4]+' \r'))
            print('01 -> ',ser.communicate('01 3E \r'))
            print('02 -> ',ser.communicate('02 3E \r'))
            z += 1
        y += 1
    x += 1
      
