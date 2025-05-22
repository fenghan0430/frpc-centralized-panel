import os
from fastapi import APIRouter, HTTPException, Path
from entity.client import ClientConfig
from utils.ConfigManager import ConfigManager

router = APIRouter(
    prefix="/api/v1",
    responses={404: {"description": "Not found"}},
)

def check_admin_ui_port_conflict(new_port: int, current_id: str | None = None):
    """
    检查admin ui端口是否冲突

    Args:
        new_port (int): 需要验证的端口号
        current_id (str, optional): 当前客户端ID（用于修改时跳过自己）

    Raises:
        HTTPException: 如果端口冲突，抛出409错误
    """
    cmds_dir = "data/cmd"
    for entry in os.listdir(cmds_dir):
        if current_id and entry == current_id:
            continue  # 跳过当前客户端自己
        entry_path = os.path.join(cmds_dir, entry)
        config_path = os.path.join(entry_path, "frpc.toml")
        if not os.path.isdir(entry_path):
            continue
        if not os.path.exists(config_path):
            continue
        try:
            exist_config = ConfigManager(config_path).load_config()
        except Exception:
            continue
        if exist_config.webServer and exist_config.webServer.port == new_port:
            raise HTTPException(
                status_code=409,
                detail={
                    "status": 409,
                    "message": f"admin ui端口号 {new_port} 已被客户端 {entry} 占用"
                }
            )

def get_client_config(id: str):
    """
    获取客户端的配置文件。

    Args:
        id (str): 客户端ID，用于定位配置文件。

    Returns:
        ConfigManager: 已加载的客户端配置信息对象。

    Raises:
        - 404: 找不到配置文件
        - 500: 读取配置文件异常
    """
    config_path = f"data/cmd/{id}/frpc.toml"
    
    if not os.path.exists(config_path):
        raise HTTPException(
            status_code=404,
            detail={
                "status": "404",
                "message": f"客户端{id}找不到配置文件"
            }
        )
    try:
        client_config = ConfigManager(config_path).load_config()
        return client_config
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "500",
                "message": f"读取配置文件失败: {str(e)}"
            }
        )

@router.get("/client/{id}")
def get_client(
    id: str = Path(..., description="客户端ID"),
):
    """获取指定客户端配置

    Args:
        id (str): 客户端ID.

    Returns:
        - 200: 成功返回客户端配置
    
    Raises:
        - 404: 客户端ID不存在
        - 500: 读取配置文件失败
    """
    client_config = get_client_config(id)
    
    client_config.proxies = None
    client_config.visitors = None
    
    return client_config.model_dump(by_alias=True, exclude_none=True)

@router.post("/client/{id}", status_code=201)
def new_client_config(
    config: dict,
    id: str = Path(..., description="客户端ID"),
):
    """
    新建指定客户端的配置文件

    Args:
        config (dict): 配置内容
        id (str): 客户端ID

    Returns:
        - 201: 创建成功返回消息

    Raises:
        - 404: 找不到客户端目录
        - 409: 配置文件已存在
        - 422: 配置格式不正确
        - 409: admin ui 端口号冲突
        - 500: 配置保存失败
    """
    config_path = f"data/cmd/{id}"
    
    if not os.path.exists(config_path):
        raise HTTPException(
            status_code=404,
            detail={
                "status": "404",
                "message": f"找不到客户端{id}，无法创建配置文件"
            }
        )
    
    config_file_path = os.path.join(config_path, "frpc.toml")
    
    if os.path.exists(config_file_path):
        raise HTTPException(
            status_code=409,
            detail={
                "status": "409",
                "message": f"客户端{id}已存在配置文件，无法创建配置文件"
                }
            )
    
    client_config = None
    try:
        client_config = ClientConfig(**config)
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail={
                "status": 422,
                "message": f"配置文件格式不正确: {str(e)}"
            }
        )
    
    new_port = None
    if client_config.webServer and client_config.webServer.port:
        new_port = client_config.webServer.port

    if new_port is not None:
        check_admin_ui_port_conflict(new_port)
    
    client_config.proxies = None
    client_config.visitors = None
    
    try:
        ConfigManager(
            config_file = config_file_path
            ).save_config(client_config)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": 500,
                "message": f"保存配置文件失败: {str(e)}"
            }
        )
    
    return {"status": 201, "message": "配置文件创建成功"}

@router.patch("/client/{id}")
def change_client_config(
    new_config_dict: dict,
    id: str = Path(..., description="客户端ID"),
):
    """
    修改指定客户端的配置文件

    Args:
        new_config_dict (dict): 新配置内容
        id (str): 客户端ID

    Returns:
        - 200: 修改成功返回消息

    Raises:
        - 404: 配置文件不存在
        - 422: 配置格式不正确
        - 409: admin ui 端口号冲突
        - 500: 配置保存失败
    """
    config_file_path = f"data/cmd/{id}/frpc.toml"
    
    if not os.path.exists(config_file_path):
        raise HTTPException(
            status_code=404,
            detail={
                "status": "404",
                "message": f"客户端{id}找不到配置文件"
            }
        )
    
    new_config = None
    try:
        new_config = ClientConfig(**new_config_dict)
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail={
                "status": 422,
                "message": f"配置文件格式不正确: {str(e)}"
            }
        )
    
    if new_config.webServer and new_config.webServer.port:
        check_admin_ui_port_conflict(new_config.webServer.port, id)

    try:
        ConfigManager(
            config_file = config_file_path
            ).save_config(new_config)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": 500,
                "message": f"保存配置文件失败: {str(e)}"
            }
        )
    
    return {"status": 200, "message": "配置文件修改成功"}

@router.delete("/client/{id}")
def delete_client_config(
    id: str = Path(..., description="客户端ID"),
):
    """
    删除指定客户端的配置文件

    Args:
        id (str): 客户端ID

    Returns:
        - 200: 删除成功返回消息

    Raises:
        - 404: 配置文件不存在
        - 500: 删除失败
    """
    config_file_path = f"data/cmd/{id}/frpc.toml"
    
    if not os.path.exists(config_file_path):
        raise HTTPException(
            status_code=404,
            detail={
                "status": "404",
                "message": f"客户端{id}找不到配置文件"
            }
        )
    try:
        os.remove(config_file_path)
        return {"status": 200, "message": "配置文件删除成功"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": 500,
                "message": f"删除配置文件失败: {str(e)}"
            }
        )
