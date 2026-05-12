from typing import List, Any, Dict, Optional
import io

import polars as pl

from .base import (
    BaseDataFrameDataParser,
    is_temporal_field,
    is_geo_field
)
from pygwalker.services.fname_encodings import rename_columns


class PolarsDataFrameDataParser(BaseDataFrameDataParser[pl.DataFrame]):
    """prop parser for polars.DataFrame"""

    def to_records(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        df = self.df[:limit] if limit is not None else self.df
        df = df.fill_nan(None)
        return df.to_dicts()

    def to_csv(self) -> io.BytesIO:
        content = io.BytesIO()
        self.df.write_csv(content)
        return content

    def to_parquet(self) -> io.BytesIO:
        content = io.BytesIO()
        self.df.write_parquet(content, compression="snappy")
        return content

    def _rename_dataframe(self, df: pl.DataFrame) -> pl.DataFrame:
        df = df.rename({
            old_col: new_col
            for old_col, new_col in zip(df.columns, rename_columns(df.columns))
        })
        return df

    def _is_numeric_dtype(self, s: pl.Series) -> bool:
        return s.dtype in pl.NUMERIC_DTYPES

    def _is_temporal_dtype(self, s: pl.Series) -> bool:
        return s.dtype in pl.TEMPORAL_DTYPES

    def _is_integer_dtype(self, s: pl.Series) -> bool:
        return s.dtype in pl.INTEGER_DTYPES

    def _is_string_like_dtype(self, s: pl.Series) -> bool:
        return s.dtype == pl.Utf8

    def _get_sample_values(self, s: pl.Series, n: int) -> List[Any]:
        return [s[i] for i in range(min(len(s), n))]

    def _get_unique_count(self, s: pl.Series) -> int:
        return len(s.unique())

    def _infer_semantic(self, s: pl.Series, field_name: str):
        samples = self._get_sample_values(s, 20)
        return self._infer_semantic_common(s, field_name, samples)

    def _infer_analytic(self, s: pl.Series, field_name: str):
        unique_count = self._get_unique_count(s)
        return self._infer_analytic_common(s, field_name, unique_count)

    @property
    def dataset_type(self) -> str:
        return "polars_dataframe"
