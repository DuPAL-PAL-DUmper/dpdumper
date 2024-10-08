"""This file contains code to generate output files from data reads"""

import math
import hashlib

from typing import Generator, Literal

from dpdumperlib.ic.ic_definition import ICDefinition

from dpdumper.hl_board_utilities import DataElement
from dpdumper.dumper_utilities import grouped_iterator

# See https://stackoverflow.com/questions/8898807/pythonic-way-to-iterate-over-bits-of-integer
# and https://lemire.me/blog/2018/02/21/iterating-over-set-bits-quickly/
def _bits_iterator(n: int) -> Generator[int, None, None]:
    while n:
        b: int = n & (~n + 1)
        yield b
        n ^= b

def build_binary_array(ic: ICDefinition, elements: list[DataElement], hiz_high: bool = False, reverse_byte_order: bool = False) -> tuple[bytearray, bytearray, str]:
    """Builds a binary array out of data read from the IC, and returns it plus the SHA1SUM of the data

    Args:
        ic (ICDefinition): Definition of the IC that was read
        elements (list[DataElement]): Array of the reads, in addressing order, containing both data and Hi-Z info
        hiz_high (bool, optional): True if the Hi-Z pins will be represented as 1 in the binary out. Defaults to False.

    Returns:
        tuple[bytearray, bytearray, str]: Tuple containing the byte array for the data, for they hi-z and the sha1 sum for data
    """
    data_width: int = len(ic.data)
    # Use upside-down floor division: https://stackoverflow.com/questions/14822184/is-there-a-ceiling-equivalent-of-operator-in-python
    bytes_per_entry = -(data_width // -8)
    data_arr: bytearray = bytearray()
    hiz_arr: bytearray = bytearray()
    endianness: Literal['big', 'little'] = 'little' if reverse_byte_order else 'big'

    for el in elements:
        data: int = el.data | (el.z_mask if hiz_high else 0)
        data_b: bytes = data.to_bytes(bytes_per_entry, endianness)
        data_arr += bytearray(data_b)

        data_z: bytes = el.z_mask.to_bytes(bytes_per_entry, endianness)
        hiz_arr += bytearray(data_z)

    return (data_arr, hiz_arr, hashlib.sha1(data_arr).hexdigest())  

def build_output_binary_file(outf: str, data: bytearray) -> None:
    with open(outf, 'wb') as f:
        f.write(data)

def build_output_table_file(outf: str, ic: ICDefinition, elements: list[DataElement]) -> None:
    data_width: int = len(ic.data)
    address_width: int = len(ic.address)
    # Use upside-down floor division: https://stackoverflow.com/questions/14822184/is-there-a-ceiling-equivalent-of-operator-in-python
    address_bytes: int = -(address_width // -8)

    with open(outf, "wt") as f:
        f.write(f'Name:\t{ic.name}\n')
        f.write(f'Type:\t{ic.ic_type.value}\n')
        f.write(f'A:\t{len(ic.address)}\n')
        f.write(f'D:\t{len(ic.data)}\n')
        f.write('\n')

        for i, el in enumerate(elements):
            address_str: str = f'{i:0{address_bytes*2}X}'
            data_bit_list: list[str] = list(f'{el.data:0{data_width}b}')

            for hiz_pin in _bits_iterator(el.z_mask):
                data_bit_list[(data_width - 1) - int(math.log2(hiz_pin))] = 'Z'

            f.write(f'{address_str}\t{''.join(data_bit_list)}\n')

    return