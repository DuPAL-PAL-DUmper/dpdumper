"""Fixtures for testing"""

# pylint: disable=wrong-import-position

import sys
sys.path.insert(1, '.') # Make VSCode happy...

import pytest

@pytest.fixture
def pin_list_8bit() -> list[int]:
    return [1, 2, 3, 4, 10, 20, 22, 41]
