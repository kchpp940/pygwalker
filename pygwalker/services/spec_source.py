from urllib import request
from typing import Tuple
import json
import os

from pygwalker.services.global_var import GlobalVarManager
from pygwalker.services.cloud_service import read_config_from_cloud
from pygwalker.errors import InvalidConfigIdError, PrivacyError


def _is_json(s: str) -> bool:
    try:
        json.loads(s)
    except ValueError:
        return False
    return True


def _is_config_id(config_id: str) -> bool:
    if len(config_id) != 32:
        return False
    try:
        int(config_id, 16)
    except ValueError:
        return False
    return True


def _get_spec_from_server(config_id: str) -> str:
    url = f"https://i4rwxmw117.execute-api.us-east-1.amazonaws.com/default/pygwalker-config?config_id={config_id}"
    with request.urlopen(url, timeout=30) as resp:
        json_data = json.loads(resp.read().decode("utf-8"))
    
    if json_data["code"] != 0:
        raise InvalidConfigIdError(f"Invalid config id: {config_id}")
    
    return json_data["data"]["config_json"]


def _get_spec_from_url(url: str) -> str:
    with request.urlopen(url, timeout=15) as resp:
        return resp.read().decode("utf-8")


def _get_spec_from_local(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _ensure_local_file_exists(path: str) -> None:
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            f.write("")


def resolve_spec_source(spec: str) -> Tuple[str, str]:
    """
    从不同来源解析 spec 内容
    
    支持的来源类型：
    - 空字符串: 返回空 spec
    - JSON 字符串: 直接解析
    - ksf:// URL: 从云端读取
    - http/https URL: 从网络读取
    - 32 位 config_id: 从服务器读取
    - 文件路径: 从本地文件读取（不存在则创建空文件）
    
    Args:
        spec: spec 字符串，可以是 JSON、URL、文件路径等
        
    Returns:
        (spec_content, spec_type) 元组
        
    Raises:
        PrivacyError: 在离线模式下尝试访问网络
        InvalidConfigIdError: 无效的 config_id
        ValueError: 文件名过长
    """
    if not spec:
        return "", "empty_string"
    
    if _is_json(spec):
        return spec, "json_string"
    
    if spec.startswith("ksf://"):
        if GlobalVarManager.privacy == "offline":
            raise PrivacyError("Due to privacy policy, you can't use this spec offline")
        return read_config_from_cloud(spec[6:]), "json_ksf"
    
    if spec.startswith(("http:", "https:")):
        if GlobalVarManager.privacy == "offline":
            raise PrivacyError("Due to privacy policy, you can't use this spec offline")
        return _get_spec_from_url(spec), "json_http"
    
    if _is_config_id(spec):
        if GlobalVarManager.privacy == "offline":
            raise PrivacyError("Due to privacy policy, you can't use this spec offline")
        return _get_spec_from_server(spec), "json_server"
    
    if len(os.path.basename(spec)) > 200:
        raise ValueError("Spec file name too long")
    
    if os.path.exists(spec):
        return _get_spec_from_local(spec), "json_file"
    else:
        _ensure_local_file_exists(spec)
        return "", "json_file"
