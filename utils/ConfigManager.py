import json
import time
from typing import Literal
from filelock import FileLock
from pathlib import Path
import toml
from entity.client import ClientConfig
from utils.load2class import load_config

class ConfigLoadError(Exception):
    pass

class ConfigSaveError(Exception):
    pass

class ConfigManager:
    
    def __init__(self, 
                 config_file: str, 
                 timeout: int = 10, 
                 config_type: Literal['toml', 'ini'] = 'toml'):
        """
        初始化配置管理类
        
        Args:
            config_file: 配置文件路径
            timeout: 锁超时时间，默认10秒
            config_type: 配置文件类型，默认为toml
        """
        self.config_file = Path(config_file)
        self.lock_file = self.config_file.with_suffix('.lock')
        self.timeout = timeout
        self.lock = FileLock(self.lock_file, timeout=self.timeout)
        self.config_type = config_type
    
    def load_config(self) -> ClientConfig:
        """
        加载配置文件
        
        Returns:
            dict: 配置文件内容
        """
        try:
            with self.lock:
                if not self.config_file.exists():
                    raise FileNotFoundError(f"配置文件{self.config_file}不存在")
                with open(self.config_file, 'r') as f:
                    if self.config_type == 'toml':
                        toml_data = toml.load(f)
                        config = load_config(json.dumps(toml_data, indent=4))
                        return config
                    else:
                        raise NotImplementedError(f"配置文件格式{self.config_type}不支持")
        except Exception as e:
            raise ConfigLoadError(f"读取配置文件失败: {str(e)}")

    def save_config(self, config: ClientConfig):
        """
        保存配置文件
        
        Args:
            config (ClientConfig): 需要保存的config对象
        """
        
        try:
            with self.lock:
                with open(self.config_file, 'w') as f:
                    data = config.model_dump(exclude_unset= True, by_alias=True)
                    if self.config_type == 'toml':
                        toml.dump(data, f)
                    else:
                        raise NotImplementedError(f"配置文件格式{self.config_type}不支持")
        except Exception as e:
            raise ConfigSaveError(f"保存配置文件失败: {str(e)}")
