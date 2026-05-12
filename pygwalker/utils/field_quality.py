from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING
from dataclasses import dataclass
import math

import duckdb

if TYPE_CHECKING:
    from pygwalker.data_parsers.base import BaseDataParser


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


def analyze_field_quality(
    data_parser: Any,
    sample_size: int = 10000
) -> Dict[str, FieldQuality]:
    """
    Analyze the quality of all fields in the dataset.
    
    Args:
        data_parser: BaseDataParser instance
        sample_size: Maximum sample size for analysis
        
    Returns:
        Dict mapping field name to FieldQuality
    """
    field_metas = data_parser.field_metas
    placeholder_table = data_parser.placeholder_table_name
    
    results = {}
    
    for field_meta in field_metas:
        fid = field_meta["key"]
        data_type = field_meta["type"]
        
        try:
            quality = _analyze_single_field(
                data_parser,
                fid,
                data_type,
                placeholder_table,
                sample_size
            )
            results[fid] = quality
        except Exception:
            results[fid] = _create_default_quality(fid, data_type)
    
    return results


def _analyze_single_field(
    data_parser: Any,
    fid: str,
    data_type: str,
    placeholder_table: str,
    sample_size: int
) -> FieldQuality:
    """
    Analyze quality metrics for a single field.
    """
    total_count_sql = f"SELECT COUNT(*) FROM {placeholder_table}"
    total_count = _execute_sql(data_parser, total_count_sql)[0][0]
    
    if total_count == 0:
        return _create_default_quality(fid, data_type)
    
    missing_count_sql = f"SELECT COUNT(*) FROM {placeholder_table} WHERE {_quote_identifier(fid)} IS NULL"
    missing_count = _execute_sql(data_parser, missing_count_sql)[0][0]
    missing_rate = missing_count / total_count
    
    unique_count_sql = f"SELECT COUNT(DISTINCT {_quote_identifier(fid)}) FROM {placeholder_table} WHERE {_quote_identifier(fid)} IS NOT NULL"
    unique_count = _execute_sql(data_parser, unique_count_sql)[0][0]
    distinct_rate = unique_count / (total_count - missing_count) if (total_count - missing_count) > 0 else 0
    
    distribution = _calculate_distribution(
        data_parser,
        fid,
        data_type,
        placeholder_table,
        sample_size
    )
    
    anomalies = _detect_anomalies(
        data_parser,
        fid,
        data_type,
        placeholder_table,
        distribution
    )
    
    warnings = _generate_warnings(
        missing_rate,
        distinct_rate,
        data_type,
        anomalies
    )
    
    is_suitable = _is_suitable_for_analysis(
        missing_rate,
        distinct_rate,
        len(anomalies),
        data_type
    )
    
    return FieldQuality(
        fid=fid,
        missing_rate=missing_rate,
        unique_count=unique_count,
        distinct_rate=distinct_rate,
        data_type=data_type,
        distribution=distribution,
        anomalies=anomalies,
        warnings=warnings,
        is_suitable_for_analysis=is_suitable
    )


def _calculate_distribution(
    data_parser: Any,
    fid: str,
    data_type: str,
    placeholder_table: str,
    sample_size: int
) -> Dict[str, Any]:
    """
    Calculate basic distribution statistics.
    """
    distribution: Dict[str, Any] = {"type": data_type}
    
    if data_type in ("number", "int", "float"):
        stats_sql = f"""
        SELECT 
            MIN({_quote_identifier(fid)}) as min_val,
            MAX({_quote_identifier(fid)}) as max_val,
            AVG({_quote_identifier(fid)}) as avg_val,
            STDDEV({_quote_identifier(fid)}) as stddev_val
        FROM {placeholder_table}
        WHERE {_quote_identifier(fid)} IS NOT NULL
        """
        stats_result = _execute_sql(data_parser, stats_sql)
        if stats_result and stats_result[0]:
            min_val, max_val, avg_val, stddev_val = stats_result[0]
            distribution["min"] = _to_float(min_val)
            distribution["max"] = _to_float(max_val)
            distribution["mean"] = _to_float(avg_val)
            distribution["stddev"] = _to_float(stddev_val)
            
            if stddev_val and min_val and max_val and min_val != max_val:
                distribution["variation_ratio"] = float(stddev_val) / (float(max_val) - float(min_val))
    
    elif data_type in ("string", "nominal"):
        top_values_sql = f"""
        SELECT {_quote_identifier(fid)}, COUNT(*) as cnt
        FROM {placeholder_table}
        WHERE {_quote_identifier(fid)} IS NOT NULL
        GROUP BY {_quote_identifier(fid)}
        ORDER BY cnt DESC
        LIMIT 10
        """
        top_values = _execute_sql(data_parser, top_values_sql)
        distribution["topValues"] = [
            {"value": str(val), "count": int(cnt)}
            for val, cnt in top_values if val is not None
        ]
        
        if top_values:
            total_not_null = sum(cnt for _, cnt in top_values)
            if total_not_null > 0:
                distribution["entropy"] = _calculate_entropy(
                    [cnt for _, cnt in top_values],
                    total_not_null
                )
    
    elif data_type in ("datetime", "datetime_tz"):
        date_range_sql = f"""
        SELECT 
            MIN({_quote_identifier(fid)}) as min_date,
            MAX({_quote_identifier(fid)}) as max_date
        FROM {placeholder_table}
        WHERE {_quote_identifier(fid)} IS NOT NULL
        """
        date_result = _execute_sql(data_parser, date_range_sql)
        if date_result and date_result[0]:
            min_date, max_date = date_result[0]
            distribution["min_date"] = str(min_date) if min_date else None
            distribution["max_date"] = str(max_date) if max_date else None
    
    return distribution


