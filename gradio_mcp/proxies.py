import json
import logging
from math import e
import os
from typing import Dict, List, Type
from entity.proxy import HTTPProxyConfig, HTTPSProxyConfig, STCPProxyConfig, SUDPProxyConfig, TCPMuxProxyConfig, TCPProxyConfig, UDPProxyConfig, XTCPProxyConfig
from utils.ConfigManager import ConfigManager
from utils.database import DataBase
from utils.program_manager import ProgramManager
import requests

# 临时配置文件地址
database_path = "data/data.db"
#
logger = logging.getLogger("gradio_mcp.proxies")
manager = ProgramManager()

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

def check_proxy_status(ids: List[str] | None = None) -> dict:
    # 从数据库得到一个可信的id列表
    try:
        with DataBase(database_path) as db:
            results = db.query_program()
            db_id = [str(result[0]) for result in results]
    except Exception as e:
        return {
            "status": "失败",
            "message": f"数据库查询失败: {str(e)}",
            "data": None
        }
    # TODO: 检查start列表
    if not ids:
        ids = db_id
    if len(ids) == 0:
        return {
            "status": "失败",
            "message": f"传入的id列表为空",
            "data": None
        }
    proxy_status = {}
    # 处理列表中的客户端
    for id in ids:
        if id not in db_id:
            logger.warning(f"check_proxy_status: id{id}不在数据库中，跳过检测")
            continue
        
        if os.path.exists(f"data/cmd/{id}") and os.path.isfile(f"data/cmd/{id}/frpc.toml"):
            try:
                cfg = ConfigManager(f"data/cmd/{id}/frpc.toml").load_config()
            except Exception as e:
                logger.warning(f"check_proxy_status: id{id}加载配置文件出错: {str(e)}, 跳过检测")
                continue
        else:
            logger.warning(f"check_proxy_status: id{id}未找到配置文件, 跳过检测")
            continue
        
        is_program_work = False
        status = manager.get_status()
        for i in status:
            if i['id'] == id and i['status'] == "运行":
                is_program_work = True
                break
        if not is_program_work:
            if cfg.proxies:
                program_proxies_status = {}
                for proxy in cfg.proxies:
                    program_proxies_status[proxy.name] = "停止"
            proxy_status[id] = program_proxies_status
            continue
        
        is_have_web_config = cfg.webServer and \
            cfg.webServer.addr and \
            cfg.webServer.port and \
            cfg.webServer.user and \
            cfg.webServer.password

        if not is_have_web_config:
            logger.warning(f"check_proxy_status: id{id}没有配置webserver, 跳过检测")
            continue
        else:
            addr = cfg.webServer.addr # type: ignore
            port = cfg.webServer.port # type: ignore
            user = cfg.webServer.user # type: ignore
            password = cfg.webServer.password # type: ignore

        try:
            response = requests.get(f"http://{addr}:{port}/api/status", auth=(user, password)) # type: ignore
        except Exception as e:
            logger.warning(f"请求客户端{id}的webserver失败, 错误：{str(e)}，跳过检测")
            continue
        
        if response.status_code != 200:
            logger.warning(f"请求客户端{id}的webserver失败，错误码{response.status_code}, 内容：{response.text[:200].strip()}。跳过检测")
            continue
        
        # 解析响应为json
        try:
            data = response.json()
        except json.JSONDecodeError as e:
            logger.warning(f"请求客户端{id}的webserver失败，错误：{str(e)}，跳过检测")
            continue
        
        program_proxies_status = {}
        for i in data.keys():
            for i in data[i]:
                if i["status"] == "running":
                    program_proxies_status[i["name"]] = "运行"
                else:
                    program_proxies_status[i["name"]] = "错误"
        
        if cfg.proxies:
            for proxy in cfg.proxies:
                if proxy.name not in program_proxies_status.keys():
                    program_proxies_status[proxy.name] = "未知"
        proxy_status[id] = program_proxies_status
    
    return proxy_status

