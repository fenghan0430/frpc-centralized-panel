from contextlib import asynccontextmanager
import os
from fastapi import APIRouter, FastAPI
from utils.ConfigManager import ConfigManager
from api.v1.proxy import router as proxy_router
from api.v1.visitor import router as visitor_router
from api.v1.client import router as client_router
from api.v1.upload import router as upload_router
from fastapi.middleware.cors import CORSMiddleware
from utils.database import DataBase

data_path = "data/"
app = FastAPI()

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://127.0.0.1:5000"],  # 允许的源列表，这里是你的 Vue 应用地址
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有请求头
)

def init():
    """初始化应用程序数据
    """
    with DataBase(data_path + "data.db") as db:
        db.init_db()

# 检测data文件夹存不存在
if not os.path.exists(data_path):
    os.makedirs(data_path)
    init()

app.include_router(proxy_router)
app.include_router(visitor_router)
app.include_router(client_router)
app.include_router(upload_router)
