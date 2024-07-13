"""This module contains low level utility code to communicate with the board"""

from typing import final

import serial

from dupico_dumper.command_structures import CommandCode, CommandTokens

@final
class LLBoardUtilities:
    """
    This class contains basic utilities for board access.
    """

    MAX_RESPONSE_SIZE: int = 32
    ENCODING: str = 'ASCII'

    @classmethod
    def check_connection_string(cls, ser: serial.Serial) -> bool:
        retries: int = 10
        response: str

        while retries > 0:
            response = ser.readline(cls.MAX_RESPONSE_SIZE).decode(cls.ENCODING).strip()
            if response and response == CommandTokens.BOARD_ENABLED.value:
                return True
            retries = retries - 1
    
        return False

    @classmethod
    def send_command(cls, ser: serial.Serial,  cmd: CommandCode, params: list[str] = []) -> str | None:
        # If we have entries on the list, we'll use this trick to add a space at the beginning of the parameter list for command generation
        if params:
            params.insert(0, '')

        ser.write((f'{CommandTokens.CMD_START.value}{cmd.value}{' '.join(params)}{CommandTokens.CMD_END.value}').encode(cls.ENCODING))

        response: str = ser.readline(cls.MAX_RESPONSE_SIZE).decode(cls.ENCODING).strip()

        if len(response) < 3 or response[0] != CommandTokens.RESP_START.value or response[-1] != CommandTokens.RESP_END.value:
            return None
        else:
            return response[1:-1]    @classmethod