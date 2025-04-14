from pydantic import BaseModel
from typing import List, Dict, Optional
from common import (
    LogConfig, 
    WebServerConfig,
    TLSConfig,
    QUICOptions
    )
from porxy import ProxyBaseConfig
from visitor import VisitorBaseConfig

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
    auth: Optional[AuthClientConfig]
    user: Optional[str]
    serverAddr: Optional[str]
    serverPort: Optional[str]
    natHoleStunServer: str = "stun.easyvoip.com:3478"
    dnsServer: Optional[str]
    loginFailExit: bool = True
    start: Optional[List[str]]
    log: Optional[LogConfig]
    webServer: Optional[WebServerConfig]
    transport: Optional[ClientTransportConfig]
    udpPacketSize: int = 1500
    metadatas: Optional[Dict[str, str]]
    includes: Optional[List[str]]

class ClientConfig(ClientCommonConfig):
    proxies: Optional[List[ProxyBaseConfig]]
    visitors: Optional[List[VisitorBaseConfig]]
