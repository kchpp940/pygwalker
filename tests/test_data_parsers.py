import os.path
from datetime import datetime

from sqlalchemy import create_engine
import pandas as pd
import polars as pl
import pytest

from pygwalker.services.data_parsers import get_parser
from pygwalker.data_parsers.database_parser import Connector, text
from pygwalker.data_parsers.database_parser import _check_view_sql
from pygwalker.errors import ViewSqlSameColumnError
from pygwalker.data_parsers.base import is_temporal_field

datas = [
    {"name": "padnas", "count": 3, "date": "2022-01-01"},
    {"name": "polars", "count": 1, "date": "2022-01-01"},
    {"name": "modin", "count": 4, "date": "2022-01-01"},
    {"name": "pygwalker", "count": 2, "date": "2022-01-01"},
    {"name": "pygwalker", "count": 6, "date": "2022-01-01"},
]

sql = "SELECT COUNT(1) total FROM pygwalker_mid_table"
sql_result = [{"total": 5}]
raw_fields_result = [
    {'fid': 'name', 'name': 'name', 'semanticType': 'nominal', 'analyticType': 'dimension'},
    {'fid': 'count', 'name': 'count', 'semanticType': 'quantitative', 'analyticType': 'dimension'},
    {'fid': 'date', 'name': 'date', 'semanticType': 'nominal', 'analyticType': 'dimension'}
]
to_records_result = [{'name': 'padnas', 'count': 3, 'date': '2022-01-01'}]
to_records_no_kernel_result = [{'name': 'padnas', 'count': 3, 'date': '2022-01-01'}]


def test_data_parser_on_padnas():
    df = pd.DataFrame(datas)
    dataset_parser = get_parser(df)
    assert dataset_parser.get_datas_by_sql(sql) == sql_result
    assert dataset_parser.raw_fields == raw_fields_result
    assert dataset_parser.to_records(1) == to_records_result
    dataset_parser = get_parser(df)
    assert dataset_parser.to_records(1) == to_records_no_kernel_result


def test_data_parser_on_polars():
    df = pl.DataFrame(datas)
    dataset_parser = get_parser(df)
    assert dataset_parser.get_datas_by_sql(sql) == sql_result
    assert dataset_parser.raw_fields == raw_fields_result
    assert dataset_parser.to_records(1) == to_records_result
    dataset_parser = get_parser(df)
    assert dataset_parser.to_records(1) == to_records_no_kernel_result


try:
    from modin import pandas as mpd
    def test_data_parser_on_modin():
        df = mpd.DataFrame(datas)
        dataset_parser = get_parser(df)
        assert dataset_parser.get_datas_by_sql(sql) == sql_result
        assert dataset_parser.raw_fields == raw_fields_result
        assert dataset_parser.to_records(1) == to_records_result
        dataset_parser = get_parser(df)
        assert dataset_parser.to_records(1) == to_records_no_kernel_result
except ImportError:
    pass


def test_check_view_sql():
    _check_view_sql("SELECT * FROM table_name")
    _check_view_sql("SELECT a.f1, b.f2 FROM a LEFT JOIN b ON a.id = b.id")
    _check_view_sql("SELECT f1, f2 FROM table_name")

    with pytest.raises(ViewSqlSameColumnError):
        _check_view_sql("SELECT f1, f1 FROM table_name")
    with pytest.raises(ViewSqlSameColumnError):
        _check_view_sql("SELECT *, f1 FROM table_name")
    with pytest.raises(ViewSqlSameColumnError):
        _check_view_sql("SELECT * FROM a left join b on a.id = b.id")
    with pytest.raises(ViewSqlSameColumnError):
        _check_view_sql("SELECT a.* FROM a left join b on a.id = b.id")


