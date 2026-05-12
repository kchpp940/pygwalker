#!/usr/bin/env python3
"""
Integration tests for field quality analysis.
Tests the REAL data flow: DataFrame -> DataParser -> SQL queries -> field_qualities
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
import pandas as pd
import numpy as np

from pygwalker.data_parsers.pandas_parser import PandasDataFrameDataParser
from pygwalker.api.pygwalker import PygWalker


class TestFieldQualityDataParserIntegration(unittest.TestCase):
    """Test field quality through real DataParser and SQL queries."""

    def setUp(self):
        """Create test DataFrames with known characteristics."""
        np.random.seed(42)
        self.n = 100
        
        self.df_missing = pd.DataFrame({
            'id': range(self.n),
            'full_field': np.random.normal(0, 1, self.n),
            'moderate_missing': np.where(
                np.random.random(self.n) < 0.3,
                np.nan,
                np.random.normal(0, 1, self.n)
            ),
            'high_missing': np.where(
                np.random.random(self.n) < 0.6,
                np.nan,
                np.random.normal(0, 1, self.n)
            ),
            'extreme_missing': np.where(
                np.random.random(self.n) < 0.9,
                np.nan,
                np.random.normal(0, 1, self.n)
            )
        })
        
        self.df_cardinality = pd.DataFrame({
            'constant_field': ['same_value'] * self.n,
            'low_variability': np.repeat([1, 2], self.n // 2),
            'normal_variability': np.random.randint(1, 50, self.n),
            'high_cardinality': [f'user_{i}' for i in range(self.n)]
        })
        
        normal_data = np.random.normal(50, 10, self.n)
        normal_data[0] = 1000
        normal_data[1] = 2000
        self.df_outliers = pd.DataFrame({
            'with_outliers': normal_data,
            'no_outliers': np.random.normal(50, 10, self.n)
        })

    def test_missing_rate_through_real_parser(self):
        """Test missing rate calculation through real DataParser."""
        print("\n" + "="*60)
        print("TEST: Missing Rate Through Real DataParser")
        print("="*60)
        
        parser = PandasDataFrameDataParser(
            df=self.df_missing,
            field_specs=[],
            infer_string_to_date=False,
            infer_number_to_dimension=False,
            other_params={}
        )
        
        field_qualities = parser.field_qualities
        
        print(f"\nParser created successfully")
        print(f"Field qualities returned: {len(field_qualities)} fields")
        
        fields_to_check = [
            ('full_field', 0.0, 0.05),
            ('moderate_missing', 0.3, 0.1),
            ('high_missing', 0.6, 0.1),
            ('extreme_missing', 0.9, 0.1),
        ]
        
        for field_name, expected_rate, tolerance in fields_to_check:
            quality = field_qualities.get(field_name)
            self.assertIsNotNone(quality, f"Field {field_name} not found")
            
            actual_rate = quality['missingRate']
            print(f"\n  Field: {field_name}")
            print(f"    Expected: ~{expected_rate:.0%}, Actual: {actual_rate:.1%}")
            print(f"    Unique count: {quality['uniqueCount']}")
            print(f"    Warnings: {quality['warnings']}")
            print(f"    Is suitable: {quality['isSuitableForAnalysis']}")
            
            self.assertAlmostEqual(
                actual_rate, expected_rate, delta=tolerance,
                msg=f"Field {field_name}: expected ~{expected_rate:.0%}, got {actual_rate:.1%}"
            )
            
            if expected_rate > 0.8:
                self.assertFalse(
                    quality['isSuitableForAnalysis'],
                    f"Field with {expected_rate:.0%} missing should NOT be suitable"
                )
        
        print("\n  ✅ Missing rate test passed!")

    def test_unique_count_through_real_parser(self):
        """Test unique count calculation through real DataParser."""
        print("\n" + "="*60)
        print("TEST: Unique Count Through Real DataParser")
        print("="*60)
        
        parser = PandasDataFrameDataParser(
            df=self.df_cardinality,
            field_specs=[],
            infer_string_to_date=False,
            infer_number_to_dimension=False,
            other_params={}
        )
        
        field_qualities = parser.field_qualities
        
        print(f"\nParser created successfully")
        print(f"Field qualities returned: {len(field_qualities)} fields")
        
        constant_quality = field_qualities.get('constant_field')
        self.assertIsNotNone(constant_quality)
        print(f"\n  Field: constant_field")
        print(f"    Expected: 1, Actual: {constant_quality['uniqueCount']}")
        print(f"    Distinct rate: {constant_quality['distinctRate']:.2%}")
        self.assertEqual(constant_quality['uniqueCount'], 1)
        
        low_var_quality = field_qualities.get('low_variability')
        self.assertIsNotNone(low_var_quality)
        print(f"\n  Field: low_variability")
        print(f"    Expected: 2, Actual: {low_var_quality['uniqueCount']}")
        print(f"    Distinct rate: {low_var_quality['distinctRate']:.2%}")
        print(f"    Warnings: {low_var_quality['warnings']}")
        print(f"    Is suitable: {low_var_quality['isSuitableForAnalysis']}")
        self.assertEqual(low_var_quality['uniqueCount'], 2)
        
        high_card_quality = field_qualities.get('high_cardinality')
        self.assertIsNotNone(high_card_quality)
        print(f"\n  Field: high_cardinality")
        print(f"    Expected: {self.n}, Actual: {high_card_quality['uniqueCount']}")
        print(f"    Distinct rate: {high_card_quality['distinctRate']:.2%}")
        print(f"    Warnings: {high_card_quality['warnings']}")
        self.assertEqual(high_card_quality['uniqueCount'], self.n)
        self.assertTrue(
            any('High cardinality' in w for w in high_card_quality['warnings']),
            "Expected 'High cardinality' warning"
        )
        
        print("\n  ✅ Unique count test passed!")

    def test_outlier_detection_through_real_parser(self):
        """Test outlier detection through real DataParser."""
        print("\n" + "="*60)
        print("TEST: Outlier Detection Through Real DataParser")
        print("="*60)
        
        parser = PandasDataFrameDataParser(
            df=self.df_outliers,
            field_specs=[],
            infer_string_to_date=False,
            infer_number_to_dimension=False,
            other_params={}
        )
        
        field_qualities = parser.field_qualities
        
        print(f"\nParser created successfully")
        
        outlier_quality = field_qualities.get('with_outliers')
        self.assertIsNotNone(outlier_quality)
        print(f"\n  Field: with_outliers")
        print(f"    Distribution: min={outlier_quality['distribution'].get('min')}, "
              f"max={outlier_quality['distribution'].get('max')}")
        print(f"    Anomalies: {len(outlier_quality['anomalies'])}")
        for anomaly in outlier_quality['anomalies']:
            print(f"      - {anomaly['type']}: {anomaly['description']}")
        
        self.assertTrue(
            len(outlier_quality['anomalies']) > 0,
            "Expected to detect outliers in 'with_outliers' field"
        )
        
        outlier_anomaly = outlier_quality['anomalies'][0]
        self.assertEqual(outlier_anomaly['type'], 'outlier')
        
        normal_quality = field_qualities.get('no_outliers')
        self.assertIsNotNone(normal_quality)
        print(f"\n  Field: no_outliers")
        print(f"    Distribution: min={normal_quality['distribution'].get('min')}, "
              f"max={normal_quality['distribution'].get('max')}")
        print(f"    Anomalies: {len(normal_quality['anomalies'])}")
        
        print("\n  ✅ Outlier detection test passed!")

    def test_distribution_statistics_through_real_parser(self):
        """Test distribution statistics through real DataParser."""
        print("\n" + "="*60)
        print("TEST: Distribution Statistics Through Real DataParser")
        print("="*60)
        
        df_dist = pd.DataFrame({
            'numeric_normal': np.random.normal(100, 15, self.n),
            'numeric_uniform': np.random.uniform(0, 100, self.n),
            'categorical': np.random.choice(['A', 'B', 'C'], self.n, p=[0.5, 0.3, 0.2])
        })
        
        parser = PandasDataFrameDataParser(
            df=df_dist,
            field_specs=[],
            infer_string_to_date=False,
            infer_number_to_dimension=False,
            other_params={}
        )
        
        field_qualities = parser.field_qualities
        
        normal_quality = field_qualities.get('numeric_normal')
        self.assertIsNotNone(normal_quality)
        dist = normal_quality['distribution']
        print(f"\n  Field: numeric_normal")
        print(f"    Expected mean: ~100, Actual: {dist.get('mean')}")
        print(f"    Expected std: ~15, Actual: {dist.get('stddev')}")
        
        self.assertAlmostEqual(dist['mean'], 100, delta=5)
        self.assertAlmostEqual(dist['stddev'], 15, delta=5)
        
        uniform_quality = field_qualities.get('numeric_uniform')
        self.assertIsNotNone(uniform_quality)
        dist = uniform_quality['distribution']
        print(f"\n  Field: numeric_uniform")
        print(f"    Expected min: ~0, Actual: {dist.get('min')}")
        print(f"    Expected max: ~100, Actual: {dist.get('max')}")
        
        self.assertGreater(dist['min'], -5)
        self.assertLess(dist['min'], 10)
        self.assertGreater(dist['max'], 90)
        self.assertLess(dist['max'], 105)
        
        cat_quality = field_qualities.get('categorical')
        self.assertIsNotNone(cat_quality)
        dist = cat_quality['distribution']
        print(f"\n  Field: categorical")
        print(f"    Top values: {dist.get('topValues', [])[:3]}")
        
        self.assertIn('topValues', dist)
        self.assertTrue(len(dist['topValues']) > 0)
        
        top_value = dist['topValues'][0]
        print(f"    Most common value: '{top_value['value']}'")
        self.assertEqual(top_value['value'], 'A')
        
        print("\n  ✅ Distribution statistics test passed!")

    def test_field_qualities_structure(self):
        """Test that field_qualities has correct structure."""
        print("\n" + "="*60)
        print("TEST: Field Qualities Structure")
        print("="*60)
        
        df = pd.DataFrame({
            'id': range(10),
            'value': np.random.normal(0, 1, 10)
        })
        
        parser = PandasDataFrameDataParser(
            df=df,
            field_specs=[],
            infer_string_to_date=False,
            infer_number_to_dimension=False,
            other_params={}
        )
        
        field_qualities = parser.field_qualities
        
        print(f"\nParser created successfully")
        print(f"Field qualities type: {type(field_qualities)}")
        print(f"Field qualities keys: {list(field_qualities.keys())}")
        
        self.assertIsInstance(field_qualities, dict)
        self.assertEqual(len(field_qualities), 2)
        
        required_keys = [
            'fid', 'missingRate', 'uniqueCount', 'distinctRate',
            'dataType', 'distribution', 'anomalies', 'warnings',
            'isSuitableForAnalysis'
        ]
        
        for field_name, quality in field_qualities.items():
            print(f"\n  Field: {field_name}")
            print(f"    Keys: {list(quality.keys())}")
            
            for key in required_keys:
                self.assertIn(key, quality, f"Field {field_name} missing: {key}")
            
            self.assertIsInstance(quality['missingRate'], (int, float))
            self.assertIsInstance(quality['uniqueCount'], int)
            self.assertIsInstance(quality['distinctRate'], (int, float))
            self.assertIsInstance(quality['warnings'], list)
            self.assertIsInstance(quality['anomalies'], list)
            self.assertIsInstance(quality['isSuitableForAnalysis'], bool)
        
        print(f"\n  ✅ All {len(field_qualities)} fields have correct structure")
        print("\n  ✅ Structure test passed!")


class TestPygWalkerPropsIntegration(unittest.TestCase):
    """Test that PygWalker._get_props() includes fieldQualities."""

    def test_pygwalker_includes_field_qualities_in_props(self):
        """Test that PygWalker._get_props() includes fieldQualities."""
        print("\n" + "="*60)
        print("TEST: PygWalker._get_props() Includes fieldQualities")
        print("="*60)
        
        np.random.seed(42)
        n = 100
        
        df = pd.DataFrame({
            'id': range(n),
            'normal_field': np.random.normal(0, 1, n),
            'missing_field': np.where(
                np.random.random(n) < 0.4,  # 40% missing
                np.nan,
                np.random.normal(0, 1, n)
            ),
            'outlier_field': [1000, 2000] + list(np.random.normal(50, 10, n-2))  # 2 outliers
        })
        
        print(f"\nDataFrame created: {df.shape}")
        print(f"missing_field missing rate: ~40%")
        print(f"outlier_field has 2 extreme outliers (1000, 2000)")
        
        walker = PygWalker(
            gid="test_gid",
            dataset=df,
            field_specs=[],
            spec="",
            source_invoke_code="",
            theme_key="g2",
            appearance="light",
            show_cloud_tool=False,
            use_preview=False,
            kernel_computation=False,
            cloud_computation=False,
            use_save_tool=False,
            is_export_dataframe=False,
            kanaries_api_key="",
            default_tab="data",
            gw_mode="explore"
        )
        
        print(f"\nPygWalker instance created successfully")
        
        props = walker._get_props("test_comm")
        
        print(f"\nProps keys: {list(props.keys())}")
        
        self.assertIn(
            'fieldQualities', props,
            "fieldQualities not found in PygWalker._get_props() result!"
        )
        
        print(f"  ✅ fieldQualities found in props")
        
        field_qualities = props['fieldQualities']
        print(f"  fieldQualities type: {type(field_qualities)}")
        print(f"  fieldQualities keys: {list(field_qualities.keys())}")
        
        self.assertIsInstance(field_qualities, dict)
        self.assertEqual(len(field_qualities), 4)
        
        print(f"\nVerifying each field quality data...")
        
        required_keys = [
            'fid', 'missingRate', 'uniqueCount', 'distinctRate',
            'dataType', 'distribution', 'anomalies', 'warnings',
            'isSuitableForAnalysis'
        ]
        
        for field_name, quality in field_qualities.items():
            print(f"\n  Field: {field_name}")
            print(f"    Keys: {list(quality.keys())}")
            
            for key in required_keys:
                self.assertIn(
                    key, quality,
                    f"Field {field_name} missing required key: {key}"
                )
            
            self.assertIsInstance(quality['missingRate'], (int, float))
            self.assertIsInstance(quality['uniqueCount'], int)
            self.assertIsInstance(quality['distinctRate'], (int, float))
            self.assertIsInstance(quality['warnings'], list)
            self.assertIsInstance(quality['anomalies'], list)
            self.assertIsInstance(quality['isSuitableForAnalysis'], bool)
        
        print(f"\n  ✅ All {len(field_qualities)} fields have correct structure")
        
        missing_quality = field_qualities.get('missing_field')
        self.assertIsNotNone(missing_quality)
        print(f"\n  Field: missing_field")
        print(f"    Missing rate: {missing_quality['missingRate']:.1%}")
        print(f"    Unique count: {missing_quality['uniqueCount']}")
        print(f"    Warnings: {missing_quality['warnings']}")
        print(f"    Is suitable: {missing_quality['isSuitableForAnalysis']}")
        
        outlier_quality = field_qualities.get('outlier_field')
        self.assertIsNotNone(outlier_quality)
        print(f"\n  Field: outlier_field")
        print(f"    Anomalies: {len(outlier_quality['anomalies'])}")
        for anomaly in outlier_quality['anomalies']:
            print(f"      - {anomaly['type']}: {anomaly['description']}")
        print(f"    Is suitable: {outlier_quality['isSuitableForAnalysis']}")
        
        print("\n  ✅ PygWalker._get_props() integration test passed!")


def run_tests():
    """Run all integration tests."""
    print("\n" + "#"*60)
    print("#  FIELD QUALITY INTEGRATION TESTS")
    print("#  DataFrame -> DataParser -> SQL -> field_qualities")
    print("#"*60)
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestFieldQualityDataParserIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestPygWalkerPropsIntegration))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "#"*60)
    if result.wasSuccessful():
        print("#  ALL INTEGRATION TESTS PASSED!")
        print("#"*60)
        return 0
    else:
        print(f"#  {len(result.failures)} failures, {len(result.errors)} errors")
        print("#"*60)
        return 1


if __name__ == "__main__":
    sys.exit(run_tests())
