"""Fixtures for testing"""

# pylint: disable=wrong-import-position

import sys
sys.path.insert(1, '.') # Make VSCode happy...

import pytest

@pytest.fixture
def pin_list_8bit() -> list[int]:
    return [1, 2, 3, 4, 10, 20, 22, 41]

@pytest.fixture
def pin_list_18bit() -> list[int]:
    # Taken from a 27C2001, address pins
    return [12, 11, 10, 9, 8, 7, 6, 5, 27, 26, 23, 25, 4, 28, 29, 3, 2, 30]

