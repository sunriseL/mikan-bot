from pydantic import BaseModel
from typing import Optional

class FollowerConfig(BaseModel):
    """Follower 插件配置"""
    api_base_url: str = "http://192.168.1.53:8000"
    api_timeout: float = 30.0
    retry_count: int = 3
    retry_delay: float = 1.0
    
    # 支持的平台
    supported_platforms: list = ["twitter", "instagram"]
    
    # 缓存设置
    cache_enabled: bool = True
    cache_ttl: int = 300  # 5分钟缓存
    
    # 日志设置
    log_level: str = "INFO"
    log_requests: bool = True 