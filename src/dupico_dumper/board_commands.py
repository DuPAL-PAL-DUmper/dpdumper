"""This module contains higher-level code for board interfacing"""

from typing import final

import serial

from dupico_dumper.dumper_utilities import DumperUtilities
from dupico_dumper.command_structures import CommandCode

@final
class BoardCommands:
    @staticmethod
    def get_model(ser: serial.Serial) -> int | None:
        res: str | None = DumperUtilities.send_command(ser, CommandCode.MODEL)

        if res and len(res) >= 3 and res[0] == CommandCode.MODEL.value:
            return int(res[2:])
        else:
            return None
        
    @staticmethod
    def test_board(ser: serial.Serial) -> bool | None:
        res: str | None = DumperUtilities.send_command(ser, CommandCode.TEST)

        if res and len(res) == 3 and res[0] == CommandCode.TEST.value:
            return int(res[2:]) == 1
        else:
            return None