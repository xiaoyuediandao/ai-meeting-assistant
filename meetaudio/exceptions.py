"""
异常定义
"""


class ByteDanceASRError(Exception):
    """基础异常类"""
    def __init__(self, message: str, status_code: int = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class APIError(ByteDanceASRError):
    """API调用错误"""
    pass


class AuthenticationError(ByteDanceASRError):
    """认证错误"""
    pass


class AudioFormatError(ByteDanceASRError):
    """音频格式错误"""
    pass


class TaskNotFoundError(ByteDanceASRError):
    """任务未找到"""
    pass


class ServiceBusyError(ByteDanceASRError):
    """服务繁忙"""
    pass


class TimeoutError(ByteDanceASRError):
    """超时错误"""
    pass


class InvalidParameterError(ByteDanceASRError):
    """参数错误"""
    pass


# 状态码到异常的映射
STATUS_CODE_EXCEPTIONS = {
    45000001: InvalidParameterError,
    45000002: AudioFormatError,
    45000151: AudioFormatError,
    20000003: AudioFormatError,  # 静音音频
    55000031: ServiceBusyError,
}
