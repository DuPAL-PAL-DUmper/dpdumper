"""This file contains code to generate output files from data reads"""

from dupico_dumper.hl_board_utilities import DataElement
from dupico_dumper.ic.ic_definition import ICDefinition

def build_output_table_file(outf: str, ic: ICDefinition, elements: list[DataElement]) -> bool:
    with open(outf, "wt") as f:
        for i, el in enumerate(elements):
            continue

    return False