"""
工具函数
"""

import logging
import sys
from typing import Dict, Any, Optional
from urllib.parse import urlparse


def setup_logging(level: str = "INFO", format_string: Optional[str] = None) -> None:
    """
    设置日志配置
    
    Args:
        level: 日志级别
        format_string: 日志格式
    """
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=format_string,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def validate_audio_url(url: str) -> bool:
    """
    验证音频URL格式
    
    Args:
        url: 音频URL
        
    Returns:
        是否有效
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def validate_audio_format(format_str: str) -> bool:
    """
    验证音频格式
    
    Args:
        format_str: 音频格式
        
    Returns:
        是否支持
    """
    supported_formats = ["mp3", "wav", "ogg", "raw"]
    return format_str.lower() in supported_formats


def format_duration(milliseconds: int) -> str:
    """
    格式化时长显示
    
    Args:
        milliseconds: 毫秒数
        
    Returns:
        格式化的时长字符串
    """
    seconds = milliseconds / 1000
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    
    if minutes > 0:
        return f"{minutes}m{seconds}s"
    else:
        return f"{seconds}s"


def sanitize_filename(filename: str) -> str:
    """
    清理文件名，移除不安全字符
    
    Args:
        filename: 原始文件名
        
    Returns:
        清理后的文件名
    """
    import re
    # 移除或替换不安全字符
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # 移除控制字符
    filename = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', filename)
    # 限制长度
    if len(filename) > 255:
        filename = filename[:255]
    return filename


def get_error_message(status_code: int) -> str:
    """
    根据状态码获取错误描述
    
    Args:
        status_code: API状态码
        
    Returns:
        错误描述
    """
    error_messages = {
        20000000: "成功",
        20000001: "正在处理中",
        20000002: "任务在队列中",
        20000003: "静音音频",
        45000001: "请求参数无效",
        45000002: "空音频",
        45000151: "音频格式不正确",
        55000031: "服务器繁忙",
    }
    
    if status_code >= 550000 and status_code < 560000:
        return "服务内部处理错误"
    
    return error_messages.get(status_code, f"未知错误 ({status_code})")


def create_request_summary(request_data: Dict[str, Any]) -> str:
    """
    创建请求摘要用于日志
    
    Args:
        request_data: 请求数据
        
    Returns:
        请求摘要
    """
    audio = request_data.get("audio", {})
    request_config = request_data.get("request", {})
    
    summary_parts = [
        f"URL: {audio.get('url', 'N/A')}",
        f"Format: {audio.get('format', 'N/A')}",
        f"Model: {request_config.get('model_name', 'N/A')}"
    ]
    
    # 添加启用的功能
    enabled_features = []
    for feature in ["enable_itn", "enable_punc", "enable_ddc", "enable_speaker_info"]:
        if request_config.get(feature):
            enabled_features.append(feature.replace("enable_", ""))
    
    if enabled_features:
        summary_parts.append(f"Features: {', '.join(enabled_features)}")
    
    return " | ".join(summary_parts)
