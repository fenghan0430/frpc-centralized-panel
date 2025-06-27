import json
import os
from typing import Dict, Type
from entity.visitor import STCPVisitorConfig, SUDPVisitorConfig, XTCPVisitorConfig
from utils.ConfigManager import ConfigManager
from utils.database import DataBase

# 临时配置文件地址
database_path = "data/data.db"

VISITOR_TYPE_MAP: Dict[str, Type] = {
    'stcp': STCPVisitorConfig,
    'sudp': SUDPVisitorConfig,
    'xtcp': XTCPVisitorConfig,
}

def get_all_visitors() -> dict:
    """获取所有观察者  
    
    返回的格式为：
    ```json
    {
        "status": "成功",
        "message": "获取客户端列表成功",
        "data": [
            {
                "program_id": 0,
                "name": "stcp1-visitor",
                "type": "stcp",
                "serverName": "stcp",
                "secretKey": "key",
                "bindAddr" = "127.0.0.1",
                "bindPort" = 6000
            }
        ]
    }
    ```
    
    - `status`: 操作状态，成功或失败
    - `message`: 操作信息
    - `data`: 客户端列表，格式为json数组，每个元素包含以下
        - `program_id`: 客户端ID
        - `name`: 观察者名称
        - `type`: 观察者类型
        - `serverName`: 服务名称
        - `secretKey`: 观察者的认证密钥，用于安全通信  
        - `bindAddr`: 绑定到本地的IP
        - `bindPort`: 绑定到本地的端口号  
    
    Returns:
        dict: 包含状态和信息的json, 格式为`{"status": "成功"|"失败", "message": "消息", "data": 数据, json格式, 如失败data为None}`
    """
    try:
        with DataBase(database_path) as db:
            results = db.query_program()
            db_id = [str(r[0]) for r in results]
    except Exception as e:
        return {"status": "失败", "message": f"数据库查询失败: {e}", "data": None}

    if not db_id:
        return {"status": "成功", "message": "获取所有观察者成功", "data": []}

    cmd_path = os.path.join("data", "cmd")
    if not os.path.exists(cmd_path):
        return {"status": "成功", "message": "获取所有观察者成功", "data": []}

    all_visitors = []
    for folder in os.listdir(cmd_path):
        if folder not in db_id:
            # TODO: log
            continue
        cfg_file = os.path.join(cmd_path, folder, "frpc.toml")
        if not os.path.isfile(cfg_file):
            # TODO: log
            continue
        try:
            cfg = ConfigManager(cfg_file).load_config()
        except Exception:
            # TODO: log
            continue
        if not cfg.visitors:
            continue
        for v in cfg.visitors:
            d = v.model_dump(by_alias=True, exclude_none=True)
            d["program_id"] = int(folder)
            all_visitors.append(d)

    return {"status": "成功", "message": "获取所有观察者成功", "data": all_visitors}


def get_visitors_by_program_id(program_id: str) -> dict:
    """获取指定客户端ID下的观察者配置文件  
    
    返回的格式为：
        ```json
        {
            "status": "成功",
            "message": "获取客户端列表成功",
            "data": [
                {
                    "name": "stcp1-visitor",
                    "type": "stcp",
                    "serverName": "stcp",
                    "secretKey": "key",
                    "bindAddr" = "127.0.0.1",
                    "bindPort" = 6000
                }
            ]
        }
        ```

        - `status`: 操作状态，成功或失败
        - `message`: 操作信息
        - `data`: 客户端列表，格式为json数组，每个元素包含以下
            - `name`: 观察者名称
            - `type`: 观察者类型
            - `serverName`: 服务名称
            - `secretKey`: 观察者的认证密钥，用于安全通信  
            - `bindAddr`: 绑定到本地的IP
            - `bindPort`: 绑定到本地的端口号
    
    Args:
        program_id (str): 客户端ID
    
    Returns:
        dict: 包含状态和信息的json, 格式为`{"status": "成功"|"失败", "message": "消息", "data": 数据, json格式, 如失败data为None}`
    """
    if isinstance(program_id, int):
        program_id = str(program_id)

    # 验证数据库中的 id
    try:
        with DataBase(database_path) as db:
            db_id = [str(r[0]) for r in db.query_program()]
    except Exception as e:
        return {"status": "失败", "message": f"数据库查询失败: {e}", "data": None}

    cfg_file = f"data/cmd/{program_id}/frpc.toml"
    if program_id not in db_id or not os.path.isfile(cfg_file):
        return {"status": "失败", "message": f"程序{program_id}不存在或配置文件缺失", "data": None}
    
    # TODO: 这个接口下的加载参数是不是该加try
    cfg = ConfigManager(cfg_file).load_config()
    data = [v.model_dump(by_alias=True, exclude_none=True) for v in (cfg.visitors or [])]
    return {"status": "成功", "message": f"获取程序{program_id}观察者成功", "data": data}


