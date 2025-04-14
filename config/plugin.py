from pydantic import BaseModel
from typing import List, Dict
from common import HeaderOperations

class BasePlugin(BaseModel):
    _type: str

class HTTPProxyPluginOptions(BasePlugin):
    httpUser: str
    httpPassword: str

class Socks5PluginOptions(BasePlugin):
    username: str
    password: str

class StaticFilePluginOptions(BasePlugin):
    localPath: str
    stripPrefix: str
    httpUser: str
    httpPassword: str

class UnixDomainSocketPluginOptions(BasePlugin):
    unixPath: str

class HTTP2HTTPSPluginOptions(BasePlugin):
    localAddr: str
    hostHeaderRewrite: str
    requestHeaders: HeaderOperations

class HTTPS2HTTPPluginOptions(BasePlugin):
    localAddr: str
    hostHeaderRewrite: str
    requestHeaders: HeaderOperations
    enableHTTP2: bool
    crtPath: str
    keyPath: str

class HTTPS2HTTPSPluginOptions(BasePlugin):
    localAddr: str
    hostHeaderRewrite: str
    requestHeaders: HeaderOperations
    enableHTTP2: bool
    crtPath: str
    keyPath: str

class TLS2RawPluginOptions(BasePlugin):
    localAddr: str
    crtPath: str
    keyPath: str
