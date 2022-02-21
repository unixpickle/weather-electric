import csv
from dataclasses import dataclass
from typing import Dict, List, TextIO, Union


@dataclass
class ElectricUsage:
    row_type: str
    date: str
    start_time: str
    end_time: str
    usage: str
    units: str
    cost: str
    notes: str

    @classmethod
    def from_row(cls, row: Dict[str, str]) -> "ElectricUsage":
        fields = [
            "TYPE",
            "DATE",
            "START TIME",
            "END TIME",
            "USAGE",
            "UNITS",
            "COST",
            "NOTES",
        ]
        return cls(*(row[x] for x in fields))


def read_green_button_csv_file(f: Union[str, TextIO]) -> List[ElectricUsage]:
    """
    Read a CSV file exported using PG&E's "green button".
    """
    if isinstance(f, str):
        with open(f, "rt") as handle:
            return read_green_button_csv_file(handle)

    # There is a preamble before the data, and it ends with a
    # blank line.
    while True:
        line = f.readline()
        if not line.rstrip():
            break

    reader = csv.DictReader(f)
    return [ElectricUsage.from_row(row) for row in reader]
