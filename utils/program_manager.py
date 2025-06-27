import threading
from typing import Any, Dict, List
from utils.frpc_instance import FrpcInstance
import logging

class ProgramManager:
    """
    FRPC 多实例管理器。
    用于统一管理多个 FRPC 实例的生命周期及状态。
    """
    # 单例代码
    _instance_lock = threading.Lock()
    def __new__(cls, *args, **kwargs):
        if not hasattr(ProgramManager, "_instance"):
            with ProgramManager._instance_lock:
                if not hasattr(ProgramManager, "_instance"):
                    ProgramManager._instance = object.__new__(cls)  
        return ProgramManager._instance
    
    def __init__(self):
        """
        初始化 ProgramManger，创建空实例列表。
        """
        self.instances = []
        self.logger = logging.getLogger("utils.program_manager")

    def add_instance(self, id: str, frpc_path: str, config_path: str):
        """
        添加并启动一个新的 FRPC 实例。

        Args:
            id (str): frpc 实例的唯一标识。
            frpc_path (str): frpc 可执行文件路径。
            config_path (str): 配置文件路径。

        Raises:
            ValueError: 如果已存在相同 id 的实例。
        """
        for item in self.instances:
            if item['id'] == id:
                raise ValueError(f"已存在 id 为 {id} 的 FRPC 实例")
        frpc = FrpcInstance(frpc_path, config_path, id)
        frpc.start()
        self.instances.append({
            "id": id,
            "obj": frpc,
        })

    def get_status(self) -> List[Dict[str, Any]]:
        """
        实时获取所有 FRPC 实例的当前状态。

        Returns:
            list: 每个元素为 {'id', 'status'} 的列表。
        """
        status_list = []
        for item in self.instances:
            status = "运行" if item['obj'].is_running() else "停止"
            status_list.append({"id": item['id'], "status": status})
        return status_list

    def get_instance(self, id: str) -> FrpcInstance | None:
        """
        获取指定 id 的 FRPC 实例对象。

        Args:
            id (str): 实例的唯一标识。

        Returns:
            FrpcInstance: 找到的实例对象，未找到返回 None。
        """
        for item in self.instances:
            if item['id'] == id:
                return item['obj']
        return None

    def stop_all(self):
        """
        停止所有正在运行的 FRPC 实例。
        """
        self.logger.info("正在关闭所有 Frpc")
        for item in self.instances:
            if item['obj'].is_running():
                item['obj'].stop()
