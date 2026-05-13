"""Tests for spec_pipeline module - full spec loading and saving pipeline."""
import pytest
import json
from copy import deepcopy

from pygwalker.services.spec_pipeline import load_spec, save_spec, _normalize_spec_obj
from pygwalker.services.field_completion import (
    fill_new_fields,
    update_field_properties,
    extract_existing_fids,
    collect_new_fields,
    update_encoding_channels,
    ENCODING_CHANNELS
)
from pygwalker.services.version_compatibility import (
    apply_version_compatibility,
    create_spec_for_save,
    VERSION_ADAPTERS,
    Adapter_0_4_7a5,
)


@pytest.fixture
def sample_gw_spec():
    """Create a sample graphic-walker spec with multiple charts."""
    return [
        {
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
                "color": [],
                "opacity": [],
                "size": [],
                "shape": [],
                "radius": [],
                "theta": [],
                "longitude": [],
                "latitude": [],
                "geoId": [],
                "details": [],
                "filters": [],
                "text": []
            },
            "layout": {
                "showActions": False,
                "showTableSummary": False,
                "stack": "stack",
                "size": {"mode": "fixed", "width": 350, "height": 345}
            },
            "visId": "gw_chart1",
            "name": "Sales by Category"
        },
        {
            "config": {
                "defaultAggregated": True,
                "geoms": ["line"],
                "coordSystem": "generic",
                "limit": -1,
                "timezoneDisplayOffset": 0
            },
            "encodings": {
                "dimensions": [
                    {
                        "dragId": "gw_abc1",
                        "fid": "date",
                        "name": "Date",
                        "basename": "Date",
                        "semanticType": "temporal",
                        "analyticType": "dimension",
                        "offset": 0
                    }
                ],
                "measures": [
                    {
                        "dragId": "gw_def2",
                        "fid": "profit",
                        "name": "Profit",
                        "basename": "Profit",
                        "analyticType": "measure",
                        "semanticType": "quantitative",
                        "aggName": "avg",
                        "offset": 0
                    }
                ],
                "rows": [
                    {
                        "dragId": "gw_def2",
                        "fid": "profit",
                        "name": "Profit",
                        "basename": "Profit",
                        "analyticType": "measure",
                        "semanticType": "quantitative",
                        "aggName": "avg",
                        "offset": 0
                    }
                ],
                "columns": [
                    {
                        "dragId": "gw_abc1",
                        "fid": "date",
                        "name": "Date",
                        "basename": "Date",
                        "semanticType": "temporal",
                        "analyticType": "dimension",
                        "offset": 0
                    }
                ],
                "color": [],
                "opacity": [],
                "size": [],
                "shape": [],
                "radius": [],
                "theta": [],
                "longitude": [],
                "latitude": [],
                "geoId": [],
                "details": [],
                "filters": [],
                "text": []
            },
            "layout": {
                "showActions": False,
                "showTableSummary": False,
                "stack": "stack",
                "size": {"mode": "fixed", "width": 350, "height": 345}
            },
            "visId": "gw_chart2",
            "name": "Profit over Time"
        }
    ]


@pytest.fixture
def sample_fields():
    """Create sample field definitions."""
    return [
        {"fid": "category", "name": "Category", "analyticType": "dimension", "semanticType": "nominal"},
        {"fid": "date", "name": "Date", "analyticType": "dimension", "semanticType": "temporal"},
        {"fid": "sales", "name": "Sales", "analyticType": "measure", "semanticType": "quantitative"},
        {"fid": "profit", "name": "Profit", "analyticType": "measure", "semanticType": "quantitative"}
    ]


class TestFieldCompletion:
    """Tests for field_completion module."""
    
    def test_update_field_properties_preserves_aggregation(self, sample_fields):
        """Test: update_field_properties preserves aggregation methods."""
        all_fields_map = {f["fid"]: f for f in sample_fields}
        
        field = {
            "fid": "sales",
            "name": "Old Name",
            "analyticType": "measure",
            "semanticType": "quantitative",
            "aggName": "sum"
        }
        
        result = update_field_properties(field, all_fields_map)
        
        assert result["aggName"] == "sum", "aggName should be preserved"
        assert result["name"] == "Sales", "name should be updated from source"
        assert result["basename"] == "Sales", "basename should be set"
    
    def test_update_field_properties_skips_computed_fields(self):
        """Test: computed fields are not modified."""
        all_fields_map = {}
        
        computed_field = {
            "fid": "gw_count_fid",
            "name": "Row count",
            "analyticType": "measure",
            "semanticType": "quantitative",
            "aggName": "sum",
            "computed": True,
            "expression": {"op": "one", "params": [], "as": "gw_count_fid"},
            "offset": 0
        }
        
        result = update_field_properties(computed_field, all_fields_map)
        
        assert result["computed"] == True
        assert result["expression"] == computed_field["expression"]
        assert result["aggName"] == "sum"
    
    def test_extract_existing_fids(self, sample_gw_spec):
        """Test: extract_existing_fids correctly extracts fid from dimensions and measures."""
        chart1 = sample_gw_spec[0]
        fids = extract_existing_fids(chart1)
        
        assert "category" in fids
        assert "sales" in fids
        assert len(fids) == 2
    
    def test_collect_new_fields_dimensions_and_measures(self, sample_fields):
        """Test: collect_new_fields correctly separates new dimensions and measures."""
        existing_fids = {"category", "sales"}
        
        result = collect_new_fields(sample_fields, existing_fids)
        
        dimension_fids = [f["fid"] for f in result["dimensions"]]
        measure_fids = [f["fid"] for f in result["measures"]]
        
        assert "date" in dimension_fids, "date should be in new dimensions"
        assert "profit" in measure_fids, "profit should be in new measures"
        assert all("dragId" in f for f in result["dimensions"])
        assert all("basename" in f for f in result["measures"])
    
    def test_fill_new_fields_preserves_chart_order(self, sample_gw_spec, sample_fields):
        """Test: fill_new_fields preserves the order of charts."""
        result = fill_new_fields(deepcopy(sample_gw_spec), sample_fields)
        
        assert len(result) == 2
        assert result[0]["name"] == "Sales by Category"
        assert result[1]["name"] == "Profit over Time"
    
    def test_fill_new_fields_preserves_encoding_channels(self, sample_gw_spec, sample_fields):
        """Test: fill_new_fields preserves encoding channel configurations."""
        result = fill_new_fields(deepcopy(sample_gw_spec), sample_fields)
        
        chart1 = result[0]
        assert chart1["encodings"]["rows"][0]["fid"] == "sales"
        assert chart1["encodings"]["columns"][0]["fid"] == "category"
        assert chart1["encodings"]["rows"][0]["aggName"] == "sum"


