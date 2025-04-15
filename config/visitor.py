from pydantic import BaseModel, Field
from typing import Literal, Optional

class VisitorTransport(BaseModel):
    useEncryption: Optional[bool]
    useCompression: Optional[bool]

class VisitorBaseConfig(BaseModel):
    name: str
    type_: Literal['stcp', 'sudp', 'xtcp'] = Field(..., alias="type")
    transport: Optional[VisitorTransport]
    secretKey: Optional[str]
    serverUser: Optional[str]
    serverName: Optional[str]
    bindAddr: Optional[str]
    bindPort: Optional[int]

class STCPVisitorConfig(VisitorBaseConfig):
    pass

class SUDPVisitorConfig(VisitorBaseConfig):
    pass

class XTCPVisitorConfig(VisitorBaseConfig):
    protocol: Literal['quic', 'kcp'] = 'quic'
    keepTunnelOpen: Optional[bool]
    maxRetriesAnHour: int = 8
    minRetryInterval: int = 90
    fallbackTo: Optional[str]
    fallbackTimeoutMs: Optional[int]