def test_connector():
    csv_file = os.path.join(os.path.dirname(__file__), "bike_sharing_dc.csv")
    database_url = "duckdb:///:memory:"
    view_sql = f"SELECT 1"
    data_count = 17379

    connector = Connector(database_url, view_sql)
    result = connector.query_datas(f"SELECT COUNT(1) count FROM read_csv_auto('{csv_file}')")
    assert result[0]["count"] == data_count
    assert connector.dialect_name == "duckdb"
    assert connector.view_sql == view_sql
    assert connector.url == database_url

    engine = create_engine(database_url)
    connector = Connector.from_sqlalchemy_engine(engine, view_sql)
    result = connector.query_datas(f"SELECT COUNT(1) count FROM read_csv_auto('{csv_file}')")
    assert result[0]["count"] == data_count
    assert connector.dialect_name == "duckdb"
    assert connector.view_sql == view_sql
    assert connector.url == database_url

    engine = create_engine(database_url)
    with engine.connect() as conn:
        conn.execute(text(f"CREATE TABLE test_datas AS SELECT * FROM read_csv_auto('{csv_file}')"))
        connector = Connector.from_sqlalchemy_connection(conn, view_sql)
        result = connector.query_datas(f"SELECT COUNT(1) count FROM test_datas")
        assert result[0]["count"] == data_count
        assert connector.dialect_name == "duckdb"
        assert connector.view_sql == view_sql
        assert connector.url == database_url


class TestTemporalFieldInference:
    """Regression tests for temporal field inference."""

    def test_is_temporal_field_with_native_datetime(self):
        """Native datetime objects should be identified as temporal."""
        assert is_temporal_field(datetime(2022, 1, 1), infer_string_to_date=False) is True
        assert is_temporal_field(datetime(2022, 1, 1), infer_string_to_date=True) is True

    def test_is_temporal_field_with_valid_date_string(self):
        """Valid date strings should be identified when infer_string_to_date is True."""
        assert is_temporal_field("2022-01-01", infer_string_to_date=True) is True
        assert is_temporal_field("2022/01/01", infer_string_to_date=True) is True
        assert is_temporal_field("2022-01-01 12:00:00", infer_string_to_date=True) is True

    def test_is_temporal_field_with_none_values(self):
        """None values should not be identified as temporal."""
        assert is_temporal_field(None, infer_string_to_date=True) is False
        assert is_temporal_field(None, infer_string_to_date=False) is False

    def test_is_temporal_field_with_empty_string(self):
        """Empty strings should not be identified as temporal."""
        assert is_temporal_field("", infer_string_to_date=True) is False
        assert is_temporal_field("   ", infer_string_to_date=True) is False

    def test_is_temporal_field_with_invalid_date_string(self):
        """Invalid date strings should not be identified as temporal."""
        assert is_temporal_field("abc123", infer_string_to_date=True) is False
        assert is_temporal_field("hello world", infer_string_to_date=True) is False
        assert is_temporal_field("not-a-date", infer_string_to_date=True) is False

    def test_is_temporal_field_with_numeric_strings(self):
        """Numeric strings should not be identified as temporal."""
        assert is_temporal_field("12345", infer_string_to_date=True) is False
        assert is_temporal_field("123.45", infer_string_to_date=True) is False

    def test_is_temporal_field_with_out_of_range_year(self):
        """Dates with years outside reasonable range should not be identified as temporal."""
        assert is_temporal_field("1000-01-01", infer_string_to_date=True) is False
        assert is_temporal_field("2500-01-01", infer_string_to_date=True) is False

    def test_parser_first_value_none_but_subsequent_are_dates(self):
        """Parser should check multiple values - if first is None but others are dates (with infer_string_to_date=True)."""
        datas = [
            {"id": 1, "date_col": None},
            {"id": 2, "date_col": "2022-01-01"},
            {"id": 3, "date_col": "2022-01-02"},
        ]
        df = pd.DataFrame(datas)
        parser = get_parser(df, infer_string_to_date=True)
        date_field = next(f for f in parser.raw_fields if f["fid"] == "date_col")
        assert date_field["semanticType"] == "temporal"

    def test_parser_regular_strings_not_mistaken_for_dates(self):
        """Regular strings should remain nominal."""
        datas = [
            {"id": 1, "category": "A"},
            {"id": 2, "category": "B"},
            {"id": 3, "category": "C"},
        ]
        df = pd.DataFrame(datas)
        parser = get_parser(df)
        cat_field = next(f for f in parser.raw_fields if f["fid"] == "category")
        assert cat_field["semanticType"] == "nominal"

    def test_parser_numeric_strings_not_mistaken_for_dates(self):
        """Numeric strings should remain quantitative or nominal, not temporal."""
        datas = [
            {"id": 1, "code": "12345"},
            {"id": 2, "code": "67890"},
            {"id": 3, "code": "11111"},
        ]
        df = pd.DataFrame(datas)
        parser = get_parser(df)
        code_field = next(f for f in parser.raw_fields if f["fid"] == "code")
        assert code_field["semanticType"] != "temporal"

    def test_parser_pandas_datetime_type(self):
        """Pandas datetime columns should be identified as temporal."""
        datas = {"id": [1, 2], "value": [10, 20]}
        df = pd.DataFrame(datas)
        df["date_col"] = pd.to_datetime(["2022-01-01", "2022-01-02"])
        parser = get_parser(df)
        date_field = next(f for f in parser.raw_fields if f["fid"] == "date_col")
        assert date_field["semanticType"] == "temporal"

    def test_parser_default_infer_string_to_date_false(self):
        """With default (infer_string_to_date=False), date strings should remain nominal."""
        datas = [
            {"id": 1, "date_col": "2022-01-01"},
            {"id": 2, "date_col": "2022-01-02"},
        ]
        df = pd.DataFrame(datas)
        parser = get_parser(df)
        date_field = next(f for f in parser.raw_fields if f["fid"] == "date_col")
        assert date_field["semanticType"] == "nominal"

    def test_parser_explicit_infer_string_to_date_true(self):
        """With infer_string_to_date=True, date strings should be identified as temporal."""
        datas = [
            {"id": 1, "date_col": "2022-01-01"},
            {"id": 2, "date_col": "2022-01-02"},
        ]
        df = pd.DataFrame(datas)
        parser = get_parser(df, infer_string_to_date=True)
        date_field = next(f for f in parser.raw_fields if f["fid"] == "date_col")
        assert date_field["semanticType"] == "temporal"


