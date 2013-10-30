import obd2

ser = obd2.ObdConnection('/dev/ttyUSB0', wait_time=0)

print(ser.communicate('AT H1 \r'))

x = 0x6 
z = 0
for a in range(0x7):
    y = 1
    for b in range(0x10):
        z = 0 
        for c in range(1):
            print('--------------------------------------------------')
            print('Address -> ', ser.communicate('AT SH '+hex(x)[2:4]+hex(y)[2:4]+hex(z)[2:4]+' \r'))
            print('01 -> ', ser.communicate('01 3E \r'))
            print('02 -> ', ser.communicate('02 3E \r'))
            print('03 -> ', ser.communicate('3E \r'))
            print('04 -> ', ser.communicate('09 0A \r'))
        y += 1
    x += 1
      
