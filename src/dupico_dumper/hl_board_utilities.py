"""This module contains high level utility code to perform operations on the board"""

from typing import final, NamedTuple

import serial
from dupico_dumper.ic.ic_definition import ICDefinition
from dupico_dumper.board_commands import BoardCommands
from dupico_dumper.ic.ic_utilities import ICUtilities

@final
class DataElement(NamedTuple):
    data: int
    z_mask: int = 0

@final
class HLBoardUtilities:
    """
    This class contains high level utilities to perform operations on the board
    """

    @staticmethod
    def read_ic(ser: serial.Serial, ic: ICDefinition) -> list[DataElement] | None:
        read_data: list[DataElement] = []
        addr_combs: int = 1 << (len(ic.address) - 1) # Calculate the number of addresses that this IC supports

        try:
            BoardCommands.write_pins(ser, 0)
            BoardCommands.set_power(ser, True)
                
            data_on_mapped: int = ICUtilities.map_value_to_pins(ic.data, 0xFFFFFFFFFFFFFFFF) # Use this to detect if we have data pins in high impedance
            act_h_mapped: int = ICUtilities.map_value_to_pins(ic.act_h_enable, 0xFFFFFFFFFFFFFFFF)
            wr_l_mapped: int = ICUtilities.map_value_to_pins(ic.act_l_write, 0xFFFFFFFFFFFFFFFF) # Make sure that we do not try to write anything

            for i in range(0, addr_combs):
                address_mapped: int = ICUtilities.map_value_to_pins(ic.address, i)
                
                # We will write the following, in sequence, and check their outputs for differences
                # If there are differences on the data pins, it means the IC has data outputs in high-impedance state
                out_data_h: int = data_on_mapped | act_h_mapped | wr_l_mapped | address_mapped
                out_data_l: int = act_h_mapped | wr_l_mapped | address_mapped

                read_pull_h: int | None = BoardCommands.write_pins(out_data_h)
                read_pull_l: int | None = BoardCommands.write_pins(out_data_l)

                if read_pull_h is None or read_pull_l is None:
                    return None

                hiz_pins: int = read_pull_h ^ read_pull_l

                data_remapped: int = ICUtilities.map_pins_to_value(ic.data, read_pull_l)
                hiz_remapped: int = ICUtilities.map_pins_to_value(ic.data, hiz_pins)

                read_data.append(DataElement(data=data_remapped, hiz_pins=hiz_remapped))
        finally:
            BoardCommands.set_power(ser, False)

        return read_data
    
    @staticmethod
    def write_ic(ser: serial.Serial, ic: ICDefinition, data: list[int]) -> bool:
        return False