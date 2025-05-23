import os
from typing import Dict, Type
from fastapi import APIRouter, HTTPException, Path
from entity.proxy import HTTPProxyConfig, HTTPSProxyConfig, STCPProxyConfig, SUDPProxyConfig, TCPMuxProxyConfig, TCPProxyConfig, UDPProxyConfig, XTCPProxyConfig
from utils.ConfigManager import ConfigManager
from utils.database import DataBase

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

# 临时配置文件地址
database_path = "data/data.db"
#

router = APIRouter(
    prefix="/api/v1",
    responses={404: {"description": "Not found"}},
)

def get_all_proxy():
    """获取所有代理配置

    Returns:
        config (List[Dict[str, Any]]): 包含客户端id+代理配置的字典, 没有配置返回空字典
    
    Raises:
        HTTPException: 
            - 500: 数据库查询失败
            - 500: 读取文件夹失败
    """
    # 数据库验证id存不存在, 防止未知id
    # 从数据库得到一个可信的id列表
    try:
        with DataBase(database_path) as db:
            results = db.query_program()
            db_id = [str(result[0]) for result in results]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"status": 500, "message": f"数据库查询失败: {str(e)}"}
        )
    
    if not db_id:
        return []
    
    all_proxies = []
    # 得到data/cmd/下的文件夹
    cmd_path = os.path.join("data", "cmd")
    if not os.path.exists(cmd_path):
        return []
    
    try:
        folder_names = [f for f in os.listdir(cmd_path) if os.path.isdir(os.path.join(cmd_path, f))]
    except OSError as e:
        raise HTTPException(
            status_code=500, 
            detail={"status": 500, "message": f"无法读取配置文件夹: {str(e)}"}
            )
    
    for folder_name in folder_names:
        # 验证文件夹名在不在db id, 如不在，跳过
        if folder_name not in db_id:
            # TODO: log
            continue
        
        # 验证文件夹下有没有frpc.toml, 如没有，跳过
        config_path = os.path.join(cmd_path, folder_name, "frpc.toml")
        if not os.path.exists(config_path):
            # TODO: log
            continue
        
        # 加载config, 如果错误，跳过
        try:
            client_config_manager = ConfigManager(config_path)
            client_config = client_config_manager.load_config()
        except Exception:
            # TODO: log
            continue
        
        # 检查config.proxies是否为空, 如为空，跳过
        if not client_config.proxies:
            continue
        
        # 读取每一条proxy，添加上client_id, 值为cid
        for proxy in client_config.proxies:
            proxy_dict = proxy.model_dump(by_alias=True, exclude_none=True)
            proxy_dict["client_id"] = int(folder_name)
            # 添加到all_proxies
            all_proxies.append(proxy_dict)
    
    # 返回all_proxies
    return all_proxies

@router.get("/proxy")
async def getProxy():
    """获取所有隧道信息

    Returns:
        _type_: _description_
    """

    return get_all_proxy()

@router.get("/proxy/{client_id}/{proxy_name}", status_code=200)
async def get_proxy_by_name(
    proxy_name: str = Path(..., description="隧道名称"),
    client_id: int = Path(..., description="客户端ID"),
    ):
    """
    获取指定 name 的隧道配置
    """
    # 数据库验证id存不存在, 防止未知id
    # 从数据库得到一个可信的id列表
    try:
        with DataBase(database_path) as db:
            results = db.query_program()
            db_id = [result[0] for result in results]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"status": 500, "message": f"数据库查询失败: {str(e)}"}
        )
    
    if client_id not in db_id:
        raise HTTPException(status_code=400, detail={"status": 404, "message": "无效的客户端ID"})
    
    if not os.path.isfile(f"data/cmd/{client_id}/frpc.toml"):
        raise HTTPException(status_code=400, detail={"status": 404, "message": "客户端ID对应的frpc.toml文件不存在"})
    
    client_config = ConfigManager(f"data/cmd/{client_id}/frpc.toml").load_config()

    # 没有任何隧道
    if not client_config.proxies:
        raise HTTPException(
            status_code=404,
            detail={"status": 404, "message": "没有找到任何隧道"}
        )

    # 根据 name 查找
    for proxy in client_config.proxies:
        if proxy.name == proxy_name:
            return proxy.model_dump(by_alias=True, exclude_none=True)

    # 未找到对应隧道
    raise HTTPException(
        status_code=404,
        detail={"status": 404, "message": f"未找到名为 {proxy_name} 的隧道"}
    )

