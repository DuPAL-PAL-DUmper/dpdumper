"""Contains the class that defines the connections of an IC"""

from typing import final

from dupico_dumper.ic.ic_types import ICType

@final
class ICDefinition:
    type: ICType

    def __init__(self, type: ICType):
        self.type = type
