"""
配置管理
"""

import os
from typing import Optional
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class Config:
    """配置类"""
    
    # API配置
    APP_KEY: str = os.getenv("BYTEDANCE_APP_KEY", "")
    ACCESS_KEY: str = os.getenv("BYTEDANCE_ACCESS_KEY", "")
    
    # API端点
    SUBMIT_URL: str = os.getenv(
        "BYTEDANCE_SUBMIT_URL", 
        "https://openspeech.bytedance.com/api/v3/auc/bigmodel/submit"
    )
    QUERY_URL: str = os.getenv(
        "BYTEDANCE_QUERY_URL",
        "https://openspeech.bytedance.com/api/v3/auc/bigmodel/query"
    )
    
    # 客户端配置
    DEFAULT_TIMEOUT: int = int(os.getenv("DEFAULT_TIMEOUT", "30"))
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_DELAY: float = float(os.getenv("RETRY_DELAY", "1.0"))
    
    # 固定值
    RESOURCE_ID: str = "volc.bigasr.auc"
    SEQUENCE: str = "-1"
    
    @classmethod
    def validate(cls) -> bool:
        """验证配置是否完整"""
        if not cls.APP_KEY:
            raise ValueError("BYTEDANCE_APP_KEY is required")
        if not cls.ACCESS_KEY:
            raise ValueError("BYTEDANCE_ACCESS_KEY is required")
        return True
    
    @classmethod
    def from_dict(cls, config_dict: dict) -> 'Config':
        """从字典创建配置"""
        config = cls()
        for key, value in config_dict.items():
            if hasattr(config, key.upper()):
                setattr(config, key.upper(), value)
        return config


# 默认配置实例
config = Config()
