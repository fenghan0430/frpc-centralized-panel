import json
from typing import Any, Dict, List, Type
from entity.client import ClientConfig
from entity.porxy import (
    TCPMuxProxyConfig,
    TCPProxyConfig,
    UDPProxyConfig,
    HTTPProxyConfig,
    HTTPSProxyConfig,
    STCPProxyConfig,
    SUDPProxyConfig,
    XTCPProxyConfig,
    )
from entity.visitor import (
    STCPVisitorConfig, 
    SUDPVisitorConfig, 
    XTCPVisitorConfig
    )

# 定义类型映射
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

VISITOR_TYPE_MAP: Dict[str, Type] = {
    'stcp': STCPVisitorConfig,
    'sudp': SUDPVisitorConfig,
    'xtcp': XTCPVisitorConfig,
}

def load_config(file_path: str) -> ClientConfig:
    """从指定的JSON文件加载配置"""
    with open(file_path, "r") as f:
        json_data = json.load(f)
    
    # 提取并移除proxies和visitors
    json_proxies = json_data.pop("proxies", [])
    json_visitors = json_data.pop("visitors", [])
    
    # 创建基本配置
    config = ClientConfig(**json_data)
    
    # 加载proxies
    config.proxies = load_items(json_proxies, PROXY_TYPE_MAP, "Proxy", 
                               ['tcp', 'udp', 'http', 'https', 'tcpmux', 'stcp', 'sudp', 'xtcp'])
    
    # 加载visitors
    config.visitors = load_items(json_visitors, VISITOR_TYPE_MAP, "Visitor", 
                                ['stcp', 'sudp', 'xtcp'])
    
    return config

def load_items(items: List[Dict[str, Any]], 
               type_map: Dict[str, Type], 
               item_type: str, 
               allowed_types: List[str]) -> List[Any]:
    """根据类型映射加载配置项"""
    result = []
    for item in items:
        item_type_value = item.get('type')
        if item_type_value in type_map:
            config_class = type_map[item_type_value]
            result.append(config_class(**item))
        else:
            print(f"警告: {item_type}配置{item}未被加载, 因为他不属于{allowed_types}中任何一种")
    return result
