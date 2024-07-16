"""This module contains miscellaneous utilities for the dumper"""

from typing import Iterable, Tuple, TypeVar, final

from serial.tools.list_ports import comports

T = TypeVar('T')
def grouped_iterator(iterable: Iterable[T], n: int) -> Iterable[Tuple[T, ...]]:
    return zip(*[iter(iterable)]*n)


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