#!/usr/bin/python

import serial,os


class ObdConnection:
    def __init__(self, port, bauds=38400, timeout=1, prot_no=0):
        self.ser_con = serial.Serial(port, bauds, timeout=timeout)
        self.set_protocol(prot_no)

    # uses the AT SP Command to set the choosen protocol
    # 0 = auto detection
    def set_protocol(self, prot_no):
        self.write('AT SP' + str(prot_no) + ' \r');sleep(40);
        answer = self.readline(); print(answer)
        if 'OK' in answer:
            return True, answer
        return False, answer

    def write(self, data):
        byte_count = self.ser_con.write(data)
        return byte_count


    def readline(self):
        return str(self.ser_con.readline())


class ObdFunctions:
    def __init__(self, connection):
        self.con = connection

    # the method expects an answer like 01 00 \rSEARCHING...\rXX YY ZZ ... \r\r
    # the interesting part is between the last \r to \r\r
    def get_supported_pids_mode_1(self):
        self.con.write('01 00 \r')
        answer = self.con.readline(); print(answer);
        end_index = answer.find('\r\r')
        start_index = answer.rfind('\r', end_index)
        supported_encoded = answer[start_index + 1:end_index - 1].split(' ')
        supported_decoded = []
        i = 48 
        #for elem in supported_encoded:
        #    bin_comp = 0b10000000; 
        #    for x in range(8):
        #        if (int(elem, 16) & bin_comp) == bin_comp:
        #            supported_decoded.append(i)
        #        i -= 1
        #        bin_comp -= (bin_comp / 2)
        #supported_decoded = sorted(supported_decoded)
        return supported_decoded