def get_visitor_by_name(program_id: str, visitor_name: str) -> dict:
    """获取指定客户端ID下的指定name的观察者配置文件  

    返回的格式为：
    ```json
    {
        "status": "成功",
        "message": "获取观察者成功",
        "data": [
            {
                "name": "stcp1-visitor",
                "type": "stcp",
                "serverName": "stcp",
                "secretKey": "key",
                "bindAddr" = "127.0.0.1",
                "bindPort" = 6000
            }
        ]
    }
    ```
    
    - `status`: 操作状态，成功或失败
    - `message`: 操作信息
    - `data`: 客户端列表，格式为json数组，每个元素包含以下
        - `name`: 观察者名称
        - `type`: 观察者类型
        - `serverName`: 服务名称
        - `secretKey`: 观察者的认证密钥，用于安全通信  
        - `bindAddr`: 绑定到本地的IP
        - `bindPort`: 绑定到本地的端口号 
    
    Args:
        program_id (str): 程序ID
        visitor_name (str): 观察者名称
    
    Returns:
        dict: 包含状态和信息的json, 格式为`{"status": "成功"|"失败", "message": "消息", "data": 数据, json格式, 如失败data为None}`
    """
    resp = get_visitors_by_program_id(program_id)
    if resp["status"] != "成功":
        return resp
    for v in resp["data"]:
        if v.get("name") == visitor_name:
            return {"status": "成功", "message": "获取观察者成功", "data": v}
    return {"status": "失败", "message": f"观察者 {visitor_name} 不存在", "data": None}


def new_visitor(program_id: str, data: str) -> dict:
    """新建指定客户端 ID 下的观察者配置
    
    传入参数示例(不是全部):
    - program_id: 客户端 ID，整数或字符串
    - data: 新观察者配置，JSON 字符串。必须包含以下字段：
        - name: 观察者名称，和要修改的name一致
        - type: 观察者类型，和要修改的type一致
        - serverName: 服务端名称，用于关联后端服务
        - secretKey: 认证密钥，用于安全通信
        - bindAddr: 绑定的本地 IP 地址（例如 "127.0.0.1"）
        - bindPort: 绑定的本地端口（整数, 65535 以内）
    
    返回的格式:
    ```json
    {
        "status": "成功"|"失败",
        "message": "提示信息"
    }
    ```
    
    Args:
        program_id (str): 客户端 ID
        data (str): 新观察者配置的 JSON 字符串
    
    Returns:
        dict: 操作结果，格式 `{"status": "成功"|"失败", "message": "具体信息"}`
    """
    if isinstance(program_id, int):
        program_id = str(program_id)
    # 验证 program_id
    try:
        with DataBase(database_path) as db:
            db_id = [str(r[0]) for r in db.query_program()]
    except Exception as e:
        return {"status": "失败", "message": f"数据库查询失败: {e}"}
    if program_id not in db_id:
        return {"status": "失败", "message": f"程序{program_id}不存在"}
    cfg_file = f"data/cmd/{program_id}/frpc.toml"
    if not os.path.isfile(cfg_file):
        return {"status": "失败", "message": f"配置文件不存在: {cfg_file}"}

    try:
        body = json.loads(data)
    except json.JSONDecodeError as e:
        return {"status": "失败", "message": f"JSON 解析失败: {e}"}

    if "type" not in body:
        return {"status": "失败", "message": "缺少 type 字段"}
    if body["type"] not in VISITOR_TYPE_MAP:
        return {"status": "失败", "message": f"无效的类型: {body['type']}"}

    try:
        new_cfg = VISITOR_TYPE_MAP[body["type"]](**body)
    except Exception as e:
        return {"status": "失败", "message": f"配置校验失败: {e}"}

    manager = ConfigManager(cfg_file)
    cfg = manager.load_config()
    cfg.visitors = cfg.visitors or []

    # 唯一性检查
    for v in cfg.visitors:
        if v.name == new_cfg.name:
            return {"status": "失败", "message": f"名字 {v.name} 已被占用"}
        if v.bindAddr == new_cfg.bindAddr and v.bindPort == new_cfg.bindPort:
            return {"status": "失败", "message": f"网络地址 {v.bindAddr}:{v.bindPort} 已被占用"}

    cfg.visitors.append(new_cfg)
    manager.save_config(cfg)
    return {"status": "成功", "message": f"观察者 {new_cfg.name} 创建成功"}