def get_all_proxies():
    """获取所有隧道  
    
    返回的格式为：
    ```json
    {
        "status": "成功",
        "message": "获取客户端列表成功",
        "data": [
            {
                "program_id": 0,
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
        - `program_id`: 客户端ID
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
        
        proxy_status = check_proxy_status([folder_name])
        
        # 读取每一条proxy，添加上program_id, 值为cid
        for proxy in client_config.proxies:
            proxy_dict = proxy.model_dump(by_alias=True, exclude_none=True)
            proxy_dict["program_id"] = int(folder_name)
            proxy_dict["status"] = proxy_status[folder_name][proxy.name]
            # 添加到all_proxies
            all_proxies.append(proxy_dict)
    
    return {
        "status": "成功",
        "message": "获取所有隧道成功",
        "data": all_proxies
    }

def get_proxy_by_program_id(program_id: str) -> dict:
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
        program_id (str): 客户端ID

    Returns:
        dict: 包含状态和信息的json, 格式为`{"status": "成功"|"失败", "message": "消息", "data": 数据, json格式, 如失败data为Nano}`
    """
    if isinstance(program_id, int):
        try:
            program_id = str(program_id)
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
    
    if not os.path.isfile(f"data/cmd/{program_id}/frpc.toml"):
        return {
            "status": "失败",
            "message": f"客户端{program_id}对应的frpc配置文件不存在",
            "data": None
        }
    
    config = ConfigManager(f"data/cmd/{program_id}/frpc.toml").load_config()
    
    all_proxies = []
    if config.proxies:
        all_proxies = []
        for i in config.proxies:
            all_proxies.append(i.model_dump(by_alias=True, exclude_none=True))
        return {
            "status": "成功",
            "message": f"获取客户端{program_id}数据成功",
            "data": all_proxies
        }
    else:
        return {
            "status": "成功",
            "message": f"获取客户端{program_id}数据成功",
            "data": []
        }

