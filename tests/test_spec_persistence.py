"""Regression tests for spec persistence.

This test verifies that when a chart config is saved and reloaded:
1. Dimension fields are preserved
2. Measure fields are preserved
3. Aggregation methods (aggName) are preserved
4. Encoding channels (rows, columns, color, etc.) are preserved
5. Field properties (analyticType, semanticType) are preserved
"""
import pytest
from copy import deepcopy

from pygwalker.services.spec import fill_new_fields


@pytest.fixture
def sample_spec():
    """Create a realistic sample spec that mimics what graphic-walker exports"""
    return [{
        "config": {
            "defaultAggregated": True,
            "geoms": ["bar"],
            "coordSystem": "generic",
            "limit": -1,
            "timezoneDisplayOffset": 0
        },
        "encodings": {
            "dimensions": [
                {
                    "dragId": "gw_d0SN",
                    "fid": "category",
                    "name": "Category",
                    "basename": "Category",
                    "semanticType": "nominal",
                    "analyticType": "dimension",
                    "offset": 0
                },
                {
                    "dragId": "gw_fCVU",
                    "fid": "subcategory",
                    "name": "Subcategory",
                    "basename": "Subcategory",
                    "semanticType": "nominal",
                    "analyticType": "dimension",
                    "offset": 0
                }
            ],
            "measures": [
                {
                    "dragId": "gw_oE-g",
                    "fid": "sales",
                    "name": "Sales",
                    "basename": "Sales",
                    "analyticType": "measure",
                    "semanticType": "quantitative",
                    "aggName": "sum",
                    "offset": 0
                },
                {
                    "dragId": "gw_LZNz",
                    "fid": "profit",
                    "name": "Profit",
                    "basename": "Profit",
                    "analyticType": "measure",
                    "semanticType": "quantitative",
                    "aggName": "avg",
                    "offset": 0
                },
                {
                    "dragId": "gw_count_fid",
                    "fid": "gw_count_fid",
                    "name": "Row count",
                    "analyticType": "measure",
                    "semanticType": "quantitative",
                    "aggName": "sum",
                    "computed": True,
                    "expression": {"op": "one", "params": [], "as": "gw_count_fid"},
                    "offset": 0
                }
            ],
            "rows": [
                {
                    "dragId": "gw_XI5j",
                    "fid": "sales",
                    "name": "Sales",
                    "basename": "Sales",
                    "analyticType": "measure",
                    "semanticType": "quantitative",
                    "aggName": "sum",
                    "offset": 0
                }
            ],
            "columns": [
                {
                    "dragId": "gw_d0SN",
                    "fid": "category",
                    "name": "Category",
                    "basename": "Category",
                    "semanticType": "nominal",
                    "analyticType": "dimension",
                    "offset": 0
                }
            ],
            "color": [
                {
                    "dragId": "gw_fCVU",
                    "fid": "subcategory",
                    "name": "Subcategory",
                    "basename": "Subcategory",
                    "semanticType": "nominal",
                    "analyticType": "dimension",
                    "offset": 0
                }
            ],
            "opacity": [],
            "size": [],
            "shape": [],
            "radius": [],
            "theta": [],
            "longitude": [],
            "latitude": [],
            "geoId": [],
            "details": [],
            "filters": [
                {
                    "dragId": "gw_U38p",
                    "fid": "sales",
                    "name": "Sales",
                    "basename": "Sales",
                    "analyticType": "measure",
                    "semanticType": "quantitative",
                    "aggName": "sum",
                    "rule": {"type": "range", "value": [0, 10000]},
                    "offset": 0
                }
            ],
            "text": []
        },
        "layout": {
            "showActions": False,
            "showTableSummary": False,
            "stack": "stack",
            "size": {"mode": "fixed", "width": 350, "height": 345}
        },
        "visId": "gw_test123",
        "name": "Sales by Category"
    }]


@pytest.fixture
def all_fields():
    """Create all fields from the data source (same schema as saved spec)"""
    return [
        {"fid": "category", "name": "Category", "analyticType": "dimension", "semanticType": "nominal"},
        {"fid": "subcategory", "name": "Subcategory", "analyticType": "dimension", "semanticType": "nominal"},
        {"fid": "sales", "name": "Sales", "analyticType": "measure", "semanticType": "quantitative"},
        {"fid": "profit", "name": "Profit", "analyticType": "measure", "semanticType": "quantitative"}
    ]


