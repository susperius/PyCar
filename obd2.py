#!/usr/bin/python

import serial
import time


class ObdConnection:
    sleep_time = 0

    def __init__(self, port, bauds=38400, timeout=1, prot_no=0, wait_time=0.5):
        self.ser_con = serial.Serial(port, bauds, timeout=timeout)
        self.set_protocol(prot_no)
        self.sleep_time = wait_time

    # uses the AT SP Command to set the choosen protocol
    # 0 = auto detection
    def set_protocol(self, prot_no):
        self.write('AT SP' + str(prot_no) + ' \r')
        answer = self.readline()
        if 'OK' in answer:
            return True, answer
        return False, answer

    def write(self, data):
        print('DATA -> ',data)
        byte_count = self.ser_con.write(data)
        time.sleep(self.sleep_time)
        return byte_count

    def readline(self):
        time.sleep(self.sleep_time)
        return self.ser_con.readline()


class ObdFunctions:
    def __init__(self, connection):
        self.con = connection

    # the method expects an answer like 01 00 \rSEARCHING...\rXX YY ZZ ... \r\r
    # the interesting part is between the last \r to \r\r
    def get_supported_pids_mode_1(self):
        info_pids = ['00', '20', '40', '80', 'A0', 'C0']
        supported_decoded = []
        i = 1
        for pid in info_pids:
            supported_encoded = self.__get_decoded_pids_mode_1(pid)
            supported_decoded += self.__decode_supported_pids_mode_1(supported_encoded, int(info_pids[i-1],16))
            print('DECODED -> ',supported_decoded)
            print('INFO_PIDS -> ',info_pids[i])
            if int(info_pids[i], 16) in supported_decoded:
                i += 1
                continue
            else:
                break
        return supported_decoded

    def __get_decoded_pids_mode_1(self, block_no):
        self.con.write('01 '+block_no+' \r')
        answer = self.con.readline()
        print('RAW ANSWER -> ',answer)
        end_index = answer.find('\r\r') - 1 # cut off the last space
        # 41_XX_ should be skipped cause it's the answer status
        start_index = answer.find('41 '+block_no) + 6
        print('SHORTENED ANSWER -> ',answer[start_index:end_index])
        supported_encoded = answer[start_index:end_index].split(' ')
        return supported_encoded

    @staticmethod
    def __decode_supported_pids_mode_1(supported_encoded, base_pid):
        i = base_pid + 1
        supported_decoded = []
        for elem in supported_encoded:
            print('ENCODED ELEM -> ',elem)
            bin_comp = 0b10000000
            for x in range(8):
                if (int(elem, 16) & bin_comp) == bin_comp:
                    supported_decoded.append(i)
                i += 1
                bin_comp -= (bin_comp / 2)
        supported_decoded = sorted(supported_decoded)
        return supported_decoded
