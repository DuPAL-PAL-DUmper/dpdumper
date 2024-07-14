"""This module contains low level utility code to communicate with the board"""

from typing import final

import serial

from dupico_dumper.command_structures import CommandCode, CommandTokens

@final
class LLBoardUtilities:
    """
    This class contains basic utilities for board access.
    """

    _MAX_RESPONSE_SIZE: int = 32
    _ENCODING: str = 'ASCII'

    @classmethod
    def check_connection_string(cls, ser: serial.Serial, retries: int = 10) -> bool:
        response: str

        while retries > 0:
            response = ser.readline(cls._MAX_RESPONSE_SIZE).decode(cls._ENCODING).strip()
            if response and response == CommandTokens.BOARD_ENABLED.value:
                return True
            retries = retries - 1
    
        return False

    @classmethod
    def send_command(cls, ser: serial.Serial, cmd: CommandCode, params: list[str] = [], retries: int = 5) -> str | None:
        ser.write(cls.build_command(cmd, params))

        return cls.read_response_string(ser, retries)
    
    @classmethod
    def build_command(cls, cmd: CommandCode, params: list[str] = []) -> bytes:
        # If we have entries on the list, we'll use this trick to add a space at the beginning of the parameter list for command generation
        if params:
            params.insert(0, '')

        return f'{CommandTokens.CMD_START.value}{cmd.value}{' '.join(params)}{CommandTokens.CMD_END.value}'.encode(cls._ENCODING)
    
    @classmethod
    def read_response_string(cls, ser: serial.Serial, retries: int = 5) -> str | None:
        while retries > 0:
            response: str = ser.readline(cls._MAX_RESPONSE_SIZE).decode(cls._ENCODING).strip()

            if len(response) < 3 or response[0] != CommandTokens.RESP_START.value or response[-1] != CommandTokens.RESP_END.value:
                retries = retries - 1
            else:
                return response[1:-1]
        
        return None
