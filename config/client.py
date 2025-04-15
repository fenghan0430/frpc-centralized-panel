from pydantic import BaseModel
from typing import List, Dict, Optional
from config.common import (
    LogConfig, 
    WebServerConfig,
    TLSConfig,
    QUICOptions
    )
from config.porxy import ProxyBaseConfig
from config.visitor import VisitorBaseConfig

class TLSClientConfig(TLSConfig):
    enable: Optional[bool]
    disableCustomTLSFirstByte: Optional[bool]

class ClientTransportConfig(BaseModel):
    protocol: Optional[str]
    dialServerTimeout: Optional[int]
    dialServerKeepalive: Optional[int]
    connectServerLocalIP: Optional[str]
    proxyURL: Optional[str]
    poolCount: Optional[int]
    tcpMux: Optional[bool]
    tcpMuxKeepaliveInterval: Optional[int]
    quic: Optional[QUICOptions]
    heartbeatInterval: Optional[int]
    heartbeatTimeout: Optional[int]
    tls: Optional[TLSClientConfig]

class AuthOIDCClientConfig(BaseModel):
    clientID: Optional[str]
    clientSecret: Optional[str]
    audience: Optional[str]
    scope: Optional[str]
    tokenEndpointURL: Optional[str]
    additionalEndpointParams: Optional[Dict[str, str]]

class AuthClientConfig(BaseModel):
    method: Optional[str]
    additionalScopes: Optional[List[str]]
    token: Optional[str]
    oidc: Optional[AuthOIDCClientConfig]

class ClientCommonConfig(BaseModel):
    auth: Optional[AuthClientConfig] = None
    user: Optional[str] = None
    serverAddr: Optional[str] = None
    serverPort: Optional[str] = None
    natHoleStunServer: str = "stun.easyvoip.com:3478"
    dnsServer: Optional[str] = None
    loginFailExit: bool = True
    start: Optional[List[str]] = None
    log: Optional[LogConfig] = None
    webServer: Optional[WebServerConfig] = None
    transport: Optional[ClientTransportConfig] = None
    udpPacketSize: int = 1500
    metadatas: Optional[Dict[str, str]] = None
    includes: Optional[List[str]] = None

class ClientConfig(ClientCommonConfig):
    proxies: Optional[List[ProxyBaseConfig]] = None
    visitors: Optional[List[VisitorBaseConfig]] = None
