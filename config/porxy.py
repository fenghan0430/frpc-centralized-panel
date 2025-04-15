from pydantic import BaseModel, Field
from typing import List, Dict, Literal, Optional
from config.plugin import BasePlugin
from config.common import HTTPHeader, HeaderOperations

class ProxyBackend(BaseModel):
    localIP: str = "127.0.0.1"
    localPort: int
    plugin: BasePlugin

class ProxyTransport(BaseModel):
    useEncryption: bool
    useCompression: bool
    bandwidthLimit: str
    bandwidthLimitMode: str
    proxyProtocolVersion: str

class LoadBalancerConfig(BaseModel):
    group: str
    groupKey: str

class HealthCheckConfig(BaseModel):
    type_: Literal['tcp', 'http'] = Field(..., alias="type")
    timeoutSeconds: int = 3
    maxFailed: int = 1
    intervalSeconds: int = 10
    path: Optional[str]
    httpHeaders: Optional[List[HTTPHeader]]

class ProxyBaseConfig(ProxyBackend):
    name: str
    type_: Literal['tcp', 'udp', 'http', 'https', 'tcpmux', 'stcp', 'sudp', 'xtcp'] \
        = Field(..., alias="type")
    annotations: Optional[Dict[str, str]]
    transport: Optional[ProxyTransport]
    metadatas: Optional[Dict[str, str]]
    loadBalancer: Optional[LoadBalancerConfig]
    healthCheck: Optional[HealthCheckConfig]

class DomainConfig(BaseModel):
    customDomains: Optional[List[str]]
    subDomain: Optional[str]

class TCPProxyConfig(ProxyBaseConfig):
    remotePort: Optional[int]

class UDPProxyConfig(ProxyBaseConfig):
    remotePort: Optional[int]

class HTTPProxyConfig(ProxyBaseConfig, DomainConfig):
    locations: Optional[List[str]]
    httpUser: Optional[str]
    httpPassword: Optional[str]
    hostHeaderRewrite: Optional[str]
    requestHeaders: Optional[HeaderOperations]
    responseHeaders: Optional[HeaderOperations]
    routeByHTTPUser: Optional[str]

class HTTPSProxyConfig(ProxyBaseConfig, DomainConfig):
    pass

class TCPMuxProxyConfig(ProxyBaseConfig, DomainConfig):
    httpUser: Optional[str]
    httpPassword: Optional[str]
    routeByHTTPUser: Optional[str]
    multiplexer: Optional[str]

class STCPProxyConfig(ProxyBaseConfig):
    secretKey: Optional[str]
    allowUsers: Optional[List[str]]

class XTCPProxyConfig(ProxyBaseConfig):
    secretKey: Optional[str]
    allowUsers: Optional[List[str]]

class SUDPProxyConfig(ProxyBaseConfig):
    secretKey: Optional[str]
    allowUsers: Optional[List[str]]
