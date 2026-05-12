from typing import List, Dict, Any
from packaging.version import Version
from copy import deepcopy
import json

from pygwalker.services.fname_encodings import rename_columns


class SpecVersionAdapter:
    """
    版本适配器基类
    所有版本迁移逻辑都应该实现这个基类
    """
    
    version_threshold: str = "0.0.0"
    
    @classmethod
    def should_apply(cls, spec_version: str) -> bool:
        return Version(spec_version or "0.1.0") <= Version(cls.version_threshold)
    
    @classmethod
    def adapt(cls, spec_obj: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError("Subclasses must implement adapt method")


class Adapter_0_3_17a4(SpecVersionAdapter):
    """
    版本 0.3.17a4 及以下的适配器
    处理旧版本的 fid 到新 fid 的映射转换
    """
    
    version_threshold: str = "0.3.17a4"
    
    @classmethod
    def adapt(cls, spec_obj: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(spec_obj.get("config"), str):
            return spec_obj
        
        config = spec_obj["config"]
        config_obj = json.loads(config)
        
        for chart_item in config_obj:
            old_fid_fname_map = {
                field["fid"]: field["name"]
                for field in chart_item["encodings"]["dimensions"] + chart_item["encodings"]["measures"]
                if not field.get("computed", False) and field.get("fid") not in ["gw_mea_val_fid", "gw_mea_key_fid"]
            }
            
            old_fid_list = []
            fname_list = []
            for old_fid, fname in old_fid_fname_map.items():
                old_fid_list.append(old_fid)
                fname_list.append(fname)
            
            new_fid_list = rename_columns(fname_list)
            for old_fid, new_fid in zip(old_fid_list, new_fid_list):
                config = config.replace(old_fid, new_fid)
        
        spec_obj["config"] = config
        return spec_obj


def _is_gw_chart_config(config_item: Dict[str, Any]) -> bool:
    """检查是否是 graphic-walker 图表配置格式"""
    return not bool({"config", "encodings", "visId"} - set(config_item.keys()))


class Adapter_0_4_7a5(SpecVersionAdapter):
    """
    版本 0.4.7a5 及以下的适配器
    处理时区偏移和字段 offset 的默认值设置
    """
    
    version_threshold: str = "0.4.7a5"
    
    @classmethod
    def adapt(cls, spec_obj: Dict[str, Any]) -> Dict[str, Any]:
        config = spec_obj.get("config", [])
        if not isinstance(config, list) or not config:
            return spec_obj
        
        if not _is_gw_chart_config(config[0]):
            return spec_obj
        
        config = deepcopy(config)
        
        for chart_item in config:
            if "config" in chart_item and chart_item["config"].get("timezoneDisplayOffset", None) is None:
                chart_item["config"]["timezoneDisplayOffset"] = 0
            
            if "encodings" in chart_item:
                for item_list in chart_item["encodings"].values():
                    for item in item_list:
                        item["offset"] = 0
                        if isinstance(item.get("expression", {}).get("params"), list):
                            for param in item["expression"]["params"]:
                                if param.get("type") == "offset":
                                    param["value"] = 0
        
        spec_obj["config"] = config
        return spec_obj


VERSION_ADAPTERS: List[SpecVersionAdapter] = [
    Adapter_0_3_17a4,
    Adapter_0_4_7a5,
]


def apply_version_compatibility(spec_obj: Dict[str, Any]) -> Dict[str, Any]:
    """
    应用所有需要的版本兼容性适配器
    
    Args:
        spec_obj: 原始 spec 对象
        
    Returns:
        转换后的 spec 对象
    """
    version = spec_obj.get("version", "0.1.0")
    
    for adapter in VERSION_ADAPTERS:
        if adapter.should_apply(version):
            spec_obj = adapter.adapt(spec_obj)
    
    return spec_obj


def get_current_version() -> str:
    """获取当前 pygwalker 版本"""
    from pygwalker import __version__
    return __version__


def create_spec_for_save(
    vis_spec: List[Dict[str, Any]],
    chart_map: Dict[str, Any],
    workflow_list: List[Any]
) -> Dict[str, Any]:
    """
    创建用于保存的 spec 对象
    
    Args:
        vis_spec: 可视化配置列表
        chart_map: 图表映射
        workflow_list: 工作流列表
        
    Returns:
        标准化的 spec 对象，可直接序列化为 JSON
    """
    return {
        "config": vis_spec,
        "chart_map": chart_map,
        "version": get_current_version(),
        "workflow_list": workflow_list,
    }
