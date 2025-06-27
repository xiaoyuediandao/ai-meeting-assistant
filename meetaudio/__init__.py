"""
火山引擎语音识别API Python客户端

提供简单易用的接口来调用火山引擎大模型录音文件识别服务。
"""

from .client import ByteDanceASRClient
from .models import ASRResult, ASRUtterance, AudioInfo
from .exceptions import (
    ByteDanceASRError,
    APIError,
    AuthenticationError,
    AudioFormatError,
    TaskNotFoundError,
    ServiceBusyError
)

__version__ = "1.0.0"
__author__ = "ByteDance ASR Client"

__all__ = [
    "ByteDanceASRClient",
    "ASRResult", 
    "ASRUtterance",
    "AudioInfo",
    "ByteDanceASRError",
    "APIError",
    "AuthenticationError", 
    "AudioFormatError",
    "TaskNotFoundError",
    "ServiceBusyError"
]
