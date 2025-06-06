from typing import List
from pydantic import BaseModel, Field

from gradio_mcp.clients import get_all_clients

import os
from typing import Dict, Type
from fastapi import APIRouter, HTTPException, Path
from entity.proxy import HTTPProxyConfig, HTTPSProxyConfig, STCPProxyConfig, SUDPProxyConfig, TCPMuxProxyConfig, TCPProxyConfig, UDPProxyConfig, XTCPProxyConfig
from utils.ConfigManager import ConfigManager
from utils.database import DataBase

proxies = ["ssh-t4", "mc-server"]

def check_client_id(client_id: int) -> bool:
    """检查指定的 client_id 是否存在于 clients 列表中

    Args:
        client_id (int): 要检查的客户端ID

    Returns:
        bool: 如果存在返回 True，否则返回 False
    """
    clients = get_all_clients()["data"]
    for client in clients:
        if client["id"] == client_id:
            return True
    return False

def get_all_proxy():
    """获取所有隧道  
    
    返回的格式为：
    ```json
    {
        "status": "成功",
        "message": "获取客户端列表成功",
        "data": [
            {
                "client_id": 0,
                "name": "ssh-t4",
                "type": "tcp",
                "localIp": "10.0.0.1",
                "localPort": 22,
                "remotePort": 1022
            }
        ]
    }
    ```
    
    - `status`: 操作状态，成功或失败
    - `message`: 操作信息
    - `data`: 客户端列表，格式为json数组，每个元素包含以下
        - `client_id`: 客户端ID
        - `name`: 隧道名称
        - `type`: 隧道类型
        - `localIp`: 本地IP地址
        - `localPort`: 本地端口
        - `remotePort`: 远程端口
    
    Returns:
        dict: 包含状态和信息的json, 格式为`{"status": "成功"|"失败", "message": "消息", "data": 数据, json格式, 如失败data为Nano}`
    """
    return {
        "status": "成功",
        "message": "获取所有隧道成功",
        "data": [
            {
                "client_id": 1,
                "name": "ssh-t4",
                "type": "tcp",
                "localIp": "10.0.0.1",
                "localPort": 22,
                "remotePort": 1022
            },
            {
                "client_id": 1,
                "name": "mc-server",
                "type": "udp",
                "localIp": "10.0.0.2",
                "localPort": 25565,
                "remotePort": 25565
            }
        ]
    }

def get_proxy_by_client_id(client_id: int) -> dict:
    """根据客户端ID获取该客户端下的所有隧道
    
    返回的格式为：
    ```json
    {
        "status": "成功",
        "message": "获取客户端列表成功",
        "data": [
            {
                "name": "ssh-t4",
                "type": "tcp",
                "localIp": "10.0.0.1",
                "localPort": 22,
                "remotePort": 1022
            }
        ]
    }
    ```
    
    - `status`: 操作状态，成功或失败
    - `message`: 操作信息
    - `data`: 客户端列表，格式为json数组，每个元素包含以下
        - `name`: 隧道名称
        - `type`: 隧道类型
        - `localIp`: 本地IP地址
        - `localPort`: 本地端口
        - `remotePort`: 远程端口
    
    Args:
        client_id (int): 客户端ID

    Returns:
        dict: 包含状态和信息的json, 格式为`{"status": "成功"|"失败", "message": "消息", "data": 数据, json格式, 如失败data为Nano}`
    """
    if isinstance(client_id, str):
        try:
            client_id = int(client_id)
        except ValueError:
            return {
                "status": "失败",
                "message": "客户端ID格式错误",
                "data": None
            }
    
    if not check_client_id(client_id):
        return {
            "status": "失败",
            "message": f"客户端{client_id}不存在",
            "data": None
        }
    
    if client_id == 0:
        return {
            "status": "成功",
            "message": f"获取客户端{client_id}数据成功",
            "data": []
        }
    elif client_id == 1:
        return {
            "status": "成功",
            "message": f"获取客户端{client_id}数据成功",
            "data": [
                {
                    "client_id": 1,
                    "name": "ssh-t4",
                    "type": "tcp",
                    "localIp": "10.0.0.1",
                    "localPort": 22,
                    "remotePort": 1022
                },
                {
                    "client_id": 1,
                    "name": "mc-server",
                    "type": "udp",
                    "localIp": "10.0.0.2",
                    "localPort": 25565,
                    "remotePort": 25565
                }
            ]
        }
    elif client_id == 2:
        return {
            "status": "成功",
            "message": f"获取客户端{client_id}数据成功",
            "data": []
        }
    else:
        return {
            "status": "失败",
            "message": f"客户端{client_id}不存在",
            "data": None
        }

