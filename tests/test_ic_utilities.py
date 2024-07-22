"""Tests for IC Utilities"""

# pylint: disable=wrong-import-position,wrong-import-order

import sys
sys.path.insert(0, '.') # Make VSCode happy...

from dupico_dumper.dupico_library.pin_mapping_utilities import PinMappingUtilities
import pytest

def test_map_value_to_pins_8bit(pin_list_8bit):
    """Test a mapping of a value to specific pins"""
    assert PinMappingUtilities.map_value_to_pins(pins=pin_list_8bit, value=0xFF) == 0x800018020F
    assert PinMappingUtilities.map_value_to_pins(pins=pin_list_8bit, value=0xAA) == 0x800008000A

def test_map_value_to_pins_18bit(pin_list_18bit):
    """Test a mapping of a value to specific pins"""
    assert PinMappingUtilities.map_value_to_pins(pins=pin_list_18bit, value=0x3FFFF) == 0x1FA00FFE
    assert PinMappingUtilities.map_value_to_pins(pins=pin_list_18bit, value=0x12345) == 0x7000A22
    
def test_map_pins_to_value_8bit(pin_list_8bit):
    """Test a mapping of data read from pins to original value"""
    assert PinMappingUtilities.map_pins_to_value(pins=pin_list_8bit, value=0x800018020F) == 0xFF
    assert PinMappingUtilities.map_pins_to_value(pins=pin_list_8bit, value=0x800008000A) == 0xAA

def test_map_pins_to_value_18bit(pin_list_18bit):
    """Test a mapping of data read from pins to original value"""
    assert PinMappingUtilities.map_pins_to_value(pins=pin_list_18bit, value=0x1FA00FFE) == 0x3FFFF
    assert PinMappingUtilities.map_pins_to_value(pins=pin_list_18bit, value=0x7000A22) == 0x12345
1    