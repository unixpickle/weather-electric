from collections import defaultdict
from typing import Callable, Dict, List

import numpy as np
from sklearn.base import BaseEstimator

from .aggregate import AggregateRow, row_usage_rate

Model = Callable[[AggregateRow], float]


def model_mse(dataset: List[AggregateRow], model: Model) -> float:
    """
    Compute the hourly usage prediction MSE of a model on a dataset.
    """
    return _mean([(model(x) - row_usage_rate(x)) ** 2 for x in dataset])


def zero_model(_: AggregateRow) -> float:
    """
    A Model that returns 0.
    """
    return 0.0


def create_mean_model(dataset: List[AggregateRow]) -> Model:
    """
    Create a baseline model that always predicts the mean usage of a dataset.
    """
    x = _mean([row_usage_rate(x) for x in dataset])
    return lambda _: x


def create_hourly_model(dataset: List[AggregateRow]) -> Model:
    """
    Create a model that predicts usage based on the hour of the day.
    """
    hourly_avgs = usage_per_hour(dataset)
    return lambda row: hourly_avgs[_row_hour(row)]


def usage_per_hour(dataset: List[AggregateRow]) -> Dict[int, float]:
    """
    Get the mean usage rate per hour of the day.
    """
    hourly_usages = {
        i: [row for row in dataset if _row_hour(row) == i] for i in range(24)
    }
    hourly_avgs = {
        i: _mean([row_usage_rate(x) for x in rows]) for i, rows in hourly_usages.items()
    }
    return hourly_avgs


def create_temp_model(dataset: List[AggregateRow]) -> Model:
    """
    Create a model that bins usage per temperature degree.
    """
    temp_usages = usage_per_temp(dataset)
    return lambda row: temp_usages[round(float(row["temp"]))]


def usage_per_temp(dataset: List[AggregateRow]) -> Dict[int, float]:
    """
    Get the mean usage rate per temperature degree.
    """
    temp_usages = defaultdict(list)
    for row in dataset:
        temp_usages[round(float(row["temp"]))].append(row_usage_rate(row))
    return {k: _mean(v) for k, v in temp_usages.items()}


def create_scikit_model(
    dataset: List[AggregateRow],
    predictor: BaseEstimator,
    fields: List[str],
    residual: Model = zero_model,
) -> Model:
    """
    Create a model using a sklearn estimator.

    An optional residual model may be passed, in which case the resulting model
    predicts the difference between the real usage and the output of residual.
    """

    def row_values(x: AggregateRow) -> np.ndarray:
        return np.array(
            [float(x[k]) if k != "hour" else float(_row_hour(x)) for k in fields]
        )

    data_inputs = np.stack([row_values(x) for x in dataset], axis=0)
    data_outputs = np.array([row_usage_rate(x) - residual(x) for x in dataset])
    predictor.fit(data_inputs, data_outputs)
    return lambda x: float(predictor.predict(row_values(x)[None])[0]) + residual(x)


def _row_hour(row: AggregateRow) -> int:
    return int(row["start_time"].split(":")[0])


def _mean(xs):
    return sum(xs) / len(xs)
