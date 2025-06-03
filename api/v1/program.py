import os
import shutil
from fastapi import APIRouter, Depends, Form, HTTPException, Path
from pydantic import BaseModel, Field
import requests
from utils.ConfigManager import ConfigManager
from utils.database import DataBase
from utils.function_from_main import get_manager_from_main
from utils.program_manager import ProgramManager

# test
database_path = "data/data.db"

ACTION_LIST = ["start", "stop", "restart", "reload"]

router = APIRouter(
    prefix="/api/v1",
    responses={404: {"description": "Not found"}},
)

def validate_temp_exe_dir(file_id: str) -> str:
    """
    校验临时上传目录下的exe文件是否合法

    Args:
        file_id (str): 临时文件夹ID

    Raises:
        HTTPException: 当file_id格式错误、目录不存在或文件不满足要求时抛出

    Returns:
        str: 有效的exe文件绝对路径
    """
    if not file_id.startswith("exe-"):
        raise HTTPException(
            status_code=400,
            detail={"status": 400, "message": "file_id格式非法，必须以exe-开头"}
        )
    temp_dir = os.path.join("data", "temp", file_id)
    if not os.path.isdir(temp_dir):
        raise HTTPException(
            status_code=404,
            detail={"status": 404, "message": f"file_id:{file_id}不存在"}
        )
    files = os.listdir(temp_dir)
    file_name = files[0]
    return os.path.join(temp_dir, file_name)

@router.post("/program", status_code=201)
async def upload_program(
    name = Form(..., description="程序名称"),
    file_id = Form(..., description="上传文件id"),
    description = Form(None, description="程序描述"),
):
    """
    接收客户端提交的程序信息，完成数据库插入并移动可执行文件到目标目录

    Args:
        request (Request): FastAPI请求对象

    Raises:
        HTTPException: 校验file_id不通过或数据库、文件操作异常则抛出

    Returns:
        JSONResponse: 返回新增的程序数据库ID及相关信息
    """

    exe_path = validate_temp_exe_dir(file_id)

    try:
        with DataBase(database_path) as db:
            # 验证 name 是否重复
            exist = db.query_program(name=name)
            if exist:
                raise HTTPException(
                    status_code=409,
                    detail={"status": 409, "message": f"程序名称“{name}”已存在"}
                )
            program_id = db.insert_program(name=name, description=description)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"status": 500, "message": f"数据库操作失败: {str(e)}"}
        )

    dest_dir = os.path.join("data", "cmd", str(program_id))
    os.makedirs(dest_dir, exist_ok=True)
    dest_exe_path = os.path.join(dest_dir, os.path.basename(exe_path))
    try:
        shutil.copy2(exe_path, dest_exe_path)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"status": 500, "message": f"文件复制失败: {str(e)}"}
        )

    return {"id": program_id, "status": 201, "message": "程序新建成功"}

@router.get("/program", status_code=200)
async def list_programs(manager: ProgramManager = Depends(get_manager_from_main)):
    """
    获取数据库中所有程序信息，并携带当前运行状态。

    Returns:
        list: 包含所有程序的列表，每个元素包含 id, name, description, status。其中 status 为"运行"、"停止"或"未运行"。
    """
    try:
        with DataBase(database_path) as db:
            results = db.query_program()
            programs = [
                {"id": row[0], "name": row[1], "description": row[2]}
                for row in results
            ]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"status": 500, "message": f"数据库查询失败: {str(e)}"}
        )

    # 获取所有实例的运行状态信息
    instance_status_list = manager.get_status()  # 例: [{"id": 1, "status": "运行"}, ...]
    id_status_map = {str(item["id"]): item["status"] for item in instance_status_list}

    # 运行过的id集合
    status_ids = set(id_status_map.keys())
    for program in programs:
        program_id_str = str(program["id"])
        # 若程序ID未出现在status列表中，标记为"未运行"
        if program_id_str in status_ids:
            program["status"] = id_status_map[program_id_str]
        else:
            program["status"] = "未运行"

    return programs

@router.delete("/program/{program_id}", status_code=200)
async def delete_program(
    program_id: int = Path(..., description="要删除的程序ID")
):
    """
    删除指定程序记录及关联文件夹

    Args:
        program_id (int): 程序ID

    Raises:
        HTTPException: 数据库/文件操作异常或找不到记录

    Returns:
        dict: 删除结果及状态信息
    """
    try:
        with DataBase(database_path) as db:
            # 尝试删除数据库中的记录
            success = db.delete_program(program_id)
            if not success:
                raise HTTPException(
                    status_code=404,
                    detail={"status": 404, "message": f"未找到ID为{program_id}的程序"}
                )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"status": 500, "message": f"数据库操作失败: {str(e)}"}
        )
    # 数据库删除成功后，尝试删除目标目录
    cmd_dir = os.path.join("data", "cmd", str(program_id))
    try:
        if os.path.isdir(cmd_dir):
            shutil.rmtree(cmd_dir)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"status": 500, "message": f"程序文件夹删除失败: {str(e)}"}
        )

    return {"id": program_id, "status": 200, "message": "程序删除成功"}

