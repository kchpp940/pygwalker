#!/usr/bin/env python3
"""
Regression tests for field quality analysis module.
Tests: missing rate, unique count, anomaly detection, serialization.
"""

import unittest
import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class FieldQuality:
    fid: str
    missing_rate: float
    unique_count: int
    distinct_rate: float
    data_type: str
    distribution: Dict[str, Any]
    anomalies: List[Dict[str, Any]]
    warnings: List[str]
    is_suitable_for_analysis: bool


def _generate_warnings(
    missing_rate: float,
    distinct_rate: float,
    data_type: str,
    anomalies: List[Dict[str, Any]]
) -> List[str]:
    warnings: List[str] = []
    
    if missing_rate > 0.5:
        warnings.append(f"High missing rate ({missing_rate*100:.1f}%)")
    elif missing_rate > 0.2:
        warnings.append(f"Moderate missing rate ({missing_rate*100:.1f}%)")
    
    if distinct_rate < 0.01 and data_type in ("number", "int", "float"):
        warnings.append("Low variability - consider if this is a constant field")
    
    if distinct_rate > 0.95 and data_type in ("string", "nominal"):
        warnings.append("High cardinality - may not be suitable for categorical analysis")
    
    high_anomalies = [a for a in anomalies if a.get("severity") == "high"]
    if high_anomalies:
        warnings.append(f"Detected {len(high_anomalies)} high-severity anomalies")
    
    return warnings


def _is_suitable_for_analysis(
    missing_rate: float,
    distinct_rate: float,
    anomaly_count: int,
    data_type: str
) -> bool:
    if missing_rate > 0.8:
        return False
    
    if distinct_rate < 0.02 and data_type in ("number", "int", "float"):
        return False
    
    if anomaly_count > 5:
        return False
    
    return True


def field_quality_to_dict(quality: FieldQuality) -> Dict[str, Any]:
    return {
        "fid": quality.fid,
        "missingRate": quality.missing_rate,
        "uniqueCount": quality.unique_count,
        "distinctRate": quality.distinct_rate,
        "dataType": quality.data_type,
        "distribution": quality.distribution,
        "anomalies": quality.anomalies,
        "warnings": quality.warnings,
        "isSuitableForAnalysis": quality.is_suitable_for_analysis
    }


class TestFieldQualityMissingRate(unittest.TestCase):
    """Test missing rate calculation and warnings."""

    def test_no_missing_values(self):
        """No missing values should have no warnings and be suitable."""
        warnings = _generate_warnings(0.0, 0.5, "number", [])
        suitable = _is_suitable_for_analysis(0.0, 0.5, 0, "number")
        self.assertEqual(warnings, [])
        self.assertTrue(suitable)

    def test_low_missing_rate(self):
        """10% missing should have no warnings and be suitable."""
        warnings = _generate_warnings(0.1, 0.5, "number", [])
        suitable = _is_suitable_for_analysis(0.1, 0.5, 0, "number")
        self.assertEqual(warnings, [])
        self.assertTrue(suitable)

    def test_moderate_missing_rate(self):
        """30% missing should have moderate warning but still suitable."""
        warnings = _generate_warnings(0.3, 0.5, "number", [])
        suitable = _is_suitable_for_analysis(0.3, 0.5, 0, "number")
        self.assertTrue(any("Moderate missing rate" in w for w in warnings))
        self.assertTrue(suitable)

    def test_high_missing_rate(self):
        """60% missing should have high warning but still suitable (<80%)."""
        warnings = _generate_warnings(0.6, 0.5, "number", [])
        suitable = _is_suitable_for_analysis(0.6, 0.5, 0, "number")
        self.assertTrue(any("High missing rate" in w for w in warnings))
        self.assertTrue(suitable)

    def test_extreme_missing_rate(self):
        """90% missing should have high warning and NOT be suitable."""
        warnings = _generate_warnings(0.9, 0.5, "number", [])
        suitable = _is_suitable_for_analysis(0.9, 0.5, 0, "number")
        self.assertTrue(any("High missing rate" in w for w in warnings))
        self.assertFalse(suitable)


