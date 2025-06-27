"""
数据模型测试
"""

import pytest
from meetaudio.models import (
    WordInfo, ASRUtterance, AudioInfo, ASRResult, 
    TaskStatus, SubmitRequest
)


class TestWordInfo:
    """WordInfo测试类"""
    
    def test_word_info_creation(self):
        """测试WordInfo创建"""
        word = WordInfo(
            text="测试",
            start_time=1000,
            end_time=2000,
            blank_duration=100
        )
        
        assert word.text == "测试"
        assert word.start_time == 1000
        assert word.end_time == 2000
        assert word.blank_duration == 100
    
    def test_word_info_default_blank_duration(self):
        """测试WordInfo默认空白时长"""
        word = WordInfo(
            text="测试",
            start_time=1000,
            end_time=2000
        )
        
        assert word.blank_duration == 0


class TestASRUtterance:
    """ASRUtterance测试类"""
    
    def test_utterance_creation(self):
        """测试ASRUtterance创建"""
        utterance = ASRUtterance(
            text="这是一个测试句子",
            start_time=0,
            end_time=3000,
            definite=True
        )
        
        assert utterance.text == "这是一个测试句子"
        assert utterance.start_time == 0
        assert utterance.end_time == 3000
        assert utterance.definite is True
    
    def test_utterance_with_words(self):
        """测试包含单词信息的ASRUtterance"""
        words = [
            WordInfo(text="这", start_time=0, end_time=500),
            WordInfo(text="是", start_time=500, end_time=1000),
        ]
        
        utterance = ASRUtterance(
            text="这是",
            start_time=0,
            end_time=1000,
            words=words
        )
        
        assert len(utterance.words) == 2
        assert utterance.words[0].text == "这"
        assert utterance.words[1].text == "是"


class TestAudioInfo:
    """AudioInfo测试类"""
    
    def test_audio_info_creation(self):
        """测试AudioInfo创建"""
        audio_info = AudioInfo(duration=10000)
        assert audio_info.duration == 10000


class TestASRResult:
    """ASRResult测试类"""
    
    def test_asr_result_creation(self):
        """测试ASRResult创建"""
        result = ASRResult(text="完整的识别文本")
        assert result.text == "完整的识别文本"
        assert result.utterances is None
        assert result.audio_info is None
    
    def test_asr_result_with_utterances(self):
        """测试包含分句信息的ASRResult"""
        utterances = [
            ASRUtterance(text="第一句", start_time=0, end_time=2000),
            ASRUtterance(text="第二句", start_time=2000, end_time=4000),
        ]
        
        result = ASRResult(
            text="第一句第二句",
            utterances=utterances
        )
        
        assert len(result.utterances) == 2
        assert result.utterances[0].text == "第一句"
        assert result.utterances[1].text == "第二句"


class TestTaskStatus:
    """TaskStatus测试类"""
    
    def test_task_status_success(self):
        """测试成功状态"""
        status = TaskStatus(
            status_code=20000000,
            message="OK"
        )
        
        assert status.is_success
        assert not status.is_processing
        assert not status.is_failed
    
    def test_task_status_processing(self):
        """测试处理中状态"""
        status = TaskStatus(
            status_code=20000001,
            message="Processing"
        )
        
        assert not status.is_success
        assert status.is_processing
        assert not status.is_failed
    
    def test_task_status_queued(self):
        """测试队列中状态"""
        status = TaskStatus(
            status_code=20000002,
            message="Queued"
        )
        
        assert not status.is_success
        assert status.is_processing
        assert not status.is_failed
    
    def test_task_status_failed(self):
        """测试失败状态"""
        status = TaskStatus(
            status_code=45000001,
            message="Invalid parameters"
        )
        
        assert not status.is_success
        assert not status.is_processing
        assert status.is_failed
    
    def test_task_status_with_result(self):
        """测试包含结果的状态"""
        result = ASRResult(text="测试文本")
        status = TaskStatus(
            status_code=20000000,
            message="OK",
            result=result
        )
        
        assert status.is_success
        assert status.result is not None
        assert status.result.text == "测试文本"


class TestSubmitRequest:
    """SubmitRequest测试类"""
    
    def test_submit_request_creation(self):
        """测试SubmitRequest创建"""
        request = SubmitRequest(
            audio={"url": "http://example.com/test.mp3", "format": "mp3"},
            request={"model_name": "bigmodel", "enable_itn": True}
        )
        
        assert request.audio["url"] == "http://example.com/test.mp3"
        assert request.audio["format"] == "mp3"
        assert request.request["model_name"] == "bigmodel"
        assert request.request["enable_itn"] is True
    
    def test_submit_request_with_user(self):
        """测试包含用户信息的SubmitRequest"""
        request = SubmitRequest(
            user={"uid": "test_user"},
            audio={"url": "http://example.com/test.mp3", "format": "mp3"},
            request={"model_name": "bigmodel"}
        )
        
        assert request.user["uid"] == "test_user"
    
    def test_submit_request_with_callback(self):
        """测试包含回调的SubmitRequest"""
        request = SubmitRequest(
            audio={"url": "http://example.com/test.mp3", "format": "mp3"},
            request={"model_name": "bigmodel"},
            callback="http://example.com/callback",
            callback_data="test_data"
        )
        
        assert request.callback == "http://example.com/callback"
        assert request.callback_data == "test_data"
