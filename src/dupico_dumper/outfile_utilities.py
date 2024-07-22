"""This file contains code to generate output files from data reads"""

import math
import hashlib

from typing import Generator

from dupico_dumper.hl_board_utilities import DataElement
from dupico_dumper.ic.ic_definition import ICDefinition
from dupico_dumper.dumper_utilities import grouped_iterator

# See https://stackoverflow.com/questions/8898807/pythonic-way-to-iterate-over-bits-of-integer
# and https://lemire.me/blog/2018/02/21/iterating-over-set-bits-quickly/
def _bits_iterator(n: int) -> Generator[int, None, None]:
    while n:
        b: int = n & (~n + 1)
        yield b
        n ^= b

def build_data_list_from_file(inf: str, ic: ICDefinition) -> list[int]:
    data_list: list[int] = []
    in_content: bytes
    with open(inf, 'rb') as f:
        in_content = f.read()

    data_width: int = len(ic.data)
    bytes_per_entry = int(math.ceil(data_width / 8.0))

    for block in grouped_iterator(in_content, bytes_per_entry):
        data_list.append(int.from_bytes(block, byteorder='big', signed=False))

    return data_list

def build_binary_array(ic: ICDefinition, elements: list[DataElement], hiz_high: bool = False) -> tuple[bytearray, str]:
    """Builds a binary array out of data read from the IC, and returns it plus the SHA1SUM of the data

    Args:
        ic (ICDefinition): Definition of the IC that was read
        elements (list[DataElement]): Array of the reads, in addressing order, containing both data and Hi-Z info
        hiz_high (bool, optional): True if the Hi-Z pins will be represented as 1 in the binary out. Defaults to False.

    Returns:
        tuple[bytearray, str]: Tuple containing the byte array and the sha1 sum for it
    """
    data_width: int = len(ic.data)
    bytes_per_entry = int(math.ceil(data_width / 8.0))
    data_arr: bytearray = bytearray()

    for el in elements:
        data: int = el.data | (el.z_mask if hiz_high else 0)
        data_b: bytes = data.to_bytes(bytes_per_entry, 'big')
        data_arr.append(*data_b)

    return (data_arr, hashlib.sha1(data_arr).hexdigest())  

def build_output_binary_file(outf: str, data: bytearray) -> None:
    with open(outf, 'wb') as f:
        f.write(data)

def build_output_table_file(outf: str, ic: ICDefinition, elements: list[DataElement]) -> None:
    data_width: int = len(ic.data)
    address_width: int = len(ic.address)
    address_bytes: int = int(math.ceil(address_width / 8.0))

    with open(outf, "wt") as f:
        f.write(f'Name:\t{ic.name}\n')
        f.write(f'Type:\t{ic.type.value}\n')
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