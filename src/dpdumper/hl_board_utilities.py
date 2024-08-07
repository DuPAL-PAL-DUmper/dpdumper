"""This module contains high level utility code to perform operations on the board"""

from typing import Generator, final, NamedTuple

import serial
import math
import logging

from dupicolib.board_commands import BoardCommands

from dpdumper.ic.ic_definition import ICDefinition
from dpdumper.dumper_utilities import grouped_iterator

_LOGGER = logging.getLogger(__name__)

def _read_pin_map_generator(cmd_class: BoardCommands, ic: ICDefinition, check_hiz: bool = False, divisible_by: int = 1) -> Generator[int, None, None]:
    addr_combs: int = 1 << len(ic.address) # Calculate the number of addresses that this IC supports

    hi_pins_mapped: int = cmd_class.map_value_to_pins(ic.adapter_hi_pins, 0xFFFFFFFFFFFFFFFF)
    data_on_mapped: int = cmd_class.map_value_to_pins(ic.data, 0xFFFFFFFFFFFFFFFF) # Use this to detect if we have data pins in high impedance
    act_h_mapped: int = cmd_class.map_value_to_pins(ic.act_h_enable, 0xFFFFFFFFFFFFFFFF)
    wr_l_mapped: int = cmd_class.map_value_to_pins(ic.act_l_write, 0xFFFFFFFFFFFFFFFF) # Make sure that we do not try to write anything

    for i in range(0, addr_combs):
        address_mapped: int = cmd_class.map_value_to_pins(ic.address, i)

        # We will write the following, in sequence, and check their outputs for differences
        # If there are differences on the data pins, it means the IC has data outputs in high-impedance state
        out_data_l: int = hi_pins_mapped | act_h_mapped | wr_l_mapped | address_mapped

        yield out_data_l

        if check_hiz:
            out_data_h: int = hi_pins_mapped | data_on_mapped | act_h_mapped | wr_l_mapped | address_mapped
            yield out_data_h

    remainder: int = addr_combs % divisible_by
    if remainder > 0:
        for i in range(0, divisible_by - remainder):
            yield hi_pins_mapped # Even if we're left with nothing to try, keep the pins that must be forced high as such
            if check_hiz:
                yield hi_pins_mapped


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
    def read_ic(cls, ser: serial.Serial, cmd_class: BoardCommands, ic: ICDefinition, check_hiz: bool = False) -> list[DataElement] | None:
        read_data: list[DataElement] = []
        addr_combs: int = 1 << len(ic.address) # Calculate the number of addresses that this IC supports
        wr_responses: list[int] = []
        response: str | None = None
        block_size: int = 14 # This almost fills the buffer size on the dupico
        
        _LOGGER.debug(f'read_ic command with definition {ic.name}, checking hi-z {check_hiz}. IC has {addr_combs} addresses and data width {len(ic.data)} bits.')

        try:
            hi_pins_mapped: int = cmd_class.map_value_to_pins(ic.adapter_hi_pins, 0xFFFFFFFFFFFFFFFF)

            _LOGGER.debug(f'This IC requires the following pin mask forced high: {hi_pins_mapped:0{16}X}')

            cmd_class.write_pins(ser, hi_pins_mapped) # Start with these already enabled
            cmd_class.set_power(ser, True)

            tot_blocks: int = math.ceil(addr_combs / block_size)
            tot_blocks = tot_blocks if not check_hiz else tot_blocks * 2

            pin_map_gen = _read_pin_map_generator(cmd_class, ic, check_hiz, block_size)
            
            for i, pin_map in enumerate(grouped_iterator(pin_map_gen, block_size)):
                print(f'Reading block {i+1}/{int(tot_blocks)}'.ljust(80, ' '), end='\r')
                wre_block_responses: list[int] | None = cmd_class.write_pins_extended(ser, pin_map)

                if wre_block_responses is None:
                    return None # Something went wrong
                else:
                    wr_responses.extend(wre_block_responses)

            if check_hiz:
                for pulled_low, pulled_up in grouped_iterator(wr_responses, 2):
                    hiz_pins: int = pulled_low ^ pulled_up
                    read_data.append(DataElement(data=cmd_class.map_pins_to_value(ic.data, pulled_low), z_mask=cmd_class.map_pins_to_value(ic.data, hiz_pins)))
            else:
                for pulled_low in wr_responses:
                    read_data.append(DataElement(data=cmd_class.map_pins_to_value(ic.data, pulled_low)))
        except Exception as exc:
            _LOGGER.critical(exc)
        finally:
            print('') # Avoid writing again on the 'Testing block' string
            cmd_class.set_power(ser, False)
            cmd_class.write_pins(ser, 0)

        return read_data[:addr_combs]

    @staticmethod
    def write_ic(ser: serial.Serial, cmd_class: BoardCommands, ic: ICDefinition, data: list[int]) -> None:
        data_width: int = int(math.ceil(len(ic.data) / 8.0))
        addr_combs: int = 1 << len(ic.address) # Calculate the number of addresses that this IC supports
        _LOGGER.debug(f'write_ic command with definition {ic.name}, IC has {addr_combs} addresses and data width {data_width} bits.')

        # Check that we have enough data (or not too much) to write
        if addr_combs != len(data):
            raise ValueError(f'IC definition supports {addr_combs} addresses, but input array has {len(data)}')


        hi_pins_mapped: int = cmd_class.map_value_to_pins(ic.adapter_hi_pins, 0xFFFFFFFFFFFFFFFF)

        act_h_mapped: int = cmd_class.map_value_to_pins(ic.act_h_enable, 0xFFFFFFFFFFFFFFFF)

        # These are to disable writing
        wr_l_mapped: int = cmd_class.map_value_to_pins(ic.act_l_write, 0xFFFFFFFFFFFFFFFF)

        # These are to enable writing
        wr_h_mapped: int = cmd_class.map_value_to_pins(ic.act_h_write, 0xFFFFFFFFFFFFFFFF)

        _LOGGER.debug(f'This IC requires the following pin mask forced high: {hi_pins_mapped:0{16}X}')

        try:
            # Start with the pins that must be forced high
            cmd_class.write_pins(ser, hi_pins_mapped)
            cmd_class.set_power(ser, True)

            for i in range(0, addr_combs):
                print(f'Writing addr {i} with data {data[i]:0{data_width*2}X}'.ljust(80, ' '), end='\r')
                address_mapped: int = cmd_class.map_value_to_pins(ic.address, i)
                data_mapped: int = cmd_class.map_value_to_pins(ic.data, data[i])

                # Set data and address, but with writing disabled
                cmd_class.write_pins(ser, hi_pins_mapped | address_mapped | data_mapped | act_h_mapped | wr_l_mapped)
                # Enable writing
                cmd_class.write_pins(ser, hi_pins_mapped | address_mapped | data_mapped | act_h_mapped | wr_h_mapped)
                # Disable writing before switching to the next address
                cmd_class.write_pins(ser, hi_pins_mapped | address_mapped | data_mapped | act_h_mapped | wr_l_mapped)
        finally:
            print('')
            cmd_class.set_power(ser, False)
            cmd_class.write_pins(ser, 0)


                