class TestVersionCompatibility:
    """Tests for version_compatibility module."""
    
    def test_adapter_0_4_7a5_adds_timezone_offset(self):
        """Test: Adapter_0_4_7a5 adds timezoneDisplayOffset if missing."""
        spec_obj = {
            "version": "0.4.0",
            "config": [
                {
                    "config": {"defaultAggregated": True},
                    "encodings": {"dimensions": [], "measures": []},
                    "visId": "test"
                }
            ]
        }
        
        result = apply_version_compatibility(spec_obj)
        
        assert result["config"][0]["config"]["timezoneDisplayOffset"] == 0
    
    def test_adapter_0_4_7a5_adds_offset_to_fields(self):
        """Test: Adapter_0_4_7a5 adds offset=0 to all fields."""
        spec_obj = {
            "version": "0.4.0",
            "config": [
                {
                    "config": {"timezoneDisplayOffset": 0},
                    "encodings": {
                        "dimensions": [{"fid": "a", "name": "A"}],
                        "measures": [{"fid": "b", "name": "B"}]
                    },
                    "visId": "test"
                }
            ]
        }
        
        result = apply_version_compatibility(spec_obj)
        
        assert result["config"][0]["encodings"]["dimensions"][0]["offset"] == 0
        assert result["config"][0]["encodings"]["measures"][0]["offset"] == 0
    
    def test_adapter_not_applied_for_newer_versions(self):
        """Test: adapters are not applied for versions newer than threshold."""
        spec_obj = {
            "version": "1.0.0",
            "config": [
                {
                    "config": {"defaultAggregated": True},
                    "encodings": {
                        "dimensions": [{"fid": "a", "name": "A"}],
                        "measures": []
                    },
                    "visId": "test"
                }
            ]
        }
        
        result = apply_version_compatibility(spec_obj)
        
        assert "timezoneDisplayOffset" not in result["config"][0]["config"]
        assert "offset" not in result["config"][0]["encodings"]["dimensions"][0]


class TestSpecPipeline:
    """Tests for spec_pipeline module."""
    
    def test_normalize_gw_config_list(self, sample_gw_spec):
        """Test: list of gw configs is normalized correctly."""
        result, spec_type = _normalize_spec_obj(sample_gw_spec, "json_obj")
        
        assert spec_type == "gw_list"
        assert result["chart_map"] == {}
        assert result["workflow_list"] == []
        assert result["config"] == sample_gw_spec
    
    def test_normalize_vega_single(self):
        """Test: single vega config dict is normalized correctly."""
        vega_spec = {
            "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
            "mark": "bar",
            "encoding": {}
        }
        
        result, spec_type = _normalize_spec_obj(vega_spec, "json_obj")
        
        assert spec_type == "vega_single"
        assert result["config"] == [vega_spec]
    
    def test_save_spec_creates_standard_format(self, sample_gw_spec):
        """Test: save_spec creates spec in standard format."""
        result = save_spec(
            vis_spec=sample_gw_spec,
            chart_map={},
            workflow_list=[]
        )
        
        assert "config" in result
        assert "chart_map" in result
        assert "version" in result
        assert "workflow_list" in result
        assert result["config"] == sample_gw_spec


class TestLoadSpec:
    """Tests for load_spec function."""
    
    def test_load_empty_string(self, sample_fields):
        """Test: load_spec handles empty string correctly."""
        result, spec_type = load_spec("", sample_fields)
        
        assert spec_type == "empty_string"
        assert result["config"] == []
        assert result["chart_map"] == {}
    
    def test_load_gw_config_list(self, sample_gw_spec, sample_fields):
        """Test: load_spec processes gw config list with field completion."""
        result, spec_type = load_spec(sample_gw_spec, sample_fields)
        
        assert spec_type == "gw_list"
        assert len(result["config"]) == 2
        assert "dimensions" in result["config"][0]["encodings"]
        assert "measures" in result["config"][0]["encodings"]
    
    def test_load_vega_list_skips_field_completion(self, sample_fields):
        """Test: load_spec skips field completion for vega specs."""
        vega_list = [
            {
                "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
                "mark": "bar",
                "encoding": {}
            }
        ]
        
        result, spec_type = load_spec(vega_list, sample_fields)
        
        assert spec_type == "vega_list"
        assert result["config"] == vega_list
