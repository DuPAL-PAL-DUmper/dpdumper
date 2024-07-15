"""This module contains miscellaneous utilities for the dumper"""

from typing import final

from serial.tools.list_ports import comports

@final
class DumperUtilities:
    """
    This class contains basic utilities for the dumper.
    """

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