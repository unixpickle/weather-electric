from dataclasses import dataclass
from typing import Dict, Iterable, Iterator

from .pge_data import ElectricUsage
from .weather_data import HourlyWeather, WeatherAPI


@dataclass
class UsageAndWeather:
    usage: ElectricUsage
    weather: HourlyWeather

    @classmethod
    def empty(cls) -> "UsageAndWeather":
        return cls(
            ElectricUsage(*map(str, range(8))), HourlyWeather(*map(str, range(16)))
        )

    def to_csv_row(self) -> Dict[str, str]:
        result = self.usage.__dict__.copy()
        result.update(
            {
                k: v
                for k, v in self.weather.__dict__.items()
                if k not in ["date", "time"]
            }
        )
        return result


def aggregate_usage(
    api: WeatherAPI, usage: Iterable[ElectricUsage], location: str
) -> Iterator[UsageAndWeather]:
    for usage_unit in usage:
        hourly_weathers = api.hourly_weather(location, usage_unit.date)
        unit_time = int(usage_unit.start_time.split(":")[0]) * 100
        hour = next(x for x in hourly_weathers if int(x.time) == unit_time)
        yield UsageAndWeather(usage=usage_unit, weather=hour)
