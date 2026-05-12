from typing import List, Dict, Any, Union, Tuple
import json

from pygwalker.services.spec_source import resolve_spec_source
from pygwalker.services.version_compatibility import (
    apply_version_compatibility,
    create_spec_for_save,
)
from pygwalker.services.field_completion import fill_new_fields


def _is_gw_config(config: Dict[str, Any]) -> bool:
    """检查是否是 graphic-walker 配置格式"""
    return not bool({"config", "encodings", "visId"} - set(config.keys()))


def _is_pygwalker_config(config: Dict[str, Any]) -> bool:
    """检查是否是 pygwalker 配置格式"""
    return "config" in config and isinstance(config["config"], (list, str))


def _normalize_spec_obj(spec_obj: Any, spec_type: str) -> Dict[str, Any]:
    """
    标准化 spec 对象为统一的 pygwalker 格式
    
    支持的输入格式：
    - list: graphic-walker 配置列表 或 vega 配置列表
    - dict: graphic-walker 单个配置 或 pygwalker 完整配置
    
    Returns:
        标准化的 pygwalker 格式: {"chart_map": {}, "config": [...], "workflow_list": []}
    """
    if isinstance(spec_obj, list):
        if spec_obj and not _is_gw_config(spec_obj[0]):
            return {"chart_map": {}, "config": spec_obj, "workflow_list": []}, "vega_list"
        else:
            return {"chart_map": {}, "config": spec_obj, "workflow_list": []}, "gw_list"
    
    if isinstance(spec_obj, dict):
        if not _is_pygwalker_config(spec_obj):
            return {"chart_map": {}, "config": [spec_obj], "workflow_list": []}, "vega_single"
    
    return spec_obj, spec_type


def _parse_config_to_list(spec_obj: Dict[str, Any]) -> Dict[str, Any]:
    """
    如果 config 是 JSON 字符串，解析为列表
    
    这个步骤在版本兼容处理之后执行，因为 0.3.17a4 的适配器需要处理字符串格式。
    """
    if isinstance(spec_obj.get("config"), str):
        spec_obj["config"] = json.loads(spec_obj["config"])
    return spec_obj


def load_spec(
    spec: Union[str, List[Any], Dict[str, Any]],
    field_specs: List[Dict[str, str]]
) -> Tuple[Dict[str, Any], str]:
    """
    完整的 spec 加载管道
    
    处理流程：
    1. 解析来源（字符串/文件/URL/云端/服务器）
    2. 标准化格式（统一为 pygwalker 格式）
    3. 应用版本兼容（0.3.17a4 及之前版本）
    4. 解析 JSON 字符串 config
    5. 应用版本兼容（0.4.7a5 及之前版本）
    6. 字段补全（更新现有字段，添加新字段）
    
    Args:
        spec: spec 输入，可以是字符串、列表或字典
        field_specs: 当前数据源的字段定义
        
    Returns:
        (spec_obj, spec_type) 元组
        spec_obj 包含: chart_map, config, workflow_list, version
    """
    spec_type = "json_obj"
    
    if isinstance(spec, str):
        spec, source_type = resolve_spec_source(spec)
        if not spec:
            return {"chart_map": {}, "config": [], "workflow_list": []}, source_type
        
        try:
            spec_obj = json.loads(spec)
        except json.decoder.JSONDecodeError as e:
            raise ValueError("spec is not a valid json") from e
        
        spec_type = source_type
    else:
        spec_obj = spec
    
    spec_obj, spec_type = _normalize_spec_obj(spec_obj, spec_type)
    
    spec_obj = apply_version_compatibility(spec_obj)
    
    spec_obj = _parse_config_to_list(spec_obj)
    
    if not spec_type.startswith("vega") and spec_obj.get("config"):
        spec_obj["config"] = fill_new_fields(spec_obj["config"], field_specs)
    
    return spec_obj, spec_type


def save_spec(
    vis_spec: List[Dict[str, Any]],
    chart_map: Dict[str, Any],
    workflow_list: List[Any]
) -> Dict[str, Any]:
    """
    创建用于保存的 spec 对象
    
    这是 create_spec_for_save 的别名，保持 API 一致性
    
    Args:
        vis_spec: 可视化配置列表
        chart_map: 图表映射
        workflow_list: 工作流列表
        
    Returns:
        标准化的 spec 对象，可直接序列化为 JSON
    """
    return create_spec_for_save(vis_spec, chart_map, workflow_list)
