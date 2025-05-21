from contextlib import asynccontextmanager
import logging
import os
import shutil
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from utils.database import DataBase
from utils.program_manager import ProgramManager

data_path = "data/"

def init():
    """初始化应用程序数据
    """
    with DataBase(data_path + "data.db") as db:
        db.init_db()

def clear_upload_temp():
    """
    清理上传的临时缓存文件夹。

    遍历并删除 `data_path/temp/` 目录下的所有文件和子文件夹。

    Args:
        None

    Returns:
        None
    """
    temp_dir = os.path.join(data_path, "temp")
    if not os.path.exists(temp_dir):
        return
    for item in os.listdir(temp_dir):
        item_path = os.path.join(temp_dir, item)
        if os.path.isdir(item_path):
            shutil.rmtree(item_path)
        elif os.path.isfile(item_path):
            os.remove(item_path)
    app.state.logger.info("缓存清理完成")

@asynccontextmanager
async def lifespan(app: FastAPI):

    app.state.logger = logging.getLogger("uvicorn.error")
    app.state.program_manager = ProgramManager()
    clear_upload_temp()
    yield
    
    program_manager: ProgramManager = app.state.program_manager
    program_manager.stop_all()

app = FastAPI(lifespan=lifespan)

def get_manager() -> ProgramManager:
    global app
    return app.state.program_manager

def get_logger() -> logging.Logger:
    global app
    return app.state.logger

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://127.0.0.1:5000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 检测data文件夹存不存在
if not os.path.exists(data_path):
    os.makedirs(data_path)
    init()

from api.v1.proxy import router as proxy_router
from api.v1.visitor import router as visitor_router
from api.v1.client import router as client_router
from api.v1.upload import router as upload_router
from api.v1.program import router as program_router

app.include_router(proxy_router)
app.include_router(visitor_router)
app.include_router(client_router)
app.include_router(upload_router)
app.include_router(program_router)