@router.patch("/proxy/{client_id}", status_code=200)
async def update_proxy_by_name(
    data: dict,
    client_id: int = Path(..., description="客户端ID"),
    ):
    """
    更新指定 name 的隧道配置
    """
    # 数据库验证id存不存在, 防止未知id
    # 从数据库得到一个可信的id列表
    try:
        with DataBase(database_path) as db:
            results = db.query_program()
            db_id = [result[0] for result in results]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"status": 500, "message": f"数据库查询失败: {str(e)}"}
        )
    
    if client_id not in db_id:
        raise HTTPException(status_code=400, detail={"status": 404, "message": "无效的客户端ID"})
    
    if not os.path.isfile(f"data/cmd/{client_id}/frpc.toml"):
        raise HTTPException(status_code=400, detail={"status": 404, "message": "客户端ID对应的frpc.toml文件不存在"})
    
    config = ConfigManager(f"data/cmd/{client_id}/frpc.toml")
    
    if "type" not in data.keys():
        raise HTTPException(status_code=400, detail={"status": 400, "message": "请求体中缺少type字段"})
    
    if "name" not in data.keys():
        raise HTTPException(status_code=400, detail={"status": 400, "message": "请求体中缺少name字段"})
    
    proxy_name = data['name']
    
    if data["type"] not in PROXY_TYPE_MAP.keys():
        raise HTTPException(status_code=400, detail={"status": 400, "message": "类型%s不是一个有效的类型"%data["type"]})
    
    client_config = config.load_config()
    if not client_config.proxies:
        raise HTTPException(status_code=404, detail={"status": 404, "message": "没有找到任何隧道"})

    # 查找要更新的隧道
    for idx, proxy in enumerate(client_config.proxies):
        if proxy.name == proxy_name:
            old_proxy = proxy
            target_index = idx
            break
    else:
        raise HTTPException(status_code=404, detail={"status": 404, "message": f"未找到名为 {proxy_name} 的隧道"})

    # 不允许修改隧道类型
    if "type" in data and data["type"] != old_proxy.type_:
        raise HTTPException(status_code=400, detail={"status": 400, "message": "不支持修改隧道类型, 旧隧道为: %s, 新隧道为: %s" % (old_proxy.type_, data["type"])})

    # 合并旧数据与新传入字段，并进行校验
    merged = old_proxy.model_dump()
    merged.update(data)
    try:
        updated_proxy = PROXY_TYPE_MAP[old_proxy.type_](**merged)
    except Exception as e:
        raise HTTPException(status_code=422, detail={"status": 422, "message": "配置格式不正确: " + str(e), "input": data})

    # 唯一性检查（跳过自身）
    for i, other in enumerate(client_config.proxies):
        if i == target_index:
            continue
        # 名称冲突
        if updated_proxy.name == other.name:
            raise HTTPException(status_code=409, detail={"status": 409, "message": f"名字{updated_proxy.name}已经被占用"})
        # tcp/udp 端口冲突
        if old_proxy.type_ in ['tcp', 'udp'] and other.type_ in ['tcp', 'udp']:
            if updated_proxy.remotePort and other.remotePort == updated_proxy.remotePort: # type: ignore
                raise HTTPException(status_code=409, detail={"status": 409, "message": f"端口{updated_proxy.remotePort}已经被占用"})
        # http/https 域名冲突
        if old_proxy.type_ in ['http', 'https'] and other.type_ in ['http', 'https']:
            if updated_proxy.customDomains:
                for d in updated_proxy.customDomains:
                    if other.customDomains and d in other.customDomains: # type: ignore
                        raise HTTPException(status_code=409, detail={"status": 409, "message": f"域名{d}已经被{other.name}占用"})

    # 应用更新并保存
    client_config.proxies[target_index] = updated_proxy
    config.save_config(client_config)

    return {"status": 200, "message": f"更新隧道 {proxy_name} 成功"}