MODIN_AVAILABLE = False
try:
    from modin import pandas as mpd
    MODIN_AVAILABLE = True
except ImportError:
    pass


class TestParserConsistency:
    """Regression tests: pandas, polars, modin must produce identical field inference."""

    reference_datas = [
        {"name": "A", "category": 1, "date_str": "2022-01-01", "latitude": 37.77, "longitude": -122.42, "small_int": 1, "price": 100.0},
        {"name": "B", "category": 2, "date_str": "2022-01-02", "latitude": 40.71, "longitude": -74.00, "small_int": 2, "price": 200.0},
        {"name": "C", "category": 3, "date_str": "2022-01-03", "latitude": 41.88, "longitude": -87.63, "small_int": 3, "price": 300.0},
        {"name": "D", "category": 1, "date_str": "2022-01-04", "latitude": 34.05, "longitude": -118.24, "small_int": 1, "price": 400.0},
    ]

    expected_fields = {
        "name": {"semanticType": "nominal", "analyticType": "dimension"},
        "category": {"semanticType": "quantitative", "analyticType": "dimension"},
        "date_str": {"semanticType": "temporal", "analyticType": "dimension"},
        "latitude": {"semanticType": "quantitative", "analyticType": "dimension"},
        "longitude": {"semanticType": "quantitative", "analyticType": "dimension"},
        "small_int": {"semanticType": "quantitative", "analyticType": "dimension"},
        "price": {"semanticType": "quantitative", "analyticType": "measure"},
    }

    def _assert_fields_match(self, fields, expected):
        for f in fields:
            fid = f["fid"]
            assert f["semanticType"] == expected[fid]["semanticType"], f"{fid} semanticType mismatch"
            assert f["analyticType"] == expected[fid]["analyticType"], f"{fid} analyticType mismatch"

    def _get_inference(self, parser):
        return {f["fid"]: {"semanticType": f["semanticType"], "analyticType": f["analyticType"]} for f in parser.raw_fields}

    def test_pandas_field_inference(self):
        """pandas: date string -> temporal, geo fields -> dimension, small integer -> dimension."""
        df = pd.DataFrame(self.reference_datas)
        parser = get_parser(df, infer_string_to_date=True, infer_number_to_dimension=True)
        self._assert_fields_match(parser.raw_fields, self.expected_fields)

    def test_polars_field_inference(self):
        """polars: date string -> temporal, geo fields -> dimension, small integer -> dimension."""
        df = pl.DataFrame(self.reference_datas)
        parser = get_parser(df, infer_string_to_date=True, infer_number_to_dimension=True)
        self._assert_fields_match(parser.raw_fields, self.expected_fields)

    @pytest.mark.skipif(not MODIN_AVAILABLE, reason="modin not installed")
    def test_modin_field_inference(self):
        """modin: date string -> temporal, geo fields -> dimension, small integer -> dimension."""
        df = mpd.DataFrame(self.reference_datas)
        parser = get_parser(df, infer_string_to_date=True, infer_number_to_dimension=True)
        self._assert_fields_match(parser.raw_fields, self.expected_fields)

    def test_pandas_vs_polars_consistency(self):
        """pandas and polars must agree on every field."""
        pdf = pd.DataFrame(self.reference_datas)
        pldf = pl.DataFrame(self.reference_datas)
        p1 = get_parser(pdf, infer_string_to_date=True, infer_number_to_dimension=True)
        p2 = get_parser(pldf, infer_string_to_date=True, infer_number_to_dimension=True)
        assert self._get_inference(p1) == self._get_inference(p2)

    @pytest.mark.skipif(not MODIN_AVAILABLE, reason="modin not installed")
    def test_pandas_vs_modin_consistency(self):
        """pandas and modin must agree on every field."""
        pdf = pd.DataFrame(self.reference_datas)
        mdf = mpd.DataFrame(self.reference_datas)
        p1 = get_parser(pdf, infer_string_to_date=True, infer_number_to_dimension=True)
        p2 = get_parser(mdf, infer_string_to_date=True, infer_number_to_dimension=True)
        assert self._get_inference(p1) == self._get_inference(p2)

    @pytest.mark.skipif(not MODIN_AVAILABLE, reason="modin not installed")
    def test_pandas_polars_modin_all_consistent(self):
        """pandas, polars, modin all three must produce identical field inference."""
        pdf = pd.DataFrame(self.reference_datas)
        pldf = pl.DataFrame(self.reference_datas)
        mdf = mpd.DataFrame(self.reference_datas)
        p_pandas = get_parser(pdf, infer_string_to_date=True, infer_number_to_dimension=True)
        p_polars = get_parser(pldf, infer_string_to_date=True, infer_number_to_dimension=True)
        p_modin = get_parser(mdf, infer_string_to_date=True, infer_number_to_dimension=True)
        pandas_infer = self._get_inference(p_pandas)
        assert self._get_inference(p_polars) == pandas_infer
        assert self._get_inference(p_modin) == pandas_infer