class TestFieldQualityUniqueCount(unittest.TestCase):
    """Test unique count and cardinality warnings."""

    def test_constant_numeric_field(self):
        """Constant numeric field (0.1% distinct) should have low variability warning."""
        warnings = _generate_warnings(0.0, 0.001, "number", [])
        suitable = _is_suitable_for_analysis(0.0, 0.001, 0, "number")
        self.assertTrue(any("Low variability" in w for w in warnings))
        self.assertFalse(suitable)

    def test_low_variability_numeric(self):
        """Low variability (0.5% distinct) should have warning and not be suitable."""
        warnings = _generate_warnings(0.0, 0.005, "number", [])
        suitable = _is_suitable_for_analysis(0.0, 0.005, 0, "number")
        self.assertTrue(any("Low variability" in w for w in warnings))
        self.assertFalse(suitable)

    def test_normal_variability_numeric(self):
        """Normal variability (50% distinct) should have no warnings."""
        warnings = _generate_warnings(0.0, 0.5, "number", [])
        suitable = _is_suitable_for_analysis(0.0, 0.5, 0, "number")
        self.assertEqual(warnings, [])
        self.assertTrue(suitable)

    def test_high_cardinality_string(self):
        """Very high cardinality string (99% distinct) should have warning."""
        warnings = _generate_warnings(0.0, 0.99, "string", [])
        suitable = _is_suitable_for_analysis(0.0, 0.99, 0, "string")
        self.assertTrue(any("High cardinality" in w for w in warnings))
        self.assertTrue(suitable)


class TestFieldQualityAnomalyDetection(unittest.TestCase):
    """Test anomaly detection warnings."""

    def test_no_anomalies(self):
        """No anomalies should have no warnings and be suitable."""
        warnings = _generate_warnings(0.0, 0.5, "number", [])
        suitable = _is_suitable_for_analysis(0.0, 0.5, 0, "number")
        self.assertEqual(warnings, [])
        self.assertTrue(suitable)

    def test_medium_anomaly(self):
        """Single medium anomaly should have no specific warning."""
        anomalies = [{"type": "outlier", "severity": "medium", "description": "Test"}]
        warnings = _generate_warnings(0.0, 0.5, "number", anomalies)
        suitable = _is_suitable_for_analysis(0.0, 0.5, len(anomalies), "number")
        self.assertEqual(warnings, [])
        self.assertTrue(suitable)

    def test_high_anomaly(self):
        """Single high anomaly should have high-severity warning."""
        anomalies = [{"type": "outlier", "severity": "high", "description": "Test"}]
        warnings = _generate_warnings(0.0, 0.5, "number", anomalies)
        suitable = _is_suitable_for_analysis(0.0, 0.5, len(anomalies), "number")
        self.assertTrue(any("high-severity anomalies" in w for w in warnings))
        self.assertTrue(suitable)

    def test_multiple_high_anomalies(self):
        """6 high anomalies should have warning and NOT be suitable."""
        anomalies = [
            {"type": "outlier", "severity": "high", "description": f"Test{i}"}
            for i in range(6)
        ]
        warnings = _generate_warnings(0.0, 0.5, "number", anomalies)
        suitable = _is_suitable_for_analysis(0.0, 0.5, len(anomalies), "number")
        self.assertTrue(any("high-severity anomalies" in w for w in warnings))
        self.assertFalse(suitable)


