"""
Test cases for RecommendationExplainer service.
Covers:
1. Chart type explanation
2. Field type explanation
3. Aggregation explanation
4. Visual encoding explanation
"""

import pytest
import sys
import os
import json
import importlib.util

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
INTEGRATION_DIR = os.path.dirname(TEST_DIR)
PROJECT_DIR = os.path.dirname(INTEGRATION_DIR)

module_path = os.path.join(PROJECT_DIR, "pygwalker", "services", "recommendation_explainer.py")
spec = importlib.util.spec_from_file_location("recommendation_explainer", module_path)
module = importlib.util.module_from_spec(spec)
sys.modules["recommendation_explainer"] = module
spec.loader.exec_module(module)

RecommendationExplainer = module.RecommendationExplainer
ChartType = module.ChartType
VisualEncodingType = module.VisualEncodingType
AggregationType = module.AggregationType


class TestRecommendationExplainer:
    """Test suite for RecommendationExplainer."""

    @pytest.fixture
    def sample_field_qualities(self):
        """Create sample field qualities for testing."""
        return {
            "category": {
                "fid": "category",
                "missingRate": 0.0,
                "uniqueCount": 5,
                "distinctRate": 0.2,
                "dataType": "string",
                "distribution": {
                    "type": "string",
                    "topValues": [
                        {"value": "A", "count": 100},
                        {"value": "B", "count": 80},
                        {"value": "C", "count": 60}
                    ]
                },
                "anomalies": [],
                "warnings": [],
                "isSuitableForAnalysis": True
            },
            "sales": {
                "fid": "sales",
                "missingRate": 0.05,
                "uniqueCount": 100,
                "distinctRate": 0.9,
                "dataType": "number",
                "distribution": {
                    "type": "number",
                    "min": 100,
                    "max": 1000,
                    "mean": 500,
                    "stddev": 200,
                    "variation_ratio": 0.4
                },
                "anomalies": [],
                "warnings": [],
                "isSuitableForAnalysis": True
            },
            "date": {
                "fid": "date",
                "missingRate": 0.0,
                "uniqueCount": 365,
                "distinctRate": 0.95,
                "dataType": "datetime",
                "distribution": {
                    "type": "datetime",
                    "min_date": "2023-01-01",
                    "max_date": "2023-12-31"
                },
                "anomalies": [],
                "warnings": [],
                "isSuitableForAnalysis": True
            }
        }

    @pytest.fixture
    def sample_metas(self):
        """Create sample field metas for testing."""
        return [
            {"fid": "category", "name": "Category", "analyticType": "dimension", "semanticType": "nominal"},
            {"fid": "sales", "name": "Sales", "analyticType": "measure", "semanticType": "quantitative"},
            {"fid": "date", "name": "Date", "analyticType": "dimension", "semanticType": "temporal"}
        ]

    @pytest.fixture
    def bar_chart_spec(self):
        """Create a bar chart specification."""
        return {
            "config": {"geom": "interval"},
            "encodings": {
                "rows": [
                    {"fid": "sales", "name": "Sales", "analyticType": "measure", "semanticType": "quantitative", "aggName": "sum"}
                ],
                "columns": [
                    {"fid": "category", "name": "Category", "analyticType": "dimension", "semanticType": "nominal"}
                ]
            }
        }

    @pytest.fixture
    def line_chart_spec(self):
        """Create a line chart specification."""
        return {
            "config": {"geom": "line"},
            "encodings": {
                "rows": [
                    {"fid": "sales", "name": "Sales", "analyticType": "measure", "semanticType": "quantitative", "aggName": "avg"}
                ],
                "columns": [
                    {"fid": "date", "name": "Date", "analyticType": "dimension", "semanticType": "temporal"}
                ]
            }
        }

    @pytest.fixture
    def scatter_plot_spec(self):
        """Create a scatter plot specification."""
        return {
            "config": {"geom": "point"},
            "encodings": {
                "rows": [
                    {"fid": "sales", "name": "Sales", "analyticType": "measure", "semanticType": "quantitative", "aggName": "none"}
                ],
                "columns": [
                    {"fid": "category", "name": "Category", "analyticType": "dimension", "semanticType": "nominal"}
                ],
                "color": [
                    {"fid": "category", "name": "Category", "analyticType": "dimension", "semanticType": "nominal"}
                ]
            }
        }

    def test_initialization(self, sample_field_qualities):
        """Test that RecommendationExplainer can be initialized."""
        explainer = RecommendationExplainer(sample_field_qualities)
        assert explainer is not None
        assert explainer.field_qualities == sample_field_qualities

    def test_chart_type_explanation_bar(self, sample_field_qualities, sample_metas, bar_chart_spec):
        """Test chart type explanation for bar chart."""
        explainer = RecommendationExplainer(sample_field_qualities)
        explanation = explainer.explain_recommendation(bar_chart_spec, sample_metas)
        
        assert "chartType" in explanation
        assert explanation["chartType"]["type"] == ChartType.BAR.value
        assert len(explanation["chartType"]["reasons"]) > 0
        assert len(explanation["chartType"]["advantages"]) > 0
        
        reasons_text = " ".join(explanation["chartType"]["reasons"])
        assert "维度" in reasons_text or "分类" in reasons_text
        
        advantages_text = " ".join(explanation["chartType"]["advantages"])
        assert "比较" in advantages_text or "对比" in advantages_text

    def test_chart_type_explanation_line(self, sample_field_qualities, sample_metas, line_chart_spec):
        """Test chart type explanation for line chart."""
        explainer = RecommendationExplainer(sample_field_qualities)
        explanation = explainer.explain_recommendation(line_chart_spec, sample_metas)
        
        assert "chartType" in explanation
        assert explanation["chartType"]["type"] == ChartType.LINE.value
        assert len(explanation["chartType"]["reasons"]) > 0
        
        reasons_text = " ".join(explanation["chartType"]["reasons"])
        assert "时间" in reasons_text or "趋势" in reasons_text

    def test_chart_type_explanation_scatter(self, sample_field_qualities, sample_metas, scatter_plot_spec):
        """Test chart type explanation for scatter plot."""
        explainer = RecommendationExplainer(sample_field_qualities)
        explanation = explainer.explain_recommendation(scatter_plot_spec, sample_metas)
        
        assert "chartType" in explanation
        assert explanation["chartType"]["type"] == ChartType.SCATTER.value

    def test_field_type_explanation(self, sample_field_qualities, sample_metas, bar_chart_spec):
        """Test field type explanation."""
        explainer = RecommendationExplainer(sample_field_qualities)
        explanation = explainer.explain_recommendation(bar_chart_spec, sample_metas)
        
        assert "fields" in explanation
        fields = explanation["fields"]
        assert len(fields) > 0
        
        category_field = next((f for f in fields if f["fieldName"] == "Category"), None)
        assert category_field is not None
        assert category_field["fieldType"] == "dimension"
        assert category_field["semanticType"] == "nominal"
        assert len(category_field["reason"]) > 0
        
        sales_field = next((f for f in fields if f["fieldName"] == "Sales"), None)
        assert sales_field is not None
        assert sales_field["fieldType"] == "measure"
        assert sales_field["semanticType"] == "quantitative"

    def test_aggregation_explanation(self, sample_field_qualities, sample_metas, bar_chart_spec):
        """Test aggregation explanation."""
        explainer = RecommendationExplainer(sample_field_qualities)
        explanation = explainer.explain_recommendation(bar_chart_spec, sample_metas)
        
        assert "aggregations" in explanation
        aggregations = explanation["aggregations"]
        assert len(aggregations) > 0
        
        sales_agg = next((a for a in aggregations if a["fieldName"] == "Sales"), None)
        assert sales_agg is not None
        assert sales_agg["aggregationType"] == AggregationType.SUM.value
        assert len(sales_agg["reason"]) > 0
        
        reason_text = sales_agg["reason"]
        assert "求和" in reason_text or "sum" in reason_text.lower()

    def test_aggregation_explanation_avg(self, sample_field_qualities, sample_metas, line_chart_spec):
        """Test aggregation explanation for average."""
        explainer = RecommendationExplainer(sample_field_qualities)
        explanation = explainer.explain_recommendation(line_chart_spec, sample_metas)
        
        aggregations = explanation["aggregations"]
        sales_agg = next((a for a in aggregations if a["fieldName"] == "Sales"), None)
        assert sales_agg is not None
        assert sales_agg["aggregationType"] == AggregationType.AVG.value
        
        reason_text = sales_agg["reason"]
        assert "平均" in reason_text or "avg" in reason_text.lower()

    def test_visual_encoding_explanation(self, sample_field_qualities, sample_metas, scatter_plot_spec):
        """Test visual encoding explanation."""
        explainer = RecommendationExplainer(sample_field_qualities)
        explanation = explainer.explain_recommendation(scatter_plot_spec, sample_metas)
        
        assert "visualEncoding" in explanation
        encoding = explanation["visualEncoding"]
        
        assert VisualEncodingType.Y.value in encoding
        assert VisualEncodingType.X.value in encoding
        assert VisualEncodingType.COLOR.value in encoding
        
        assert "Sales" in encoding[VisualEncodingType.Y.value]
        assert "Category" in encoding[VisualEncodingType.X.value]
        assert "Category" in encoding[VisualEncodingType.COLOR.value]

    def test_overall_summary(self, sample_field_qualities, sample_metas, bar_chart_spec):
        """Test overall summary generation."""
        explainer = RecommendationExplainer(sample_field_qualities)
        explanation = explainer.explain_recommendation(bar_chart_spec, sample_metas)
        
        assert "overallSummary" in explanation
        summary = explanation["overallSummary"]
        assert len(summary) > 0
        assert "柱状图" in summary or "bar" in summary.lower()

    def test_data_insights(self, sample_field_qualities, sample_metas, bar_chart_spec):
        """Test data insights generation."""
        explainer = RecommendationExplainer(sample_field_qualities)
        explanation = explainer.explain_recommendation(bar_chart_spec, sample_metas)
        
        assert "dataInsights" in explanation
        assert isinstance(explanation["dataInsights"], list)

    def test_identify_chart_type_from_geom(self, sample_field_qualities):
        """Test chart type identification from geom field."""
        explainer = RecommendationExplainer(sample_field_qualities)
        
        test_cases = [
            ("interval", ChartType.BAR),
            ("line", ChartType.LINE),
            ("area", ChartType.AREA),
            ("point", ChartType.SCATTER),
            ("arc", ChartType.PIE),
        ]
        
        for geom, expected_type in test_cases:
            spec = {"config": {"geom": geom}, "encodings": {}}
            chart_type = explainer._identify_chart_type(spec)
            assert chart_type == expected_type, f"Expected {expected_type} for geom '{geom}', got {chart_type}"

    def test_extract_field_info(self, sample_field_qualities, sample_metas, bar_chart_spec):
        """Test field info extraction."""
        explainer = RecommendationExplainer(sample_field_qualities)
        field_info = explainer._extract_field_info(bar_chart_spec, sample_metas)
        
        assert len(field_info) == 2
        
        sales_info = next((f for f in field_info if f["fid"] == "sales"), None)
        assert sales_info is not None
        assert sales_info["name"] == "Sales"
        assert sales_info["analytic_type"] == "measure"
        assert sales_info["aggregation"] == "sum"
        
        category_info = next((f for f in field_info if f["fid"] == "category"), None)
        assert category_info is not None
        assert category_info["name"] == "Category"
        assert category_info["analytic_type"] == "dimension"

    def test_explanation_to_dict_structure(self, sample_field_qualities, sample_metas, bar_chart_spec):
        """Test that explanation has correct dictionary structure."""
        explainer = RecommendationExplainer(sample_field_qualities)
        explanation = explainer.explain_recommendation(bar_chart_spec, sample_metas)
        
        required_keys = [
            "chartType",
            "fields",
            "aggregations",
            "visualEncoding",
            "overallSummary",
            "dataInsights"
        ]
        
        for key in required_keys:
            assert key in explanation, f"Missing required key: {key}"
        
        assert "type" in explanation["chartType"]
        assert "reasons" in explanation["chartType"]
        assert "advantages" in explanation["chartType"]
        
        if explanation["fields"]:
            field = explanation["fields"][0]
            assert "fieldName" in field
            assert "fieldType" in field
            assert "semanticType" in field
            assert "reason" in field
        
        if explanation["aggregations"]:
            agg = explanation["aggregations"][0]
            assert "fieldName" in agg
            assert "aggregationType" in agg
            assert "reason" in agg

    def test_empty_spec_handling(self, sample_field_qualities, sample_metas):
        """Test handling of empty specification."""
        explainer = RecommendationExplainer(sample_field_qualities)
        empty_spec = {"config": {}, "encodings": {}}
        
        explanation = explainer.explain_recommendation(empty_spec, sample_metas)
        
        assert explanation is not None
        assert "chartType" in explanation
        assert "fields" in explanation

    def test_json_serializable(self, sample_field_qualities, sample_metas, bar_chart_spec):
        """Test that explanation is JSON serializable."""
        explainer = RecommendationExplainer(sample_field_qualities)
        explanation = explainer.explain_recommendation(bar_chart_spec, sample_metas)
        
        json_str = json.dumps(explanation, ensure_ascii=False)
        parsed_back = json.loads(json_str)
        
        assert parsed_back["chartType"]["type"] == explanation["chartType"]["type"]
        assert len(parsed_back["fields"]) == len(explanation["fields"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
