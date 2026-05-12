from typing import List, Dict, Any, Optional
import json
import random

from .encode import DataFrameEncoder


def estimate_average_data_size(datas: List[Dict[str, Any]]) -> int:
    """Estimate average data bytes size"""
    smp0 = datas[::max(len(datas)//32, 1)]
    smp1 = datas[::max(len(datas)//37, 1)]
    avg_size = len(json.dumps(smp0, cls=DataFrameEncoder)) / len(smp0)
    avg_size = max(avg_size, len(json.dumps(smp1, cls=DataFrameEncoder)) / len(smp1))
    return avg_size


def smart_sample_datas(
    datas: List[Dict[str, Any]],
    max_count: int,
    preserve_boundaries: bool = True
) -> List[Dict[str, Any]]:
    """
    Smart sampling that preserves data distribution characteristics.
    
    Strategy:
    1. For small datasets (<= max_count): return all data
    2. For moderate datasets (max_count < n <= 2*max_count): use stratified sampling
    3. For large datasets (> 2*max_count): use reservoir sampling with boundary preservation
    
    Args:
        datas: Original data list
        max_count: Maximum sample size
        preserve_boundaries: Whether to preserve first/last records
        
    Returns:
        Sampled data list
    """
    n = len(datas)
    if n <= max_count:
        return datas
    
    if preserve_boundaries and max_count >= 2:
        boundary_count = min(2, max_count)
        sample_count = max_count - boundary_count
        
        middle_data = datas[boundary_count:-boundary_count] if boundary_count == 2 else datas[1:]
        
        if len(middle_data) <= sample_count:
            sampled_middle = middle_data
        else:
            step = len(middle_data) / sample_count
            sampled_middle = [
                middle_data[int(i * step)] 
                for i in range(sample_count)
            ]
        
        if boundary_count == 2:
            return [datas[0]] + sampled_middle + [datas[-1]]
        else:
            return [datas[0]] + sampled_middle
    
    step = n / max_count
    return [datas[int(i * step)] for i in range(max_count)]


def sample_datas_by_byte_limit(
    datas: List[Dict[str, Any]],
    byte_limit: int,
    min_sample_size: int = 100
) -> List[Dict[str, Any]]:
    """
    Sample data based on byte limit, with smart distribution preservation.
    
    Args:
        datas: Original data list
        byte_limit: Maximum byte size
        min_sample_size: Minimum sample size to preserve
        
    Returns:
        Sampled data list
    """
    if len(datas) <= 1024:
        return datas
    
    avg_size = estimate_average_data_size(datas)
    max_count = int(byte_limit / avg_size)
    max_count = max(min_sample_size, max_count)
    
    if len(datas) <= 2 * max_count:
        return datas
    
    return smart_sample_datas(datas, max_count)
