"""
pytest配置文件
"""

import pytest
import os
from unittest.mock import patch


@pytest.fixture
def mock_env_vars():
    """模拟环境变量"""
    env_vars = {
        'BYTEDANCE_APP_KEY': 'test_app_key',
        'BYTEDANCE_ACCESS_KEY': 'test_access_key',
        'BYTEDANCE_SUBMIT_URL': 'https://test.example.com/submit',
        'BYTEDANCE_QUERY_URL': 'https://test.example.com/query',
        'DEFAULT_TIMEOUT': '30',
        'MAX_RETRIES': '3',
        'RETRY_DELAY': '1.0'
    }
    
    with patch.dict(os.environ, env_vars):
        yield env_vars


@pytest.fixture
def sample_audio_url():
    """示例音频URL"""
    return "https://example.com/sample.mp3"


@pytest.fixture
def sample_task_id():
    """示例任务ID"""
    return "12345678-1234-1234-1234-123456789012"


@pytest.fixture
def sample_asr_result():
    """示例ASR结果"""
    from meetaudio.models import ASRResult, ASRUtterance, AudioInfo
    
    utterances = [
        ASRUtterance(
            text="这是第一句话",
            start_time=0,
            end_time=2000
        ),
        ASRUtterance(
            text="这是第二句话",
            start_time=2000,
            end_time=4000
        )
    ]
    
    return ASRResult(
        text="这是第一句话这是第二句话",
        utterances=utterances,
        audio_info=AudioInfo(duration=4000)
    )
