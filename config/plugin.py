from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from config.common import HeaderOperations

class BasePlugin(BaseModel):
    type_: str = Field(..., alias="type")

class HTTPProxyPluginOptions(BasePlugin):
    httpUser: Optional[str]
    httpPassword: Optional[str]

class Socks5PluginOptions(BasePlugin):
    username: Optional[str]
    password: Optional[str]

class StaticFilePluginOptions(BasePlugin):
    localPath: str
    stripPrefix: Optional[str]
    httpUser: Optional[str]
    httpPassword: Optional[str]

class UnixDomainSocketPluginOptions(BasePlugin):
    unixPath: str

class HTTP2HTTPSPluginOptions(BasePlugin):
    localAddr: str
    hostHeaderRewrite: Optional[str]
    requestHeaders: Optional[HeaderOperations]

class HTTPS2HTTPPluginOptions(BasePlugin):
    localAddr: str
    hostHeaderRewrite: Optional[str]
    requestHeaders: Optional[HeaderOperations]
    enableHTTP2: bool = True
    crtPath: Optional[str]
    keyPath: Optional[str]

class HTTPS2HTTPSPluginOptions(BasePlugin):
    localAddr: str
    hostHeaderRewrite: Optional[str]
    requestHeaders: Optional[HeaderOperations]
    enableHTTP2: bool = True
    crtPath: Optional[str]
    keyPath: Optional[str]

class TLS2RawPluginOptions(BasePlugin):
    localAddr: str
    crtPath: str
    keyPath: str
