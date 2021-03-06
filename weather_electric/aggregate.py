import csv
from dataclasses import dataclass
from typing import Dict, Iterable, Iterator, List

from .pge_data import ElectricUsage
from .weather_data import HourlyWeather, WeatherAPI

AggregateRow = Dict[str, str]


@dataclass
class UsageAndWeather:
    usage: ElectricUsage
    weather: HourlyWeather

    @classmethod
    def empty(cls) -> "UsageAndWeather":
        return cls(ElectricUsage(*map(str, range(8))), HourlyWeather(*map(str, range(16))))

    def to_csv_row(self) -> AggregateRow:
        result = self.usage.__dict__.copy()
        result.update({k: v for k, v in self.weather.__dict__.items() if k not in ["date", "time"]})
        return result


def aggregate_usage(
    api: WeatherAPI, usage: Iterable[ElectricUsage], location: str
) -> Iterator[UsageAndWeather]:
    for usage_unit in usage:
        hourly_weathers = api.hourly_weather(location, usage_unit.date)
        unit_time = int(usage_unit.start_time.split(":")[0]) * 100
        hour = next(x for x in hourly_weathers if int(x.time) == unit_time)
        yield UsageAndWeather(usage=usage_unit, weather=hour)


def load_aggregate_csv(csv_path: str) -> List[AggregateRow]:
    """
    Load a CSV file that was written by converting UsageAndWeather objects to
    CSV rows with the to_csv_row() method.
    """
    with open(csv_path, "r") as f:
        return list(csv.DictReader(f))


def add_delta_columns(rows: List[AggregateRow]) -> List[AggregateRow]:
    """
    Add fields ending in '_prev', '_next', and '_dt' that indicate the change
    in a field over time.
    """
    res = [x.copy() for x in rows]
    for i, v in enumerate(res):
        prev_i, next_i = max(i - 1, 0), min(len(res) - 1, i + 1)
        prev, next = res[prev_i], res[next_i]
        for k in v.keys():
            try:
                float(v[k])
                prev_val = float(prev[k])
                next_val = float(next[k])
            except ValueError:
                continue
            v[k + "_prev"] = prev[k]
            v[k + "_next"] = next[k]
            v[k + "_dt"] = str((next_val - prev_val) / (next_i - prev_i))
    return res


def row_duration(row: AggregateRow) -> float:
    """
    Get the duration of a row (in hours).
    """
    start_hr, start_min = row["start_time"].split(":")
    end_hr, end_min = row["end_time"].split(":")
    elapsed = float(end_hr) - float(start_hr)
    if elapsed < 0:
        # Assume at most one day difference.
        elapsed += 24
    elapsed += (float(end_min) - float(start_min)) / 60
    return elapsed


def row_usage_rate(row: AggregateRow) -> float:
    """
    Get the hourly electric usage implied by a given row.

    Note that the row may be more or less than an hour.
    """
    return float(row["usage"]) / row_duration(row)
