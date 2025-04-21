from contextlib import asynccontextmanager
from fastapi import APIRouter, FastAPI
from utils.ConfigManager import ConfigManager
from api.v1.proxy import router as proxy_router
from api.v1.visitor import router as visitor_router
from fastapi.middleware.cors import CORSMiddleware

# 临时配置文件地址
config_file = "temp_tool/test_config.toml"
#

app = FastAPI()

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # 允许的源列表，这里是你的 Vue 应用地址
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有请求头
)

app.include_router(proxy_router)
app.include_router(visitor_router)
