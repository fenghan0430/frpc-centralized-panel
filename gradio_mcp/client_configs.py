import json
import logging
import os
from entity.client import ClientConfig
from utils.ConfigManager import ConfigManager
from utils.database import DataBase

# 数据库和命令目录
database_path = "data/data.db"
cmd_dir = "data/cmd"
logger = logging.getLogger("gradio_mcp.client_configs")

def check_admin_ui_port_conflict(
    new_port: int, 
    current_id: str | None = None
    ) -> dict | None:
    """
    检查 admin UI 端口是否与其他客户端配置冲突。

    遍历 cmd_dir 下所有客户端的 frpc.toml 配置，若发现已有客户端的
    webServer.port 与 new_port 相同，则返回冲突信息，否则返回 None。

    Args:
        new_port (int): 待检测的 admin UI 端口号。
        current_id (str | None): 当前客户端 ID（更新时跳过自身），默认为 None。

    Returns:
        dict | None: 
            - 若发生冲突，返回 {"status": "失败", "message": "..."}； 
            - 无冲突时返回 None。
    """
    for entry in os.listdir(cmd_dir):
        if current_id and entry == current_id:
            continue
        cfg_file = os.path.join(cmd_dir, entry, "frpc.toml")
        if not os.path.isfile(cfg_file):
            continue
        try:
            exist_cfg = ConfigManager(cfg_file).load_config()
        except Exception:
            logger.warning(f"在验证端口冲突时，读取配置文件 {cfg_file} 时出错，已跳过")
            continue
        if exist_cfg.webServer and exist_cfg.webServer.port == new_port:
            return {
                "status": "失败",
                "message": f"admin ui端口号 {new_port} 已被客户端 {entry} 占用"
            }
    return None


def get_client_config_by_id(program_id: str) -> dict:
    """根据ID获取单个客户端配置
    
    注意这里修改的不是隧道(proxy)和观察者(visitor)的配置信息，client_configs接口仅处理client与server的连接配置。  
    
    返回格式(不是全部参数):
    ```json
    {
        "status": "成功",
        "message": "获取客户端配置成功",
        "data": {
            "serverAddr" = "127.0.0.1",
            "serverPort" = 25566,
        }
    }
    ```
    
    - `status`: 请求状态，成功或失败
    - `message`: 请求结果的描述信息
    - `data`: 客户端配置
        - `serverAddr`: 服务器地址
        - `serverPort`: 服务器端
    
    Args:
        program_id (str): 客户端ID
    
    Returns:
        dict: 包含请求状态、消息和客户端配置的字典
    """
    if isinstance(program_id, int):
        program_id = str(program_id)

    try:
        with DataBase(database_path) as db:
            ids = [str(r[0]) for r in db.query_program()]
    except Exception as e:
        return {"status": "失败", "message": f"数据库查询失败: {e}", "data": None}

    if program_id not in ids:
        return {"status": "失败", "message": f"程序{program_id}不存在", "data": None}

    cfg_file = os.path.join(cmd_dir, program_id, "frpc.toml")
    if not os.path.isfile(cfg_file):
        return {"status": "失败", "message": f"配置文件不存在: {cfg_file}", "data": None}

    try:
        cfg = ConfigManager(cfg_file).load_config()
    except Exception as e:
        return {"status": "失败", "message": f"读取配置失败: {e}", "data": None}

    cfg.proxies = None
    cfg.visitors = None
    return {
        "status": "成功",
        "message": f"获取程序{program_id}配置成功",
        "data": cfg.model_dump(by_alias=True, exclude_none=True),
    }


def new_client_config(program_id: str, data: str) -> dict:
    """创建指定客户端ID的配置文件
    
    注意这里修改的不是隧道(proxy)和观察者(visitor)的配置信息，client_configs接口仅处理client与server的连接配置。  
    
    请求示例(不是全部参数):  
    - program_id = "0"
    - data = {"serverAddr": "127.0.0.1", "serverPort": 7000}  
    
    返回格式:
    ```json
    {
        "status": "成功",
        "message": "获取客户端配置成功",
    }
    ```
    
    - `status`: 请求状态，成功或失败
    - `message`: 请求结果的描述信息
    
    Args:
        program_id (str): 客户端ID
        data (str): 客户端配置数据
    
    Returns:
        dict: 包含请求状态、消息和客户端配置的字典
    """
    if isinstance(program_id, int):
        program_id = str(program_id)

    # 验证程序存在
    try:
        with DataBase(database_path) as db:
            ids = [str(r[0]) for r in db.query_program()]
    except Exception as e:
        return {"status": "失败", "message": f"数据库查询失败: {e}"}

    if program_id not in ids:
        return {"status": "失败", "message": f"程序{program_id}不存在"}

    folder = os.path.join(cmd_dir, program_id)
    if not os.path.isdir(folder):
        return {"status": "失败", "message": f"客户端目录不存在: {folder}"}

    cfg_file = os.path.join(folder, "frpc.toml")
    if os.path.exists(cfg_file):
        return {"status": "失败", "message": f"配置文件已存在: {cfg_file}"}

    try:
        body = json.loads(data)
        cfg = ClientConfig(**body)
    except json.JSONDecodeError as e:
        return {"status": "失败", "message": f"JSON 解析失败: {e}"}
    except Exception as e:
        return {"status": "失败", "message": f"配置校验失败: {e}"}

    # 检查 admin ui 端口冲突
    if cfg.webServer and cfg.webServer.port:
        msg = check_admin_ui_port_conflict(cfg.webServer.port)
        if msg:
            return msg

    cfg.proxies = None
    cfg.visitors = None

    try:
        ConfigManager(cfg_file).save_config(cfg)
    except Exception as e:
        return {"status": "失败", "message": f"保存配置失败: {e}"}

    return {"status": "成功", "message": f"客户端{program_id}配置创建成功"}


