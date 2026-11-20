"""Календарь и прошлые измерения; Load_Type не используется в прогнозе."""

import pandas as pd

from .data_preparation import ROOT, TARGET_COLUMN, load_raw_data

LAG_FEATURES: list[str] = ["usage_lag_1", "usage_lag_96", "usage_lag_672"]
CALENDAR_FEATURES: list[str] = ["nsm", "hour", "month", "day_of_week", "week_status"]
ALL_FEATURES: list[str] = [*LAG_FEATURES, *CALENDAR_FEATURES]


def build_feature_dataset(raw_data: pd.DataFrame) -> pd.DataFrame:
    """Создать доступные на момент прогноза признаки и целевой столбец."""
    target: pd.Series = raw_data[TARGET_COLUMN]
    feature_dataset = pd.DataFrame(index=raw_data.index)
    feature_dataset["nsm"] = raw_data["NSM"]
    feature_dataset["hour"] = raw_data["NSM"] // 3600
    feature_dataset["month"] = (
        pd.DatetimeIndex(raw_data.index) - pd.Timedelta(minutes=15)
    ).month
    feature_dataset["day_of_week"] = raw_data["Day_of_week"]
    feature_dataset["week_status"] = raw_data["WeekStatus"]
    for lag in [1, 96, 672]:  # 15 мин, сутки, неделя
        feature_dataset[f"usage_lag_{lag}"] = target.shift(lag)
    feature_dataset[TARGET_COLUMN] = target
    # Первая неделя не имеет недельного лага.
    return feature_dataset.dropna()


def prepare_feature_dataset(save: bool = True) -> pd.DataFrame:
    """Полностью подготовить датасет и при необходимости сохранить его."""
    feature_dataset = build_feature_dataset(load_raw_data())
    if save:
        destination = ROOT / "data/processed/steel_features.csv"
        destination.parent.mkdir(parents=True, exist_ok=True)
        feature_dataset.to_csv(destination)
    return feature_dataset
