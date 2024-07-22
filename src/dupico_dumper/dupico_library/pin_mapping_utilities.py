"""This file contains utility code to handle pin to command mapping"""

from typing import final, Dict

@final
class PinMappingUtilities:
    # The following map is used to associate a pin number (e.g. pin 1 or 10) on the socket
    # with the corresponding bit index used to access said pin by the dupico
    PIN_NUMBER_TO_INDEX_MAP: Dict[int, int] = {
        1: 0, 2: 1, 3: 2,
        4: 3, 5: 4, 6: 5,
        7: 6, 8: 7, 9: 8,
        10: 9, 11: 10, 12: 11,
        13: 12, 14: 13, 15: 14,
        16: 15, 17: 16, 18: 17,
        19: 18, 20: 19, 22: 20,
        23: 21, 24: 22, 25: 23,
        26: 24, 27: 25, 28: 26,
        29: 27, 30: 28, 31: 29,
        32: 30, 33: 31, 34: 32,
        35: 33, 36: 34, 37: 35,
        38: 36, 39: 37, 40: 38,
        41: 39
    }

    @classmethod
    def map_value_to_pins(cls, pins: list[int], value: int) -> int:
        """This method takes a number to set on selected pins and uses a list of said pins to
        convert into it into a value that can address those pins

        Args:
            pins (list[int]): A list of the pins associated to every bit of the input value (1-index based)
            value (int): The value to map to the pins

        Returns:
            int: A value that can be used by the dupico to address and change the selected pins
        """

        ret_val: int = 0

        for idx, pin in enumerate(pins):
            if value & (1 << idx):
                ret_val = ret_val | (1 << cls.PIN_NUMBER_TO_INDEX_MAP[pin])

        return ret_val
    
    @classmethod
    def map_pins_to_value(cls, pins: list[int], value: int) -> int:
        """This method performs the reverse operation of map_value_to pins: it converts
        a value read from the dupico representing the "addresses" of the pins into a value that
        actually represent the number that those pins compose

        Args:
            pins (list[int]): The list of pins associated to the value
            value (int): the value representing the pin state

        Returns:
            int: the actual number that those pins are forming
        """        

        ret_val: int = 0

        for idx, pin in enumerate(pins):
            if value & (1 << cls.PIN_NUMBER_TO_INDEX_MAP[pin]):
                ret_val = ret_val | (1 << idx)

        return ret_val
