"""
Combine PG&E electric usage with corresponding historical weather data in a
single CSV file.

Before running the script, you should download your hourly usage data from PG&E
using the Green Button.

You also need to setup an API key on https://www.worldweatheronline.com/. This
API key must be passed via the --api_key flag, e.g. `--api_key XXXX`.

Finally, you must figure out a way to identify your location to the weather
API. This can be a latitude,longitude pair. Pass the location via the
`--location` flag, e.g. `--location 35.9828,-121.1231`.

Finaly usage of the script might look like:

    python -m weather_electric.dump_aggregate \
        --api_key XXXX \
        --location 35.9828,-121.1231 \
        /path/to/pge_data.csv \
        aggregate_output.csv

The script will show a loading indicator as it fetches weather data for each
day in the PG&E data file. Additionally, it will create a `weather_cache/`
sub-directory in the current working directory so that future invocations will
not have to re-fetch historical weather data.
"""

import argparse
import csv

from tqdm.auto import tqdm
from weather_electric.aggregate import UsageAndWeather, aggregate_usage
from weather_electric.pge_data import read_green_button_csv_file
from weather_electric.weather_data import WeatherAPI


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--location", type=str, required=True)
    parser.add_argument("--api_key", type=str, required=True)
    parser.add_argument("pge_data", type=str)
    parser.add_argument("output_path", type=str)
    args = parser.parse_args()

    api_client = WeatherAPI(api_key=args.api_key)
    electric_data = read_green_button_csv_file(args.pge_data)
    aggregate = aggregate_usage(api_client, electric_data, args.location)

    with open(args.output_path, "w") as f:
        writer = csv.DictWriter(
            f, fieldnames=sorted(UsageAndWeather.empty().to_csv_row().keys())
        )
        writer.writeheader()
        writer.writerows(x.to_csv_row() for x in tqdm(aggregate))


if __name__ == "__main__":
    main()
