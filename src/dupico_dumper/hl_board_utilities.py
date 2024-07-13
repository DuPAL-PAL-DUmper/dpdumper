"""This module contains high level utility code to perform operations on the board"""

from typing import final, NamedTuple

import serial
from dupico_dumper.ic.ic_definition import ICDefinition

@final
class DataElement(NamedTuple):
    data: int
    z_mask: int = 0

@final
class HLBoardUtilities:
    """
    This class contains high level utilities to perform operations on the board
    """

    @staticmethod
    def read_ic(ser: serial.Serial, ic: ICDefinition) -> list[DataElement]:
        return []
    
    @staticmethod
    def write_ic(ser: serial.Serial, ic: ICDefinition, data: list[int]) -> bool:
        return False