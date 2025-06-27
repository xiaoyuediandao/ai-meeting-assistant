"""
增强的语音识别客户端，专为会议场景优化
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from .client import ByteDanceASRClient
from .models import ASRResult, ASRUtterance
from .exceptions import ByteDanceASRError

logger = logging.getLogger(__name__)


class MeetingASRClient(ByteDanceASRClient):
    """会议专用语音识别客户端"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.speaker_mapping = {}  # 说话人映射
        
    def submit_meeting_audio(
        self,
        audio_url: str,
        audio_format: str = "wav",
        enable_speaker_separation: bool = True,
        enable_dialect_support: bool = True,
        **kwargs
    ) -> str:
        """
        提交会议音频进行识别
        
        Args:
            audio_url: 音频文件URL
            audio_format: 音频格式
            enable_speaker_separation: 启用说话人分离
            enable_dialect_support: 启用方言支持
            **kwargs: 其他参数
            
        Returns:
            任务ID
        """
        # 会议场景优化配置
        meeting_config = {
            "enable_itn": True,  # 文本规范化
            "enable_punc": True,  # 标点符号
            "enable_ddc": True,  # 语义顺滑
            "enable_speaker_info": enable_speaker_separation,  # 说话人分离
            "show_utterances": True,  # 详细分句
            "vad_segment": True,  # VAD分句
            "end_window_size": 800,  # 强制判停时间
        }
        
        # 合并用户配置
        meeting_config.update(kwargs)
        
        logger.info(f"提交会议音频识别: {audio_url}")
        logger.info(f"会议配置: {meeting_config}")
        
        return self.submit_audio(
            audio_url=audio_url,
            audio_format=audio_format,
            **meeting_config
        )
    
    def get_meeting_result(self, task_id: str) -> Optional['MeetingResult']:
        """
        获取会议识别结果
        
        Args:
            task_id: 任务ID
            
        Returns:
            会议结果对象
        """
        status = self.get_result(task_id)
        
        if status.is_success and status.result:
            return MeetingResult.from_asr_result(status.result)
        elif status.is_failed:
            raise ByteDanceASRError(f"识别失败: {status.message}", status.status_code)
        else:
            return None  # 仍在处理中
    
    def wait_for_meeting_result(
        self,
        task_id: str,
        timeout: int = 900,  # 15分钟超时
        poll_interval: int = 5
    ) -> 'MeetingResult':
        """
        等待会议识别完成
        
        Args:
            task_id: 任务ID
            timeout: 超时时间（秒）
            poll_interval: 轮询间隔（秒）
            
        Returns:
            会议结果对象
        """
        result = self.wait_for_result(task_id, timeout, poll_interval)
        return MeetingResult.from_asr_result(result)


class MeetingResult:
    """会议识别结果"""
    
    def __init__(
        self,
        full_text: str,
        utterances: List[ASRUtterance],
        duration: int,
        speakers: Dict[str, List[ASRUtterance]] = None
    ):
        self.full_text = full_text
        self.utterances = utterances
        self.duration = duration
        self.speakers = speakers or {}
        
    @classmethod
    def from_asr_result(cls, asr_result: ASRResult) -> 'MeetingResult':
        """从ASR结果创建会议结果"""
        duration = asr_result.audio_info.duration if asr_result.audio_info else 0
        
        # 按说话人分组
        speakers = {}
        if asr_result.utterances:
            for utterance in asr_result.utterances:
                speaker_id = utterance.speaker_id or "未知说话人"
                if speaker_id not in speakers:
                    speakers[speaker_id] = []
                speakers[speaker_id].append(utterance)
        
        return cls(
            full_text=asr_result.text,
            utterances=asr_result.utterances or [],
            duration=duration,
            speakers=speakers
        )
    
    def get_speaker_content(self, speaker_id: str) -> str:
        """获取指定说话人的发言内容"""
        if speaker_id not in self.speakers:
            return ""
        
        return " ".join([utterance.text for utterance in self.speakers[speaker_id]])
    
    def get_last_speakers(self, count: int = 2) -> List[Tuple[str, str]]:
        """
        获取最后几位说话人的发言内容
        
        Args:
            count: 说话人数量
            
        Returns:
            [(说话人ID, 发言内容), ...]
        """
        if not self.utterances:
            return []
        
        # 按时间排序，获取最后的发言
        sorted_utterances = sorted(self.utterances, key=lambda x: x.start_time)
        
        # 找到最后几位说话人
        last_speakers = []
        seen_speakers = set()
        
        # 从后往前遍历
        for utterance in reversed(sorted_utterances):
            speaker_id = utterance.speaker_id or "未知说话人"
            if speaker_id not in seen_speakers:
                seen_speakers.add(speaker_id)
                if len(seen_speakers) <= count:
                    # 获取该说话人的所有发言
                    speaker_content = self.get_speaker_content(speaker_id)
                    last_speakers.append((speaker_id, speaker_content))
                else:
                    break
        
        # 按发言时间顺序返回
        return list(reversed(last_speakers))
    
    def get_meeting_summary(self) -> Dict[str, Any]:
        """获取会议摘要信息"""
        return {
            "duration_minutes": round(self.duration / 60000, 1),
            "total_speakers": len(self.speakers),
            "total_utterances": len(self.utterances),
            "speaker_list": list(self.speakers.keys()),
            "word_count": len(self.full_text),
        }
    
    def extract_key_information(self) -> Dict[str, List[str]]:
        """
        提取关键信息（简单版本，后续可用AI增强）
        
        Returns:
            包含决策点、行动项等的字典
        """
        # 简单的关键词匹配
        decisions = []
        actions = []
        responsibilities = []
        deadlines = []
        
        text = self.full_text
        
        # 决策关键词
        decision_keywords = ["决定", "确定", "同意", "批准", "通过", "否决", "拒绝"]
        for keyword in decision_keywords:
            if keyword in text:
                # 简单提取包含关键词的句子
                sentences = text.split("。")
                for sentence in sentences:
                    if keyword in sentence:
                        decisions.append(sentence.strip())
        
        # 行动项关键词
        action_keywords = ["需要", "要求", "安排", "负责", "完成", "执行", "落实"]
        for keyword in action_keywords:
            if keyword in text:
                sentences = text.split("。")
                for sentence in sentences:
                    if keyword in sentence:
                        actions.append(sentence.strip())
        
        # 时间关键词
        time_keywords = ["月底", "周内", "明天", "下周", "月", "日", "年"]
        for keyword in time_keywords:
            if keyword in text:
                sentences = text.split("。")
                for sentence in sentences:
                    if keyword in sentence and any(action in sentence for action in ["完成", "提交", "汇报"]):
                        deadlines.append(sentence.strip())
        
        return {
            "decisions": list(set(decisions))[:5],  # 去重并限制数量
            "actions": list(set(actions))[:5],
            "responsibilities": responsibilities,
            "deadlines": list(set(deadlines))[:3],
        }
