#!/usr/bin/python

import serial
import time
import obd2pids


class ObdConnection:
    """
    This class does all the connection stuff
    @author Susperius
    @contact susperius@gmail.com
    """
    sleep_time = 0
    protocols = {0: 'Automatic', 1: 'SAE J1850 PWM', 2: 'SAE J1850 VPW', 3: 'ISO 9141-2', 4: 'ISO 14230-4 KWP',
                 5: 'ISO 14230-4 KWP (fast init)', 6: 'ISO 15765-4 CAN (11 bit ID, 500 kbaud',
                 7: 'ISO 15765-4 CAN (29 bit ID, 500 kbaud', 8: 'ISO 15765-4 CAN (11 bit ID, 250 kbaud)',
                 9: 'ISO 15765-4 CAN (29 bit ID, 250 kbaud', 10: 'SAE J1939 CAN (29 bit ID, 250 kbaud)',
                 11: 'User defined CAN', 12: 'User defined CAN'}

    def __init__(self, port, bauds=38400, timeout=1, prot_no=0, wait_time=0.5):
        """
        @param port Only tested on Linux system, it's expected as string and should look like "/dev/ttyUSBx"
        @rtype : ObdConnection
        """
        self.ser_con = serial.Serial(port, bauds, timeout=timeout)
        self.set_protocol(prot_no)
        self.sleep_time = wait_time

    # uses the AT SP Command to set the choosen protocol
    # 0 = auto detection
    def set_protocol(self, prot_no):
        self.write('AT D \r')
        self.write('AT SP' + str(prot_no) + ' \r')
        answer = self.readline()
        if 'OK' in answer:
            return True, answer
        return False, answer

    def show_header(self, show):
        if show:
            sh = '1'
        else:
            sh = '0'
        return self.communicate('AT H'+sh)

    def set_header(self, header):
        return self.communicate('AT SH '+header)

    def write(self, data):
        byte_count = self.ser_con.write(data)
        time.sleep(self.sleep_time)
        return byte_count

    def readline(self):
        time.sleep(self.sleep_time)
        return self.ser_con.readline()

    def communicate(self, data):
        self.write(data)
        return self.readline()
    
    def sniff(self):
        sav_time = self.sleep_time
        self.sleep_time = 0
        self.communicate('AT H1 \r')
        self.communicate('AT CAF0 \r')
        self.communicate('AT MA \r')
        try:
            while True:
                print('',self.readline())
        except KeyboardInterrupt:
            print('Stop Sniffing -> CTRL+C received')
            self.communicate('AT D \r')
            self.sleep_time = sav_time


