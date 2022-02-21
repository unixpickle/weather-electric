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
    aggregate = aggregate_usage(api_client, tqdm(electric_data), args.location)

    with open(args.output_path, "w") as f:
        writer = csv.DictWriter(
            f, fieldnames=sorted(UsageAndWeather.empty().to_csv_row().keys())
        )
        writer.writeheader()
        writer.writerows(x.to_csv_row() for x in aggregate)


if __name__ == "__main__":
    main()
