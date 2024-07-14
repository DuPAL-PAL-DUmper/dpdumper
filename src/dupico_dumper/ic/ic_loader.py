"""This class contains code to extract an IC definition from a properly formatted TOML file"""

from typing import Any, final
from dupico_dumper.ic.ic_definition import ICDefinition
from dupico_dumper.ic.ic_types import ICType

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

    @classmethod
    def extract_definition_from_file(cls, filepath: str) -> ICDefinition:
        with open(filepath, "rb") as f:
            toml_data: dict[str, Any] = tomllib.load(f)
            type: ICType = ICType(toml_data[cls._KEY_TYPE])
            return ICDefinition(name=toml_data[cls._KEY_NAME],
                                type=type,
                                address=toml_data[cls._KEY_PINOUT][cls._KEY_PINOUT_ADDRESS],
                                data=toml_data[cls._KEY_PINOUT][cls._KEY_PINOUT_DATA],
                                act_h_enable=toml_data[cls._KEY_PINOUT][cls._KEY_PINOUT_H_ENABLE],
                                act_l_enable=toml_data[cls._KEY_PINOUT][cls._KEY_PINOUT_L_ENABLE],
                                act_h_write=toml_data[cls._KEY_PINOUT][cls._KEY_PINOUT_H_WRITE],
                                act_l_write=toml_data[cls._KEY_PINOUT][cls._KEY_PINOUT_L_WRITE])
