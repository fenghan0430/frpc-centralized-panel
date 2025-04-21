from pydantic import BaseModel, SerializeAsAny
from typing import List, Dict, Optional
from entity.common import (
    LogConfig, 
    WebServerConfig,
    TLSConfig,
    QUICOptions
    )
from entity.proxy import ProxyBaseConfig
from entity.visitor import VisitorBaseConfig

class TLSClientConfig(TLSConfig):
    enable: Optional[bool] = None
    disableCustomTLSFirstByte: Optional[bool] = None

class ClientTransportConfig(BaseModel):
    protocol: Optional[str] = None
    dialServerTimeout: int = 10
    dialServerKeepalive: Optional[int] = None
    connectServerLocalIP: Optional[str] = None
    proxyURL: Optional[str] = None
    poolCount: Optional[int] = None
    tcpMux: Optional[bool] = None
    tcpMuxKeepaliveInterval: Optional[int] = None
    quic: Optional[QUICOptions] = None
    heartbeatInterval: Optional[int] = None # 这个选项建议由tcpMuxKeepaliveInterval代替
    heartbeatTimeout: Optional[int] = None 
    tls: Optional[TLSClientConfig] = None

class AuthOIDCClientConfig(BaseModel):
    clientID: Optional[str] = None
    clientSecret: Optional[str] = None
    audience: Optional[str] = None
    scope: Optional[str] = None
    tokenEndpointURL: Optional[str] = None
    additionalEndpointParams: Optional[Dict[str, str]] = None

class AuthClientConfig(BaseModel):
    method: str = "token"
    additionalScopes: Optional[List[str]] = None
    token: Optional[str] = None
    oidc: Optional[AuthOIDCClientConfig] = None

class ClientCommonConfig(BaseModel):
    auth: Optional[AuthClientConfig] = None
    user: Optional[str] = None
    serverAddr: Optional[str] = None
    serverPort: Optional[int] = None
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
    proxies: Optional[List[SerializeAsAny[ProxyBaseConfig]]] = []
    visitors: Optional[List[SerializeAsAny[VisitorBaseConfig]]] = []
