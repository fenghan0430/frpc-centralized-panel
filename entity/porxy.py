from pydantic import BaseModel, Field
from typing import List, Dict, Literal, Optional
from entity.plugin import BasePlugin
from entity.common import HTTPHeader, HeaderOperations

class ProxyBackend(BaseModel):
    localIP: str = "127.0.0.1"
    localPort: Optional[int] = None
    plugin: Optional[BasePlugin] = None

class ProxyTransport(BaseModel):
    useEncryption: Optional[bool] = None
    useCompression: Optional[bool] = None
    bandwidthLimit: Optional[str] = None
    bandwidthLimitMode: Optional[str] = None
    proxyProtocolVersion: Optional[str] = None

class LoadBalancerConfig(BaseModel):
    group: str
    groupKey: Optional[str] = None

class HealthCheckConfig(BaseModel):
    type_: Literal['tcp', 'http'] = Field(..., alias="type")
    timeoutSeconds: int = 3
    maxFailed: int = 1
    intervalSeconds: int = 10
    path: Optional[str] = None
    httpHeaders: Optional[List[HTTPHeader]] = None

class ProxyBaseConfig(ProxyBackend):
    name: str
    type_: Literal['tcp', 'udp', 'http', 'https', 'tcpmux', 'stcp', 'sudp', 'xtcp'] \
        = Field(..., alias="type")
    annotations: Optional[Dict[str, str]] = None
    transport: Optional[ProxyTransport] = None
    metadatas: Optional[Dict[str, str]] = None
    loadBalancer: Optional[LoadBalancerConfig] = None
    healthCheck: Optional[HealthCheckConfig] = None
    
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.__annotations__.update(kwargs.get('model_config', {}))
    
class DomainConfig(BaseModel):
    customDomains: Optional[List[str]] = None
    subDomain: Optional[str] = None

class TCPProxyConfig(ProxyBaseConfig):
    remotePort: Optional[int] = None

class UDPProxyConfig(ProxyBaseConfig):
    remotePort: Optional[int] = None

class HTTPProxyConfig(ProxyBaseConfig, DomainConfig):
    locations: Optional[List[str]] = None
    httpUser: Optional[str] = None
    httpPassword: Optional[str] = None
    hostHeaderRewrite: Optional[str] = None
    requestHeaders: Optional[HeaderOperations] = None
    responseHeaders: Optional[HeaderOperations] = None
    routeByHTTPUser: Optional[str] = None

class HTTPSProxyConfig(ProxyBaseConfig, DomainConfig):
    pass

class TCPMuxProxyConfig(ProxyBaseConfig, DomainConfig):
    httpUser: Optional[str] = None
    httpPassword: Optional[str] = None
    routeByHTTPUser: Optional[str] = None
    multiplexer: Optional[str] = None

class STCPProxyConfig(ProxyBaseConfig):
    secretKey: Optional[str] = None
    allowUsers: Optional[List[str]] = None

class XTCPProxyConfig(ProxyBaseConfig):
    secretKey: Optional[str] = None
    allowUsers: Optional[List[str]] = None

class SUDPProxyConfig(ProxyBaseConfig):
    secretKey: Optional[str] = None
    allowUsers: Optional[List[str]] = None
