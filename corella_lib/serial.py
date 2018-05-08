import logging
import re
import time

import serial


# Initialise logger
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class Corella(object):
    BATTERY_REGEX = re.compile(r'^(?P<battery>\d+\.\d+)')

    COMMAND_AT = 'AT'
    COMMAND_AT_DIAGNOSTICS = 'AT+DIAGNOSTICS?'
    COMMAND_AT_ID = 'AT+ID?'
    COMMAND_AT_LEDS = 'AT+LEDS={state}'
    COMMAND_AT_SEND = 'AT+SEND={packet_id},{data}'
    COMMAND_AT_STATUS = 'AT+STATUS?'
    COMMAND_AT_VERSION = 'AT+VERSION?'

    DATA_SIZE = 12

    DEFAULT_BAUDRATE = 9600
    DEFAULT_TIMEOUT = 1

    FIELD_DIAGNOSTICS_BATTERY = 'BATTERY'
    FIELD_DIAGNOSTICS_MAX_TEMP = 'MAX TEMP'
    FIELD_DIAGNOSTICS_MIN_TEMP = 'MIN TEMP'

    FIELD_VERSION_FIRMWARE = 'F.W'
    FIELD_VERSION_HARDWARE = 'H.W'

    RESPONSE_ERROR = 'ERROR'
    RESPONSE_OK = 'OK'

    STATE_LEDS_OFF = 'OFF'
    STATE_LEDS_ON = 'ON'

    def __init__(self,
                 port,
                 baudrate=None,
                 timeout=None,
                 verbose=True,
                 handle_throttling=True):
        self._serial = self._init_serial(port, baudrate, timeout)
        self.verbose = verbose
        self.handle_throttling = handle_throttling

    def _init_serial(self, port, baudrate, timeout):
        return serial.Serial(
            port=port,
            baudrate=baudrate or self.DEFAULT_BAUDRATE,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=timeout or self.DEFAULT_TIMEOUT,
            xonxoff=False,
            rtscts=False,
            write_timeout=None,
            dsrdtr=False,
            inter_byte_timeout=None,
        )

    def _readlines(self):
        lines = []

        waiting = True
        while waiting:
            line_bytes = self._serial.readline()
            line = line_bytes.decode().strip()
            if line:
                lines.append(line)
            else:
                waiting = False

        return lines

    @staticmethod
    def _parse_diagnostics(diagnostics):
        response = {}

        for diagnostic in diagnostics:
            key, value = diagnostic.split('=', 1)
            response[key] = value

        return response

    @staticmethod
    def _parse_version(version):
        response = {}

        for line in version[1:]:
            key, value = line.split('=', 1)
            response[key] = value

        return response

    def _wait_throttle(self):
        self._log(logger.info, 'Checking throttling...')
        response = self.request_status()

        if not response:
            self._log(logger.info, 'No throttling required')
            return

        line = response.pop()

        # Handle OK response
        if line == self.RESPONSE_OK:
            self._log(logger.info, 'No throttling required')
            return

        # Handle WAIT response (WAIT X SEC)
        __, seconds, __ = line.split()
        seconds = int(seconds)
        self._log(
            logger.info, 'Waiting {} seconds for throttling...'.format(seconds)
        )
        time.sleep(seconds + 1)

    def _pack_data(self, data):
        data_format = '{{:{0}.{0}}}'.format(self.DATA_SIZE)
        packed_data = data_format.format(data)
        data_length = len(data)
        packed_data_length = len(packed_data)
        if packed_data != data:
            if packed_data_length > data_length:
                warning_message = 'Original message padded to 12 bytes!'
            elif packed_data_length < data_length:
                warning_message = 'Original message truncated to 12 bytes!'
            else:
                warning_message = 'Original message forced to 12 bytes!'

            self._log(logger.warning, warning_message)

        return packed_data

    def _log(self, method, message):
        if self.verbose:
            method(message)

    @staticmethod
    def encode_command(command):
        return '{}\r\n'.format(command).encode()

    @property
    def connected(self):
        return self._serial.is_open

    @property
    def id(self):
        response = self.request_id()
        return response.pop()

    @property
    def diagnostics(self):
        response = self.request_diagnostics()
        return self._parse_diagnostics(response)

    @property
    def max_temp(self):
        max_temp = self.diagnostics[self.FIELD_DIAGNOSTICS_MAX_TEMP]
        return float(max_temp)

    @property
    def min_temp(self):
        min_temp = self.diagnostics[self.FIELD_DIAGNOSTICS_MIN_TEMP]
        return float(min_temp)

    @property
    def version(self):
        response = self.request_version()
        return self._parse_version(response)

    @property
    def firmware_version(self):
        return self.version[self.FIELD_VERSION_FIRMWARE]

    @property
    def hardware_version(self):
        return self.version[self.FIELD_VERSION_HARDWARE]

    @property
    def battery(self):
        battery = self.diagnostics[self.FIELD_DIAGNOSTICS_BATTERY]
        match = self.BATTERY_REGEX.match(battery)
        return float(match.groupdict()['battery'])

    def connect(self):
        if self.connected:
            self._log(logger.warning, 'Already connected!')
        else:
            self._serial.open()
            self._log(logger.info, 'Connected!')

        return self.connected

    def request(self, command, throttle=False):
        if not self.connected:
            self.connect()

        if throttle and self.handle_throttling:
            self._wait_throttle()

        encoded_command = self.encode_command(command)
        self._log(logger.info, 'Requesting: {}'.format(encoded_command))
        self._serial.write(encoded_command)
        response = self._readlines()
        self._log(logger.info, 'Response received: {}'.format(response))
        return response

    def request_attention(self):
        return self.request(self.COMMAND_AT)

    def request_diagnostics(self):
        return self.request(self.COMMAND_AT_DIAGNOSTICS)

    def request_id(self):
        return self.request(self.COMMAND_AT_ID)

    def request_status(self):
        return self.request(self.COMMAND_AT_STATUS)

    def request_version(self):
        return self.request(self.COMMAND_AT_VERSION)

    def send(self, packet_id, data):
        packed_data = self._pack_data(data)
        command = self.COMMAND_AT_SEND.format(
            packet_id=packet_id, data=packed_data
        )
        response = self.request(command, throttle=True)
        return response.pop()

    def turn_on_leds(self):
        response = self.request(
            self.COMMAND_AT_LEDS.format(state=self.STATE_LEDS_ON)
        )
        return response.pop()

    def turn_off_leds(self):
        response = self.request(
            self.COMMAND_AT_LEDS.format(state=self.STATE_LEDS_OFF)
        )
        return response.pop()
