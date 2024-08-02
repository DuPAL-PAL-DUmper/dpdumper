"""Contains the class that defines the connections of an IC"""

from typing import final

from dpdumper.ic.ic_types import ICType

@final
class ICDefinition:
    name: str
    type: ICType
    address: list[int]
    data: list[int]
    act_h_enable: list[int]
    act_l_enable: list[int]
    act_h_write: list[int]
    act_l_write: list[int]
    adapter_hi_pins: list[int]
    hw_model: int
    adapter_notes: str | None = None

    @staticmethod
    def _remap_pin_array(zif_map: list[int], pins: list[int]) -> list[int]:
        remapped: list[int] = []

        for pin in pins:
            remapped.append(zif_map[pin - 1]) # Remember that pin numbering is 1-based

        return remapped       

    def __init__(self,
                 name: str, 
                 type: ICType, 
                 zif_map: list[int],
                 address: list[int],
                 data: list[int],
                 act_h_enable: list[int],
                 act_l_enable: list[int],
                 act_h_write: list[int],
                 act_l_write: list[int],
                 adapter_hi_pins: list[int],
                 hw_model: int,
                 adapter_notes: str | None = None):
        
        self.name = name
        self.type = type
        self.hw_model = hw_model
        self.adapter_notes = adapter_notes
        self.adapter_hi_pins = adapter_hi_pins

        # Remap pins on the ZIF socket
        self.address = self._remap_pin_array(zif_map, address)
        self.data = self._remap_pin_array(zif_map, data)
        self.act_h_enable = self._remap_pin_array(zif_map, act_h_enable)
        self.act_l_enable = self._remap_pin_array(zif_map, act_l_enable)
        self.act_h_write = self._remap_pin_array(zif_map, act_h_write)
        self.act_l_write = self._remap_pin_array(zif_map, act_l_write)

