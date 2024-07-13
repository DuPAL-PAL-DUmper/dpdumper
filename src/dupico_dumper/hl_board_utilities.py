"""This module contains high level utility code to perform operations on the board"""

from typing import final, TypeAlias

import serial
from dupico_dumper.ic.ic_definition import ICDefinition

TriStateList: TypeAlias = list[bool | None]

@final
class HLBoardUtilities:
    """
    This class contains high level utilities to perform operations on the board
    """

    @classmethod
    def check_connection_string(cls, ser: serial.Serial, ic: ICDefinition) -> TriStateList:
        return [True, None]