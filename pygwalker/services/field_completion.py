from typing import List, Dict, Any
from copy import deepcopy

from pygwalker.utils.randoms import rand_str


ENCODING_CHANNELS = [
    "rows", "columns", "color", "opacity", "size", "shape", 
    "radius", "theta", "longitude", "latitude", "geoId", 
    "details", "filters", "text"
]


def update_field_properties(
    field: Dict[str, Any],
    all_fields_map: Dict[str, Dict[str, Any]]
) -> Dict[str, Any]:
    """
    从 all_fields 更新字段属性
    
    Args:
        field: 要更新的字段
        all_fields_map: 所有字段的 fid -> field 映射
        
    Returns:
        更新后的字段
    """
    if field.get("computed", False):
        return field
    
    fid = field.get("fid")
    if fid is None or fid not in all_fields_map:
        return field
    
    source_field = all_fields_map[fid]
    
    updated_field = {
        **field,
        "name": source_field.get("name", field.get("name", "")),
        "analyticType": source_field.get("analyticType", field.get("analyticType", "dimension")),
        "semanticType": source_field.get("semanticType", field.get("semanticType", "nominal")),
    }
    
    if "basename" not in updated_field:
        updated_field["basename"] = updated_field["name"]
    
    return updated_field


def extract_existing_fids(
    chart_item: Dict[str, Any]
) -> set:
    """
    从图表配置中提取已存在的字段 fid
    
    Args:
        chart_item: 单个图表配置
        
    Returns:
        已存在的 fid 集合
    """
    encodings = chart_item.get("encodings", {})
    existing_fids = set()
    
    for field in encodings.get("dimensions", []):
        fid = field.get("fid")
        if fid:
            existing_fids.add(fid)
    
    for field in encodings.get("measures", []):
        fid = field.get("fid")
        if fid:
            existing_fids.add(fid)
    
    return existing_fids


def create_new_gw_field(
    field: Dict[str, Any]
) -> Dict[str, Any]:
    """
    创建新的 graphic-walker 字段对象
    
    Args:
        field: 原始字段定义
        
    Returns:
        带有 gw 所需属性的字段
    """
    return {
        **field,
        "basename": field["name"],
        "dragId": "GW_" + rand_str(),
        "offset": 0
    }


def collect_new_fields(
    all_fields: List[Dict[str, Any]],
    existing_fids: set
) -> Dict[str, List[Dict[str, Any]]]:
    """
    收集新字段（在 all_fields 中但不在配置中的字段）
    
    Args:
        all_fields: 数据源的所有字段
        existing_fids: 已存在于配置中的 fid 集合
        
    Returns:
        包含新维度和新度量的字典
    """
    new_dimensions = []
    new_measures = []
    
    for field in all_fields:
        if field["fid"] not in existing_fids:
            gw_field = create_new_gw_field(field)
            if field["analyticType"] == "dimension":
                new_dimensions.append(gw_field)
            else:
                new_measures.append(gw_field)
    
    return {
        "dimensions": new_dimensions,
        "measures": new_measures
    }


def update_encoding_channels(
    chart_item: Dict[str, Any],
    all_fields_map: Dict[str, Dict[str, Any]]
) -> Dict[str, Any]:
    """
    更新编码通道中的字段属性
    
    Args:
        chart_item: 单个图表配置
        all_fields_map: 所有字段的 fid -> field 映射
        
    Returns:
        更新后的图表配置
    """
    chart_item = deepcopy(chart_item)
    encodings = chart_item["encodings"]
    
    encodings["dimensions"] = [
        update_field_properties(field, all_fields_map) 
        for field in encodings.get("dimensions", [])
    ]
    encodings["measures"] = [
        update_field_properties(field, all_fields_map) 
        for field in encodings.get("measures", [])
    ]
    
    for channel in ENCODING_CHANNELS:
        if channel in encodings and isinstance(encodings[channel], list):
            encodings[channel] = [
                update_field_properties(field, all_fields_map) 
                for field in encodings[channel]
            ]
    
    return chart_item


def fill_new_fields(
    config: List[Dict[str, Any]],
    all_fields: List[Dict[str, str]]
) -> List[Dict[str, Any]]:
    """
    当数据源 schema 改变时，填充新字段到每个图表配置并更新现有字段
    
    这个函数确保：
    1. 图表顺序保持不变
    2. 字段映射正确更新（从当前数据源）
    3. 编码配置（rows, columns, color 等）保持原样
    4. 聚合方法 (aggName) 保持不变
    5. 计算字段不被修改
    
    Args:
        config: 图表配置列表
        all_fields: 数据源的所有字段定义
        
    Returns:
        更新后的图表配置列表
    """
    config = deepcopy(config)
    
    all_fields_map = {field["fid"]: field for field in all_fields}
    
    for chart_item in config:
        updated_item = update_encoding_channels(chart_item, all_fields_map)
        chart_item.update(updated_item)
        
        existing_fids = extract_existing_fids(chart_item)
        
        new_fields = collect_new_fields(all_fields, existing_fids)
        
        chart_item["encodings"]["dimensions"].extend(new_fields["dimensions"])
        chart_item["encodings"]["measures"].extend(new_fields["measures"])
    
    return config