class TestDimensionPreservation:
    """Tests for dimension field preservation"""
    
    def test_dimensions_preserved(self, sample_spec, all_fields):
        """Test: Dimension fields are preserved after reload"""
        result = fill_new_fields(deepcopy(sample_spec), all_fields)
        
        orig_dims = {f["fid"]: f for f in sample_spec[0]["encodings"]["dimensions"]}
        result_dims = {f["fid"]: f for f in result[0]["encodings"]["dimensions"]}
        
        for fid in ["category", "subcategory"]:
            assert fid in result_dims, f"Dimension '{fid}' should be preserved"
            
            result_field = result_dims[fid]
            orig_field = orig_dims[fid]
            
            assert result_field["analyticType"] == orig_field["analyticType"], \
                f"Dimension '{fid}' analyticType should match"
            assert result_field["semanticType"] == orig_field["semanticType"], \
                f"Dimension '{fid}' semanticType should match"
            assert result_field["name"] == orig_field["name"], \
                f"Dimension '{fid}' name should match"


class TestMeasurePreservation:
    """Tests for measure field preservation"""
    
    def test_measures_preserved(self, sample_spec, all_fields):
        """Test: Measure fields are preserved after reload"""
        result = fill_new_fields(deepcopy(sample_spec), all_fields)
        
        orig_meas = {f["fid"]: f for f in sample_spec[0]["encodings"]["measures"]}
        result_meas = {f["fid"]: f for f in result[0]["encodings"]["measures"]}
        
        for fid in ["sales", "profit"]:
            assert fid in result_meas, f"Measure '{fid}' should be preserved"
            
            result_field = result_meas[fid]
            orig_field = orig_meas[fid]
            
            assert result_field["analyticType"] == orig_field["analyticType"], \
                f"Measure '{fid}' analyticType should match"
            assert result_field["semanticType"] == orig_field["semanticType"], \
                f"Measure '{fid}' semanticType should match"
    
    def test_aggregation_preserved(self, sample_spec, all_fields):
        """Test: Aggregation methods (aggName) are preserved after reload"""
        result = fill_new_fields(deepcopy(sample_spec), all_fields)
        
        orig_meas = {f["fid"]: f for f in sample_spec[0]["encodings"]["measures"]}
        result_meas = {f["fid"]: f for f in result[0]["encodings"]["measures"]}
        
        assert result_meas["sales"]["aggName"] == "sum", \
            f"sales aggName should be 'sum', got '{result_meas['sales'].get('aggName')}'"
        assert result_meas["profit"]["aggName"] == "avg", \
            f"profit aggName should be 'avg', got '{result_meas['profit'].get('aggName')}'"
        
        assert result_meas["sales"]["aggName"] == orig_meas["sales"]["aggName"], \
            "sales aggName should match original"
        assert result_meas["profit"]["aggName"] == orig_meas["profit"]["aggName"], \
            "profit aggName should match original"


class TestEncodingChannelPreservation:
    """Tests for encoding channel preservation"""
    
    def test_encoding_channels_preserved(self, sample_spec, all_fields):
        """Test: Encoding channels (rows, columns, color, filters) are preserved after reload"""
        result = fill_new_fields(deepcopy(sample_spec), all_fields)
        
        encodings = result[0]["encodings"]
        
        assert len(encodings["rows"]) == 1, "rows should have 1 field"
        assert encodings["rows"][0]["fid"] == "sales", "rows[0] should be 'sales'"
        
        assert len(encodings["columns"]) == 1, "columns should have 1 field"
        assert encodings["columns"][0]["fid"] == "category", "columns[0] should be 'category'"
        
        assert len(encodings["color"]) == 1, "color should have 1 field"
        assert encodings["color"][0]["fid"] == "subcategory", "color[0] should be 'subcategory'"
        
        assert len(encodings["filters"]) == 1, "filters should have 1 field"
        assert encodings["filters"][0]["fid"] == "sales", "filters[0] should be 'sales'"
        assert encodings["filters"][0]["aggName"] == "sum", "filters[0] aggName should be 'sum'"
    
    def test_encoding_channels_field_properties_updated(self, sample_spec, all_fields):
        """Test: Field properties in encoding channels are updated from current data source"""
        all_fields_updated = deepcopy(all_fields)
        all_fields_updated[0]["semanticType"] = "ordinal"
        
        result = fill_new_fields(deepcopy(sample_spec), all_fields_updated)
        
        encodings = result[0]["encodings"]
        
        assert encodings["columns"][0]["semanticType"] == "ordinal", \
            f"columns semanticType should be updated to 'ordinal', got '{encodings['columns'][0]['semanticType']}'"


