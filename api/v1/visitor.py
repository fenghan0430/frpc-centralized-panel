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
        raise HTTPException(status_code=400, detail={"status": 400, "message": "请求体中缺少type字段"})
    
    if data["type"] not in VISITOR_TYPE_MAP.keys():
        raise HTTPException(status_code=400, detail={"status": 400, "message": "类型%s不是一个有效的类型"%data["type"]})
    
    try:
        # 转为实体类，顺便验证合不合法
        new_visitor_config = VISITOR_TYPE_MAP[data["type"]](**data)
    except Exception as e:
        raise HTTPException(status_code=422, 
                            detail={"status": 422, "message": "配置文件格式不正确: " + str(e), "input": data})

    client_config = config.load_config()
    
    if client_config.visitors == None:
        client_config.visitors = []
    
    for i in client_config.visitors:
        # 检测名字是否重名，也许事应该前端也做一遍？
        if i.name == new_visitor_config.name:
            raise HTTPException(status_code=409, detail={"status": 409, "message": f"名字{new_visitor_config.name}已经被占用"})
        # 检测端口是否重复
        if i.bindAddr == new_visitor_config.bindAddr:
            if i.bindPort == new_visitor_config.bindPort:  # type: ignore
                raise HTTPException(status_code=409, detail=
                                    {"status": 409, "message": "网络地址%s:%s已经被占用"%(new_visitor_config.bindAddr, new_visitor_config.bindPort)})
        
        client_config.visitors.append(new_visitor_config)
        config.save_config(client_config)
        # print("接收到配置：%s"%new_visitor_config.model_dump(exclude_none=True, by_alias=True))
        
        return {"status": 201, "message": "接收配置%s创建成功"%new_visitor_config.name}

@router.delete("/visitor/{visitor_name}", status_code=200)
async def delete_visitor(visitor_name: str):
    """删除指定的接收配置

    Args:
        visitor_name (str): 接收配置的唯一标识

    Returns:
        dict: 删除结果的状态信息
    """
    client_config = config.load_config()
    
    if client_config.visitors is None or not client_config.visitors:
        raise HTTPException(status_code=404, detail={"status": 404, "message": "没有找到任何接收配置"})
    
    # 查找并删除指定的接收配置
    visitor_to_delete = None
    for visitor in client_config.visitors:
        if visitor.name == visitor_name:
            visitor_to_delete = visitor
            break
    
    if visitor_to_delete is None:
        raise HTTPException(status_code=404, detail={"status": 404, "message": f"未找到名为 {visitor_name} 的接收配置"})
    
    client_config.visitors.remove(visitor_to_delete)
    config.save_config(client_config)
    
    return {"status": 200, "message": f"成功删除接收配置 {visitor_name}"}
