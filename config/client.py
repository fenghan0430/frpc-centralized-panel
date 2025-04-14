from pydantic import BaseModel
from typing import List, Dict
from common import (
    LogConfig, 
    WebServerConfig,
    TLSConfig,
    QUICOptions
    )

class TLSClientConfig(TLSConfig):
    enable: bool
    disableCustomTLSFirstByte: bool

class ClientTransportConfig(BaseModel):
    protocol: str
    dialServerTimeout: int
    dialServerKeepalive: int
    connectServerLocalIP: str
    proxyURL: str
    poolCount: int
    tcpMux: bool
    tcpMuxKeepaliveInterval: int
    quic: QUICOptions
    heartbeatInterval: int
    heartbeatTimeout: int
    tls: TLSClientConfig

class AuthOIDCClientConfig(BaseModel):
    clientID: str
    clientSecret: str
    audience: str
    scope: str
    tokenEndpointURL: str
    additionalEndpointParams: Dict[str, str]

class AuthClientConfig(BaseModel):
    method: str
    additionalScopes: List[str]
    token: str
    oidc: AuthOIDCClientConfig

class ClientCommonConfig(BaseModel):
    auth: AuthClientConfig
    user: str
    serverAddr: str
    serverPort: str
    natHoleStunServer: str
    dnsServer: str
    loginFailExit: bool
    start: List[str]
    log: LogConfig
    webServer: WebServerConfig
    transport: ClientTransportConfig
    udpPacketSize: int
    metadatas: Dict[str, str]
    includes: List[str]

class ClientConfig(ClientCommonConfig):
    proxies: str # TODO： 实体化隧道和监听后需要修改
    visitors: str