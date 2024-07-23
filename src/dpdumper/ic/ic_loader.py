"""This class contains code to extract an IC definition from a properly formatted TOML file"""

from typing import Any, final
from dpdumper.ic.ic_definition import ICDefinition
from dpdumper.ic.ic_types import ICType

import tomllib

@final
class ICLoader:
    _KEY_NAME: str = 'name'
    _KEY_TYPE: str = 'type'
    _KEY_PINOUT: str = 'pinout'
    _KEY_PINOUT_ADDRESS:str = 'address'
    _KEY_PINOUT_DATA:str = 'data'
    _KEY_PINOUT_H_ENABLE: str = 'H_enable'
    _KEY_PINOUT_L_ENABLE: str = 'L_enable'
    _KEY_PINOUT_H_WRITE: str = 'H_write'
    _KEY_PINOUT_L_WRITE: str = 'L_write'
    _KEY_ADAPTER: str = 'adapter'
    _KEY_ADAPTER_HI_PINS: str = 'hi_pins'
    _KEY_REQUIREMENTS: str = 'requirements'
    _KEY_REQUIREMENTS_HARDWARE: str = 'hardware'

    @classmethod
    def extract_definition_from_file(cls, filepath: str) -> ICDefinition:
        with open(filepath, "rb") as f:
            toml_data: dict[str, Any] = tomllib.load(f)

            hw_req: str | None = toml_data[cls._KEY_REQUIREMENTS][cls._KEY_REQUIREMENTS_HARDWARE]

            if hw_req is None or hw_req != 3: # Ideally we should provide a path to remap old hardware pinouts to new hardware revisions
                raise ValueError('Hardware revision not supported')

            type: ICType = ICType(toml_data[cls._KEY_TYPE])
            return ICDefinition(name=toml_data[cls._KEY_NAME],
                                type=type,
                                address=toml_data[cls._KEY_PINOUT][cls._KEY_PINOUT_ADDRESS],
                                data=toml_data[cls._KEY_PINOUT][cls._KEY_PINOUT_DATA],
                                act_h_enable=toml_data[cls._KEY_PINOUT][cls._KEY_PINOUT_H_ENABLE],
                                act_l_enable=toml_data[cls._KEY_PINOUT][cls._KEY_PINOUT_L_ENABLE],
                                act_h_write=toml_data[cls._KEY_PINOUT][cls._KEY_PINOUT_H_WRITE],
                                act_l_write=toml_data[cls._KEY_PINOUT][cls._KEY_PINOUT_L_WRITE],
                                adapter_hi_pins=toml_data[cls._KEY_ADAPTER][cls._KEY_ADAPTER_HI_PINS])
