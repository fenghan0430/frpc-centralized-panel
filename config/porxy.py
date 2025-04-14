from pydantic import BaseModel
from typing import List, Dict
from plugin import BasePlugin
from common import HTTPHeader, HeaderOperations

class ProxyBackend(BaseModel):
    localIP: str
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
    _type: str
    timeoutSeconds: int
    maxFailed: int
    intervalSeconds: int
    path: str
    httpHeaders: List[HTTPHeader]

class ProxyBaseConfig(ProxyBackend):
    name: str
    _type: str # type
    annotations: Dict[str, str]
    transport: ProxyTransport
    metadatas: Dict[str, str]
    loadBalancer: LoadBalancerConfig
    healthCheck: HealthCheckConfig

class DomainConfig(BaseModel):
    customDomains: List[str]
    subDomain: str

class TCPProxyConfig(ProxyBaseConfig):
    remotePort: int

class UDPProxyConfig(ProxyBaseConfig):
    remotePort: int

class HTTPProxyConfig(ProxyBaseConfig, DomainConfig):
    locations: List[str]
    httpUser: str
    httpPassword: str
    hostHeaderRewrite: str
    requestHeaders: HeaderOperations
    responseHeaders: HeaderOperations
    routeByHTTPUser: str

class HTTPSProxyConfig(ProxyBaseConfig, DomainConfig):
    pass

class TCPMuxProxyConfig(ProxyBaseConfig, DomainConfig):
    httpUser: str
    httpPassword: str
    routeByHTTPUser: str
    multiplexer: str

class STCPProxyConfig(ProxyBaseConfig):
    secretKey: str
    allowUsers: List[str]

class XTCPProxyConfig(ProxyBaseConfig):
    secretKey: str
    allowUsers: List[str]

class SUDPProxyConfig(ProxyBaseConfig):
    secretKey: str
    allowUsers: List[str]