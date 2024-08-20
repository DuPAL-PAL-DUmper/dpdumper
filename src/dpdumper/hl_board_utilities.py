"""This module contains high level utility code to perform operations on the board"""

from typing import Generator, final, NamedTuple

import serial
import math
import logging

from dupicolib.hardware_board_commands import HardwareBoardCommands
from dpdumperlib.ic.ic_definition import ICDefinition

from dpdumper.dumper_utilities import grouped_iterator

_LOGGER = logging.getLogger(__name__)

# Taken from https://stackoverflow.com/questions/3173320/text-progress-bar-in-terminal-with-block-characters
def _print_progressBar (iteration: int, total: int, prefix: str = '', suffix: str = '', decimals: int = 1, length: int = 50, fill: str = '█', printEnd: str = '\r'):
    percent: str = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength: int = int(length * iteration // total)
    bar: str = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = printEnd)
    # Print New Line on Complete
    if iteration == total: 
        print()

def _read_pin_map_generator(cmd_class: type[HardwareBoardCommands], ic: ICDefinition, check_hiz: bool = False) -> Generator[int, None, None]:
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
    def read_ic(cls, ser: serial.Serial, cmd_class: type[HardwareBoardCommands], ic: ICDefinition, check_hiz: bool = False) -> list[DataElement] | None:
        read_data: list[DataElement] = []
        addr_combs: int = 1 << len(ic.address) # Calculate the number of addresses that this IC supports
        wr_responses: list[int] = []
        
        _LOGGER.debug(f'read_ic command with definition {ic.name}, checking hi-z {check_hiz}. IC has {addr_combs} addresses and data width {len(ic.data)} bits.')

        try:
            hi_pins_mapped: int = cmd_class.map_value_to_pins(ic.adapter_hi_pins, 0xFFFFFFFFFFFFFFFF)

            _LOGGER.debug(f'This IC requires the following pin mask forced high: {hi_pins_mapped:0{16}X}')

            cmd_class.write_pins(hi_pins_mapped, ser) # Start with these already enabled
            cmd_class.set_power(True, ser)

            tot_combs: int = addr_combs if not check_hiz else addr_combs * 2

            pin_map_gen = _read_pin_map_generator(cmd_class, ic, check_hiz)
            
            for i, pin_map in enumerate(pin_map_gen):
                if i % 250 == 0:
                    _print_progressBar(i, tot_combs)

                wr_addr_response: int | None = cmd_class.write_pins(pin_map, ser)

                if wr_addr_response is None:
                    return None # Something went wrong
                else:
                    wr_responses.append(wr_addr_response)

            _print_progressBar(tot_combs, tot_combs)

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
            cmd_class.set_power(False, ser)
            cmd_class.write_pins(0, ser)

        return read_data[:addr_combs]

    @staticmethod
    def write_ic(ser: serial.Serial, cmd_class: type[HardwareBoardCommands], ic: ICDefinition, data: list[int]) -> None:
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
            cmd_class.write_pins(hi_pins_mapped, ser)
            cmd_class.set_power(True, ser)

            for i in range(0, addr_combs):
                if i % 250 == 0:
                    _print_progressBar(i, addr_combs)
                
                address_mapped: int = cmd_class.map_value_to_pins(ic.address, i)
                data_mapped: int = cmd_class.map_value_to_pins(ic.data, data[i])

                # Set data and address, but with writing disabled
                cmd_class.write_pins(hi_pins_mapped | address_mapped | data_mapped | act_h_mapped | wr_l_mapped, ser)
                # Enable writing
                cmd_class.write_pins(hi_pins_mapped | address_mapped | data_mapped | act_h_mapped | wr_h_mapped, ser)
                # Disable writing before switching to the next address
                cmd_class.write_pins(hi_pins_mapped | address_mapped | data_mapped | act_h_mapped | wr_l_mapped, ser)
            
            _print_progressBar(addr_combs, addr_combs)
        finally:
            print('')
            cmd_class.set_power(False, ser)
            cmd_class.write_pins(0, ser)


                
