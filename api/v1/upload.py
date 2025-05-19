from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
import os
import uuid
import shutil

router = APIRouter(
    prefix="/api/v1",
    responses={404: {"description": "Not found"}},
)

# 支持的文件类型
ALLOWED_TYPES = ['exe', 'txt']

def is_binary_file(file_path) -> bool:
    """
    判断文件是否为二进制文件。
    Args:
        file_path (str): 文件路径。

    Returns:
        bool: 如果是二进制文件返回True，否则返回False。
    """
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(1024)
            if b'\0' in chunk:
                return True
    except Exception:
        return False
    return False

def is_text_file(file_path) -> bool:
    """
    判断文件是否为文本文件。

    Args:
        file_path (str): 文件路径。

    Returns:
        bool: 如果是文本文件返回True，否则返回False。
    """
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(1024)
            if any(b < 9 or (14 < b < 32 and b not in (10, 13)) for b in chunk):
                return False
    except Exception:
        return False
    return True

@router.post("/upload")
async def upload_file(
    type: str = Form(..., description="文件类型（exe或txt）"),
    file: UploadFile = File(..., description="上传的文件")
):
    """
    上传文件接口。

    Args:
        type (str): 文件类型，只能为'exe'或'txt'。
        file (UploadFile): 上传的文件对象。

    Returns:
        JSONResponse: 包含上传后文件唯一ID的响应，带类型前缀（如 exe-xxxxxx 或 txt-xxxxxx）。

    Raises:
        HTTPException: 文件类型不合法或内容不符合要求时抛出异常。
    """
    # 限制类型
    if type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="只允许exe或txt类型")

    # 生成随机的id
    unique_id = f"{type}-{uuid.uuid4().hex}"

    # 选择保存路径
    save_dir = f"data/temp/{unique_id}"
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, file.filename) # type: ignore

    # 保存上传文件
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 文件类型验证
    if type == "exe":
        # 必须为二进制可执行
        if not is_binary_file(save_path):
            shutil.rmtree(save_dir)
            raise HTTPException(status_code=400, detail="exe文件必须为二进制程序")
    elif type == "txt":
        # 必须为文本文件
        if not is_text_file(save_path):
            shutil.rmtree(save_dir)
            raise HTTPException(status_code=400, detail="txt文件必须为文本文件")

    # 返回id
    return JSONResponse(content={"id": unique_id})