class TestOutlierHandling:
    """Regression tests: outlier/exception sample handling across parsers."""

    def test_pandas_none_values_skipped(self):
        """None values should be skipped when inferring date strings."""
        datas = [
            {"id": 1, "date_col": None},
            {"id": 2, "date_col": None},
            {"id": 3, "date_col": "2022-01-01"},
            {"id": 4, "date_col": "2022-01-02"},
        ]
        df = pd.DataFrame(datas)
        parser = get_parser(df, infer_string_to_date=True)
        date_field = next(f for f in parser.raw_fields if f["fid"] == "date_col")
        assert date_field["semanticType"] == "temporal"

    def test_polars_none_values_skipped(self):
        """None values should be skipped when inferring date strings."""
        datas = [
            {"id": 1, "date_col": None},
            {"id": 2, "date_col": None},
            {"id": 3, "date_col": "2022-01-01"},
            {"id": 4, "date_col": "2022-01-02"},
        ]
        df = pl.DataFrame(datas)
        parser = get_parser(df, infer_string_to_date=True)
        date_field = next(f for f in parser.raw_fields if f["fid"] == "date_col")
        assert date_field["semanticType"] == "temporal"

    @pytest.mark.skipif(not MODIN_AVAILABLE, reason="modin not installed")
    def test_modin_none_values_skipped(self):
        """None values should be skipped when inferring date strings."""
        datas = [
            {"id": 1, "date_col": None},
            {"id": 2, "date_col": None},
            {"id": 3, "date_col": "2022-01-01"},
            {"id": 4, "date_col": "2022-01-02"},
        ]
        df = mpd.DataFrame(datas)
        parser = get_parser(df, infer_string_to_date=True)
        date_field = next(f for f in parser.raw_fields if f["fid"] == "date_col")
        assert date_field["semanticType"] == "temporal"

    def test_pandas_empty_strings_skipped(self):
        """Empty strings should be skipped when inferring date strings."""
        datas = [
            {"id": 1, "date_col": ""},
            {"id": 2, "date_col": "   "},
            {"id": 3, "date_col": "2022-01-01"},
            {"id": 4, "date_col": "2022-01-02"},
        ]
        df = pd.DataFrame(datas)
        parser = get_parser(df, infer_string_to_date=True)
        date_field = next(f for f in parser.raw_fields if f["fid"] == "date_col")
        assert date_field["semanticType"] == "temporal"

    def test_polars_empty_strings_skipped(self):
        """Empty strings should be skipped when inferring date strings."""
        datas = [
            {"id": 1, "date_col": ""},
            {"id": 2, "date_col": "   "},
            {"id": 3, "date_col": "2022-01-01"},
            {"id": 4, "date_col": "2022-01-02"},
        ]
        df = pl.DataFrame(datas)
        parser = get_parser(df, infer_string_to_date=True)
        date_field = next(f for f in parser.raw_fields if f["fid"] == "date_col")
        assert date_field["semanticType"] == "temporal"

    @pytest.mark.skipif(not MODIN_AVAILABLE, reason="modin not installed")
    def test_modin_empty_strings_skipped(self):
        """Empty strings should be skipped when inferring date strings."""
        datas = [
            {"id": 1, "date_col": ""},
            {"id": 2, "date_col": "   "},
            {"id": 3, "date_col": "2022-01-01"},
            {"id": 4, "date_col": "2022-01-02"},
        ]
        df = mpd.DataFrame(datas)
        parser = get_parser(df, infer_string_to_date=True)
        date_field = next(f for f in parser.raw_fields if f["fid"] == "date_col")
        assert date_field["semanticType"] == "temporal"

    def test_pandas_invalid_dates_not_mistaken(self):
        """Invalid date strings should not cause field to be marked as temporal."""
        datas = [
            {"id": 1, "date_col": "not-a-date"},
            {"id": 2, "date_col": "hello"},
            {"id": 3, "date_col": "12345"},
        ]
        df = pd.DataFrame(datas)
        parser = get_parser(df, infer_string_to_date=True)
        date_field = next(f for f in parser.raw_fields if f["fid"] == "date_col")
        assert date_field["semanticType"] == "nominal"

    def test_polars_invalid_dates_not_mistaken(self):
        """Invalid date strings should not cause field to be marked as temporal."""
        datas = [
            {"id": 1, "date_col": "not-a-date"},
            {"id": 2, "date_col": "hello"},
            {"id": 3, "date_col": "12345"},
        ]
        df = pl.DataFrame(datas)
        parser = get_parser(df, infer_string_to_date=True)
        date_field = next(f for f in parser.raw_fields if f["fid"] == "date_col")
        assert date_field["semanticType"] == "nominal"

    @pytest.mark.skipif(not MODIN_AVAILABLE, reason="modin not installed")
    def test_modin_invalid_dates_not_mistaken(self):
        """Invalid date strings should not cause field to be marked as temporal."""
        datas = [
            {"id": 1, "date_col": "not-a-date"},
            {"id": 2, "date_col": "hello"},
            {"id": 3, "date_col": "12345"},
        ]
        df = mpd.DataFrame(datas)
        parser = get_parser(df, infer_string_to_date=True)
        date_field = next(f for f in parser.raw_fields if f["fid"] == "date_col")
        assert date_field["semanticType"] == "nominal"

    def test_pandas_mixed_outliers_with_valid_dates(self):
        """Mixed outliers (None, empty strings, invalid dates) should not prevent valid date detection."""
        datas = [
            {"id": 1, "date_col": None},
            {"id": 2, "date_col": ""},
            {"id": 3, "date_col": "   "},
            {"id": 4, "date_col": "not-a-date"},
            {"id": 5, "date_col": "2022-01-01"},
            {"id": 6, "date_col": "2022-01-02"},
        ]
        df = pd.DataFrame(datas)
        parser = get_parser(df, infer_string_to_date=True)
        date_field = next(f for f in parser.raw_fields if f["fid"] == "date_col")
        assert date_field["semanticType"] == "temporal"

    def test_polars_mixed_outliers_with_valid_dates(self):
        """Mixed outliers (None, empty strings, invalid dates) should not prevent valid date detection."""
        datas = [
            {"id": 1, "date_col": None},
            {"id": 2, "date_col": ""},
            {"id": 3, "date_col": "   "},
            {"id": 4, "date_col": "not-a-date"},
            {"id": 5, "date_col": "2022-01-01"},
            {"id": 6, "date_col": "2022-01-02"},
        ]
        df = pl.DataFrame(datas)
        parser = get_parser(df, infer_string_to_date=True)
        date_field = next(f for f in parser.raw_fields if f["fid"] == "date_col")
        assert date_field["semanticType"] == "temporal"

    @pytest.mark.skipif(not MODIN_AVAILABLE, reason="modin not installed")
    def test_modin_mixed_outliers_with_valid_dates(self):
        """Mixed outliers (None, empty strings, invalid dates) should not prevent valid date detection."""
        datas = [
            {"id": 1, "date_col": None},
            {"id": 2, "date_col": ""},
            {"id": 3, "date_col": "   "},
            {"id": 4, "date_col": "not-a-date"},
            {"id": 5, "date_col": "2022-01-01"},
            {"id": 6, "date_col": "2022-01-02"},
        ]
        df = mpd.DataFrame(datas)
        parser = get_parser(df, infer_string_to_date=True)
        date_field = next(f for f in parser.raw_fields if f["fid"] == "date_col")
        assert date_field["semanticType"] == "temporal"

    def test_pandas_polars_outlier_handling_consistency(self):
        """pandas and polars must handle outliers identically."""
        datas = [
            {"id": 1, "date_col": None},
            {"id": 2, "date_col": ""},
            {"id": 3, "date_col": "not-a-date"},
            {"id": 4, "date_col": "2022-01-01"},
        ]
        pdf = pd.DataFrame(datas)
        pldf = pl.DataFrame(datas)
        p1 = get_parser(pdf, infer_string_to_date=True)
        p2 = get_parser(pldf, infer_string_to_date=True)
        p1_infer = {f["fid"]: {"semanticType": f["semanticType"], "analyticType": f["analyticType"]} for f in p1.raw_fields}
        p2_infer = {f["fid"]: {"semanticType": f["semanticType"], "analyticType": f["analyticType"]} for f in p2.raw_fields}
        assert p1_infer == p2_infer
