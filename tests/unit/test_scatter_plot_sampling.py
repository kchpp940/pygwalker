"""Regression tests for scatter plot sampling optimization.

Tests cover:
1. Large scatter plots (>50K points) should be sampled
2. Non-scatter plots should NOT be sampled
3. Small datasets (<=50K points) should NOT be sampled
4. Sampled data should preserve first and last records
"""

import pytest
from pygwalker.utils.estimate_tools import (
    smart_sample_datas,
    sample_datas_by_byte_limit
)
from pygwalker.services.render import (
    is_scatter_plot_spec,
    apply_scatter_plot_sampling
)
from pygwalker._constants import (
    SCATTER_PLOT_SAMPLE_LIMIT,
    SCATTER_PLOT_LARGE_DATA_THRESHOLD
)


class TestSmartSampleDatas:
    """Tests for smart_sample_datas function"""

    def test_sampling_reduces_size(self):
        """Sampling should reduce dataset size to target count"""
        data = [{"x": i, "y": i * 2} for i in range(100000)]
        sampled = smart_sample_datas(data, 10000)
        
        assert len(sampled) == 10000

    def test_preserves_first_record(self):
        """Sampled data should preserve first record"""
        data = [{"x": i, "y": i * 2} for i in range(100000)]
        sampled = smart_sample_datas(data, 10000)
        
        assert sampled[0] == data[0]

    def test_preserves_last_record(self):
        """Sampled data should preserve last record"""
        data = [{"x": i, "y": i * 2} for i in range(100000)]
        sampled = smart_sample_datas(data, 10000)
        
        assert sampled[-1] == data[-1]

    def test_small_dataset_no_sampling(self):
        """Small datasets should not be sampled"""
        data = [{"x": i} for i in range(100)]
        sampled = smart_sample_datas(data, 10000)
        
        assert len(sampled) == 100

    def test_empty_data(self):
        """Empty data should return empty"""
        sampled = smart_sample_datas([], 100)
        
        assert len(sampled) == 0

    def test_single_record(self):
        """Single record should be preserved"""
        data = [{"x": 1}]
        sampled = smart_sample_datas(data, 100)
        
        assert sampled == data

    def test_two_records(self):
        """Two records should both be preserved"""
        data = [{"x": 1}, {"x": 2}]
        sampled = smart_sample_datas(data, 100)
        
        assert sampled == data


class TestIsScatterPlotSpec:
    """Tests for is_scatter_plot_spec function"""

    def test_point_geom_is_scatter(self):
        """Point geometry should be recognized as scatter plot"""
        spec = {
            "config": {
                "geoms": ["point"],
                "defaultAggregated": False
            }
        }
        
        assert is_scatter_plot_spec(spec) is True

    def test_circle_geom_is_scatter(self):
        """Circle geometry should be recognized as scatter plot"""
        spec = {
            "config": {
                "geoms": ["circle"],
                "defaultAggregated": False
            }
        }
        
        assert is_scatter_plot_spec(spec) is True

    def test_tick_geom_is_scatter(self):
        """Tick geometry should be recognized as scatter plot"""
        spec = {
            "config": {
                "geoms": ["tick"],
                "defaultAggregated": False
            }
        }
        
        assert is_scatter_plot_spec(spec) is True

    def test_bar_geom_not_scatter(self):
        """Bar geometry should NOT be recognized as scatter plot"""
        spec = {
            "config": {
                "geoms": ["bar"],
                "defaultAggregated": False
            }
        }
        
        assert is_scatter_plot_spec(spec) is False

    def test_line_geom_not_scatter(self):
        """Line geometry should NOT be recognized as scatter plot"""
        spec = {
            "config": {
                "geoms": ["line"],
                "defaultAggregated": False
            }
        }
        
        assert is_scatter_plot_spec(spec) is False

    def test_aggregated_not_scatter(self):
        """Aggregated plots should NOT be recognized as scatter plots"""
        spec = {
            "config": {
                "geoms": ["point"],
                "defaultAggregated": True
            }
        }
        
        assert is_scatter_plot_spec(spec) is False

    def test_missing_config(self):
        """Missing config should return False"""
        spec = {}
        
        assert is_scatter_plot_spec(spec) is False

    def test_missing_geoms(self):
        """Missing geoms should return False"""
        spec = {
            "config": {
                "defaultAggregated": False
            }
        }
        
        assert is_scatter_plot_spec(spec) is False


