import io
from typing import Any, Dict, List, Optional

from modin import pandas as mpd

from .base import (
    BaseDataFrameDataParser,
    FieldSpec,
    is_temporal_field,
    is_geo_field
)
from pygwalker.services.fname_encodings import rename_columns


class ModinPandasDataFrameDataParser(BaseDataFrameDataParser[mpd.DataFrame]):
    """prop parser for modin.pandas.DataFrame"""
    def __init__(
        self,
        df: mpd.DataFrame,
        field_specs: List[FieldSpec],
        infer_string_to_date: bool,
        infer_number_to_dimension: bool,
        other_params: Dict[str, Any]
    ):
        super().__init__(df, field_specs, infer_string_to_date, infer_number_to_dimension, other_params)
        self._duckdb_df = self.df._to_pandas()

    def to_records(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        df = self.df[:limit] if limit is not None else self.df
        df = df.replace({float('nan'): None})
        return df.to_dict(orient='records')

    def to_csv(self) -> io.BytesIO:
        content = io.BytesIO()
        self.df.to_csv(content, index=False)
        return content

    def to_parquet(self) -> io.BytesIO:
        content = io.BytesIO()
        self.df.to_parquet(content, index=False, compression="snappy")
        return content

    def _rename_dataframe(self, df: mpd.DataFrame) -> mpd.DataFrame:
        df = df.reset_index(drop=True)
        df.columns = rename_columns(list(df.columns))
        return df

    def _is_numeric_dtype(self, s: mpd.Series) -> bool:
        return s.dtype.kind in "fcmiu"

    def _is_temporal_dtype(self, s: mpd.Series) -> bool:
        return s.dtype.kind in "M"

    def _is_integer_dtype(self, s: mpd.Series) -> bool:
        return s.dtype.kind in "iu"

    def _is_string_like_dtype(self, s: mpd.Series) -> bool:
        return s.dtype.kind in "bOSUV"

    def _get_sample_values(self, s: mpd.Series, n: int) -> List[Any]:
        return [s.iloc[i] for i in range(min(len(s), n))]

    def _get_unique_count(self, s: mpd.Series) -> int:
        return len(s.unique())

    def _infer_semantic(self, s: mpd.Series, field_name: str):
        samples = self._get_sample_values(s, 20)
        return self._infer_semantic_common(s, field_name, samples)

    def _infer_analytic(self, s: mpd.Series, field_name: str):
        unique_count = self._get_unique_count(s)
        return self._infer_analytic_common(s, field_name, unique_count)

    @property
    def dataset_type(self) -> str:
        return "modin_dataframe"
