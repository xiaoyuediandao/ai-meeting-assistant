"""
客户端测试
"""

import pytest
import uuid
from unittest.mock import Mock, patch

from meetaudio.client import ByteDanceASRClient
from meetaudio.models import ASRResult, TaskStatus
from meetaudio.exceptions import (
    AuthenticationError, APIError, InvalidParameterError,
    AudioFormatError, ServiceBusyError
)


class TestByteDanceASRClient:
    """ByteDanceASRClient测试类"""
    
    def test_init_with_credentials(self):
        """测试使用凭据初始化"""
        client = ByteDanceASRClient(
            app_key="test_app_key",
            access_key="test_access_key"
        )
        assert client.app_key == "test_app_key"
        assert client.access_key == "test_access_key"
    
    def test_init_without_credentials(self):
        """测试没有凭据时初始化失败"""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(AuthenticationError):
                ByteDanceASRClient()
    
    def test_get_headers(self):
        """测试请求头生成"""
        client = ByteDanceASRClient(
            app_key="test_app_key",
            access_key="test_access_key"
        )
        
        request_id = str(uuid.uuid4())
        headers = client._get_headers(request_id)
        
        assert headers["X-Api-App-Key"] == "test_app_key"
        assert headers["X-Api-Access-Key"] == "test_access_key"
        assert headers["X-Api-Request-Id"] == request_id
        assert headers["X-Api-Resource-Id"] == "volc.bigasr.auc"
        assert headers["X-Api-Sequence"] == "-1"
    
    @patch('meetaudio.client.requests.Session.post')
    def test_submit_audio_success(self, mock_post):
        """测试成功提交音频"""
        # 模拟成功响应
        mock_response = Mock()
        mock_response.headers = {
            "X-Api-Status-Code": "20000000",
            "X-Api-Message": "OK"
        }
        mock_post.return_value = mock_response
        
        client = ByteDanceASRClient(
            app_key="test_app_key",
            access_key="test_access_key"
        )
        
        task_id = client.submit_audio(
            audio_url="http://example.com/test.mp3",
            audio_format="mp3"
        )
        
        assert isinstance(task_id, str)
        assert len(task_id) > 0
        mock_post.assert_called_once()
    
    @patch('meetaudio.client.requests.Session.post')
    def test_submit_audio_invalid_params(self, mock_post):
        """测试提交音频时参数无效"""
        mock_response = Mock()
        mock_response.headers = {
            "X-Api-Status-Code": "45000001",
            "X-Api-Message": "Invalid parameters"
        }
        mock_post.return_value = mock_response
        
        client = ByteDanceASRClient(
            app_key="test_app_key",
            access_key="test_access_key"
        )
        
        with pytest.raises(InvalidParameterError):
            client.submit_audio(
                audio_url="invalid_url",
                audio_format="mp3"
            )
    
    @patch('meetaudio.client.requests.Session.post')
    def test_get_result_success(self, mock_post):
        """测试成功获取结果"""
        mock_response = Mock()
        mock_response.headers = {
            "X-Api-Status-Code": "20000000",
            "X-Api-Message": "OK"
        }
        mock_response.content = b'{"result": {"text": "test text"}}'
        mock_response.json.return_value = {
            "result": {"text": "test text"},
            "audio_info": {"duration": 5000}
        }
        mock_post.return_value = mock_response
        
        client = ByteDanceASRClient(
            app_key="test_app_key",
            access_key="test_access_key"
        )
        
        task_id = str(uuid.uuid4())
        status = client.get_result(task_id)
        
        assert isinstance(status, TaskStatus)
        assert status.is_success
        assert status.result is not None
        assert status.result.text == "test text"
    
    @patch('meetaudio.client.requests.Session.post')
    def test_get_result_processing(self, mock_post):
        """测试获取处理中状态"""
        mock_response = Mock()
        mock_response.headers = {
            "X-Api-Status-Code": "20000001",
            "X-Api-Message": "Processing"
        }
        mock_response.content = b''
        mock_post.return_value = mock_response
        
        client = ByteDanceASRClient(
            app_key="test_app_key",
            access_key="test_access_key"
        )
        
        task_id = str(uuid.uuid4())
        status = client.get_result(task_id)
        
        assert status.is_processing
        assert not status.is_success
        assert not status.is_failed
    
    @patch('meetaudio.client.requests.Session.post')
    def test_get_result_failed(self, mock_post):
        """测试获取失败状态"""
        mock_response = Mock()
        mock_response.headers = {
            "X-Api-Status-Code": "55000031",
            "X-Api-Message": "Service busy"
        }
        mock_response.content = b''
        mock_post.return_value = mock_response
        
        client = ByteDanceASRClient(
            app_key="test_app_key",
            access_key="test_access_key"
        )
        
        task_id = str(uuid.uuid4())
        status = client.get_result(task_id)
        
        assert status.is_failed
        assert not status.is_success
        assert not status.is_processing
    
    @patch('meetaudio.client.ByteDanceASRClient.get_result')
    def test_wait_for_result_success(self, mock_get_result):
        """测试等待结果成功"""
        # 模拟先处理中，然后成功
        mock_status_processing = TaskStatus(
            status_code=20000001,
            message="Processing"
        )
        mock_status_success = TaskStatus(
            status_code=20000000,
            message="OK",
            result=ASRResult(text="test text")
        )
        
        mock_get_result.side_effect = [mock_status_processing, mock_status_success]
        
        client = ByteDanceASRClient(
            app_key="test_app_key",
            access_key="test_access_key"
        )
        
        task_id = str(uuid.uuid4())
        result = client.wait_for_result(task_id, timeout=10, poll_interval=1)
        
        assert isinstance(result, ASRResult)
        assert result.text == "test text"
    
    @patch('meetaudio.client.ByteDanceASRClient.get_result')
    def test_wait_for_result_timeout(self, mock_get_result):
        """测试等待结果超时"""
        mock_status_processing = TaskStatus(
            status_code=20000001,
            message="Processing"
        )
        mock_get_result.return_value = mock_status_processing
        
        client = ByteDanceASRClient(
            app_key="test_app_key",
            access_key="test_access_key"
        )
        
        task_id = str(uuid.uuid4())
        
        with pytest.raises(Exception):  # TimeoutError
            client.wait_for_result(task_id, timeout=2, poll_interval=1)
    
    def test_handle_error_mapping(self):
        """测试错误处理映射"""
        client = ByteDanceASRClient(
            app_key="test_app_key",
            access_key="test_access_key"
        )
        
        # 测试参数错误
        with pytest.raises(InvalidParameterError):
            client._handle_error(45000001, "Invalid parameters")
        
        # 测试音频格式错误
        with pytest.raises(AudioFormatError):
            client._handle_error(45000151, "Invalid audio format")
        
        # 测试服务繁忙
        with pytest.raises(ServiceBusyError):
            client._handle_error(55000031, "Service busy")
        
        # 测试未知错误
        with pytest.raises(APIError):
            client._handle_error(99999999, "Unknown error")