class TestApplyScatterPlotSampling:
    """Tests for apply_scatter_plot_sampling function"""

    @pytest.fixture
    def scatter_spec(self):
        return {
            "config": {
                "geoms": ["point"],
                "defaultAggregated": False
            }
        }

    @pytest.fixture
    def bar_spec(self):
        return {
            "config": {
                "geoms": ["bar"],
                "defaultAggregated": True
            }
        }

    def test_large_scatter_sampled(self, scatter_spec):
        """Large scatter plot (>50K points) should be sampled"""
        data = [{"x": i, "y": i * 2} for i in range(60000)]
        sampled = apply_scatter_plot_sampling(scatter_spec, data)
        
        assert len(sampled) == SCATTER_PLOT_SAMPLE_LIMIT
        assert len(sampled) < len(data)

    def test_non_scatter_not_sampled(self, bar_spec):
        """Non-scatter plots should NOT be sampled, even with large data"""
        data = [{"x": i, "y": i * 2} for i in range(60000)]
        sampled = apply_scatter_plot_sampling(bar_spec, data)
        
        assert len(sampled) == 60000

    def test_small_scatter_not_sampled(self, scatter_spec):
        """Small scatter plots (<=50K points) should NOT be sampled"""
        data = [{"x": i, "y": i * 2} for i in range(40000)]
        sampled = apply_scatter_plot_sampling(scatter_spec, data)
        
        assert len(sampled) == 40000

    def test_threshold_scatter_not_sampled(self, scatter_spec):
        """Scatter plots at exact threshold (50K points) should NOT be sampled"""
        data = [{"x": i, "y": i * 2} for i in range(SCATTER_PLOT_LARGE_DATA_THRESHOLD)]
        sampled = apply_scatter_plot_sampling(scatter_spec, data)
        
        assert len(sampled) == SCATTER_PLOT_LARGE_DATA_THRESHOLD

    def test_above_threshold_sampled(self, scatter_spec):
        """Scatter plots just above threshold (>50K points) should be sampled"""
        data = [{"x": i, "y": i * 2} for i in range(SCATTER_PLOT_LARGE_DATA_THRESHOLD + 1)]
        sampled = apply_scatter_plot_sampling(scatter_spec, data)
        
        assert len(sampled) == SCATTER_PLOT_SAMPLE_LIMIT

    def test_sampled_scatter_preserves_first(self, scatter_spec):
        """Sampled scatter plot should preserve first record"""
        data = [{"x": i, "y": i * 2} for i in range(60000)]
        sampled = apply_scatter_plot_sampling(scatter_spec, data)
        
        assert sampled[0] == data[0]

    def test_sampled_scatter_preserves_last(self, scatter_spec):
        """Sampled scatter plot should preserve last record"""
        data = [{"x": i, "y": i * 2} for i in range(60000)]
        sampled = apply_scatter_plot_sampling(scatter_spec, data)
        
        assert sampled[-1] == data[-1]

    def test_empty_data(self, scatter_spec):
        """Empty data should return empty"""
        sampled = apply_scatter_plot_sampling(scatter_spec, [])
        
        assert len(sampled) == 0

    def test_single_record(self, scatter_spec):
        """Single record should be preserved"""
        data = [{"x": 1}]
        sampled = apply_scatter_plot_sampling(scatter_spec, data)
        
        assert sampled == data


class TestSampleDatasByByteLimit:
    """Tests for sample_datas_by_byte_limit function"""

    def test_small_dataset_not_sampled(self):
        """Small datasets should not be sampled"""
        data = [{"x": i} for i in range(2000)]
        sampled = sample_datas_by_byte_limit(data, 100000, 100)
        
        assert len(sampled) == 2000

    def test_large_dataset_sampled(self):
        """Large datasets should be sampled"""
        data = [{"x": i, "y": i * 2, "z": str(i)} for i in range(100000)]
        sampled = sample_datas_by_byte_limit(data, 100000, 100)
        
        assert len(sampled) < 100000

    def test_min_sample_size_respected(self):
        """Minimum sample size should be respected"""
        data = [{"x": i, "y": i * 2, "z": str(i)} for i in range(100000)]
        min_size = 500
        sampled = sample_datas_by_byte_limit(data, 10000, min_size)
        
        assert len(sampled) >= min_size


class TestThresholdConstants:
    """Tests for sampling threshold constants"""

    def test_sample_limit_positive(self):
        """Sample limit should be positive"""
        assert SCATTER_PLOT_SAMPLE_LIMIT > 0

    def test_large_data_threshold_positive(self):
        """Large data threshold should be positive"""
        assert SCATTER_PLOT_LARGE_DATA_THRESHOLD > 0

    def test_sample_limit_less_than_threshold(self):
        """Sample limit should be less than threshold"""
        assert SCATTER_PLOT_SAMPLE_LIMIT < SCATTER_PLOT_LARGE_DATA_THRESHOLD