def get_proxy_by_name(
    client_id: int,
    proxy_name: str
    ):
    """根据proxy_name获取代理信息  

    返回的格式为：
    ```json
    {
        "status": "成功",
        "message": "获取客户端列表成功",
        "data": {
            "name": "ssh-t4",
            "type": "tcp",
            "localIp": "10.0.0.1",
            "localPort": 22,
            "remotePort": 1022
        }
    }
    ```
    
    - `status`: 操作状态，成功或失败
    - `message`: 操作信息
    - `data`: 隧道配置，格式为json数组，每个元素包含以下
        - `name`: 隧道名称
        - `type`: 隧道类型
        - `localIp`: 本地IP地址
        - `localPort`: 本地端口
        - `remotePort`: 远程端口
    
    Args:
        client_id (int): 客户端ID
        proxy_name (str): 隧道名称
    
    Returns:
        dict: 包含状态和信息的json, 格式为`{"status": "成功"|"失败", "message": "消息", "data": 数据, json格式, 如失败data为Nano}`
    """
    if isinstance(client_id, str):
        try:
            client_id = int(client_id)
        except ValueError:
            return {
                "status": "失败",
                "message": "客户端ID格式错误",
                "data": None
            }
    
    if not check_client_id(client_id):
        return {
            "status": "失败",
            "message": f"客户端{client_id}不存在",
            "data": None
        }
    
    if client_id in [0, 2]:
        return {
            "status": "失败",
            "message": f"客户端{client_id}下没有配置文件{proxy_name}",
            "data": None
        }
    
    global proxies
    if proxy_name not in proxies:
        return {
            "status": "失败",
            "message": f"客户端{client_id}下没有配置文件{proxy_name}",
            "data": None
        }

    return {
        "status": "成功",
        "message": "获取配置成功",
        "data": {
            "name": proxy_name,
            "type": "tcp",
            "localIp": "10.1.1.1",
            "localPort": 822,
            "remotePort": 1022
        }
    }

class Proxy(BaseModel):
    name: str = Field(..., description="隧道名")
    type_: str = Field(..., description="隧道类型", alias="type")
    localIp: str = Field(..., description="本地IP地址")
    localPort: int = Field(..., description="本地端口")
    remotePort: int = Field(..., description="远程端口")

def new_proxy(data: str) -> dict:
    """新建隧道  

    数据的格式：  
    ```json
    {
        "name": "ssh-t4",
        "type": "tcp",
        "localIp": "10.0.0.1",
        "localPort": 22,
        "remotePort": 1022
    }
    ```
    
    - name: 隧道名称
    - type: 隧道类型
    - localIp: 本地IP地址
    - localPort: 本地端口
    - remotePort: 远程端口
    
    Args:
        data (str): 隧道数据json字符串

    Returns:
        dict: 格式为 `{"status": "成功"|"失败", "message": "内容"}` 的字典
    """
    
    try:
        proxy = Proxy.model_validate_json(data)
    except Exception as e:
        return {
            "status": "失败",
            "message": f"数据格式错误, 错误内容：{str(e)}",
        }
    
    if proxy.name in ["ssh-t4", "mc-server"]:
        return {
            "status": "失败",
            "message": f"隧道名称 {proxy.name} 已存在"
        }
    
    if proxy.type_ not in ['tcp', 'udp']:
        return {
            "status": "失败",
            "message": f"隧道类型 {proxy.type_} 不支持"
        }
    
    if proxy.remotePort in [1022, 25565]:
        return {
            "status": "失败",
            "message": f"端口 {proxy.remotePort} 不可用"
        }
    
    return {"status": "成功", "message": f"隧道 {proxy.name} 创建成功"}

def update_proxy_by_name(data: str) -> dict:
    """修改隧道  

    数据的格式：  
    ```json
    {
        "name": "ssh-t4",
        "type": "tcp",
        "localIp": "10.0.0.1",
        "localPort": 22,
        "remotePort": 1022
    }
    ```
    
    - name: 隧道名称
    - type: 隧道类型
    - localIp: 本地IP地址
    - localPort: 本地端口
    - remotePort: 远程端口  
    
    要修改的数据的name必须存在才能修改

    Args:
        data (str): 隧道数据json字符串

    Returns:
        dict: 格式为 `{"status": "成功"|"失败", "message": "内容"}` 的字典
    """
    try:
        new_proxy = Proxy.model_validate_json(data)
    except Exception as e:
        return {
            "status": "失败",
            "message": f"数据格式错误, 错误内容：{str(e)}",
        }
    
    if new_proxy.name not in ["ssh-t4", "mc-server"]:
        return {
            "status": "失败",
            "message": f"隧道名称 {new_proxy.name} 不存在"
        }
    
    if new_proxy.type_ not in ['tcp', 'udp']:
        return {
            "status": "失败",
            "message": f"隧道类型 {new_proxy.type_} 不支持"
        }
    
    try:
        if new_proxy.name == "ssh-t4" and new_proxy.remotePort == 25565:
            raise Exception()
        if new_proxy.name == "mc-server" and new_proxy.remotePort == 1022:
            raise Exception()
    except Exception:
        return {
            "status": "失败",
            "message": f"端口 {new_proxy.remotePort} 不可用"
        }
    
    return {"status": "成功", "message": f"隧道 {new_proxy.name} 修改成功"}

def delete_proxy_by_name(proxy_name: str) -> dict:
    """根据隧道名删除隧道

    根据隧道名删除隧道，如果隧道不存在则返回失败。
    
    Args:
        proxy_name (str): 隧道名

    Returns:
        dict: 格式为 `{"status": "成功"|"失败", "message": "内容"}` 的字典
    """
    
    if proxy_name not in ["ssh-t4", "mc-server"]:
        return {"status": "失败", "message": f"隧道 {proxy_name} 不存在"}
    
    return {
        "status": "成功", 
        "message": f"删除 {proxy_name} 成功"
    }