@router.post("/proxy/{client_id}", status_code=201)
async def newProxy(
    data: dict,
    client_id: int = Path(..., description="客户端ID"),
    ):
    """_summary_

    Args:
        data (RequestProxy): _description_

    Returns:
        _type_: _description_
    """
    # 数据库验证id存不存在, 防止未知id
    # 从数据库得到一个可信的id列表
    try:
        with DataBase(database_path) as db:
            results = db.query_program()
            db_id = [result[0] for result in results]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"status": 500, "message": f"数据库查询失败: {str(e)}"}
        )
    
    if client_id not in db_id:
        raise HTTPException(status_code=400, detail={"status": 404, "message": "无效的客户端ID"})
    
    if not os.path.isfile(f"data/cmd/{client_id}/frpc.toml"):
        raise HTTPException(status_code=400, detail={"status": 404, "message": "客户端ID对应的frpc.toml文件不存在"})
    
    config = ConfigManager(f"data/cmd/{client_id}/frpc.toml")
    
    if "type" not in data.keys():
        raise HTTPException(status_code=400, detail={"status": 400, "message": "请求体中缺少type字段"})
    
    if data["type"] not in PROXY_TYPE_MAP.keys():
        raise HTTPException(status_code=400, detail={"status": 400, "message": "类型%s不是一个有效的类型"%data["type"]})
    
    try:
        # 转为实体类，顺便验证合不合法
        new_proxy_config = PROXY_TYPE_MAP[data["type"]](**data)
    except Exception as e:
        raise HTTPException(status_code=422, 
                            detail={"status": 422, "message": "配置文件格式不正确: " + str(e), "input": data})
    
    # 检测
    client_config = config.load_config()
    if not client_config.proxies:
        client_config.proxies = []
    
    for i in client_config.proxies:
        # 检测名字是否重名，也许事应该前端也做一遍？
        if i.name == new_proxy_config.name:
            raise HTTPException(status_code=409, detail={"status": 409, "message": f"名字{new_proxy_config.name}已经被占用"})
        # 检测tcp, udp端口是否重复
        if data["type"] in ['tcp', 'udp'] and i.type_ in ['tcp', 'udp']:
            if new_proxy_config.remotePort == None:
                raise HTTPException(status_code=422, detail={"status": 422, "message": "remotePort为空,不支持这样的写法"})
            if i.remotePort == None: # type: ignore
                continue
            if i.remotePort == new_proxy_config.remotePort:  # type: ignore
                raise HTTPException(status_code=409, detail={"status": 409, "message": f"端口{new_proxy_config.remotePort}已经被占用"})
        # 检测http, https绑定域名是否重复
        if data["type"] in ['http', 'https'] and i.type_ in ['http', 'https']:
            if i.customDomains == None: # type: ignore
                continue
            if new_proxy_config.customDomains == None:
                raise HTTPException(status_code=422, detail={"status": 422, "message": "customDomains为空,不支持这样的写法"})
            for domain in i.customDomains: # type: ignore
                for domain2 in new_proxy_config.customDomains: # type: ignore
                    if domain == domain2:
                        return {"status": "error", "message": f"域名{domain2}已经被{i.name}占用"}
    # 添加隧道到配置文件
    client_config.proxies.append(new_proxy_config)
    config.save_config(client_config)
    # 热加载配置文件

    return {"status": 201, "message": f"创建{new_proxy_config.type_}隧道{new_proxy_config.name}成功"}

@router.delete("/proxy/{client_id}/{proxy_name}", status_code=200)
async def delete_proxy_by_name(
    proxy_name: str = Path(..., description="隧道ID"),
    client_id: int = Path(..., description="客户端ID"),
    ):
    """删除指定的隧道

    Args:
        proxy_id (str): 隧道的唯一标识

    Returns:
        dict: 删除结果的状态信息
    """
    # 数据库验证id存不存在, 防止未知id
    # 从数据库得到一个可信的id列表
    try:
        with DataBase(database_path) as db:
            results = db.query_program()
            db_id = [result[0] for result in results]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"status": 500, "message": f"数据库查询失败: {str(e)}"}
        )
    
    if client_id not in db_id:
        raise HTTPException(status_code=400, detail={"status": 404, "message": "无效的客户端ID"})
    
    if not os.path.isfile(f"data/cmd/{client_id}/frpc.toml"):
        raise HTTPException(status_code=400, detail={"status": 404, "message": "客户端ID对应的frpc.toml文件不存在"})
    
    config = ConfigManager(f"data/cmd/{client_id}/frpc.toml")
    client_config = config.load_config()
    
    if client_config.proxies is None or not client_config.proxies:
        raise HTTPException(status_code=404, detail={"status": 404, "message": "没有找到任何隧道"})
    
    # 查找并删除指定的隧道
    proxy_to_delete = None
    for proxy in client_config.proxies:
        if proxy.name == proxy_name:
            proxy_to_delete = proxy
            break
    
    if proxy_to_delete is None:
        raise HTTPException(status_code=404, detail={"status": 404, "message": f"未找到名为 {proxy_name} 的隧道"})
    
    client_config.proxies.remove(proxy_to_delete)
    config.save_config(client_config)
    
    return {"status": 200, "message": f"成功删除隧道 {proxy_name}"}
