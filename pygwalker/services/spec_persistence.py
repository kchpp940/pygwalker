from typing import Dict, Any, List, Optional

from pygwalker.services.version_compatibility import create_spec_for_save


def build_update_spec_obj(
    vis_spec: List[Dict[str, Any]],
    workflow_list: Optional[List[Any]] = None,
) -> Dict[str, Any]:
    """
    从前端通信数据构建 update 用的 spec 对象
    
    用于 update_spec 通信端点：从 data["visSpec"] 和 data.get("workflowList")
    构建标准化的 spec 对象，用于持久化。
    
    chart_map 始终为空对象，因为 save_chart_endpoint 单独处理图表数据。
    
    Args:
        vis_spec: 前端传来的可视化配置列表（data["visSpec"]）
        workflow_list: 前端传来的工作流列表（data.get("workflowList")），默认为空列表
        
    Returns:
        标准化的 spec 对象，可直接序列化为 JSON 写入文件或上传云端
    """
    return create_spec_for_save(
        vis_spec=vis_spec,
        chart_map={},
        workflow_list=workflow_list or [],
    )


def build_upload_spec_obj(
    vis_spec: List[Dict[str, Any]],
    workflow_list: List[Any],
) -> Dict[str, Any]:
    """
    从当前实例状态构建 upload 用的 spec 对象
    
    用于 upload_spec_to_cloud 通信端点：从 self.vis_spec 和 self.workflow_list
    构建标准化的 spec 对象，用于上传到云端。
    
    chart_map 始终为空对象，因为云端只需要配置信息。
    
    Args:
        vis_spec: 当前实例的可视化配置（self.vis_spec）
        workflow_list: 当前实例的工作流列表（self.workflow_list）
        
    Returns:
        标准化的 spec 对象，可直接序列化为 JSON 上传到云端
    """
    return create_spec_for_save(
        vis_spec=vis_spec,
        chart_map={},
        workflow_list=workflow_list,
    )
