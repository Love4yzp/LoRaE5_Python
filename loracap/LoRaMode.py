import re
from loracap.ATProtocol import *
from loracap.utility import *
from loracap.macro import *
from typing import Optional
NO_RESPONSE = '_'

class LoRaMode(ATProtocol):

    def __init__(self):
        super(LoRaMode, self).__init__()
        self.event_responses = queue.Queue()
        self._awaiting_response_for = None

    def connection_made(self, transport):
        super(LoRaMode, self).connection_made(transport)
        self.transport.serial.reset_input_buffer()

    def fetch(self, command):
        """
        Directly command set without waiting for response.
        """
        return self.command(command, NO_RESPONSE)

    def command(self, command, response='OK', timeout=5) -> Optional[str]:
        """
        Set an AT command and wait for the response.
        """
        with self.lock:  # ensure that just one thread is sending commands at once
            self.write_line(command)
            while True:
                try:
                    line = self.responses.get(timeout=timeout)
                    logging.debug("%s -> %r", command, line)
                    if response == NO_RESPONSE or response in line:
                        return line
                except queue.Empty:
                    raise ATException('AT command timeout ({!r})'.format(command))
    
    def __transmitData(self, type:str, data:str) -> str:
        sub_command = ['TXLRPKT', 'TXLRSTR']
        if type not in sub_command:
            raise ValueError('type must be one of {}'.format(sub_command))
        command = f"AT+TEST={type}, \"{data}\"" 
        return self.fetch(command)
    
    def send_str(self, text:str):
        return self.__transmitData('TXLRSTR', text)
    
    def send_hex(self, text:str):
        return self.__transmitData('TXLRPKT', text)

    def isConnected(self):
        return 'OK' in self.command("AT", response='OK')

    def __str__(self):
        return f"DevEui: {self.DevEui}, DevAddr: {self.DevAddr}, AppEui: {self.AppEui}"

    @property
    def LogLevel(self):
        raise AttributeError("""
              You can only set the log level
              DEBUG/INFO/WARN/ERROR/FATAL/PANIC/QUIET
              LogLevel = QUIET
              LogLevel = quiet
              """)
    
    @LogLevel.setter
    def LogLevel(self, level:str):
        level = level.upper()
        level_list = [x.name for x in DebugLevel]
        print("LogLevel = ", level)
        if level in level_list:
            return self.fetch(f"AT+LOG={level}")
        raise ValueError("Invalid Debug Level")
    
    # Device Identification

    @property
    def DevAddr(self):
        """'+ID: DevAddr, 32:30:C9:A3"""
        response = self.fetch('AT+ID=DevAddr')
        return hex_value(response)

    @DevAddr.setter
    def DevAddr(self, value):
        formatted_value = validate_and_format_hex(value, 8)  # DevAddr should be 8 hexadecimal characters
        return self.fetch(f'AT+ID=DevAddr,\"{formatted_value}\"')

    @property
    def DevEui(self):
        response =  self.fetch('AT+ID=DevEui')
        return hex_value(response)

    @DevEui.setter
    def DevEui(self, value):
        formatted_value = validate_and_format_hex(value, 16)  # DevEui should be 16 hexadecimal characters
        return self.fetch(f'AT+ID=DevEui,\"{formatted_value}\"')
        
    @property
    def AppEui(self):
        response =  self.fetch('AT+ID=AppEui')
        return hex_value(response)
    
    @AppEui.setter
    def AppEui(self, value):
        formatted_value = validate_and_format_hex(value, 16)  # AppEui should be 16 hexadecimal characters
        return self.fetch(f'AT+ID=AppEui,\"{formatted_value}\"')

    # The keys used for communication
    @property
    def NwkSKey(self):
        logging.error("NwkSKey is write-only for security reasons.")
    
    @NwkSKey.setter
    def NwkSKey(self, value):
        formatted_value = validate_and_format_hex(value, 32)  # AppEui should be 16 hexadecimal characters
        return self.fetch(f'AT+KEY=NWKSKEY,\"{formatted_value}\"')

    @property
    def AppSKey(self):
        logging.error('AppSKey is write-only for security reasons.')

    @AppSKey.setter
    def AppSKey(self, value):
        formatted_value = validate_and_format_hex(value, 32)  # AppEui should be 16 hexadecimal characters
        return self.fetch(f'AT+KEY=AppSKey,\"{formatted_value}\"')

    @property
    def AppKey(self):
        logging.error('AppKey is write-only for security reasons.')
    
    @AppKey.setter
    def AppKey(self, value):
        formatted_value = validate_and_format_hex(value, 32)  # AppEui should be 16 hexadecimal characters
        return self.fetch(f'AT+KEY=AppKey,\"{formatted_value}\"')

    @property
    def mode(self) -> str:
        response = self.fetch('AT+MODE?')
        match = re.search(r"\+MODE: (\w+)", response)
        if match:
            return match.group(1)
        else:
            return ""

    @mode.setter
    def mode(self, value) -> str:
        if value not in LORA_MODE:
            raise ValueError('Invalid mode')
        return self.fetch(f'AT+MODE={value}')