class TestComputedFields:
    """Tests for computed fields"""
    
    def test_computed_fields_not_modified(self, sample_spec, all_fields):
        """Test: Computed fields (Row count, etc.) are not modified"""
        result = fill_new_fields(deepcopy(sample_spec), all_fields)
        
        orig_meas = {f["fid"]: f for f in sample_spec[0]["encodings"]["measures"]}
        result_meas = {f["fid"]: f for f in result[0]["encodings"]["measures"]}
        
        computed_field = result_meas["gw_count_fid"]
        orig_computed = orig_meas["gw_count_fid"]
        
        assert computed_field["computed"] == True, "Computed field should remain computed"
        assert computed_field["expression"] == orig_computed["expression"], \
            "Computed field expression should not be modified"
        assert computed_field["aggName"] == orig_computed["aggName"], \
            "Computed field aggName should be preserved"


class TestNewFields:
    """Tests for new field addition"""
    
    def test_new_fields_added(self, sample_spec, all_fields):
        """Test: New fields from data source are added to dimensions/measures"""
        all_fields_with_new = deepcopy(all_fields)
        all_fields_with_new.append({
            "fid": "quantity", 
            "name": "Quantity", 
            "analyticType": "measure", 
            "semanticType": "quantitative"
        })
        all_fields_with_new.append({
            "fid": "region", 
            "name": "Region", 
            "analyticType": "dimension", 
            "semanticType": "nominal"
        })
        
        result = fill_new_fields(deepcopy(sample_spec), all_fields_with_new)
        
        result_dims = {f["fid"]: f for f in result[0]["encodings"]["dimensions"]}
        result_meas = {f["fid"]: f for f in result[0]["encodings"]["measures"]}
        
        assert "region" in result_dims, "New dimension 'region' should be added"
        assert "quantity" in result_meas, "New measure 'quantity' should be added"
        
        assert "basename" in result_dims["region"], "New field should have basename"
        assert "dragId" in result_dims["region"], "New field should have dragId"


class TestRoundtrip:
    """Complete roundtrip tests"""
    
    def test_roundtrip_preservation(self, sample_spec, all_fields):
        """Test: Complete save -> reload roundtrip"""
        saved_spec = sample_spec
        current_data_fields = all_fields
        
        loaded_spec = fill_new_fields(deepcopy(saved_spec), current_data_fields)
        
        encodings = loaded_spec[0]["encodings"]
        
        dim_fids = [f["fid"] for f in encodings["dimensions"]]
        meas_fids = [f["fid"] for f in encodings["measures"]]
        
        assert "category" in dim_fids, "category should be in dimensions"
        assert "subcategory" in dim_fids, "subcategory should be in dimensions"
        assert "sales" in meas_fids, "sales should be in measures"
        assert "profit" in meas_fids, "profit should be in measures"
        assert "gw_count_fid" in meas_fids, "gw_count_fid should be in measures"
        
        row_fids = [f["fid"] for f in encodings["rows"]]
        col_fids = [f["fid"] for f in encodings["columns"]]
        color_fids = [f["fid"] for f in encodings["color"]]
        filter_fids = [f["fid"] for f in encodings["filters"]]
        
        assert "sales" in row_fids, "sales should be in rows"
        assert "category" in col_fids, "category should be in columns"
        assert "subcategory" in color_fids, "subcategory should be in color"
        assert "sales" in filter_fids, "sales should be in filters"
        
        sales_in_rows = next(f for f in encodings["rows"] if f["fid"] == "sales")
        assert sales_in_rows["aggName"] == "sum", "sales in rows should have aggName=sum"