def get_proxy_by_name(
    program_id: str,
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
        program_id (str): 客户端ID
        proxy_name (str): 隧道名称
    
    Returns:
        dict: 包含状态和信息的json, 格式为`{"status": "成功"|"失败", "message": "消息", "data": 数据, json格式, 如失败data为Nano}`
    """
    if isinstance(program_id, int):
        try:
            program_id = str(program_id)
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
    
    if program_id not in db_id:
        return {
            "status": "失败",
            "message": f"客户端{program_id}不存在",
            "data": None
        }
    
    if not os.path.isfile(f"data/cmd/{program_id}/frpc.toml"):
        return {
            "status": "失败",
            "message": f"客户端{program_id}对应的frpc配置文件不存在",
            "data": None
        }
    
    config = ConfigManager(f"data/cmd/{program_id}/frpc.toml").load_config()
    
    # 根据 name 
    if config.proxies:
        for proxy in config.proxies:
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

def new_proxy(program_id: str, data: str) -> dict:
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
        program_id (str): 客户端ID,在这个客户端新建文件
        data (str): 隧道数据json字符串

    Returns:
        dict: 格式为 `{"status": "成功"|"失败", "message": "内容"}` 的字典
    """
    if isinstance(program_id, int):
        try:
            program_id = str(program_id)
        except ValueError:
            return {
                "status": "失败",
                "message": "客户端ID格式错误",
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
        }
    
    if program_id not in db_id:
        return {
            "status": "失败",
            "message": f"客户端{program_id}不存在",
        }
    
    if not os.path.isfile(f"data/cmd/{program_id}/frpc.toml"):
        return {
            "status": "失败",
            "message": f"客户端{program_id}对应的frpc配置文件不存在",
        }
    
    try:
        data_dict = json.loads(data)
    except json.JSONDecodeError as e:
        return {
            "status": "失败",
            "message": f"data json解析失败, 错误内容：{str(e)}",
        }
    
    if "type" not in data_dict.keys():
        return {
            "status": "失败",
            "message": f"请求体中缺少type字段",
        }
    
    if data_dict["type"] not in PROXY_TYPE_MAP.keys():
        return {
            "status": "失败",
            "message": f"类型{data_dict['type']}不是一个有效的类型",
        }
    
    config_manager = ConfigManager(f"data/cmd/{program_id}/frpc.toml")
    
    try:
        # 转为实体类，顺便验证合不合法
        new_proxy_config = PROXY_TYPE_MAP[data_dict["type"]](**data_dict)
    except Exception as e:
        return {
            "status": "失败",
            "message": f"配置文件格式不正确: {str(e)}",
        }
    
    # 检测
    config = config_manager.load_config()
    if not config.proxies:
        config.proxies = []
    
    for i in config.proxies:
        # 检测名字是否重名，也许事应该前端也做一遍？
        if i.name == new_proxy_config.name:
            return {
                "status": "失败",
                "message": f"名字{new_proxy_config.name}已经被占用",
            }
        # 检测tcp, udp端口是否重复
        if data_dict["type"] in ['tcp', 'udp'] and i.type_ in ['tcp', 'udp']:
            if new_proxy_config.remotePort == None:
                return {
                    "status": "失败",
                    "message": "remotePort为空,不支持这样的写法",
                }
            if i.remotePort == None: # type: ignore
                continue
            if i.remotePort == new_proxy_config.remotePort:  # type: ignore
                return {
                    "status": "失败",
                    "message": f"端口{new_proxy_config.remotePort}已经被占用",
                }
        # 检测http, https绑定域名是否重复
        if data_dict["type"] in ['http', 'https'] and i.type_ in ['http', 'https']:
            if i.customDomains == None: # type: ignore
                continue
            if new_proxy_config.customDomains == None:
                return {
                    "status": "失败",
                    "message": "customDomains为空,不支持这样的写法",
                }
            for domain in i.customDomains: # type: ignore
                for domain2 in new_proxy_config.customDomains: # type: ignore
                    if domain == domain2:
                        return {
                            "status": "失败",
                            "message": f"域名{domain2}已经被{i.name}占用",
                        }
    # 添加隧道到配置文件
    config.proxies.append(new_proxy_config)
    config_manager.save_config(config)
    
    return {"status": "成功", "message": f"隧道 {new_proxy_config.name} 创建成功"}

def update_proxy_by_name(program_id: str, data: str) -> dict:
    """修改隧道  

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
    
    - `name`: 隧道名称，需要是存在的隧道
    - `type`: 隧道类型，必须和原隧道一样，不支持修改
    - `localIp`: 本地IP地址
    - `localPort`: 本地端口
    - `remotePort`: 远程端口  
    

    Args:
        program_id (str): 客户端ID
        data (str): 隧道数据json字符串

    Returns:
        dict: 格式为 `{"status": "成功"|"失败", "message": "内容"}` 的字典
    """
    
    if isinstance(program_id, int):
        try:
            program_id = str(program_id)
        except ValueError:
            return {
                "status": "失败",
                "message": "客户端ID格式错误",
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
        }
    
    if program_id not in db_id:
        return {
            "status": "失败",
            "message": f"客户端{program_id}不存在",
        }
    
    if not os.path.isfile(f"data/cmd/{program_id}/frpc.toml"):
        return {
            "status": "失败",
            "message": f"客户端{program_id}对应的frpc配置文件不存在",
        }
    
    config_manager = ConfigManager(f"data/cmd/{program_id}/frpc.toml")
    
    try:
        data_dict = json.loads(data)
    except json.JSONDecodeError as e:
        return {
            "status": "失败",
            "message": f"data json解析失败, 错误内容：{str(e)}",
        }
    
    if "type" not in data_dict.keys():
        return {
            "status": "失败",
            "message": f"请求体中缺少type字段",
        }
    
    if "name" not in data_dict.keys():
        return {
            "status": "失败",
            "message": f"请求体中缺少name字段",
        }
    
    proxy_name = data_dict['name']
    
    if data_dict["type"] not in PROXY_TYPE_MAP.keys():
        return {
            "status": "失败",
            "message": f"类型{data_dict['type']}不是一个有效的类型",
        }
    
    config = config_manager.load_config()
    if not config.proxies:
        return {
            "status": "失败",
            "message": f"客户端{program_id}下找不到{data_dict['name']}隧道",
        }

    # 查找要更新的隧道
    for idx, proxy in enumerate(config.proxies):
        if proxy.name == proxy_name:
            old_proxy = proxy
            target_index = idx
            break
    else:
        return {
            "status": "失败",
            "message": f"客户端{program_id}下找不到{data_dict['name']}隧道",
        }
    
    if "type" in data and data_dict["type"] != old_proxy.type_:
        return {
            "status": "失败",
            "message": f"不支持修改隧道类型, 旧隧道为: {old_proxy.type_}, 新隧道为: {data_dict['type']}",
        }
    
    # 合并旧数据与新传入字段，并进行校验
    merged = old_proxy.model_dump()
    merged.update(data_dict)
    try:
        updated_proxy = PROXY_TYPE_MAP[old_proxy.type_](**merged)
    except Exception as e:
        return {
            "status": "失败",
            "message": f"数据格式错误, 错误内容：{str(e)}",
        }
    
    # 唯一性检查（跳过自身）
    for i, other in enumerate(config.proxies):
        if i == target_index:
            continue
        # 名称冲突
        if updated_proxy.name == other.name:
            return {
                "status": "失败",
                "message": f"名字{updated_proxy.name}已经被占用",
            }
        # tcp/udp 端口冲突
        if old_proxy.type_ in ['tcp', 'udp'] and other.type_ in ['tcp', 'udp']:
            if updated_proxy.remotePort and other.remotePort == updated_proxy.remotePort: # type: ignore
                return {
                    "status": "失败",
                    "message": f"端口{updated_proxy.remotePort}已经被占用",
                }
        # http/https 域名冲突
        if old_proxy.type_ in ['http', 'https'] and other.type_ in ['http', 'https']:
            if updated_proxy.customDomains:
                for d in updated_proxy.customDomains:
                    if other.customDomains and d in other.customDomains: # type: ignore
                        return {
                                "status": "失败",
                                "message": f"域名{d}已经被{other.name}占用",
                            }

    # 应用更新并保存
    config.proxies[target_index] = updated_proxy
    config_manager.save_config(config)
    
    return {"status": "成功", "message": f"隧道 {updated_proxy.name} 修改成功"}

def delete_proxy_by_name(program_id: str, proxy_name: str) -> dict:
    """根据隧道名删除隧道

    根据隧道名删除隧道，如果隧道不存在则返回失败。  
    
    注意: 使用这个函数之前一定要得到用户的肯定!丢失的数据无法复原!
    
    Args:
        program_id (str): 客户端ID
        proxy_name (str): 隧道名

    Returns:
        dict: 格式为 `{"status": "成功"|"失败", "message": "内容"}` 的字典
    """
    if isinstance(program_id, int):
        try:
            program_id = str(program_id)
        except ValueError:
            return {
                "status": "失败",
                "message": "客户端ID格式错误",
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
        }
    
    if program_id not in db_id:
        return {
            "status": "失败",
            "message": f"客户端{program_id}不存在",
        }
    
    if not os.path.isfile(f"data/cmd/{program_id}/frpc.toml"):
        return {
            "status": "失败",
            "message": f"客户端{program_id}对应的frpc配置文件不存在",
        }
    
    config_manager = ConfigManager(f"data/cmd/{program_id}/frpc.toml")
    config = config_manager.load_config()
    
    if config.proxies is None or not config.proxies:
        return {
            "status": "失败",
            "message": f"客户端{program_id}下找不到隧道{proxy_name}",
        }

    # 查找并删除指定的隧道
    proxy_to_delete = None
    for proxy in config.proxies:
        if proxy.name == proxy_name:
            proxy_to_delete = proxy
            break
    
    if proxy_to_delete is None:
        return {
            "status": "失败",
            "message": f"客户端{program_id}下找不到隧道{proxy_name}",
        }
    
    config.proxies.remove(proxy_to_delete)
    config_manager.save_config(config)
    
    return {
        "status": "成功", 
        "message": f"成功删除隧道 {proxy_name}"
    }