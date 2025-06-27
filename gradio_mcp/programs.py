from utils.locale_m import _
import asyncio
import logging
import os
import shutil
from utils.ConfigManager import ConfigManager
from utils.database import DataBase
from utils.program_manager import ProgramManager
import gradio as gr
import requests

# 临时配置文件地址
database_path = "data/data.db"
#
logger = logging.getLogger("gradio_mcp.programs")

ACTION_LIST = ["start", "stop", "restart", "reload"]

manager = ProgramManager()

def list_programs() -> dict:
    """返回frpc客户端列表

    返回的格式为：
    ```json
    {
        "status": "成功",
        "message": "获取客户端列表成功",
        "data": [
            {
                "id": 0,
                "name": "示例 HK",
                "description": "连接HK的客户端",
                "status": "运行",
            },
        ]
    }
    ```
    
    - `status`: 操作状态，成功或失败
    - `message`: 操作信息
    - `data`: 客户端列表，格式为json数组，每个元素包含以下
        - `id`: 客户端唯一标识
        - `name`: 用户给客户端备注的名字
        - `description`: 用户给的客户端备注，选填
        - `status`: 客户端状态，目前有三种：运行、停止和为运行
            - `运行`: 客户端正在运行
            - `停止`: 客户端已停止
            - `未运行`: 客户端在MCP服务器启动后没运行过
    
    Returns:
        dict: 包含状态和信息的json, 格式为`{"status": "成功"|"失败", "message": "消息", "data": 数据, json格式, 如失败data为Nano}`
    """
    global manager, database_path
    
    try:
        with DataBase(database_path) as db:
            results = db.query_program()
            programs = [
                {"id": row[0], "name": row[1], "description": row[2]}
                for row in results
            ]
    except Exception as e:
        return {
            "status": "成功",
            "message": f"数据库查询失败: {str(e)}",
            "data": None
        }
    
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
    
    return {
        "status": "成功",
        "message": "获取客户端列表成功",
        "data": programs,
    }

def delete_program(program_id: str) -> dict:
    """根据客户端ID删除客户端及其配置文件  
    
    注意: 使用这个函数之前一定要得到用户的肯定!丢失的数据无法复原!

    Args:
        program_id (str): 要删除的客户端ID

    Returns:
        dict: 包含状态和信息的json, 格式为`{"status": "成功"|"失败", "message": "内容"}`
    """
    global database_path
    
    if isinstance(program_id, str):
        try:
            program_id_int = int(program_id)
        except ValueError:
            return {
                "status": "失败",
                "message": "客户端ID格式错误",
            }
    
    try:
        with DataBase(database_path) as db:
            # 尝试删除数据库中的记录
            success = db.delete_program(program_id_int)
            if not success:
                return {
                    "status": "失败",
                    "message": f"未找到ID为{program_id_int}的程序"
                }
    except Exception as e:
        return {
            "status": "失败",
            "message": f"数据库操作失败: {str(e)}"
        }

    # 数据库删除成功后，尝试删除目标目录
    cmd_dir = os.path.join("data", "cmd", str(program_id_int))
    try:
        if os.path.isdir(cmd_dir):
            shutil.rmtree(cmd_dir)
    except Exception as e:
        return {
            "status": "失败",
            "message": f"程序文件夹删除失败: {str(e)}"
        }
    
    return {
        "status": "成功",
        "message": f"删除ID为{program_id_int}的客户端成功"
    }

def start_program(program_id: str,) -> dict:
    """根据程序ID启动FRPC程序

    Args:
        program_id (str): 程序ID

    Returns:
        dict: 包含状态和信息的json, 格式为`{"status": "成功"|"失败", "message": "内容"}`
    """
    global manager
    
    if not os.path.exists(f"data/cmd/{program_id}/frpc"):
        return {
            "status": "失败",
            "message": f"程序ID为{program_id}的FRPC可执行文件不存在",
        }
    
    if not os.path.exists(f"data/cmd/{program_id}/frpc.toml"):
        return {
            "status": "失败",
            "message": f"程序ID为{program_id}的FRPC配置文件不存在"
        }
    
    for i in manager.get_status():
        if i["id"] == program_id:
            manager.get_instance(i["id"]).start() # type: ignore
            return {
                "status": "成功", 
                "message": f"程序ID为{program_id}的程序已启动"
            }
    # 如果不在列表中, 先添加进列表，默认启动
    manager.add_instance(
        id=program_id,
        frpc_path=f"data/cmd/{program_id}/frpc",
        config_path=f"data/cmd/{program_id}/frpc.toml"
    )
    
    return {
        "status": "成功", 
        "message": f"程序ID为{program_id}的程序已启动"
    }

