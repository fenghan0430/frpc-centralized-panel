from math import e
from typing import Dict, Type
from fastapi import APIRouter

from entity.apiProxy import RequestProxy
from entity.proxy import HTTPProxyConfig, HTTPSProxyConfig, STCPProxyConfig, SUDPProxyConfig, TCPMuxProxyConfig, TCPProxyConfig, UDPProxyConfig, XTCPProxyConfig
from entity.visitor import STCPVisitorConfig, SUDPVisitorConfig, XTCPVisitorConfig
from utils.ConfigManager import ConfigManager

# 临时配置文件地址
config_file = "temp_tool/test_config.toml"
#

config = ConfigManager(config_file)

router = APIRouter(
    prefix="/api/v1",
    responses={404: {"description": "Not found"}},
)

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

@router.get("/proxy")
async def getProxy():
    return config.load_config().model_dump(by_alias=True, exclude_unset=True)

@router.post("/proxy", status_code=201)
async def newProxy(data: RequestProxy):
    try:
        if data.type_ in PROXY_TYPE_MAP.keys():
            # 转为实体类，顺便验证合不合法
            new_proxy_config = PROXY_TYPE_MAP[data.type_](**data.data)
            # 检测名字是否重名，也许事应该前端也做一遍？
            client_config = config.load_config()
            if client_config.proxies == None:
                client_config.proxies = []
            for i in client_config.proxies:
                if i.name == new_proxy_config.name:
                    return {"status": "error", "message": f"名字{new_proxy_config.name}已经被占用"}
                if data.type_ in ['tcp', 'udp']:
                    if i.remotePort == new_proxy_config.remotePort: # type: ignore
                        return {"status": "error", "message": f"端口{new_proxy_config.remotePort}已经被占用"}
            # 添加隧道到配置文件
            client_config.proxies.append(new_proxy_config)
            config.save_config(client_config)
            # 热加载配置文件
            
        elif data.type_ in VISITOR_TYPE_MAP.keys():
            new_proxy_config = VISITOR_TYPE_MAP[data.type_](**data.data)
            
            client_config = config.load_config()
            if client_config.visitors == None:
                client_config.visitors = []
            for i in client_config.visitors:
                if i.name == new_proxy_config.name:
                    return {"status": "error", "message": f"名字{new_proxy_config.name}已经被占用"}
                if i.bindAddr != None and i.bindAddr == new_proxy_config.bindAddr: # 通过配置文件验证本地端口占用
                    if i.bindPort == new_proxy_config.bindPort:
                        return {"status": "error", "message": f"地址{new_proxy_config.bindAddr}:{new_proxy_config.bindPort}已经被占用"}
            
            client_config.visitors.append(new_proxy_config)
            config.save_config(client_config)
        else:
            return {"status": "error", "message": f"类型{data.type_}不是一个有效的类型"}
    except Exception as e:
        print(e)
        return {"status": "error", "message": str(e)} # TODO 应返回错误码

    return {"status": "ok"}