def start_program(
    program_id: str,
    manager: ProgramManager,
):
    """启动指定ID的程序。

    如果程序已经存在于管理器中则直接启动，
    如果不存在则尝试根据指定路径加载FRPC可执行文件和配置文件，并注册后启动。

    Args:
        program_id (str): 要启动的程序ID。
        manager (ProgramManager): 程序管理器实例。

    Raises:
        HTTPException: 当对应的FRPC可执行文件或配置文件不存在时，抛出404异常。

    Returns:
        dict: 包含启动状态和消息的字典，例如 {'status': 200, 'message': '程序ID为xxx的程序已启动'}
    """
    if not os.path.exists(f"data/cmd/{program_id}/frpc"):
        raise HTTPException(
            status_code=404,
            detail={"status": 404, "message": f"程序ID为{program_id}的FRPC可执行文件不存在"}
            )
    
    if not os.path.exists(f"data/cmd/{program_id}/frpc.toml"):
        raise HTTPException(
            status_code=404,
            detail={"status": 404, "message": f"程序ID为{program_id}的FRPC配置文件不存在"}
            )
    
    for i in manager.get_status():
        if i["id"] == program_id:
            manager.get_instance(i["id"]).start() # type: ignore
            return {"status": 200, "message": f"程序ID为{program_id}的程序已启动"}
        
    manager.add_instance(
        id=program_id,
        frpc_path=f"data/cmd/{program_id}/frpc",
        config_path=f"data/cmd/{program_id}/frpc.toml"
    )
    
    return {"status": 200, "message": f"程序ID为{program_id}的程序已启动"}

async def stop_program(
    program_id: str,
    manager: ProgramManager,
):
    """停止指定ID的程序。

    如果程序在管理器中运行则调用其实例的 stop 方法，否则返回无需停止。

    Args:
        program_id (str): 要停止的程序ID。
        manager (ProgramManager): 程序管理器实例。

    Returns:
        dict: 包含停止状态和消息的字典。例如 {'status': 200, 'message': '程序ID为xxx的程序已停止'}
              若未找到需停止的实例，返回 {'status': 204, 'message': '程序ID为xxx未在运行，无需停止'}
    """
    for i in manager.get_status():
        if i["id"] == program_id:
            try:
                await manager.get_instance(i["id"]).stop() # type: ignore
                return {"status": 200, "message": f"程序ID为{program_id}的程序已停止"}
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail={"status": 500, "message": f"程序ID为{program_id}停止失败: {str(e)}"}
                )
    return {"status": 204, "message": f"程序ID为{program_id}未在运行，无需停止"}

async def reload_program(
    program_id: str,
    manager: ProgramManager
):
    """重新加载指定程序的配置文件

    Args:
        program_id (str): 需要重载的程序ID
        manager (ProgramManager): 程序管理器实例

    Returns:
        dict: 包含状态和消息的字典
    
    Raises:
        HTTPException: 当程序未运行、配置文件缺失或重载失败时抛出异常
    """
    # 检查程序是否正在运行
    status = manager.get_status()
    for i in status:
        if i['id'] == program_id and i['status'] == "运行":
            break
    else:
        raise HTTPException(
            status_code=422,
            detail={"status": 422, "message": f"程序 {program_id} 未运行"}
        )

    # 检查配置文件是否存在
    if not os.path.isfile(f"data/cmd/{program_id}/frpc.toml"):
        raise HTTPException(
            status_code=422,
            detail={"status": 422, "message": f"程序 {program_id} 没有配置文件"}
        )
    
    try:
        config = ConfigManager(f"data/cmd/{program_id}/frpc.toml")
        client_config = config.load_config()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"status": 500, "message": f"无法读取配置文件: {str(e)}"}
        )
    
    is_have_web_config = client_config.webServer and \
        client_config.webServer.addr and \
        client_config.webServer.port and \
        client_config.webServer.user and \
        client_config.webServer.password
    
    if not is_have_web_config:
        raise HTTPException(
            status_code=422,
            detail={"status": 422, "message":"无法reload, webserver未配置"}
        )
    else:
        addr = client_config.webServer.addr # type: ignore
        port = client_config.webServer.port # type: ignore
        user = client_config.webServer.user # type: ignore
        password = client_config.webServer.password # type: ignore
    
    try:
        response = requests.get(f"http://{addr}:{port}/api/reload", auth=(user, password)) # type: ignore
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail={"status": 422, "message":"无法reload, 访问webserver失败。%s"%str(e)}
        )
    
    if response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail={
                "status": "502", 
                "message": f"使用frpc reload失败，错误码{response.status_code}, 内容：{response.text[:200].strip()}。"
            }
        )
    
    return {"status": 200, "message": "重载成功"}

class ProgramControllerResponse(BaseModel):
    action: str = Field(..., description="操作类型，支持 start, stop, restart")

@router.post("/program/{program_id}")
async def program_controller(
    body: ProgramControllerResponse,
    program_id: str = Path(..., description="要操作的程序ID"),
    manager: ProgramManager = Depends(get_manager_from_main),
    ):
    action = body.action
    
    # 从数据库中验证程序ID是否存在
    try:
        with DataBase(database_path) as db:
            program = db.query_program(program_id=program_id)
            if not program:
                raise HTTPException(
                    status_code=404,
                    detail={"status": 404, "message": f"未找到ID为{program_id}的程序"}
                )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"status": 500, "message": f"数据库查询失败: {str(e)}"}
        )
    # 从动作列表中验证动作是否合法
    if action not in ACTION_LIST:
        raise HTTPException(
            status_code=400,
            detail={"status": 400, "message": f"不支持的操作类型: {action}"}
        )
    
    if action == "start":
        msg = start_program(program_id, manager)
        return msg
    
    if action == "stop":
        msg = await stop_program(program_id, manager)
        return msg
    
    if action == "restart":
        await stop_program(program_id, manager)
        msg = start_program(program_id, manager)
        return msg
    
    if action == "reload":
        return await reload_program(program_id, manager)
