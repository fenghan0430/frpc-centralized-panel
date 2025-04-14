from pydantic import BaseModel
from typing import List, Dict

class ProxyBaseConfig(BaseModel):
    pass

class ProxyTransport(BaseModel):
    pass

class ProxyBackend(BaseModel):
    pass

class LoadBalancerConfig(BaseModel):
    pass

class HealthCheckConfig(BaseModel):
    pass

class DomainConfig(BaseModel):
    pass

class TCPProxyConfig(ProxyBaseConfig):
    pass