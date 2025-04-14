from pydantic import BaseModel
from typing import List, Dict

class VisitorTransport(BaseModel):
    useEncryption: bool
    useCompression: bool

class VisitorBaseConfig(BaseModel):
    name: str
    visitor_type: str # type
    transport: VisitorTransport
    secretKey: str
    serverUser: str
    serverName: str
    bindAddr: str
    bindPort: int

class STCPVisitorConfig(VisitorBaseConfig):
    pass

class SUDPVisitorConfig(VisitorBaseConfig):
    pass

class XTCPVisitorConfig(VisitorBaseConfig):
    protocol: str
    keepTunnelOpen: bool
    maxRetriesAnHour: int
    minRetryInterval: int
    fallbackTo: str
    fallbackTimeoutMs: int
