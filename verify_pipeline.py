#!/usr/bin/env python3
"""Verify the data pipeline refactoring.

This script tests the new unified data pipeline.
"""
import sys
from typing import List, Dict, Any


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


def run_tests():
    """Run all tests for the data pipeline."""
    print("=" * 60)
    print("Testing data pipeline refactoring...")
    print("=" * 60)
    
    print("\n1. Testing imports...")
    try:
        from pygwalker.services.data_pipeline import (
            DataPipeline, PipelineBuilder, create_pipeline_builder,
            FilterStage, SamplingStage, PipelineContext
        )
        print("   ✓ Imports successful")
    except Exception as e:
        print(f"   ✗ Import failed: {e}")
        return False
    
    print("\n2. Creating sample data...")
    sample_data = [
        {"id": 1, "name": "Alice", "age": 25, "category": "A", "score": 85.5},
        {"id": 2, "name": "Bob", "age": 30, "category": "B", "score": 92.3},
        {"id": 3, "name": "Charlie", "age": 35, "category": "A", "score": 78.9},
        {"id": 4, "name": "Diana", "age": 40, "category": "C", "score": 95.1},
        {"id": 5, "name": "Eve", "age": 45, "category": "B", "score": 88.7},
    ]
    print("   ✓ Sample data created")
    
    print("\n3. Creating mock data source...")
    mock_source = MockDataSource(sample_data)
    print("   ✓ Mock data source created")
    
    print("\n4. Testing FilterStage (range filter)...")
    try:
        from pygwalker.services.data_pipeline import create_pipeline_builder
        
        pipeline = create_pipeline_builder(mock_source).with_filter([
            {
                "fid": "age",
                "conditionType": "range",
                "value": [30, 40],
                "enabled": True
            }
        ]).build()
        
        result = pipeline.execute(payload={})
        
        assert len(result) == 2, f"Expected 2 rows, got {len(result)}"
        names = {row["name"] for row in result}
        assert "Bob" in names, "Bob should be in result"
        assert "Diana" in names, "Diana should be in result"
        print("   ✓ Range filter works correctly")
    except Exception as e:
        print(f"   ✗ Range filter failed: {e}")
        return False
    
    print("\n5. Testing FilterStage (one of filter)...")
    try:
        pipeline = create_pipeline_builder(mock_source).with_filter([
            {
                "fid": "category",
                "conditionType": "one of",
                "value": ["A", "B"],
                "enabled": True
            }
        ]).build()
        
        result = pipeline.execute(payload={})
        
        assert len(result) == 4, f"Expected 4 rows, got {len(result)}"
        names = {row["name"] for row in result}
        assert "Alice" in names, "Alice should be in result"
        assert "Bob" in names, "Bob should be in result"
        assert "Charlie" in names, "Charlie should be in result"
        assert "Eve" in names, "Eve should be in result"
        assert "Diana" not in names, "Diana should not be in result"
        print("   ✓ One of filter works correctly")
    except Exception as e:
        print(f"   ✗ One of filter failed: {e}")
        return False
    
    print("\n6. Testing FilterStage (greater than filter)...")
    try:
        pipeline = create_pipeline_builder(mock_source).with_filter([
            {
                "fid": "age",
                "conditionType": "greater than",
                "value": 35,
                "enabled": True
            }
        ]).build()
        
        result = pipeline.execute(payload={})
        
        assert len(result) == 2, f"Expected 2 rows, got {len(result)}"
        names = {row["name"] for row in result}
        assert "Diana" in names, "Diana should be in result"
        assert "Eve" in names, "Eve should be in result"
        print("   ✓ Greater than filter works correctly")
    except Exception as e:
        print(f"   ✗ Greater than filter failed: {e}")
        return False
    
    print("\n7. Testing FilterStage (equals filter)...")
    try:
        pipeline = create_pipeline_builder(mock_source).with_filter([
            {
                "fid": "category",
                "conditionType": "equals",
                "value": "C",
                "enabled": True
            }
        ]).build()
        
        result = pipeline.execute(payload={})
        
        assert len(result) == 1, f"Expected 1 row, got {len(result)}"
        assert result[0]["name"] == "Diana", "Diana should be the only one"
        print("   ✓ Equals filter works correctly")
    except Exception as e:
        print(f"   ✗ Equals filter failed: {e}")
        return False
    
    print("\n8. Testing FilterStage (contains filter)...")
    try:
        pipeline = create_pipeline_builder(mock_source).with_filter([
            {
                "fid": "name",
                "conditionType": "contains",
                "value": "a",
                "enabled": True
            }
        ]).build()
        
        result = pipeline.execute(payload={})
        names = {row["name"] for row in result}
        assert "Alice" in names, "Alice should be in result"
        assert "Diana" in names, "Diana should be in result"
        assert "Charlie" in names, "Charlie should be in result"
        print("   ✓ Contains filter works correctly")
    except Exception as e:
        print(f"   ✗ Contains filter failed: {e}")
        return False
    
    print("\n9. Testing multiple filters with AND logic...")
    try:
        pipeline = create_pipeline_builder(mock_source).with_filter([
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
        
        assert len(result) == 2, f"Expected 2 rows, got {len(result)}"
        names = {row["name"] for row in result}
        assert "Charlie" in names, "Charlie should be in result"
        assert "Eve" in names, "Eve should be in result"
        print("   ✓ Multiple filters (AND) works correctly")
    except Exception as e:
        print(f"   ✗ Multiple filters (AND) failed: {e}")
        return False
    
    print("\n10. Testing multiple filters with OR logic...")
    try:
        pipeline = create_pipeline_builder(mock_source).with_filter([
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
        
        assert len(result) == 2, f"Expected 2 rows, got {len(result)}"
        names = {row["name"] for row in result}
        assert "Alice" in names, "Alice should be in result"
        assert "Diana" in names, "Diana should be in result"
        print("   ✓ Multiple filters (OR) works correctly")
    except Exception as e:
        print(f"   ✗ Multiple filters (OR) failed: {e}")
        return False
    
    print("\n11. Testing disabled filter...")
    try:
        pipeline = create_pipeline_builder(mock_source).with_filter([
            {
                "fid": "category",
                "conditionType": "equals",
                "value": "C",
                "enabled": False
            }
        ]).build()
        
        result = pipeline.execute(payload={})
        
        assert len(result) == 5, f"Expected 5 rows, got {len(result)}"
        print("   ✓ Disabled filter ignored correctly")
    except Exception as e:
        print(f"   ✗ Disabled filter failed: {e}")
        return False
    
    print("\n12. Testing empty filters...")
    try:
        pipeline = create_pipeline_builder(mock_source).with_filter([]).build()
        result = pipeline.execute(payload={})
        assert len(result) == 5, f"Expected 5 rows, got {len(result)}"
        print("   ✓ Empty filters ignored correctly")
    except Exception as e:
        print(f"   ✗ Empty filters failed: {e}")
        return False
    
    print("\n13. Testing smart sampling...")
    try:
        large_data = sample_data * 100
        large_source = MockDataSource(large_data)
        
        pipeline = create_pipeline_builder(large_source).with_smart_sampling(
            sample_size=5,
            preserve_boundaries=True
        ).build()
        
        result = pipeline.execute(payload={})
        
        assert len(result) == 5, f"Expected 5 rows, got {len(result)}"
        print("   ✓ Smart sampling works correctly")
    except Exception as e:
        print(f"   ✗ Smart sampling failed: {e}")
        return False
    
    print("\n14. Testing pipeline builder chaining...")
    try:
        large_data = sample_data * 10
        large_source = MockDataSource(large_data)
        
        pipeline = create_pipeline_builder(large_source)\
            .with_filter([
                {"fid": "category", "conditionType": "one of", "value": ["A", "B"], "enabled": True}
            ])\
            .with_smart_sampling(sample_size=5, preserve_boundaries=False)\
            .with_metadata(source="test")\
            .build()
        
        result = pipeline.execute(payload={})
        
        assert len(result) == 5, f"Expected 5 rows, got {len(result)}"
        for row in result:
            assert row["category"] in ["A", "B"], f"Category should be A or B, got {row['category']}"
        print("   ✓ Pipeline builder chaining works correctly")
    except Exception as e:
        print(f"   ✗ Pipeline builder chaining failed: {e}")
        return False
    
    print("\n15. Testing batch execution...")
    try:
        pipeline = create_pipeline_builder(mock_source).build()
        
        results = pipeline.execute_batch(payload_list=[{}, {}, {}])
        
        assert len(results) == 3, f"Expected 3 batches, got {len(results)}"
        for result in results:
            assert len(result) == 5, f"Expected 5 rows, got {len(result)}"
        print("   ✓ Batch execution works correctly")
    except Exception as e:
        print(f"   ✗ Batch execution failed: {e}")
        return False
    
    print("\n16. Testing configure method...")
    try:
        pipeline = create_pipeline_builder(mock_source).build()
        
        pipeline.configure(
            filters=[{"fid": "category", "conditionType": "equals", "value": "A", "enabled": True}],
            filter_logic="AND"
        )
        
        result = pipeline.execute(payload={})
        
        assert len(result) == 2, f"Expected 2 rows, got {len(result)}"
        names = {row["name"] for row in result}
        assert "Alice" in names, "Alice should be in result"
        assert "Charlie" in names, "Charlie should be in result"
        print("   ✓ Configure method works correctly")
    except Exception as e:
        print(f"   ✗ Configure method failed: {e}")
        return False
    
    print("\n17. Testing SQL execution...")
    try:
        pipeline = create_pipeline_builder(mock_source).with_filter([
            {
                "fid": "age",
                "conditionType": "less than",
                "value": 30,
                "enabled": True
            }
        ]).build()
        
        result = pipeline.execute(sql="SELECT * FROM test")
        
        assert len(result) == 1, f"Expected 1 row, got {len(result)}"
        assert result[0]["name"] == "Alice", "Alice should be the only one"
        print("   ✓ SQL execution works correctly")
    except Exception as e:
        print(f"   ✗ SQL execution failed: {e}")
        return False
    
    print("\n18. Testing rule-based filter...")
    try:
        pipeline = create_pipeline_builder(mock_source).with_filter([
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
        
        assert len(result) == 2, f"Expected 2 rows, got {len(result)}"
        names = {row["name"] for row in result}
        assert "Bob" in names, "Bob should be in result"
        assert "Diana" in names, "Diana should be in result"
        print("   ✓ Rule-based filter works correctly")
    except Exception as e:
        print(f"   ✗ Rule-based filter failed: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("All tests passed!")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
