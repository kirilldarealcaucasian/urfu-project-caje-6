"""Предобработка обучается только внутри Pipeline каждого фолда."""

from typing import Literal

from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from .data_preparation import RANDOM_STATE

type Scaler = TransformerMixin | Literal["passthrough"]


def build_regression_pipeline(
    feature_names: list[str],
    regressor: BaseEstimator,
    scaler: Scaler = "passthrough",
) -> Pipeline:
    """Объединить преобразование признаков и регрессор в один Pipeline."""
    categorical_features = [
        feature_name
        for feature_name in feature_names
        if feature_name in ("hour", "day_of_week", "week_status")
    ]
    numeric_features = [
        feature_name
        for feature_name in feature_names
        if feature_name not in categorical_features
    ]
    preprocessor = ColumnTransformer(
        [
            ("numeric", scaler, numeric_features),
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                categorical_features,
            ),
        ]
    )
    return Pipeline([("preprocessor", preprocessor), ("regressor", regressor)])


def build_boosting_regressor(feature_names: list[str]) -> Pipeline:
    """Создать основной градиентный бустинг с предобработкой."""
    # Число итераций фиксировано: внутреннее случайное разбиение не требуется.
    regressor = HistGradientBoostingRegressor(
        random_state=RANDOM_STATE,
        early_stopping=False,
    )
    return build_regression_pipeline(feature_names, regressor)
