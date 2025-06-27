from pydantic import BaseModel
from typing import Dict, Optional

class LogConfig(BaseModel):
    to: Optional[str] = None
    level: str = "info"
    maxDays: int = 3
    disablePrintColor: Optional[bool] = None

class TLSConfig(BaseModel):
    certFile: Optional[str] = None
    keyFile: Optional[str] = None
    trustedCaFile: Optional[str] = None
    serverName: Optional[str] = None

class WebServerConfig(BaseModel):
    addr: str = "127.0.0.1"
    port: int
    user: Optional[str] = None
    password: Optional[str] = None 
    assetsDir: Optional[str] = None
    pprofEnable: Optional[str] = None
    tls: Optional[TLSConfig] = None

class QUICOptions(BaseModel):
    keepalivePeriod: int = 10
    maxIdleTimeout: int = 30
    maxIncomingStreams: int = 100000

class HeaderOperations(BaseModel):
    header_set: Optional[Dict[str, str]] = None

class HTTPHeader(BaseModel):
    name: str
    value: str
