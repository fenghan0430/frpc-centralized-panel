from typing import Dict, Type

from fastapi import APIRouter, HTTPException
from entity.visitor import STCPVisitorConfig, SUDPVisitorConfig, XTCPVisitorConfig
from utils.ConfigManager import ConfigManager

VISITOR_TYPE_MAP: Dict[str, Type] = {
    'stcp': STCPVisitorConfig,
    'sudp': SUDPVisitorConfig,
    'xtcp': XTCPVisitorConfig,
}

# 临时配置文件地址
config_file = "temp_tool/test_config.toml"
#

config = ConfigManager(config_file)

router = APIRouter(
    prefix="/api/v1",
    responses={404: {"description": "Not found"}},
)

@router.get("/visitor")
async def getProxy():
    """获取所有接收配置

    Returns:
        _type_: _description_
    """
    client_config = config.load_config()
    return_data = []
    
    if client_config.visitors == None:
        return []
    
    for i in client_config.visitors:
        return_data.append(i.model_dump(by_alias=True, exclude_none=True))
    
    return return_data

@router.post("/visitor", status_code=201)
def newVisitor(data: dict):
    
    if "type" not in data.keys():
        raise HTTPException(status_code=400, detail={"status": 400, "massage": "请求体中缺少type字段"})
    
    if data["type"] not in VISITOR_TYPE_MAP.keys():
        raise HTTPException(status_code=400, detail={"status": 400, "massage": "类型%s不是一个有效的类型"%data["type"]})
    
    try:
        # 转为实体类，顺便验证合不合法
        new_visitor_config = VISITOR_TYPE_MAP[data["type"]](**data)
        print(new_visitor_config.model_dump(exclude_none=True, by_alias=True))
    except Exception as e:
        raise HTTPException(status_code=422, 
                            detail={"status": 422, "massage": "配置文件格式不正确: " + str(e), "input": data})

    client_config = config.load_config()
    
    if client_config.visitors == None:
        client_config.visitors = []
    
    for i in client_config.visitors:
        # 检测名字是否重名，也许事应该前端也做一遍？
        if i.name == new_visitor_config.name:
            raise HTTPException(status_code=409, detail={"status": 409, "massage": f"名字{new_visitor_config.name}已经被占用"})
        # 检测端口是否重复
        # if data["type"] in ['tcp', 'udp'] and i.type_ in ['tcp', 'udp']:
        #     if new_proxy_config.remotePort == None:
        #         raise HTTPException(status_code=422, detail={"status": 422, "massage": "remotePort为空,不支持这样的写法"})
        #     if i.remotePort == new_proxy_config.remotePort:  # type: ignore
        #         raise HTTPException(status_code=409, detail={"status": 409, "massage": f"端口{new_proxy_config.remotePort}已经被占用"})
        if i.bindAddr == new_visitor_config.bindAddr:
            if i.bindPort == new_visitor_config.bindPort:  # type: ignore
                raise HTTPException(status_code=409, detail={"status": 409, "massage": f"端口{new_visitor_config.remotePort}已经被占用"})
"""
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
            
            # client_config.visitors.append(new_proxy_config)
            # config.save_config(client_config)
        else:
            return {"status": "error", "message": f"类型{data.type_}不是一个有效的类型"}
"""