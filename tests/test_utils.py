"""
工具函数测试
"""

import pytest
from meetaudio.utils import (
    validate_audio_url, validate_audio_format, format_duration,
    sanitize_filename, get_error_message, create_request_summary
)


class TestValidateAudioUrl:
    """音频URL验证测试"""
    
    def test_valid_http_url(self):
        """测试有效的HTTP URL"""
        assert validate_audio_url("http://example.com/audio.mp3") is True
    
    def test_valid_https_url(self):
        """测试有效的HTTPS URL"""
        assert validate_audio_url("https://example.com/audio.mp3") is True
    
    def test_invalid_url_no_scheme(self):
        """测试无协议的URL"""
        assert validate_audio_url("example.com/audio.mp3") is False
    
    def test_invalid_url_no_domain(self):
        """测试无域名的URL"""
        assert validate_audio_url("http://") is False
    
    def test_invalid_url_empty(self):
        """测试空URL"""
        assert validate_audio_url("") is False
    
    def test_invalid_url_malformed(self):
        """测试格式错误的URL"""
        assert validate_audio_url("not-a-url") is False


class TestValidateAudioFormat:
    """音频格式验证测试"""
    
    def test_valid_formats(self):
        """测试支持的音频格式"""
        valid_formats = ["mp3", "wav", "ogg", "raw"]
        for fmt in valid_formats:
            assert validate_audio_format(fmt) is True
    
    def test_valid_formats_uppercase(self):
        """测试大写的音频格式"""
        valid_formats = ["MP3", "WAV", "OGG", "RAW"]
        for fmt in valid_formats:
            assert validate_audio_format(fmt) is True
    
    def test_invalid_formats(self):
        """测试不支持的音频格式"""
        invalid_formats = ["mp4", "avi", "flac", "aac", "m4a"]
        for fmt in invalid_formats:
            assert validate_audio_format(fmt) is False
    
    def test_empty_format(self):
        """测试空格式"""
        assert validate_audio_format("") is False


class TestFormatDuration:
    """时长格式化测试"""
    
    def test_seconds_only(self):
        """测试只有秒数"""
        assert format_duration(5000) == "5s"
        assert format_duration(30000) == "30s"
    
    def test_minutes_and_seconds(self):
        """测试分钟和秒数"""
        assert format_duration(65000) == "1m5s"
        assert format_duration(125000) == "2m5s"
    
    def test_zero_duration(self):
        """测试零时长"""
        assert format_duration(0) == "0s"
    
    def test_exact_minutes(self):
        """测试整分钟"""
        assert format_duration(60000) == "1m0s"
        assert format_duration(120000) == "2m0s"


class TestSanitizeFilename:
    """文件名清理测试"""
    
    def test_normal_filename(self):
        """测试正常文件名"""
        assert sanitize_filename("normal_file.txt") == "normal_file.txt"
    
    def test_filename_with_unsafe_chars(self):
        """测试包含不安全字符的文件名"""
        unsafe = 'file<>:"/\\|?*.txt'
        expected = "file_________.txt"
        assert sanitize_filename(unsafe) == expected
    
    def test_filename_with_control_chars(self):
        """测试包含控制字符的文件名"""
        with_control = "file\x00\x1f\x7f.txt"
        expected = "file.txt"
        assert sanitize_filename(with_control) == expected
    
    def test_long_filename(self):
        """测试过长的文件名"""
        long_name = "a" * 300 + ".txt"
        result = sanitize_filename(long_name)
        assert len(result) <= 255
    
    def test_empty_filename(self):
        """测试空文件名"""
        assert sanitize_filename("") == ""


class TestGetErrorMessage:
    """错误消息获取测试"""
    
    def test_known_error_codes(self):
        """测试已知错误码"""
        assert get_error_message(20000000) == "成功"
        assert get_error_message(20000001) == "正在处理中"
        assert get_error_message(45000001) == "请求参数无效"
        assert get_error_message(55000031) == "服务器繁忙"
    
    def test_server_error_range(self):
        """测试服务器错误范围"""
        assert get_error_message(550001) == "服务内部处理错误"
        assert get_error_message(559999) == "服务内部处理错误"
    
    def test_unknown_error_code(self):
        """测试未知错误码"""
        result = get_error_message(99999999)
        assert "未知错误" in result
        assert "99999999" in result


class TestCreateRequestSummary:
    """请求摘要创建测试"""
    
    def test_basic_request_summary(self):
        """测试基本请求摘要"""
        request_data = {
            "audio": {
                "url": "http://example.com/test.mp3",
                "format": "mp3"
            },
            "request": {
                "model_name": "bigmodel"
            }
        }
        
        summary = create_request_summary(request_data)
        assert "http://example.com/test.mp3" in summary
        assert "mp3" in summary
        assert "bigmodel" in summary
    
    def test_request_summary_with_features(self):
        """测试包含功能的请求摘要"""
        request_data = {
            "audio": {
                "url": "http://example.com/test.mp3",
                "format": "mp3"
            },
            "request": {
                "model_name": "bigmodel",
                "enable_itn": True,
                "enable_punc": True,
                "enable_ddc": False,
                "enable_speaker_info": True
            }
        }
        
        summary = create_request_summary(request_data)
        assert "Features:" in summary
        assert "itn" in summary
        assert "punc" in summary
        assert "speaker_info" in summary
        # enable_ddc为False，不应该出现
        assert "ddc" not in summary
    
    def test_request_summary_missing_fields(self):
        """测试缺少字段的请求摘要"""
        request_data = {}
        
        summary = create_request_summary(request_data)
        assert "N/A" in summary
