from fastapi import APIRouter, File, UploadFile, Form, HTTPException
import os
import uuid
import shutil

router = APIRouter(
    prefix="/api/v1",
    responses={404: {"description": "Not found"}},
)

ALLOWED_TYPES = ['exe', 'txt']

def is_binary_file(file_path) -> bool:
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(1024)
            if b'\0' in chunk:
                return True
    except Exception:
        return False
    return False

def is_text_file(file_path) -> bool:
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(1024)
            if any(b < 9 or (14 < b < 32 and b not in (10, 13)) for b in chunk):
                return False
    except Exception:
        return False
    return True

@router.post("/upload", status_code=201)
async def upload_file(
    type_: str = Form(..., description="文件类型（exe或txt）", alias="type"),
    file: UploadFile = File(..., description="上传的文件")
):
    if type_ not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail={"status": 400, "message": "只允许exe或txt类型"}
        )
    unique_id = f"{type_}-{uuid.uuid4().hex}"

    save_dir = f"data/temp/{unique_id}"
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, file.filename) # type: ignore

    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    if type_ == "exe":
        if not is_binary_file(save_path):
            shutil.rmtree(save_dir)
            raise HTTPException(
                status_code=400,
                detail={"status": 400, "message": "exe文件必须为二进制程序"}
            )
        os.chmod(save_path, 0o755)
    elif type_ == "txt":
        if not is_text_file(save_path):
            shutil.rmtree(save_dir)
            raise HTTPException(
                status_code=400,
                detail={"status": 400, "message": "txt文件必须为文本文件"}
            )

    return {"id": unique_id, "status": 201, "message": "文件上传成功"}
