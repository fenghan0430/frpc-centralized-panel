from typing import List


def get_all_clients() -> dict:
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
                "description": "连接HK的客户端"
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
    
    Returns:
        dict: 包含状态和信息的json, 格式为`{"status": "成功"|"失败", "message": "消息", "data": 数据, json格式, 如失败data为Nano}`
    """
    return {
        "status": "成功",
        "message": "获取客户端列表成功",
        "data": [
            {
                "id": 0,
                "name": "AWS US",
                "description": "连接AWS US的客户端"
            },
            {
                "id": 1,
                "name": "Aliyun HK",
                "description": "连接阿里云香港的客户端"
            },
            {
                "id": 2,
                "name": "阿里云 北京",
                "description": ""
            },
        ]
    }
