from typing import Tuple, Dict, Any, List, Union

from pygwalker.services.spec_source import resolve_spec_source
from pygwalker.services.field_completion import fill_new_fields
from pygwalker.services.version_compatibility import (
    apply_version_compatibility,
    create_spec_for_save,
)
from pygwalker.services.spec_pipeline import (
    load_spec,
    save_spec,
)


def _is_gw_config(config: Dict[str, Any]) -> bool:
    return not bool({"config", "encodings", "visId"} - set(config.keys()))


def _is_pygwalker_config(config: Dict[str, Any]) -> bool:
    return "config" in config and isinstance(config["config"], (list, str))


def get_spec_json(spec: Union[str, List[Any], Dict[str, Any]]) -> Tuple[Dict[str, Any], str]:
    """
    获取 spec 的 JSON 对象和类型
    向后兼容：此函数不执行字段补全，只完成：
    1. 来源解析
    2. 格式标准化
    3. 版本兼容
    
    字段补全应该单独调用 fill_new_fields 完成。
    新代码建议直接使用 spec_pipeline.load_spec(spec, field_specs)。
    """
    import json
    
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
    
    if isinstance(spec_obj, list):
        if spec_obj and not _is_gw_config(spec_obj[0]):
            return {"chart_map": {}, "config": spec_obj, "workflow_list": []}, "vega_list"
        else:
            spec_obj = {"chart_map": {}, "config": spec_obj, "workflow_list": []}
    
    if isinstance(spec_obj, dict) and not _is_pygwalker_config(spec_obj):
        return {"chart_map": {}, "config": [spec_obj], "workflow_list": []}, "vega_single"
    
    spec_obj = apply_version_compatibility(spec_obj)
    
    if isinstance(spec_obj.get("config"), str):
        spec_obj["config"] = json.loads(spec_obj["config"])
    
    return spec_obj, spec_type