async def stop_program(program_id: str,) -> dict:
    """根据程序ID停止指定程序

    Args:
        program_id (str): 程序ID

    Returns:
        dict: 包含状态和信息的json, 格式为`{"status": "成功"|"失败", "message": "内容"}`
    """
    global manager
    
    for i in manager.get_status():
        if i["id"] == program_id:
            try:
                await manager.get_instance(i["id"]).stop() # type: ignore
                return {
                    "status": "成功", 
                    "message": f"程序ID为{program_id}的程序已停止"
                }
            except Exception as e:
                return {
                    "status": "失败", 
                    "message": f"程序ID为{program_id}停止失败: {str(e)}"
                }

    return {
        "status": "成功", 
        "message": f"程序ID为{program_id}未在运行，无需停止"
    }

async def reload_program(program_id: str,) -> dict:
    """根据程序ID热重载配置

    Args:
        program_id (str): 程序ID
    
    Returns:
        dict: 包含状态和信息的json, 格式为`{"status": "成功"|"失败", "message": "内容"}`
    """
    global manager
    
    # 检查程序是否正在运行
    is_program_work = False
    status = manager.get_status()
    for i in status:
        if i['id'] == program_id and i['status'] == "运行":
            is_program_work = True
            break
    if not is_program_work:
        return {
            "status": "失败", 
            "message": f"程序 {program_id} 未运行"
        }

    # 检查配置文件是否存在
    if not os.path.isfile(f"data/cmd/{program_id}/frpc.toml"):
        return {
            "status": "失败", 
            "message": f"程序 {program_id} 没有配置文件"
        }
    
    try:
        config_manager = ConfigManager(f"data/cmd/{program_id}/frpc.toml")
        config = config_manager.load_config()
    except Exception as e:
        return {
            "status": "失败", 
            "message": f"无法读取配置文件: {str(e)}"
        }
    
    is_have_web_config = config.webServer and \
        config.webServer.addr and \
        config.webServer.port and \
        config.webServer.user and \
        config.webServer.password
    
    if not is_have_web_config:
        return {
            "status": "失败", 
            "message": f"无法reload, 配置文件中webserver未配置, 该客户端{program_id}不支持热重载"
        }
    else:
        addr = config.webServer.addr # type: ignore
        port = config.webServer.port # type: ignore
        user = config.webServer.user # type: ignore
        password = config.webServer.password # type: ignore
    
    try:
        response = requests.get(f"http://{addr}:{port}/api/reload", auth=(user, password)) # type: ignore
    except Exception as e:
        return {
            "status": "失败", 
            "message": f"无法reload, 访问webserver失败。{str(e)}"
        }
    
    if response.status_code != 200:
        
        return {
            "status": "失败", 
            "message": f"使用frpc reload失败，错误码{response.status_code}, 内容：{response.text[:200].strip()}。"
        }
    
    return {"status": "成功", "message": "重载成功"}    

async def program_controller(program_id: str, action: str,):
    """根据指定操作控制FRPC客户端程序

    支持的操作类型包括：
    - 启动(start)：创建并运行新的客户端实例
    - 停止(stop)：终止正在运行的客户端实例
    - 重启(restart)：先停止后启动客户端
    - 热重载(reload)：在运行时更新配置

    请求参数示例：
    ```json
    {
        "program_id": "1",
        "action": "start"
    }
    ```

    返回值格式：
    ```json
    {
        "status": "成功|失败",
        "message": "操作描述信息",
    }
    ```

    异常处理逻辑：
    1. 程序ID不存在：触发数据库查询失败
    2. 非法操作类型：触发不支持的操作类型错误
    3. 文件缺失：启动时检查可执行文件和配置文件存在性
    4. ID格式错误：字符串ID转数字失败时触发

    Args:
        program_id (str): 客户端唯一标识符
        action (str): 支持的操作类型，可取值: ["start", "stop", "restart", "reload"]

    Returns:
        dict: 包含状态和信息的JSON对象，格式为：
        {
            "status": "成功|失败",
            "message": "描述操作结果的具体信息",
        }
    """
    global manager, database_path
    
    if isinstance(program_id, str):
        try:
            program_id_int = int(program_id)
        except ValueError:
            return {
                "status": "失败",
                "message": "客户端ID格式错误",
            }
    
    # 从数据库中验证程序ID是否存在
    try:
        with DataBase(database_path) as db:
            program = db.query_program(program_id=program_id_int)
            if not program:
                return {
                    "status": "失败",
                    "message": f"未找到ID为{program_id_int}的程序"
                }
    except Exception as e:
        return {
            "status": "失败",
            "message": f"数据库查询失败: {str(e)}"
        }
    
    # 从动作列表中验证动作是否合法
    if action not in ACTION_LIST:
        return {
            "status": "失败",
            "message": f"不支持的操作类型: {action}"
        }
    
    if action == "start":
        msg = start_program(program_id)
        return msg
    
    if action == "stop":
        msg = await stop_program(program_id)
        return msg
    
    if action == "restart":
        await stop_program(program_id)
        msg = start_program(program_id)
        return msg
    
    if action == "reload":
        return await reload_program(program_id)

