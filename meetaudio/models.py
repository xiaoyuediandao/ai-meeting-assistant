"""
数据模型定义
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class WordInfo(BaseModel):
    """单词信息"""
    text: str = Field(description="单词文本")
    start_time: int = Field(description="开始时间（毫秒）")
    end_time: int = Field(description="结束时间（毫秒）")
    blank_duration: int = Field(default=0, description="空白持续时间")


class ASRUtterance(BaseModel):
    """语音分句信息"""
    text: str = Field(description="分句文本内容")
    start_time: int = Field(description="开始时间（毫秒）")
    end_time: int = Field(description="结束时间（毫秒）")
    definite: bool = Field(default=True, description="是否确定")
    words: Optional[List[WordInfo]] = Field(default=None, description="单词级别信息")
    channel_id: Optional[int] = Field(default=None, description="声道ID（双声道时使用）")
    speaker_id: Optional[str] = Field(default=None, description="说话人ID")


class AudioInfo(BaseModel):
    """音频信息"""
    duration: int = Field(description="音频时长（毫秒）")


class ASRResult(BaseModel):
    """语音识别结果"""
    text: str = Field(description="完整识别文本")
    utterances: Optional[List[ASRUtterance]] = Field(default=None, description="分句信息")
    audio_info: Optional[AudioInfo] = Field(default=None, description="音频信息")


class SubmitRequest(BaseModel):
    """提交任务请求"""
    user: Optional[Dict[str, str]] = Field(default=None, description="用户信息")
    audio: Dict[str, Any] = Field(description="音频配置")
    request: Dict[str, Any] = Field(description="请求配置")
    callback: Optional[str] = Field(default=None, description="回调地址")
    callback_data: Optional[str] = Field(default=None, description="回调数据")


class TaskStatus(BaseModel):
    """任务状态"""
    status_code: int = Field(description="状态码")
    message: str = Field(description="状态消息")
    result: Optional[ASRResult] = Field(default=None, description="识别结果")
    
    @property
    def is_success(self) -> bool:
        """是否成功"""
        return self.status_code == 20000000
    
    @property
    def is_processing(self) -> bool:
        """是否正在处理"""
        return self.status_code in [20000001, 20000002]
    
    @property
    def is_failed(self) -> bool:
        """是否失败"""
        return self.status_code not in [20000000, 20000001, 20000002]
