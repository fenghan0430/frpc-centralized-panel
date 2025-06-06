from typing import List
from pydantic import BaseModel, Field
import json
from gradio_mcp.clients import get_all_clients

import os
from typing import Dict, Type
from fastapi import APIRouter, HTTPException, Path
from entity.proxy import HTTPProxyConfig, HTTPSProxyConfig, STCPProxyConfig, SUDPProxyConfig, TCPMuxProxyConfig, TCPProxyConfig, UDPProxyConfig, XTCPProxyConfig
from utils.ConfigManager import ConfigManager
from utils.database import DataBase

# 临时配置文件地址
database_path = "data/data.db"
#

PROXY_TYPE_MAP: Dict[str, Type] = {
    'tcp': TCPProxyConfig,
    'udp': UDPProxyConfig,
    'http': HTTPProxyConfig,
    'https': HTTPSProxyConfig,
    'stcp': STCPProxyConfig,
    'sudp': SUDPProxyConfig,
    'xtcp': XTCPProxyConfig,
    'tcpmux': TCPMuxProxyConfig,
}

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
        dict: 包含状态和信息的json, 格式为`{"status": "成功"|"失败", "message": "消息", "data": 数据, json格式, 如失败data为None}`
    """
    # 从数据库得到一个可信的id列表
    try:
        with DataBase(database_path) as db:
            results = db.query_program()
            db_id = [str(result[0]) for result in results]
    except Exception as e:
        return {
            "status": "成功",
            "message": f"数据库查询失败: {str(e)}",
            "data": None
        }

    
    if not db_id:
        return {
        "status": "成功",
        "message": "获取所有隧道成功",
        "data": []
    }
    
    all_proxies = []
    # 得到data/cmd/下的文件夹
    cmd_path = os.path.join("data", "cmd")
    if not os.path.exists(cmd_path):
        return {
        "status": "成功",
        "message": "获取所有隧道成功",
        "data": []
    }
    
    try:
        folder_names = [f for f in os.listdir(cmd_path) if os.path.isdir(os.path.join(cmd_path, f))]
    except OSError as e:
        return {
            "status": "成功",
            "message": f"无法读取配置文件夹: {str(e)}",
            "data": None
        }
    
    for folder_name in folder_names:
        # 验证文件夹名在不在db id, 如不在，跳过
        if folder_name not in db_id:
            # TODO: log
            continue
        
        # 验证文件夹下有没有frpc.toml, 如没有，跳过
        config_path = os.path.join(cmd_path, folder_name, "frpc.toml")
        if not os.path.exists(config_path):
            # TODO: log
            continue
        
        # 加载config, 如果错误，跳过
        try:
            client_config_manager = ConfigManager(config_path)
            client_config = client_config_manager.load_config()
        except Exception:
            # TODO: log
            continue
        
        # 检查config.proxies是否为空, 如为空，跳过
        if not client_config.proxies:
            continue
        
        # 读取每一条proxy，添加上client_id, 值为cid
        for proxy in client_config.proxies:
            proxy_dict = proxy.model_dump(by_alias=True, exclude_none=True)
            proxy_dict["client_id"] = int(folder_name)
            # 添加到all_proxies
            all_proxies.append(proxy_dict)
    
    return {
        "status": "成功",
        "message": "获取所有隧道成功",
        "data": all_proxies
    }

def get_proxy_by_client_id(client_id: str) -> dict:
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
        client_id (str): 客户端ID

    Returns:
        dict: 包含状态和信息的json, 格式为`{"status": "成功"|"失败", "message": "消息", "data": 数据, json格式, 如失败data为Nano}`
    """
    if isinstance(client_id, int):
        try:
            client_id = str(client_id)
        except ValueError:
            return {
                "status": "失败",
                "message": "客户端ID格式错误",
                "data": None
            }
    
    # 从数据库得到一个可信的id列表
    try:
        with DataBase(database_path) as db:
            results = db.query_program()
            db_id = [str(result[0]) for result in results]
    except Exception as e:
        return {
            "status": "成功",
            "message": f"数据库查询失败: {str(e)}",
            "data": None
        }
    
    if not os.path.isfile(f"data/cmd/{client_id}/frpc.toml"):
        return {
            "status": "失败",
            "message": f"客户端{client_id}对应的frpc配置文件不存在",
            "data": None
        }
    
    client_config = ConfigManager(f"data/cmd/{client_id}/frpc.toml").load_config()
    
    all_proxies = []
    if client_config.proxies:
        all_proxies = []
        for i in client_config.proxies:
            all_proxies.append(i.model_dump(by_alias=True, exclude_none=True))
        return {
            "status": "成功",
            "message": f"获取客户端{client_id}数据成功",
            "data": all_proxies
        }
    else:
        return {
            "status": "成功",
            "message": f"获取客户端{client_id}数据成功",
            "data": []
        }

