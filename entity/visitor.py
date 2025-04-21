from pydantic import BaseModel, Field
from typing import Literal, Optional, Union

class VisitorTransport(BaseModel):
    useEncryption: Optional[bool] = None
    useCompression: Optional[bool] = None

class VisitorBaseConfig(BaseModel):
    name: str
    type_: Literal['stcp', 'sudp', 'xtcp'] = Field(..., alias="type")
    bindAddr: str
    bindPort: int    
    transport: Optional[VisitorTransport] = None
    secretKey: Optional[str] = None
    serverUser: Optional[str] = None
    serverName: Optional[str] = None

class STCPVisitorConfig(VisitorBaseConfig):
    pass

class SUDPVisitorConfig(VisitorBaseConfig):
    pass

class XTCPVisitorConfig(VisitorBaseConfig):
    protocol: Literal['quic', 'kcp'] = 'quic'
    keepTunnelOpen: Optional[bool] = None
    maxRetriesAnHour: int = 8
    minRetryInterval: int = 90
    fallbackTo: Optional[str] = None
    fallbackTimeoutMs: Optional[int] = None