def update_visitor_by_name(program_id: str, data: str) -> dict:
    """修改指定客户端 ID 下的观察者配置
    
    传入参数示例(不是全部):
    - program_id: 客户端 ID，整数或字符串
    - data: 观察者配置，JSON 字符串。必须包含以下字段：
        - name: 观察者名称，和要修改的name一致
        - type: 观察者类型，和要修改的type一致
        - serverName: 服务名称
        - secretKey: 认证密钥，用于安全通信
        - bindAddr: 绑定的本地 IP 地址（例如 "127.0.0.1"）
        - bindPort: 绑定的本地端口（整数, 65535 以内）
    
    返回的格式:
    ```json
    {
        "status": "成功"|"失败",
        "message": "提示信息"
    }
    ```
    
    Args:
        program_id (str): 客户端 ID
        data (str): 新观察者配置的 JSON 字符串
    
    Returns:
        dict: 操作结果，格式 `{"status": "成功"|"失败", "message": "具体信息"}`
    """
    if isinstance(program_id, int):
        program_id = str(program_id)
    try:
        with DataBase(database_path) as db:
            db_id = [str(r[0]) for r in db.query_program()]
    except Exception as e:
        return {"status": "失败", "message": f"数据库查询失败: {e}"}
    if program_id not in db_id:
        return {"status": "失败", "message": f"程序{program_id}不存在"}

    cfg_file = f"data/cmd/{program_id}/frpc.toml"
    if not os.path.isfile(cfg_file):
        return {"status": "失败", "message": f"配置文件不存在: {cfg_file}"}

    try:
        body = json.loads(data)
    except json.JSONDecodeError as e:
        return {"status": "失败", "message": f"JSON 解析失败: {e}"}
    if "name" not in body or "type" not in body:
        return {"status": "失败", "message": "缺少 name 或 type 字段"}

    manager = ConfigManager(cfg_file)
    cfg = manager.load_config()
    if not cfg.visitors:
        return {"status": "失败", "message": f"未找到观察者 {body['name']}"}

    # 定位要更新的配置
    for idx, v in enumerate(cfg.visitors):
        if v.name == body["name"]:
            old = v
            target = idx
            break
    else:
        return {"status": "失败", "message": f"未找到观察者 {body['name']}"}

    if body["type"] != old.type_:
        return {"status": "失败", "message": f"不支持修改类型, 旧:{old.type_} 新:{body['type']}"}

    merged = old.model_dump()
    merged.update(body)
    try:
        upd = VISITOR_TYPE_MAP[old.type_](**merged)
    except Exception as e:
        return {"status": "失败", "message": f"配置校验失败: {e}"}

    # 唯一性检查（跳过自身）
    for i, other in enumerate(cfg.visitors):
        if i == target:
            continue
        if upd.name == other.name:
            return {"status": "失败", "message": f"名字 {upd.name} 冲突"}
        if upd.bindAddr == other.bindAddr and upd.bindPort == other.bindPort:
            return {"status": "失败", "message": f"地址 {upd.bindAddr}:{upd.bindPort} 冲突"}

    cfg.visitors[target] = upd
    manager.save_config(cfg)
    return {"status": "成功", "message": f"观察者 {upd.name} 修改成功"}


def delete_visitor_by_name(program_id: str, visitor_name: str) -> dict:
    """删除指定观察者
    
    返回的格式:
    ```json
    {
        "status": "成功"|"失败",
        "message": "提示信息"
    }
    ```
    
    Args:
        program_id (str): 程序ID
        visitor_name (str): 观察者名称   
    
    Returns:
        dict: 返回操作结果
    """
    if isinstance(program_id, int):
        program_id = str(program_id)
    try:
        with DataBase(database_path) as db:
            db_id = [str(r[0]) for r in db.query_program()]
    except Exception as e:
        return {"status": "失败", "message": f"数据库查询失败: {e}"}
    if program_id not in db_id:
        return {"status": "失败", "message": f"程序{program_id}不存在"}

    cfg_file = f"data/cmd/{program_id}/frpc.toml"
    if not os.path.isfile(cfg_file):
        return {"status": "失败", "message": f"配置文件不存在: {cfg_file}"}

    manager = ConfigManager(cfg_file)
    cfg = manager.load_config()
    if not cfg.visitors:
        return {"status": "失败", "message": f"未找到观察者 {visitor_name}"}

    for v in cfg.visitors:
        if v.name == visitor_name:
            cfg.visitors.remove(v)
            manager.save_config(cfg)
            return {"status": "成功", "message": f"删除观察者 {visitor_name} 成功"}

    return {"status": "失败", "message": f"未找到观察者 {visitor_name}"}
