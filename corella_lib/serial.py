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
        """
        :param port: Serial port
        :type port: str

        :param baudrate: Baud rate
        :type baudrate: int

        :param timeout: Read timeout value
        :type timeout: float

        :param verbose: Log verbose mode
        :type verbose: bool

        :param handle_throttling: Enables automatic throttling
        :type handle_throttling: bool
        """
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
        """
        Returns given command as an encoded line command

        :param command: Corella command
        :type command: str

        :returns: Given command as an encoded line command
        :rtype: bytes
        """
        return '{}\r\n'.format(command).encode()

    @property
    def connected(self):
        """
        Returns `True` if the device is connected, `False` otherwise

        :returns: `True` if the device is connected, `False` otherwise
        :rtype: bool
        """
        return self._serial.is_open

    @property
    def id(self):
        """
        Returns Corella's unique device ID which will be used to match the data
        from the Corella module to the Taggle Network

        :returns: Device ID
        :rtype: str
        """
        response = self.request_id()
        return response.pop()

    @property
    def diagnostics(self):
        """
        Returns the device's internal diagnostics which includes temperature of
        the device in degrees Celsius and the supply voltage in Volts

        :returns: Diagnostics information
        :rtype: dict
        """
        response = self.request_diagnostics()
        return self._parse_diagnostics(response)

    @property
    def max_temp(self):
        """
        Returns the device's internal maximum temperature as a 16-bit integer

        :returns: Device's maximum temperature
        :rtype: float
        """
        max_temp = self.diagnostics[self.FIELD_DIAGNOSTICS_MAX_TEMP]
        return float(max_temp)

    @property
    def min_temp(self):
        """
        Returns the device's internal minimum temperature as a 16-bit integer

        :returns: Device's minimum temperature
        :rtype: float
        """
        min_temp = self.diagnostics[self.FIELD_DIAGNOSTICS_MIN_TEMP]
        return float(min_temp)

    @property
    def version(self):
        """
        Returns device's hardware and firmware version

        :returns: Device's hardware and firmware version
        :rtype: dict
        """
        response = self.request_version()
        return self._parse_version(response)

    @property
    def firmware_version(self):
        """
        Returns device's firmware version

        :returns: Device's firmware version
        :rtype: str
        """
        return self.version[self.FIELD_VERSION_FIRMWARE]

    @property
    def hardware_version(self):
        """
        Returns the device's hardware version

        :returns: Device's hardware version
        :rtype: str
        """
        return self.version[self.FIELD_VERSION_HARDWARE]

    @property
    def battery(self):
        """
        Returns the device's current source voltage

        :returns: Device's current source voltage
        :rtype: float
        """
        battery = self.diagnostics[self.FIELD_DIAGNOSTICS_BATTERY]
        match = self.BATTERY_REGEX.match(battery)
        return float(match.groupdict()['battery'])

    def connect(self):
        """
        Connects to the device

        :returns: `True` if the device is connected, `False` otherwise
        :rtype: bool
        """
        if self.connected:
            self._log(logger.warning, 'Already connected!')
        else:
            self._serial.open()
            self._log(logger.info, 'Connected!')

        return self.connected

    def request(self, command, throttle=False):
        """
        Requests the given command and returns its response as a list of strings

        :param command: Corella command
        :type command: str

        :param throttle: Enables throttling
        :type throttle: bool

        :returns: Response of the given command
        :rtype: list
        """
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
        """
        Requests `AT` command and returns its response as a list of strings

        :returns: Response of the `AT` command
        :rtype: list
        """
        return self.request(self.COMMAND_AT)

    def request_diagnostics(self):
        """
        Requests `AT+DIAGNOSTICS?` command and returns its response as a list of
        strings

        :returns: Response of the `AT+DIAGNOSTICS?` command
        :rtype: list
        """
        return self.request(self.COMMAND_AT_DIAGNOSTICS)

    def request_id(self):
        """
        Requests `AT+ID?` command and returns its response as a list of strings

        :returns: Response of the `AT+ID?` command
        :rtype: list
        """
        return self.request(self.COMMAND_AT_ID)

    def request_status(self):
        """
        Requests `AT+STATUS?` command and returns its response as a list of
        strings

        :returns: Response of the `AT+STATUS?` command
        :rtype: list
        """
        return self.request(self.COMMAND_AT_STATUS)

    def request_version(self):
        """
        Requests `AT+VERSION?` command and returns its response as a list of
        strings

        :returns: Response of the `AT+VERSION?` command
        :rtype: list
        """
        return self.request(self.COMMAND_AT_VERSION)

    def send(self, packet_id, data):
        """
        Sends the user's data payload

        :param packet_id: Packet ID (must be in range of 1-9)
        :type packet_id: int

        :param data: Data payload
        :type data: str

        :returns: `OK` if it's successful, `ERROR` otherwise
        """
        packed_data = self._pack_data(data)
        command = self.COMMAND_AT_SEND.format(
            packet_id=packet_id, data=packed_data
        )
        response = self.request(command, throttle=True)
        return response.pop()

    def turn_on_leds(self):
        """
        Turns on device's LEDs

        :returns: `LEDS ON`
        :rtype: str
        """
        response = self.request(
            self.COMMAND_AT_LEDS.format(state=self.STATE_LEDS_ON)
        )
        return response.pop()

    def turn_off_leds(self):
        """
        Turns off device's LEDs

        :returns: `LEDS OFF`
        :rtype: str
        """
        response = self.request(
            self.COMMAND_AT_LEDS.format(state=self.STATE_LEDS_OFF)
        )
        return response.pop()
