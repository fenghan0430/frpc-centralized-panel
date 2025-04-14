from pydantic import BaseModel

class LogConfig(BaseModel):
    to: str
    level: str
    maxDays: int
    disablePrintColor: bool

class TLSConfig(BaseModel):
    certFile: str
    keyFile: str
    trustedCaFile: str
    serverName: str

class WebServerConfig(BaseModel):
    addr: str
    port: int
    user: str
    password: str
    assetsDir: str
    pprofEnable: bool
    tls: TLSConfig

class QUICOptions(BaseModel):
    keepalivePeriod: int
    maxIdleTimeout: int
    maxIncomingStreams: int
