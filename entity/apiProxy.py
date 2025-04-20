from typing import Any, Dict
from pydantic import BaseModel, Field

class RequestProxy(BaseModel):
    type_: str = Field(..., alias="type")
    data: Dict[str, Any] = Field(..., description="包含具体业务数据的字典")