class ObdFunctions:
    """
    This class helps you to read different values from the ECU via a ObdConnection object
    @author Susperius
    @contact susperius@gmail.com
    """
    def __init__(self, connection):
        self.con = connection

    def __get_encoded_value(self, mode_nr, pid):
        answer = self.con.communicate(mode_nr + ' ' + pid + ' \r\r')
        return self.__get_relevant_message_parts(answer, hex(0x40 + int(mode_nr, 16))[2:4]+' '+pid, '\r\r')

    @staticmethod
    def __get_relevant_message_parts(message, start_string, end_string):
        start_index = message.find(start_string) + len(start_string) + 1 # Skipping the start_string and the space char
        end_index = message.find(end_string) - 1  # cut off last space
        ret_message = message[start_index:end_index].split(' ')
        return ret_message

    # the method expects an answer like 01 00 \rSEARCHING...\rXX YY ZZ ... \r\r
    # the interesting part is between the last \r to \r\r
    def get_supported_pids(self, mode_nr):
        info_pids = ['00', '20', '40', '80', 'A0', 'C0']
        supported_decoded = []
        supported_pids = []
        i = 1
        for pid in info_pids:
            supported_encoded = self.__get_encoded_value('01', pid)
            supported_decoded += self.__decode_supported_pids(supported_encoded, int(info_pids[i - 1], 16))
            if int(info_pids[i], 16) in supported_decoded:
                i += 1
                continue
            else:
                break
        for pid in supported_decoded:
            supported_pids.append((hex(pid), obd2pids.pids[pid][3]))
        return supported_pids

    @staticmethod
    def __decode_supported_pids(supported_encoded, base_pid):
        i = base_pid + 1
        supported_decoded = []
        for elem in supported_encoded:
            bin_comp = 0b10000000
            for x in range(8):
                if (int(elem, 16) & bin_comp) == bin_comp:
                    supported_decoded.append(i)
                i += 1
                bin_comp -= (bin_comp / 2)
        supported_decoded = sorted(supported_decoded)
        return supported_decoded

    def get_monitor_status_since_dtc_clear(self, mode_nr):
        mon_stat_decoded = {'MIL-Indication': 0, 'DTCs-available': 0, 'Ignition-Monitor-Support': 0,
                            'Standard-Tests': {'Misfire': (0, 0), 'Fuel-System': (0, 0), 'Components': (0, 0)},
                            'Spark-Ignition-Tests': {'Catalyst': (0, 0), 'Heated-Catalyst': (0, 0),
                                                     'Evaporative-Systems': (0, 0), 'Secondary-Air-System': (0, 0),
                                                     'A/C-Refrigerant': (0, 0), 'Oxygen-Sensor': (0, 0),
                                                     'Oxygen-Sensor-Heater': (0, 0), 'EGR-Sytem': (0, 0)},
                            'Compression-Ignition-Tests': {'NMHC-Cat': (0, 0), 'N0x/Scr-Monitor': (0, 0),
                                                           'Boost-Pressure': (0, 0), 'Exhaust-Gas-Sensor': (0, 0),
                                                           'PM-Filter-Monitoring': (0, 0), 'EGR/VVT-System': (0, 0)}}
        mon_stat_encoded = self.__get_encoded_value(mode_nr, '01')
        mon_stat_decoded['MIL-Indication'] = int(mon_stat_encoded[0], 16) >> 7
        mon_stat_decoded['DTCs-available'] = int(mon_stat_encoded[0], 16) & 0b01111111
        mon_stat_decoded['Ignition-Monitor-Support'] = (int(mon_stat_encoded[1], 16) & 0b00001000) >> 3
        i = 0
        for test in mon_stat_decoded['Standard-Tests']:
            mon_stat_decoded['Standard-Tests'][test] = (
                (int(mon_stat_encoded[1], 16) >> i) & 0b00000001,
                (int(mon_stat_encoded[1], 16) >> (i + 4)) & 0b00000001)
            i += 1
        i = 0
        if mon_stat_decoded['Ignition-Monitor-Support'] == 0:
            support = 'Ignition-Monitor-Support'
        else:
            support = 'Compression-Monitor-Support'
        for test in mon_stat_decoded[support]:
            mon_stat_decoded[support][test] = (
                (int(mon_stat_encoded[2], 16) >> i) & 0b00000001, (int(mon_stat_encoded[2], 16) >> i) & 0b00000001)
            i += 1
        return mon_stat_decoded

    def get_fuel_system_status(self, mode_nr):
        fuel_system_status = {0b00000000: 'No fuel system available',
                              0b00000001: 'Open loop due to insufficient engine temperature',
                              0b00000010: 'Closed loop, using oxygen sensor feedback to determine fuel mix',
                              0b00000100: 'Open loop due to engine load OR fuel cut to deceleration',
                              0b00001000: 'Open loop due to system failure',
                              0b00010000: 'Closed loop, using at least one oxygen sensor '
                                          'but there is a fault in the feedback system'}
        status_encoded = self.__get_encoded_value(mode_nr, '03')
        status_decoded = ( fuel_system_status[int(status_encoded, 16)], fuel_system_status[int(status_encoded, 16)] )
        return status_decoded

    def get_calculated_engine_load_value(self, mode_nr):
        value_encoded = self.__get_encoded_value(mode_nr, '04')
        value_decoded = int(value_encoded[0], 16) * 100 / 255
        return value_decoded

    def get_engine_coolant_temperature(self, mode_nr):
        value_encoded = self.__get_encoded_value(mode_nr, '05')
        value_decoded = int(value_encoded[0], 16) - 40
        return value_decoded

    #Term -> 0 = Short 1 = Long
    def get_fuel_trim(self, mode_nr, term, bank_nr):
        if term == 0:
            if bank_nr == 1:
                pid = '06'
            else:
                pid = '08'
        else:
            if bank_nr == 1:
                pid = '07'
            else:
                pid = '09'
        value_encoded = self.__get_encoded_value(mode_nr, pid)
        value_decoded = (int(value_encoded[0], 16) - 128) * (100 / 128)
        return value_decoded

    def get_fuel_pressure(self, mode_nr):
        value_encoded = self.__get_encoded_value(mode_nr, '0A')
        value_decoded = int(value_encoded[0], 16) * 3
        return value_decoded

    def get_intake_manifold_absolute_pressure(self, mode_nr):
        value_encoded = self.__get_encoded_value(mode_nr, '0B')
        value_decoded = int(value_encoded[0], 16)
        return value_decoded

    def get_engine_rpm(self, mode_nr):
        value_encoded = self.__get_encoded_value(mode_nr, '0C')
        value_decoded = ((int(value_encoded[0], 16) * 256) + int(value_encoded[1], 16)) / 4
        return value_decoded

    def get_vehicle_speed(self, mode_nr):
        value_encoded = self.__get_encoded_value(mode_nr, '0D')
        value_decoded = int(value_encoded[0], 16)
        return value_decoded

    def get_timing_advance(self, mode_nr):
        value_encoded = self.__get_encoded_value(mode_nr, '0E')
        value_decoded = (int(value_encoded[0], 16) / 2) - 64
        return value_decoded

    def get_intake_air_temperature(self, mode_nr):
        value_encoded = self.__get_encoded_value(mode_nr, '0F')
        value_decoded = int(value_encoded[0], 16) - 40
        return value_decoded

    def get_maf_air_flow_rate(self, mode_nr):
        value_encoded = self.__get_encoded_value(mode_nr, '10')
        value_decoded = ((int(value_encoded[0], 16) * 256) + int(value_encoded[1], 16)) / 100
        return value_decoded

    def get_throttle_position(self, mode_nr):
        value_encoded = self.__get_encoded_value(mode_nr, '11')
        value_decoded = int(value_encoded[0], 16) * 100 / 255
        return value_decoded

    def get_commanded_secondary_air_status(self, mode_nr):
        secondary_air_status = {0b00000000: 'Upstream of catalytic converter',
                                0b00000010: 'Downstream of catalytic converter',
                                0b00000100: 'From the outside atmosphere or off'}
        value_encoded = self.__get_encoded_value(mode_nr, '12')
        return secondary_air_status[int(value_encoded[0], 16)]

    def get_available_oxygen_sensors(self, mode_nr):
        value_encoded = self.__get_encoded_value(mode_nr, '13')
        check_val = 0b00000001
        i = 1
        sensors = []
        for x in range(8):
            if int(value_encoded[0], 16) & check_val == check_val:
                sensors.append(i)
            i += 1
            check_val *= 2
        return sensors

    def get_dtc(self):
        dtc_decoded = []
        dtc_encoded = self.__get_encoded_value('03', '')
        dtc_count = int(dtc_encoded[0], 16)
        dtc_encoded.pop(0)
        i = 0
        for x in range(dtc_count):
            dtc = [dtc_encoded[i], dtc_encoded[i + 1]]
            dtc_decoded.append(self.__translate_dtc(dtc))
        return dtc_decoded

    @staticmethod
    def __translate_dtc(dtc_encoded):
        dtc_decoded = ''
        dtc_first_char = {0b00: 'P', 0b01: 'C', 0b10: 'B', 0b11: 'U'}
        dtc_second_char = {0b00: '0', 0b01: '1', 0b10: '2', 0b11: '3'}
        dtc_last_chars = {0b0000: '0', 0b0001: '1', 0b0010: '2', 0b0011: '3', 0b0100: '4', 0b0101: '5',
                          0b0110: '6', 0b0111: '7', 0b1000: '8', 0b1001: '9', 0b1010: 'A', 0b1011: 'B',
                          0b1100: 'C', 0b1101: 'D', 0b1110: 'E', 0b1111: 'F'}
        dtc_first = int(dtc_encoded[0], 16) >> 6
        dtc_decoded += dtc_first_char[dtc_first]
        dtc_second = (int(dtc_encoded[0], 16) >> 4) & 0b0011
        dtc_decoded += dtc_second_char[dtc_second]
        dtc_third = int(dtc_encoded[0], 16) & 0b00001111
        dtc_decoded += dtc_last_chars[dtc_third]
        dtc_fourth = int(dtc_encoded[1], 16) >> 4
        dtc_decoded += dtc_last_chars[dtc_fourth]
        dtc_fifth = int(dtc_encoded[1], 16) & 0b00001111
        dtc_decoded += dtc_last_chars[dtc_fifth]
        return dtc_decoded

    def clear_dtc_and_mil(self):
        answer = self.communicate('04 \r')
