"""Tests for IC Utilities"""

# pylint: disable=wrong-import-position,wrong-import-order

import sys
sys.path.insert(0, '.') # Make VSCode happy...

from src.dupico_dumper.ic.ic_utilities import ICUtilities
import pytest

def test_map_value_to_pins(pin_list_8bit):
    """Test a mapping of a value to specific pins"""
    mapped_value = ICUtilities.map_value_to_pins(pins=pin_list_8bit, value=0xFF)
    assert mapped_value == 0x800018020F
    