def _detect_anomalies(
    data_parser: Any,
    fid: str,
    data_type: str,
    placeholder_table: str,
    distribution: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Detect potential anomalies in the data.
    """
    anomalies: List[Dict[str, Any]] = []
    
    if data_type in ("number", "int", "float"):
        if distribution.get("mean") is not None and distribution.get("stddev"):
            mean = distribution["mean"]
            stddev = distribution["stddev"]
            if stddev > 0:
                z_score_threshold = 3
                outlier_sql = f"""
                SELECT {_quote_identifier(fid)}
                FROM {placeholder_table}
                WHERE {_quote_identifier(fid)} IS NOT NULL
                AND ABS(({_quote_identifier(fid)} - {mean}) / {stddev}) > {z_score_threshold}
                LIMIT 20
                """
                outliers = _execute_sql(data_parser, outlier_sql)
                if outliers:
                    anomalies.append({
                        "type": "outlier",
                        "description": f"Detected {len(outliers)} potential outliers (z-score > 3)",
                        "samples": [_to_float(val[0]) for val in outliers[:5] if val[0] is not None],
                        "severity": "medium" if len(outliers) < 10 else "high"
                    })
    
    elif data_type in ("string", "nominal"):
        top_values = distribution.get("top_values", [])
        if top_values:
            total_count = sum(v["count"] for v in top_values)
            if total_count > 0:
                for val in top_values[:3]:
                    if val["count"] / total_count > 0.9:
                        anomalies.append({
                            "type": "dominant_value",
                            "description": f"Value '{val['value']}' dominates the distribution ({val['count']/total_count*100:.1f}%)",
                            "value": val["value"],
                            "percentage": val["count"] / total_count * 100,
                            "severity": "medium"
                        })
    
    return anomalies


def _generate_warnings(
    missing_rate: float,
    distinct_rate: float,
    data_type: str,
    anomalies: List[Dict[str, Any]]
) -> List[str]:
    """
    Generate warning messages based on quality metrics.
    """
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
    """
    Determine if field is generally suitable for analysis.
    """
    if missing_rate > 0.8:
        return False
    
    if distinct_rate < 0.02 and data_type in ("number", "int", "float"):
        return False
    
    if anomaly_count > 5:
        return False
    
    return True


def _quote_identifier(fid: str) -> str:
    """
    Properly quote identifiers for SQL.
    """
    return f'"{fid}"'


def _execute_sql(data_parser: Any, sql: str) -> List[List[Any]]:
    """
    Execute SQL and return results as list of lists.
    """
    try:
        result = data_parser.get_datas_by_sql(sql)
        if not result:
            return []
        return [[row.get(key) for key in row.keys()] for row in result]
    except Exception:
        return []


def _to_float(value: Any) -> Optional[float]:
    """
    Convert value to float, handling None and special cases.
    """
    if value is None:
        return None
    try:
        if isinstance(value, (int, float)):
            if math.isinf(value) or math.isnan(value):
                return None
            return float(value)
        return float(value)
    except (TypeError, ValueError):
        return None


def _calculate_entropy(counts: List[int], total: int) -> float:
    """
    Calculate Shannon entropy of the distribution.
    """
    if total == 0:
        return 0.0
    
    entropy = 0.0
    for count in counts:
        if count > 0:
            p = count / total
            entropy -= p * math.log2(p)
    
    return entropy


def _create_default_quality(fid: str, data_type: str) -> FieldQuality:
    """
    Create a default quality object when analysis fails.
    """
    return FieldQuality(
        fid=fid,
        missing_rate=0.0,
        unique_count=0,
        distinct_rate=0.0,
        data_type=data_type,
        distribution={"type": data_type},
        anomalies=[],
        warnings=["Quality analysis unavailable"],
        is_suitable_for_analysis=True
    )


def field_quality_to_dict(quality: FieldQuality) -> Dict[str, Any]:
    """
    Convert FieldQuality to a dictionary for JSON serialization.
    """
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