def new_program(tab_var):
    """上传program的gradio界面"""

    def submit(gr_file: gr.File, name: str, description: str):
        program_id = None
        try:
            if not gr_file or not name or len(name) == 0:
                raise gr.Error(_("请正确上传客户端和设置客户端名称"))
            
            try:
                with DataBase(database_path) as db:
                    # 验证 name 是否重复
                    exist = db.query_program(name=name)
                    if exist:
                        raise gr.Error(_("名称%s已存在，请重新设置名称") % name)
                    program_id = db.insert_program(name=name, description=description)
            except gr.Error as e:
                raise e
            except Exception as e:
                logger.error("查询数据库失败，错误: %s" % str(e)) 
                raise gr.Error(_("查询数据库失败"))
            exe_path = gr_file.name  # type: ignore
            
            dest_dir = os.path.join("data", "cmd", str(program_id))
            os.makedirs(dest_dir, exist_ok=True)
            dest_exe_path = os.path.join(dest_dir, os.path.basename(exe_path))
            
            try:
                shutil.copy2(exe_path, dest_exe_path)
                os.chmod(dest_exe_path, 0o755)
            except Exception as e:
                logger.error("文件复制出错，错误: %s" % str(e))
                raise gr.Error(_("文件复制出错"))
            
            gr.Success(_("客户端创建成功"), duration=3)
        except gr.Error as e:
            logger.info("程序新建失败, 开始回退")
            if program_id is not None:
                try:
                    with DataBase(database_path) as db:
                        db.delete_program(program_id)
                except Exception as e:
                    logger.warning(f"回退时删除客户端{program_id}数据库数据错误")
            if os.path.exists(os.path.join("data", "cmd", str(program_id))):
                try:
                    shutil.rmtree(os.path.join("data", "cmd", str(program_id)))
                except Exception as e:
                    logger.warning(f"回退时删除客户端{program_id}目录错误")
            raise e # type: ignore

    gr.Markdown("## %s" % _("新建客户端"))

    file_input = gr.File(label=_("拖动或点击以上传frpc客户端程序"))
    name = gr.Textbox(label=_("客户端名称"))
    description = gr.Textbox(label=_("客户端描述"))
    
    def clean_file_input():
        return gr.File(value=None)
    def clean_textbox():
        return gr.Textbox(value=None)
    
    tab_var.select(show_api=False, fn=clean_file_input, outputs=file_input)
    tab_var.select(show_api=False, fn=clean_textbox, outputs=name)
    tab_var.select(show_api=False, fn=clean_textbox, outputs=description)
    
    btn = gr.Button(_("新建客户端"))
    btn.click(fn=submit, inputs=[file_input, name, description], show_api=False)

async def watch_log(program_name: str):
    """查看程序日志"""
    from ansi2html import Ansi2HTMLConverter
    WARNING_TEMPLATE = (
    "<p style='color: #856404; background-color: #fff3cd;"
    " border: 1px solid #ffeeba; padding: 8px;"
    " border-radius: 4px; margin-top: 10px;'>"
    f"<strong>{_('注意')}：</strong> %s" # 注意：f格式化字符串会导致无法动态切换语言
    "</p>"
    )
    program_list = list_programs()
    if not program_list["status"] == "成功":
        logger.error(f"获取程序列表数据错误，错误：{program_list['message']}")
        raise gr.Error(_("获取程序列表数据错误"))
    program_list = program_list['data'] # list
    
    program_name_id_map = {}
    for i in range(len(program_list)):
        program_name_id_map[program_list[i]['name']] = str(program_list[i]['id'])
    
    program_id = program_name_id_map[program_name]
    
    is_running = False
    for program in program_list:
        if program_id == str(program['id']) and program['status'] == "运行":
            is_running = True
    not_running_msg = None
    if not is_running:
        not_running_msg = _("程序%s未在运行，输出的日志可能过时") % program_name
    
    log_file = f"data/cmd/{program_id}/log.log"
    
    # 等待日志文件生成
    count = 0
    while not os.path.exists(log_file):
        if count > 30:
            yield WARNING_TEMPLATE % _("程序未输出日志文件")
            return
        else:
            count += 1
        await asyncio.sleep(0.1)
    
    with open(log_file, "r") as f:
        conv = Ansi2HTMLConverter(inline=True)
        f.seek(0)
        content = f.read()
        html = conv.convert(content)
        if not_running_msg:
            html += WARNING_TEMPLATE % not_running_msg
        yield html
