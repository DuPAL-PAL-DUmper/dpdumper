"""Contains the class that defines the connections of an IC"""

from dataclasses import dataclass

from dupico_dumper.ic.ic_types import ICType

@dataclass
class ICDefinition:
    name: str
    type: ICType
    address: list[int]
    data: list[int]
    act_h_enable: list[int]
    act_l_enable: list[int]
    act_h_write: list[int]
    act_l_write: list[int]
