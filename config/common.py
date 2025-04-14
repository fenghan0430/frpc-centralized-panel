from pydantic import BaseModel
from typing import Dict, Optional

class LogConfig(BaseModel):
    to: Optional[str]
    level: str = "info"
    maxDays: int = 3
    disablePrintColor: Optional[bool]

class TLSConfig(BaseModel):
    certFile: str
    keyFile: str
    trustedCaFile: Optional[str]
    serverName: Optional[str]

class WebServerConfig(BaseModel):
    addr: str = "127.0.0.1"
    port: int
    user: Optional[str]
    password: Optional[str] 
    assetsDir: Optional[str]
    pprofEnable: Optional[str]
    tls: Optional[TLSConfig]

class QUICOptions(BaseModel):
    keepalivePeriod: int = 10
    maxIdleTimeout: int = 30
    maxIncomingStreams: int = 100000

class HeaderOperations(BaseModel):
    header_set: Optional[Dict[str, str]]

class HTTPHeader(BaseModel):
    name: str
    value: str
