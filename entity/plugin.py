from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from entity.common import HeaderOperations

class BasePlugin(BaseModel):
    type_: str = Field(..., alias="type")

class HTTPProxyPluginOptions(BasePlugin):
    httpUser: Optional[str] = None
    httpPassword: Optional[str] = None

class Socks5PluginOptions(BasePlugin):
    username: Optional[str] = None
    password: Optional[str] = None

class StaticFilePluginOptions(BasePlugin):
    localPath: str
    stripPrefix: Optional[str] = None
    httpUser: Optional[str] = None
    httpPassword: Optional[str] = None

class UnixDomainSocketPluginOptions(BasePlugin):
    unixPath: str

class HTTP2HTTPSPluginOptions(BasePlugin):
    localAddr: str
    hostHeaderRewrite: Optional[str] = None
    requestHeaders: Optional[HeaderOperations] = None

class HTTPS2HTTPPluginOptions(BasePlugin):
    localAddr: str
    hostHeaderRewrite: Optional[str] = None
    requestHeaders: Optional[HeaderOperations] = None
    enableHTTP2: bool = True
    crtPath: Optional[str] = None
    keyPath: Optional[str] = None

class HTTPS2HTTPSPluginOptions(BasePlugin):
    localAddr: str
    hostHeaderRewrite: Optional[str] = None
    requestHeaders: Optional[HeaderOperations] = None
    enableHTTP2: bool = True
    crtPath: Optional[str] = None
    keyPath: Optional[str] = None

class TLS2RawPluginOptions(BasePlugin):
    localAddr: str
    crtPath: str
    keyPath: str