def update_client_config(program_id: str, data: str) -> dict:
    """修改指定客户端ID的配置文件
    
    注意这里修改的不是隧道(proxy)和观察者(visitor)的配置信息，client_configs接口仅处理client与server的连接配置。  
    
    请求示例(不是全部参数):  
    - program_id = "0"
    - data = {"serverAddr": "127.0.0.1", "serverPort": 7000}  
    
    返回格式:
    ```json
    {
        "status": "成功",
        "message": "获取客户端配置成功",
    }
    ```
    
    - `status`: 请求状态，成功或失败
    - `message`: 请求结果的描述信息
    
    Args:
        program_id (str): 客户端ID
        data (str): 新的客户端配置数据
    
    Returns:
        dict: 包含请求状态、消息和客户端配置的字典
    """
    if isinstance(program_id, int):
        program_id = str(program_id)

    # 验证程序存在
    try:
        with DataBase(database_path) as db:
            ids = [str(r[0]) for r in db.query_program()]
    except Exception as e:
        return {"status": "失败", "message": f"数据库查询失败: {e}"}
    if program_id not in ids:
        return {"status": "失败", "message": f"程序{program_id}不存在"}
    
    cfg_file = os.path.join(cmd_dir, program_id, "frpc.toml")
    if not os.path.isfile(cfg_file):
        return {"status": "失败", "message": f"配置文件不存在: {cfg_file}"}

    try:
        body = json.loads(data)
        new_cfg = ClientConfig(**body)
        old_cfg = ConfigManager(cfg_file).load_config()
    except json.JSONDecodeError as e:
        return {"status": "失败", "message": f"JSON 解析失败: {e}"}
    except Exception as e:
        return {"status": "失败", "message": f"配置校验失败: {e}"}

    # 检查 admin ui 端口冲突
    if new_cfg.webServer and new_cfg.webServer.port:
        msg = check_admin_ui_port_conflict(new_cfg.webServer.port, program_id)
        if msg:
            return msg
    
    if old_cfg.proxies:
        new_cfg.proxies = old_cfg.proxies
    
    if old_cfg.visitors:
        new_cfg.visitors = old_cfg.visitors

    try:
        ConfigManager(cfg_file).save_config(new_cfg)
    except Exception as e:
        return {"status": "失败", "message": f"保存配置失败: {e}"}

    return {"status": "成功", "message": f"客户端{program_id}配置更新成功"}


def delete_client_config(program_id: str) -> dict:
    """删除指定客户端ID的配置  
    
    **注意**：这里修改的不是隧道(proxy)和观察者(visitor)的配置信息，client_configs接口仅处理client与server的连接配置。  
    
    **注意**：删除行为会导致数据丢失，一定要用户确认后再删除!  
    
    返回格式:
    ```json
    {
        "status": "成功",
        "message": "获取客户端配置成功",
    }
    ```
    
    - `status`: 请求状态，成功或失败
    - `message`: 请求结果的描述信息
    
    Args:
        program_id (str): 客户端

    Returns:
        dict: 操作结果
    """
    if isinstance(program_id, int):
        program_id = str(program_id)

    # 验证程序存在
    try:
        with DataBase(database_path) as db:
            ids = [str(r[0]) for r in db.query_program()]
    except Exception as e:
        return {"status": "失败", "message": f"数据库查询失败: {e}"}
    if program_id not in ids:
        return {"status": "失败", "message": f"程序{program_id}不存在"}
    
    cfg_file = os.path.join(cmd_dir, program_id, "frpc.toml")
    if not os.path.isfile(cfg_file):
        return {"status": "失败", "message": f"配置文件不存在: {cfg_file}"}

    try:
        os.remove(cfg_file)
    except Exception as e:
        return {"status": "失败", "message": f"删除失败: {e}"}

    return {"status": "成功", "message": f"客户端{program_id}配置删除成功"}