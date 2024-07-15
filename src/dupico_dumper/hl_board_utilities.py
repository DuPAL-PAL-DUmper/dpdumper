"""This module contains high level utility code to perform operations on the board"""

from typing import Generator, final, NamedTuple, Iterable, TypeVar, Tuple, Iterator

import serial
import math
from dupico_dumper.ic.ic_definition import ICDefinition
from dupico_dumper.board_commands import BoardCommands
from dupico_dumper.ic.ic_utilities import ICUtilities
from dupico_dumper.command_structures import CommandCode
from dupico_dumper.ll_board_utilities import LLBoardUtilities

T = TypeVar('T')
def _grouped(iterable: Iterable[T], n: int) -> Iterable[Tuple[T, ...]]:
    return zip(*[iter(iterable)]*n)

def _write_pin_map_generator(ic: ICDefinition, tot_addrs: int, check_hiz: bool = False, divisible_by: int = 1) -> Generator[int, None, None]:
    data_on_mapped: int = ICUtilities.map_value_to_pins(ic.data, 0xFFFFFFFFFFFFFFFF) # Use this to detect if we have data pins in high impedance
    act_h_mapped: int = ICUtilities.map_value_to_pins(ic.act_h_enable, 0xFFFFFFFFFFFFFFFF)
    wr_l_mapped: int = ICUtilities.map_value_to_pins(ic.act_l_write, 0xFFFFFFFFFFFFFFFF) # Make sure that we do not try to write anything

    for i in range(0, tot_addrs):
        address_mapped: int = ICUtilities.map_value_to_pins(ic.address, i)

        # We will write the following, in sequence, and check their outputs for differences
        # If there are differences on the data pins, it means the IC has data outputs in high-impedance state
        out_data_l: int = act_h_mapped | wr_l_mapped | address_mapped

        yield out_data_l

        if check_hiz:
            out_data_h: int = data_on_mapped | act_h_mapped | wr_l_mapped | address_mapped
            yield out_data_h

    remainder: int = tot_addrs % divisible_by
    if remainder > 0:
        for i in range(0, divisible_by - remainder):
            yield 0
            if check_hiz:
                yield 0


@final
class DataElement(NamedTuple):
    data: int
    z_mask: int = 0

@final
class HLBoardUtilities:
    """
    This class contains high level utilities to perform operations on the board
    """

    _MAX_CONSECUTIVE_COMMANDS: int = 8

    @classmethod
    def read_ic(cls, ser: serial.Serial, ic: ICDefinition, check_hiz: bool = False) -> list[DataElement] | None:
        read_data: list[DataElement] = []
        addr_combs: int = 1 << (len(ic.address) - 1) # Calculate the number of addresses that this IC supports
        wr_responses: list[int] = []
        response: str | None = None
        block_size: int = 8

        try:
            BoardCommands.write_pins(ser, 0)
            BoardCommands.set_power(ser, True)
                
            data_on_mapped: int = ICUtilities.map_value_to_pins(ic.data, 0xFFFFFFFFFFFFFFFF) # Use this to detect if we have data pins in high impedance
            act_h_mapped: int = ICUtilities.map_value_to_pins(ic.act_h_enable, 0xFFFFFFFFFFFFFFFF)
            wr_l_mapped: int = ICUtilities.map_value_to_pins(ic.act_l_write, 0xFFFFFFFFFFFFFFFF) # Make sure that we do not try to write anything

            tot_blocks: int = math.ceil(addr_combs / block_size)
            tot_blocks = tot_blocks if not check_hiz else tot_blocks * 2

            pin_map_gen = _write_pin_map_generator(ic, addr_combs, check_hiz, block_size)
            
            for i, pin_map in enumerate(_grouped(pin_map_gen, block_size)):
                print(f'Testing block {i+1}/{int(tot_blocks)}')
                ser.write(LLBoardUtilities.build_command(CommandCode.EXTENDED_WRITE, [f'{entry:0{16}X}' for entry in pin_map]))

                for _ in range(0, 8):
                    response = LLBoardUtilities.read_response_string(ser)
                    if response is None or len(response) != 18 or response[0] != CommandCode.WRITE.value: # Something went wrong...
                        return None
                    wr_responses.append(int(response[2:], 16))

            if check_hiz:
                for pulled_low, pulled_up in _grouped(wr_responses, 2):
                    hiz_pins: int = pulled_low ^ pulled_up
                    read_data.append(DataElement(data=ICUtilities.map_pins_to_value(ic.data, pulled_low), z_mask=ICUtilities.map_pins_to_value(ic.data, hiz_pins)))
            else:
                for pulled_low in wr_responses:
                    read_data.append(DataElement(data=ICUtilities.map_pins_to_value(ic.data, pulled_low)))
        except Exception as exc:
            print(exc)
        finally:
            BoardCommands.set_power(ser, False)
            BoardCommands.write_pins(ser, 0)

        return read_data[:addr_combs]
    
    @staticmethod
    def write_ic(ser: serial.Serial, ic: ICDefinition, data: list[int]) -> None:
        addr_combs: int = 1 << (len(ic.address) - 1) # Calculate the number of addresses that this IC supports

        # Check that we have enough data (or not too much) to write
        if addr_combs != len(data):
            raise ValueError(f'IC definition supports {addr_combs} addresses, but input array has {len(data)}')

        act_h_mapped: int = ICUtilities.map_value_to_pins(ic.act_h_enable, 0xFFFFFFFFFFFFFFFF)

        # These are to disable writing
        wr_l_mapped: int = ICUtilities.map_value_to_pins(ic.act_l_write, 0xFFFFFFFFFFFFFFFF)

        # These are to enable writing
        wr_h_mapped: int = ICUtilities.map_value_to_pins(ic.act_h_write, 0xFFFFFFFFFFFFFFFF)

        try:
            BoardCommands.write_pins(ser, 0)
            BoardCommands.set_power(ser, True)

            for i in range(0, addr_combs):
                address_mapped: int = ICUtilities.map_value_to_pins(ic.address, i)
                data_mapped: int = ICUtilities.map_value_to_pins(ic.data, data[i])

                # Set data and address, but with writing disabled
                BoardCommands.write_pins(ser, address_mapped | data_mapped | act_h_mapped | wr_l_mapped)
                # Enable writing
                BoardCommands.write_pins(ser, address_mapped | data_mapped | act_h_mapped | wr_h_mapped)
                # Disable writing before switching to the next address
                BoardCommands.write_pins(ser, address_mapped | data_mapped | act_h_mapped | wr_l_mapped)
        finally:
            BoardCommands.set_power(ser, False)


                
