"""This file contains utility code to handle the IC definitions"""

from typing import final, Dict

@final
class ICUtilities:
    # The following map is used to associate a pin number (e.g. pin 1 or 10) on the socket
    # with the corresponding bit index used to access said pin by the dupico
    PIN_NUMBER_TO_INDEX_MAP: Dict[int, int] = {
        41: 0, 40: 1, 39: 2,
        38: 3, 37: 4, 36: 5,
        35: 6, 34: 7, 33: 8,
        32: 9, 31: 10, 30: 11,
        29: 12, 28: 13, 27: 14,
        26: 15, 25: 16, 24: 17,
        23: 18, 22: 19, 20: 20,
        19: 21, 18: 22, 17: 23,
        16: 24, 15: 25, 14: 26,
        13: 27, 12: 28, 11: 29,
        10: 30, 9: 31, 8: 32,
        7: 33, 6: 34, 5: 35,
        4: 36, 3: 37, 2: 38,
        1: 39
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
