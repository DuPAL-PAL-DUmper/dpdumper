"""This module contains higher-level code for board interfacing"""

from typing import final

import serial

from dupico_dumper.ll_board_utilities import LLBoardUtilities
from dupico_dumper.command_structures import CommandCode

@final
class BoardCommands:
    @staticmethod
    def get_model(ser: serial.Serial) -> int | None:
        """Read the model of the connected board

        Args:
            ser (serial.Serial): serial port on which to send the command

        Returns:
            int | None: Return the model number, or None if the response cannot be read correctly
        """        
        res: str | None = LLBoardUtilities.send_command(ser, CommandCode.MODEL)

        if res and len(res) >= 3 and res[0] == CommandCode.MODEL.value:
            return int(res[2:])
        else:
            return None
        
    @staticmethod
    def test_board(ser: serial.Serial) -> bool | None:
        """Perform a minimal self-test of the board

        Args:
            ser (serial.Serial): serial port on which to send the command

        Returns:
            bool | None: True if test passed correctly, False otherwise
        """        
        res: str | None = LLBoardUtilities.send_command(ser, CommandCode.TEST)

        if res and len(res) == 3 and res[0] == CommandCode.TEST.value:
            return int(res[2:]) == 1
        else:
            return None
        
    @staticmethod
    def set_power(ser: serial.Serial, state: bool) -> bool | None:
        """Enable or disable the power on the socket VCC

        Args:
            ser (serial.Serial): serial port on which to send the command
            state (bool): True if we wish power applied, False otherwise

        Returns:
            bool | None: True if power was applied, False otherwise, None in case we did not read the response correctly
        """        
        res: str | None = LLBoardUtilities.send_command(ser, CommandCode.POWER, ['1' if state else '0'])

        if res and len(res) == 3 and res[0] == CommandCode.POWER.value:
            return int(res[2:]) == 1
        else:
            return None
        
    @staticmethod
    def write_pins(ser: serial.Serial, pins: int) -> int | None:
        """Toggle the specified pins and read their status back

        Args:
            ser (serial.Serial): serial port on which to send the command
            pins (int): value that the pins will be set to. A bit set to '1' means that the pin will be pulled high

        Returns:
            int | None: The value we read back from the pins, or None in case of parsing issues
        """        
        # Format the parameter as a 16 chars hex string
        res: str | None = LLBoardUtilities.send_command(ser, CommandCode.WRITE, [f'{pins:0{16}X}'])

        if res and len(res) == 18 and res[0] == CommandCode.WRITE.value:
            return int(res[2:], 16)
        else:
            return None
        
    @staticmethod
    def read_pins(ser: serial.Serial) -> int | None:
        """Read the value of the pins

        Args:
            ser (serial.Serial): serial port on which to send the command

        Returns:
            int | None: The value we read back from the pins, or None in case of parsing issues
        """        
        res: str | None = LLBoardUtilities.send_command(ser, CommandCode.READ)

        if res and len(res) == 18 and res[0] == CommandCode.READ.value:
            return int(res[2:], 16)
        else:
            return None