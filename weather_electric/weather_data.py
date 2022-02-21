import hashlib
import os
import pickle
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import List, Optional

import requests


@dataclass
class HourlyWeather:
    date: str
    time: str
    temp: str
    wind_speed: str
    wind_dir_degree: str
    precip_inches: str
    humidity: str
    visibility: str
    pressure: str
    cloudcover: str
    heat_index: str
    dew_point: str
    wind_chill: str
    wind_gust: str
    feels_like: str
    uv_index: str

    @classmethod
    def from_element(cls, date: str, elem: ET.Element) -> "HourlyWeather":
        fields = [
            "time",
            "tempF",
            "windspeedMiles",
            "winddirDegree",
            "precipInches",
            "humidity",
            "visibilityMiles",
            "pressureInches",
            "cloudcover",
            "HeatIndexF",
            "DewPointF",
            "WindChillF",
            "WindGustMiles",
            "FeelsLikeF",
            "uvIndex",
        ]
        return cls(date, *(elem.find(x).text.strip() for x in fields))


class WeatherAPI:
    """
    Make historical weather API calls to worldweatheronline.com.

    Results are automatically cached in a provided `cache_dir` to avoid
    unnecessary API calls.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.worldweatheronline.com/premium/v1/past-weather.ashx",
        cache_dir: str = "./weather_cache",
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.cache_dir = cache_dir

    def hourly_weather(self, location: str, date: str) -> List[HourlyWeather]:
        key = self._cache_key(location, date)
        obj = self._get_cache(key)
        if obj is None:
            response = requests.get(
                self.base_url,
                params=dict(key=self.api_key, q=location, date=date, tp="1"),
            ).text
            obj = parse_hourly_weather(response)
            self._store_cache(key, obj)
        return obj

    def _get_cache(self, key: str) -> Optional[List[HourlyWeather]]:
        path = os.path.join(self.cache_dir, key + ".pkl")
        if os.path.exists(path):
            with open(path, "rb") as f:
                result = pickle.load(f)
                assert isinstance(result, list)
                for x in result:
                    assert isinstance(x, HourlyWeather)
                return result
        return None

    def _store_cache(self, key: str, result: List[HourlyWeather]):
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
        path = os.path.join(self.cache_dir, key + ".pkl")
        with open(path + ".tmp", "wb") as f:
            pickle.dump(result, f)
        os.rename(path + ".tmp", path)

    def _cache_key(self, location: str, date: str) -> str:
        return hashlib.md5(
            hashlib.md5(bytes(location, "utf-8")).digest()
            + hashlib.md5(bytes(date, "utf-8")).digest()
        ).hexdigest()


def parse_hourly_weather(data: str) -> List[HourlyWeather]:
    root = ET.fromstring(data)
    weather = root.find("weather")
    date = weather.find("date").text.strip()
    return [HourlyWeather.from_element(date, x) for x in weather.findall("hourly")]
