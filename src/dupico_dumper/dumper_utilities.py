"""This module contains miscellaneous utilities for the dumper"""

from typing import final

import serial
from serial.tools.list_ports import comports

from dupico_dumper.command_structures import CommandCode, CommandTokens

@final
class DumperUtilities:
    """
    This class contains higher level utilities for the dumper.
    """
    MAX_RESPONSE_SIZE: int = 32
    ENCODING: str = 'ASCII'

    @classmethod
    def send_command(cls, ser: serial.Serial,  cmd: CommandCode, params: list[str]) -> str | None:
        # If we have entries on the list, we'll use this trick to add a space at the beginning of the parameter list for command generation
        if params:
            params.insert(0, '')

        ser.write(bytearray(f'{CommandTokens.CMD_START.value}{cmd.value}{' '.join(params)}{CommandTokens.CMD_END.value}', cls.ENCODING))

        response: str = str(ser.readline(size=cls.MAX_RESPONSE_SIZE)).strip()

        if len(response) < 3 or response[0] != CommandTokens.RESP_START.value or response[-1] != CommandTokens.RESP_END.value:
            return None
        else:
            return response[1:-1]

    @staticmethod
    def print_serial_ports() -> None:
        """Print a list of available serial ports."""

        port_list = comports()

        if not port_list:
            print('No serial ports are available!')
        else:
            print('Available serial ports:')
            for port in port_list:
                print(f'\t{port.device} - {port.description}')        