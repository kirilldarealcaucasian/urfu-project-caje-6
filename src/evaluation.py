"""Временная кросс-валидация и сохранение результатов экспериментов."""

import json
from typing import TypedDict

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, r2_score, root_mean_squared_error
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV, TimeSeriesSplit
from sklearn.pipeline import Pipeline

from .data_preparation import ROOT, TARGET_COLUMN
from .features import ALL_FEATURES
from .type_aliases import CrossValidationSplits


class ScoreRow(TypedDict):
    """Метрики одного регрессора на одном внешнем разбиении."""

    regressor: str
    fold: int
    MAE: float
    RMSE: float
    R2: float


class RegressionExperiment:
    """Сравнение регрессоров на одинаковых временных разбиениях."""

    def __init__(self, feature_dataset: pd.DataFrame) -> None:
        self.features: pd.DataFrame = feature_dataset[list(ALL_FEATURES)]
        self.target: pd.Series = feature_dataset[TARGET_COLUMN]
        self.splits: CrossValidationSplits = list(
            TimeSeriesSplit(n_splits=5).split(self.features)
        )
        self.scores: list[ScoreRow] = []
        self.coefficient_diagnostics: list[dict[str, object]] = []
        self.hyperparameter_choices: list[dict[str, object]] = []
        self.predictions: dict[str, pd.Series] = {}

    def evaluate_regressor(
        self,
        regressor_name: str,
        feature_names: list[str],
        regressor: BaseEstimator | None = None,
    ) -> None:
        """Оценить регрессор или persistence-прогноз на всех фолдах."""
        prediction_series = pd.Series(index=self.features.index, dtype=float)
        self.predictions[regressor_name] = prediction_series

        for fold_number, (train_indices, test_indices) in enumerate(self.splits, 1):
            train_features = self.features.iloc[train_indices][list(feature_names)]
            train_target = self.target.iloc[train_indices]
            test_features = self.features.iloc[test_indices][list(feature_names)]
            actual_target = self.target.iloc[test_indices]

            if regressor is None:
                predicted_target = test_features["usage_lag_1"].to_numpy()
            else:
                regressor.fit(train_features, train_target)
                predicted_target = regressor.predict(test_features)
                self._record_regressor_diagnostics(
                    regressor_name,
                    fold_number,
                    regressor,
                )

            prediction_series.iloc[test_indices] = predicted_target
            self.scores.append(
                {
                    "regressor": regressor_name,
                    "fold": fold_number,
                    "MAE": mean_absolute_error(actual_target, predicted_target),
                    "RMSE": root_mean_squared_error(actual_target, predicted_target),
                    "R2": r2_score(actual_target, predicted_target),
                }
            )

    def _record_regressor_diagnostics(
        self,
        regressor_name: str,
        fold_number: int,
        regressor: BaseEstimator,
    ) -> None:
        """Сохранить параметры поиска или коэффициенты Ridge."""
        if isinstance(regressor, (GridSearchCV, RandomizedSearchCV)):
            self.hyperparameter_choices.append(
                {
                    "regressor": regressor_name,
                    "fold": fold_number,
                    "params": json.dumps(regressor.best_params_),
                    "inner_MAE": -regressor.best_score_,
                }
            )
            return

        if not isinstance(regressor, Pipeline):
            return
        fitted_regressor = regressor.named_steps["regressor"]
        if not isinstance(fitted_regressor, Ridge):
            return

        coefficients = fitted_regressor.coef_
        self.coefficient_diagnostics.append(
            {
                "regressor": regressor_name,
                "fold": fold_number,
                "coefficient_count": coefficients.size,
                "nonzero_count": int((np.abs(coefficients) > 1e-8).sum()),
                "maximum_absolute_coefficient": np.abs(coefficients).max(),
            }
        )

    def summarize_results(self) -> pd.DataFrame:
        """Посчитать среднее и разброс метрик по внешним фолдам."""
        return (
            pd.DataFrame(self.scores)
            .groupby("regressor", sort=False)
            .agg(
                MAE=("MAE", "mean"),
                MAE_std=("MAE", "std"),
                RMSE=("RMSE", "mean"),
                RMSE_std=("RMSE", "std"),
                R2=("R2", "mean"),
                R2_std=("R2", "std"),
            )
        )

    def save_results(
        self,
        result_name: str,
        summary: pd.DataFrame | None = None,
    ) -> None:
        """Сохранить сводку, фолды и диагностические таблицы эксперимента."""
        destination = ROOT / "results/tables"
        destination.mkdir(parents=True, exist_ok=True)
        result_summary = self.summarize_results() if summary is None else summary
        result_summary.to_csv(
            destination / f"{result_name}.csv",
            float_format="%.6f",
        )
        pd.DataFrame(self.scores).to_csv(
            destination / f"{result_name}_fold_scores.csv",
            index=False,
        )
        if self.coefficient_diagnostics:
            pd.DataFrame(self.coefficient_diagnostics).to_csv(
                destination / f"{result_name}_coefficients.csv",
                index=False,
            )
        if self.hyperparameter_choices:
            pd.DataFrame(self.hyperparameter_choices).to_csv(
                destination / f"{result_name}_parameters.csv",
                index=False,
            )