class TestFieldQualitySerialization(unittest.TestCase):
    """Test FieldQuality serialization."""

    def test_serialization_has_all_fields(self):
        """Serialized dict should contain all required keys."""
        quality = FieldQuality(
            fid="test_field",
            missing_rate=0.15,
            unique_count=100,
            distinct_rate=0.25,
            data_type="number",
            distribution={"type": "number", "min": 0, "max": 100, "mean": 50},
            anomalies=[{"type": "outlier", "severity": "medium", "description": "Test"}],
            warnings=["Moderate missing rate (15.0%)"],
            is_suitable_for_analysis=True
        )
        
        quality_dict = field_quality_to_dict(quality)
        
        required_keys = [
            "fid", "missingRate", "uniqueCount", "distinctRate",
            "dataType", "distribution", "anomalies", "warnings",
            "isSuitableForAnalysis"
        ]
        
        for key in required_keys:
            self.assertIn(key, quality_dict, f"Missing key: {key}")

    def test_serialization_values_match(self):
        """Serialized values should match original values."""
        quality = FieldQuality(
            fid="test_field",
            missing_rate=0.15,
            unique_count=100,
            distinct_rate=0.25,
            data_type="number",
            distribution={"type": "number"},
            anomalies=[],
            warnings=[],
            is_suitable_for_analysis=True
        )
        
        quality_dict = field_quality_to_dict(quality)
        
        self.assertEqual(quality_dict["fid"], "test_field")
        self.assertEqual(quality_dict["missingRate"], 0.15)
        self.assertEqual(quality_dict["uniqueCount"], 100)
        self.assertEqual(quality_dict["distinctRate"], 0.25)
        self.assertEqual(quality_dict["dataType"], "number")
        self.assertEqual(quality_dict["distribution"], {"type": "number"})
        self.assertEqual(quality_dict["anomalies"], [])
        self.assertEqual(quality_dict["warnings"], [])
        self.assertEqual(quality_dict["isSuitableForAnalysis"], True)

    def test_camel_case_conversion(self):
        """Python snake_case should be converted to JavaScript camelCase."""
        quality = FieldQuality(
            fid="field",
            missing_rate=0.1,
            unique_count=50,
            distinct_rate=0.5,
            data_type="string",
            distribution={},
            anomalies=[],
            warnings=[],
            is_suitable_for_analysis=False
        )
        
        quality_dict = field_quality_to_dict(quality)
        
        self.assertIn("missingRate", quality_dict)
        self.assertIn("uniqueCount", quality_dict)
        self.assertIn("distinctRate", quality_dict)
        self.assertIn("dataType", quality_dict)
        self.assertIn("isSuitableForAnalysis", quality_dict)
        
        self.assertNotIn("missing_rate", quality_dict)
        self.assertNotIn("unique_count", quality_dict)
        self.assertNotIn("distinct_rate", quality_dict)
        self.assertNotIn("data_type", quality_dict)
        self.assertNotIn("is_suitable_for_analysis", quality_dict)


class TestFieldQualityEdgeCases(unittest.TestCase):
    """Test edge cases."""

    def test_boundary_missing_rate_80_percent(self):
        """80% missing should still be suitable (boundary test)."""
        suitable = _is_suitable_for_analysis(0.8, 0.5, 0, "number")
        self.assertTrue(suitable)

    def test_boundary_missing_rate_81_percent(self):
        """81% missing should NOT be suitable (boundary test)."""
        suitable = _is_suitable_for_analysis(0.81, 0.5, 0, "number")
        self.assertFalse(suitable)

    def test_boundary_anomaly_count_5(self):
        """5 anomalies should still be suitable (boundary test)."""
        suitable = _is_suitable_for_analysis(0.0, 0.5, 5, "number")
        self.assertTrue(suitable)

    def test_boundary_anomaly_count_6(self):
        """6 anomalies should NOT be suitable (boundary test)."""
        suitable = _is_suitable_for_analysis(0.0, 0.5, 6, "number")
        self.assertFalse(suitable)

    def test_numeric_vs_string_warnings(self):
        """Warnings should differ based on data type."""
        numeric_warnings = _generate_warnings(0.0, 0.005, "number", [])
        string_warnings = _generate_warnings(0.0, 0.005, "string", [])
        
        self.assertTrue(any("Low variability" in w for w in numeric_warnings))
        self.assertFalse(any("Low variability" in w for w in string_warnings))


if __name__ == "__main__":
    unittest.main(verbosity=2)
