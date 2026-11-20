"""Составные типы временных разбиений для оценки моделей."""

import numpy as np
from numpy.typing import NDArray

type RowIndices = NDArray[np.integer]
type CrossValidationSplit = tuple[RowIndices, RowIndices]
type CrossValidationSplits = list[CrossValidationSplit]
