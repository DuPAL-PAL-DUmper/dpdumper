"""Module entry point"""

import importlib.metadata

__name__: str = 'dpdumper'
__version__: str = '0.0.0'

try:
    __version__ = importlib.metadata.version(__name__)
except:
    print('Could not fetch the version. Probably package not installed???')