from pycar import obd2

ser = obd2.ObdConnection('/dev/ttyUSB0', wait_time=0)

print(ser.communicate('AT H1 \r'))


class EcuFunctions:
    """
    This class has not been tested so far!!!!
    This class should help you find ECUs on the canbus
    My goal is to write a class, which does the enumeration of the ecus without CAF activated ... I hope I'll find
    some time soon ;)
    @author Susperius
    @contact susperius@gmail.com
    """
    def __init__(self, obdconnection):
        """
        @param obdconnection: ObdConnection
        @return:
        """
        self.con = obdconnection

    @staticmethod
    def __transform_intvalue_to_2char_hexstring(intvalue):
        return hex(intvalue)[2:5]

    @staticmethod
    def __transform_intvalue_to_3char_hexstring(intvalue):
        if intvalue < 0x010:
            hexstring = '00'+hex(intvalue)[2:4]
        elif intvalue < 0x100:
            hexstring = '0'+hex(intvalue)[2:5]
        else:
            hexstring = hex(intvalue)[2:6]
        return hexstring

    def enum_ecu(self, first_id, last_id):
        if (first_id or last_id) < 0x001 or (first_id or last_id) > 0x7FF:
            raise ValueError('lowest ID is 0x001 and highest is 0x7FF')
        usable_can_id = []
        start = int(first_id, 16)
        end = int(last_id, 16) + 1
        if 'OK' in self.con.communicate('AT H1 \r'):
            for x in range(start, end):
                can_id = EcuFunctions.__transform_intvalue_to_3char_hexstring(x)
                answer = self.con.communicate('AT SH '+can_id+' \r')
                if 'OK' in answer:
                    answer_header = EcuFunctions.__transform_intvalue_to_3char_hexstring(x + 0x8)
                    answer = self.con.communicate('01 3E \r')
                    answer += self.con.communicate('02 3E \r')
                    answer += self.con.communicate('3E')
                    if answer_header in answer:
                        usable_can_id.append(can_id)
                else:
                    raise IOError('ELM327: couldn\'t set the desired Header')
        else:
            raise IOError('ELM327: couldn\'t set show Header')
        return usable_can_id

    def find_supported_diagnostics(self, can_id):
        supported = []
        supported_working = []
        answer = self.con.communicate('AT SH '+can_id+' \r')
        if 'OK' in answer:
            for x in range(0x100):
                diag_id = EcuFunctions.__transform_intvalue_to_2char_hexstring(x)
                answer = self.con.communicate(diag_id+' \r')
                if ('7F' and '12') or ('7F' and '22') in answer:
                    supported.append(diag_id)
                elif '7F' in answer:
                    continue
                else:
                    supported_working.append(diag_id)
        else:
            raise IOError('ELM327: couldn\'t set desired Header')
        return {'supported': supported, 'working':supported_working}