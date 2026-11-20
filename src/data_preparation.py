"""Загрузка данных и проверка регулярности временного ряда."""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TARGET_COLUMN = "Usage_kWh"
RANDOM_STATE = 42


def load_raw_data() -> pd.DataFrame:
    """Загрузить исходные данные и проверить непрерывность временной оси."""
    raw_data = pd.read_csv(
        ROOT / "data/raw/Steel_industry_data.csv",
        encoding="utf-8-sig",
    )
    timestamp = pd.to_datetime(raw_data["date"], format="%d/%m/%Y %H:%M")
    # В исходнике 00:00 завершает указанные сутки.
    is_midnight = timestamp.dt.hour.eq(0) & timestamp.dt.minute.eq(0)
    timestamp += pd.to_timedelta(is_midnight.astype(int), unit="D")
    raw_data = (
        raw_data.drop(columns="date")
        .assign(timestamp=timestamp)
        .sort_values("timestamp")
        .set_index("timestamp")
    )
    if raw_data.index.duplicated().any() or raw_data.isna().any().any():
        raise ValueError("Пропуски или повторные временные метки в исходных данных")
    time_steps = raw_data.index.to_series().diff().dropna()
    if not time_steps.eq(pd.Timedelta("15min")).all():
        raise ValueError("Нарушен шаг временного ряда")
    return raw_data