def get_proxy_by_name(
    client_id: str,
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
        client_id (str): 客户端ID
        proxy_name (str): 隧道名称
    
    Returns:
        dict: 包含状态和信息的json, 格式为`{"status": "成功"|"失败", "message": "消息", "data": 数据, json格式, 如失败data为Nano}`
    """
    if isinstance(client_id, int):
        try:
            client_id = str(client_id)
        except ValueError:
            return {
                "status": "失败",
                "message": "客户端ID格式错误",
                "data": None
            }
    
    # 从数据库得到一个可信的id列表
    try:
        with DataBase(database_path) as db:
            results = db.query_program()
            db_id = [str(result[0]) for result in results]
    except Exception as e:
        return {
            "status": "成功",
            "message": f"数据库查询失败: {str(e)}",
            "data": None
        }
    
    if client_id not in db_id:
        return {
            "status": "失败",
            "message": f"客户端{client_id}不存在",
            "data": None
        }
    
    if not os.path.isfile(f"data/cmd/{client_id}/frpc.toml"):
        return {
            "status": "失败",
            "message": f"客户端{client_id}对应的frpc配置文件不存在",
            "data": None
        }
    
    client_config = ConfigManager(f"data/cmd/{client_id}/frpc.toml").load_config()
    
    # 根据 name 
    if client_config.proxies:
        for proxy in client_config.proxies:
            if proxy.name == proxy_name:
                return {
                "status": "成功",
                "message": "获取配置成功",
                "data": proxy.model_dump(by_alias=True, exclude_none=True)
            }
    
    return {
        "status": "失败",
        "message": f"隧道{proxy_name}不存在",
        "data": None
    }

def new_proxy(client_id: str, data: str) -> dict:
    """新建隧道  

    数据(data参数)的格式：  
    ```json
    {
        "name": "ssh-t4",
        "type": "tcp",
        "localIp": "10.0.0.1",
        "localPort": 22,
        "remotePort": 1022
    }
    ```
    
    - `name`: 隧道名称
    - `type`: 隧道类型
    - `localIp`: 本地IP地址
    - `localPort`: 本地端口
    - `remotePort`: 远程端口
    
    Args:
        client_id (str): 客户端ID,在这个客户端新建文件
        data (str): 隧道数据json字符串

    Returns:
        dict: 格式为 `{"status": "成功"|"失败", "message": "内容"}` 的字典
    """
    if isinstance(client_id, int):
        try:
            client_id = str(client_id)
        except ValueError:
            return {
                "status": "失败",
                "message": "客户端ID格式错误",
                "data": None
            }
    
    # 从数据库得到一个可信的id列表
    try:
        with DataBase(database_path) as db:
            results = db.query_program()
            db_id = [str(result[0]) for result in results]
    except Exception as e:
        return {
            "status": "成功",
            "message": f"数据库查询失败: {str(e)}",
            "data": None
        }
    
    if client_id not in db_id:
        return {
            "status": "失败",
            "message": f"客户端{client_id}不存在",
            "data": None
        }
    
    if not os.path.isfile(f"data/cmd/{client_id}/frpc.toml"):
        return {
            "status": "失败",
            "message": f"客户端{client_id}对应的frpc配置文件不存在",
            "data": None
        }
    
    try:
        data_dict = json.loads(data)
    except json.JSONDecodeError as e:
        return {
            "status": "失败",
            "message": f"data json解析失败, 错误内容：{str(e)}",
            "data": None
        }
    
    if "type" not in data_dict.keys():
        return {
            "status": "失败",
            "message": f"请求体中缺少type字段",
            "data": None
        }
    
    if data_dict["type"] not in PROXY_TYPE_MAP.keys():
        return {
            "status": "失败",
            "message": f"类型{data_dict['type']}不是一个有效的类型",
            "data": None
        }
    
    config = ConfigManager(f"data/cmd/{client_id}/frpc.toml")
    
    try:
        # 转为实体类，顺便验证合不合法
        new_proxy_config = PROXY_TYPE_MAP[data_dict["type"]](**data_dict)
    except Exception as e:
        return {
            "status": "失败",
            "message": f"配置文件格式不正确: {str(e)}",
            "data": None,
        }
    
    # 检测
    client_config = config.load_config()
    if not client_config.proxies:
        client_config.proxies = []
    
    for i in client_config.proxies:
        # 检测名字是否重名，也许事应该前端也做一遍？
        if i.name == new_proxy_config.name:
            return {
                "status": "失败",
                "message": f"名字{new_proxy_config.name}已经被占用",
                "data": None,
            }
        # 检测tcp, udp端口是否重复
        if data_dict["type"] in ['tcp', 'udp'] and i.type_ in ['tcp', 'udp']:
            if new_proxy_config.remotePort == None:
                return {
                    "status": "失败",
                    "message": "remotePort为空,不支持这样的写法",
                    "data": None,
                }
            if i.remotePort == None: # type: ignore
                continue
            if i.remotePort == new_proxy_config.remotePort:  # type: ignore
                return {
                    "status": "失败",
                    "message": f"端口{new_proxy_config.remotePort}已经被占用",
                    "data": None,
                }
        # 检测http, https绑定域名是否重复
        if data_dict["type"] in ['http', 'https'] and i.type_ in ['http', 'https']:
            if i.customDomains == None: # type: ignore
                continue
            if new_proxy_config.customDomains == None:
                return {
                    "status": "失败",
                    "message": "customDomains为空,不支持这样的写法",
                    "data": None,
                }
            for domain in i.customDomains: # type: ignore
                for domain2 in new_proxy_config.customDomains: # type: ignore
                    if domain == domain2:
                        return {
                            "status": "失败",
                            "message": f"域名{domain2}已经被{i.name}占用",
                            "data": None,
                        }
    # 添加隧道到配置文件
    client_config.proxies.append(new_proxy_config)
    config.save_config(client_config)
    
    return {"status": "成功", "message": f"隧道 {new_proxy_config.name} 创建成功"}

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