"""Tests for the unified data pipeline system."""
import pytest
from typing import List, Dict, Any
from unittest.mock import Mock, MagicMock


class MockDataSource:
    """Mock data source for testing."""
    
    def __init__(self, data: List[Dict[str, Any]]):
        self._data = data
        self.dataset_type = "test_dataframe"
    
    def get_datas_by_payload(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        return self._data.copy()
    
    def get_datas_by_sql(self, sql: str) -> List[Dict[str, Any]]:
        return self._data.copy()
    
    def batch_get_datas_by_payload(self, payload_list: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        return [self._data.copy() for _ in payload_list]
    
    def batch_get_datas_by_sql(self, sql_list: List[str]) -> List[List[Dict[str, Any]]]:
        return [self._data.copy() for _ in sql_list]


@pytest.fixture
def sample_data():
    """Create sample test data."""
    return [
        {"id": 1, "name": "Alice", "age": 25, "category": "A", "score": 85.5},
        {"id": 2, "name": "Bob", "age": 30, "category": "B", "score": 92.3},
        {"id": 3, "name": "Charlie", "age": 35, "category": "A", "score": 78.9},
        {"id": 4, "name": "Diana", "age": 40, "category": "C", "score": 95.1},
        {"id": 5, "name": "Eve", "age": 45, "category": "B", "score": 88.7},
    ]


@pytest.fixture
def mock_data_source(sample_data):
    """Create a mock data source with sample data."""
    return MockDataSource(sample_data)


class TestFilterStage:
    """Tests for the filter stage."""
    
    def test_range_filter(self, mock_data_source):
        """Test range filtering."""
        from pygwalker.services.data_pipeline import create_pipeline_builder
        
        pipeline = create_pipeline_builder(mock_data_source).with_filter([
            {
                "fid": "age",
                "conditionType": "range",
                "value": [30, 40],
                "enabled": True
            }
        ]).build()
        
        result = pipeline.execute(payload={})
        
        assert len(result) == 3
        assert {row["name"] for row in result} == {"Bob", "Charlie", "Diana"}
    
    def test_one_of_filter(self, mock_data_source):
        """Test 'one of' filtering."""
        from pygwalker.services.data_pipeline import create_pipeline_builder
        
        pipeline = create_pipeline_builder(mock_data_source).with_filter([
            {
                "fid": "category",
                "conditionType": "one of",
                "value": ["A", "B"],
                "enabled": True
            }
        ]).build()
        
        result = pipeline.execute(payload={})
        
        assert len(result) == 4
        assert {row["name"] for row in result} == {"Alice", "Bob", "Charlie", "Eve"}
    
    def test_not_in_filter(self, mock_data_source):
        """Test 'not in' filtering."""
        from pygwalker.services.data_pipeline import create_pipeline_builder
        
        pipeline = create_pipeline_builder(mock_data_source).with_filter([
            {
                "fid": "category",
                "conditionType": "not in",
                "value": ["A"],
                "enabled": True
            }
        ]).build()
        
        result = pipeline.execute(payload={})
        
        assert len(result) == 3
        assert {row["name"] for row in result} == {"Bob", "Diana", "Eve"}
    
    def test_contains_filter(self, mock_data_source):
        """Test contains filtering."""
        from pygwalker.services.data_pipeline import create_pipeline_builder
        
        pipeline = create_pipeline_builder(mock_data_source).with_filter([
            {
                "fid": "name",
                "conditionType": "contains",
                "value": "a",
                "enabled": True
            }
        ]).build()
        
        result = pipeline.execute(payload={})
        
        names = {row["name"] for row in result}
        assert "Alice" in names
        assert "Diana" in names
        assert "Charlie" in names
    
    def test_greater_than_filter(self, mock_data_source):
        """Test greater than filtering."""
        from pygwalker.services.data_pipeline import create_pipeline_builder
        
        pipeline = create_pipeline_builder(mock_data_source).with_filter([
            {
                "fid": "age",
                "conditionType": "greater than",
                "value": 35,
                "enabled": True
            }
        ]).build()
        
        result = pipeline.execute(payload={})
        
        assert len(result) == 2
        assert {row["name"] for row in result} == {"Diana", "Eve"}
    
    def test_less_than_filter(self, mock_data_source):
        """Test less than filtering."""
        from pygwalker.services.data_pipeline import create_pipeline_builder
        
        pipeline = create_pipeline_builder(mock_data_source).with_filter([
            {
                "fid": "age",
                "conditionType": "less than",
                "value": 35,
                "enabled": True
            }
        ]).build()
        
        result = pipeline.execute(payload={})
        
        assert len(result) == 2
        assert {row["name"] for row in result} == {"Alice", "Bob"}
    
    def test_equals_filter(self, mock_data_source):
        """Test equals filtering."""
        from pygwalker.services.data_pipeline import create_pipeline_builder
        
        pipeline = create_pipeline_builder(mock_data_source).with_filter([
            {
                "fid": "category",
                "conditionType": "equals",
                "value": "C",
                "enabled": True
            }
        ]).build()
        
        result = pipeline.execute(payload={})
        
        assert len(result) == 1
        assert result[0]["name"] == "Diana"
    
    def test_multiple_filters_and_logic(self, mock_data_source):
        """Test multiple filters with AND logic."""
        from pygwalker.services.data_pipeline import create_pipeline_builder
        
        pipeline = create_pipeline_builder(mock_data_source).with_filter([
            {
                "fid": "category",
                "conditionType": "one of",
                "value": ["A", "B"],
                "enabled": True
            },
            {
                "fid": "age",
                "conditionType": "greater than",
                "value": 30,
                "enabled": True
            }
        ], logic="AND").build()
        
        result = pipeline.execute(payload={})
        
        assert len(result) == 2
        assert {row["name"] for row in result} == {"Charlie", "Eve"}
    
    def test_multiple_filters_or_logic(self, mock_data_source):
        """Test multiple filters with OR logic."""
        from pygwalker.services.data_pipeline import create_pipeline_builder
        
        pipeline = create_pipeline_builder(mock_data_source).with_filter([
            {
                "fid": "category",
                "conditionType": "equals",
                "value": "C",
                "enabled": True
            },
            {
                "fid": "age",
                "conditionType": "less than",
                "value": 30,
                "enabled": True
            }
        ], logic="OR").build()
        
        result = pipeline.execute(payload={})
        
        assert len(result) == 2
        assert {row["name"] for row in result} == {"Alice", "Diana"}
    
    def test_disabled_filter(self, mock_data_source):
        """Test that disabled filters are ignored."""
        from pygwalker.services.data_pipeline import create_pipeline_builder
        
        pipeline = create_pipeline_builder(mock_data_source).with_filter([
            {
                "fid": "category",
                "conditionType": "equals",
                "value": "C",
                "enabled": False
            }
        ]).build()
        
        result = pipeline.execute(payload={})
        
        assert len(result) == 5
    
    def test_empty_filters(self, mock_data_source):
        """Test that empty filters don't affect results."""
        from pygwalker.services.data_pipeline import create_pipeline_builder
        
        pipeline = create_pipeline_builder(mock_data_source).with_filter([]).build()
        
        result = pipeline.execute(payload={})
        
        assert len(result) == 5


class TestSamplingStage:
    """Tests for the sampling stage."""
    
    def test_smart_sampling(self, mock_data_source):
        """Test smart sampling."""
        from pygwalker.services.data_pipeline import create_pipeline_builder
        
        pipeline = create_pipeline_builder(mock_data_source).with_smart_sampling(
            sample_size=3,
            preserve_boundaries=True
        ).build()
        
        result = pipeline.execute(payload={})
        
        assert len(result) == 3
    
    def test_random_sampling(self, mock_data_source):
        """Test random sampling."""
        from pygwalker.services.data_pipeline import create_pipeline_builder
        
        pipeline = create_pipeline_builder(mock_data_source).with_sampling(
            strategy="random",
            sample_size=2
        ).build()
        
        result = pipeline.execute(payload={})
        
        assert len(result) == 2
    
    def test_no_sampling_for_small_data(self):
        """Test that no sampling is applied for small datasets."""
        from pygwalker.services.data_pipeline import create_pipeline_builder
        
        small_data = [{"id": 1}, {"id": 2}, {"id": 3}]
        mock_source = MockDataSource(small_data)
        
        pipeline = create_pipeline_builder(mock_source).with_sampling(
            strategy="random",
            sample_size=10
        ).build()
        
        result = pipeline.execute(payload={})
        
        assert len(result) == 3


class TestPipelineBuilder:
    """Tests for the pipeline builder."""
    
    def test_builder_chaining(self, mock_data_source):
        """Test builder method chaining."""
        from pygwalker.services.data_pipeline import create_pipeline_builder
        
        pipeline = create_pipeline_builder(mock_data_source)\
            .with_filter([
                {"fid": "age", "conditionType": "greater than", "value": 25, "enabled": True}
            ])\
            .with_metadata(source="test")\
            .build()
        
        assert pipeline is not None
        result = pipeline.execute(payload={})
        assert len(result) == 4


class TestDataPipeline:
    """Tests for the main DataPipeline class."""
    
    def test_execute_with_payload(self, mock_data_source):
        """Test execute with payload."""
        from pygwalker.services.data_pipeline import DataPipeline, PipelineContext
        
        pipeline = DataPipeline(
            mock_data_source,
            context=PipelineContext(source_type="test")
        )
        
        result = pipeline.execute(payload={"test": "payload"})
        
        assert len(result) == 5
    
    def test_execute_with_sql(self, mock_data_source):
        """Test execute with SQL."""
        from pygwalker.services.data_pipeline import DataPipeline, PipelineContext
        
        pipeline = DataPipeline(
            mock_data_source,
            context=PipelineContext(source_type="test")
        )
        
        result = pipeline.execute(sql="SELECT * FROM test")
        
        assert len(result) == 5
    
    def test_execute_batch(self, mock_data_source):
        """Test batch execution."""
        from pygwalker.services.data_pipeline import create_pipeline_builder
        
        pipeline = create_pipeline_builder(mock_data_source).build()
        
        results = pipeline.execute_batch(payload_list=[{}, {}, {}])
        
        assert len(results) == 3
        for result in results:
            assert len(result) == 5
    
    def test_execute_batch_with_sql(self, mock_data_source):
        """Test batch execution with SQL."""
        from pygwalker.services.data_pipeline import create_pipeline_builder
        
        pipeline = create_pipeline_builder(mock_data_source).build()
        
        results = pipeline.execute_batch(sql_list=["SELECT 1", "SELECT 2"])
        
        assert len(results) == 2
        for result in results:
            assert len(result) == 5
    
    def test_configure_method(self, mock_data_source):
        """Test configure method."""
        from pygwalker.services.data_pipeline import create_pipeline_builder
        
        pipeline = create_pipeline_builder(mock_data_source).build()
        
        pipeline.configure(
            filters=[{"fid": "category", "conditionType": "equals", "value": "A", "enabled": True}],
            filter_logic="AND"
        )
        
        result = pipeline.execute(payload={})
        
        assert len(result) == 2
        assert {row["name"] for row in result} == {"Alice", "Charlie"}


class TestPipelineIntegration:
    """Integration tests for the full pipeline."""
    
    def test_filter_and_sample_combined(self, sample_data):
        """Test combining filter and sample stages."""
        from pygwalker.services.data_pipeline import create_pipeline_builder
        
        large_data = sample_data * 10
        mock_source = MockDataSource(large_data)
        
        pipeline = create_pipeline_builder(mock_source)\
            .with_filter([
                {"fid": "category", "conditionType": "one of", "value": ["A", "B"], "enabled": True}
            ])\
            .with_smart_sampling(sample_size=5, preserve_boundaries=False)\
            .build()
        
        result = pipeline.execute(payload={})
        
        assert len(result) == 5
        for row in result:
            assert row["category"] in ["A", "B"]
    
    def test_rule_based_filter(self, mock_data_source):
        """Test filter with rule-based format (from graphic-walker)."""
        from pygwalker.services.data_pipeline import create_pipeline_builder
        
        pipeline = create_pipeline_builder(mock_data_source).with_filter([
            {
                "fid": "age",
                "rule": {
                    "type": "range",
                    "value": [30, 40]
                },
                "enabled": True
            }
        ]).build()
        
        result = pipeline.execute(payload={})
        
        assert len(result) == 3
        assert {row["name"] for row in result} == {"Bob", "Charlie", "Diana"}
