"""
火山引擎语音识别API客户端
"""

import json
import uuid
import time
import logging
from typing import Optional, Dict, Any, Union
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .config import config
from .models import ASRResult, TaskStatus, SubmitRequest
from .exceptions import (
    ByteDanceASRError, APIError, AuthenticationError,
    TimeoutError, STATUS_CODE_EXCEPTIONS
)

logger = logging.getLogger(__name__)


class ByteDanceASRClient:
    """火山引擎语音识别客户端"""
    
    def __init__(
        self,
        app_key: Optional[str] = None,
        access_key: Optional[str] = None,
        timeout: int = None,
        max_retries: int = None
    ):
        """
        初始化客户端
        
        Args:
            app_key: APP ID
            access_key: Access Token
            timeout: 请求超时时间
            max_retries: 最大重试次数
        """
        self.app_key = app_key or config.APP_KEY
        self.access_key = access_key or config.ACCESS_KEY
        self.timeout = timeout or config.DEFAULT_TIMEOUT
        self.max_retries = max_retries or config.MAX_RETRIES
        
        if not self.app_key or not self.access_key:
            raise AuthenticationError("APP_KEY and ACCESS_KEY are required")
        
        # 配置HTTP会话
        self.session = requests.Session()
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=config.RETRY_DELAY,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def _get_headers(self, request_id: str) -> Dict[str, str]:
        """获取请求头"""
        return {
            "Content-Type": "application/json",
            "X-Api-App-Key": self.app_key,
            "X-Api-Access-Key": self.access_key,
            "X-Api-Resource-Id": config.RESOURCE_ID,
            "X-Api-Request-Id": request_id,
            "X-Api-Sequence": config.SEQUENCE,
        }
    
    def submit_audio(
        self,
        audio_url: str,
        audio_format: str = "mp3",
        model_name: str = "bigmodel",
        enable_itn: bool = True,
        enable_punc: bool = False,
        enable_ddc: bool = False,
        enable_speaker_info: bool = False,
        enable_channel_split: bool = False,
        show_utterances: bool = False,
        vad_segment: bool = False,
        user_id: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        提交音频文件进行识别
        
        Args:
            audio_url: 音频文件URL
            audio_format: 音频格式 (mp3, wav, ogg, raw)
            model_name: 模型名称
            enable_itn: 启用文本规范化
            enable_punc: 启用标点符号
            enable_ddc: 启用语义顺滑
            enable_speaker_info: 启用说话人分离
            enable_channel_split: 启用双声道识别
            show_utterances: 输出详细分句信息
            vad_segment: 使用VAD分句
            user_id: 用户ID
            **kwargs: 其他参数
            
        Returns:
            任务ID
        """
        task_id = str(uuid.uuid4())

        # 验证音频URL的可访问性
        if not self._validate_audio_url(audio_url):
            raise APIError(f"音频文件URL无法访问: {audio_url}")

        # 构建请求数据
        request_data = {
            "audio": {
                "url": audio_url,
                "format": audio_format,
                **{k: v for k, v in kwargs.items() if k in ["codec", "rate", "bits", "channel"]}
            },
            "request": {
                "model_name": model_name,
                "enable_itn": enable_itn,
                "enable_punc": enable_punc,
                "enable_ddc": enable_ddc,
                "enable_speaker_info": enable_speaker_info,
                "enable_channel_split": enable_channel_split,
                "show_utterances": show_utterances,
                "vad_segment": vad_segment,
                **{k: v for k, v in kwargs.items() if k in [
                    "end_window_size", "sensitive_words_filter", "corpus",
                    "boosting_table_name", "context"
                ]}
            }
        }
        
        if user_id:
            request_data["user"] = {"uid": user_id}
        
        if "callback" in kwargs:
            request_data["callback"] = kwargs["callback"]
        if "callback_data" in kwargs:
            request_data["callback_data"] = kwargs["callback_data"]
        
        headers = self._get_headers(task_id)

        # 记录详细的请求信息用于调试
        logger.info(f"提交ASR任务 - URL: {audio_url}")
        logger.info(f"请求数据: {request_data}")
        logger.info(f"请求头: {headers}")
        logger.info(f"API端点: {config.SUBMIT_URL}")

        try:
            response = self.session.post(
                config.SUBMIT_URL,
                json=request_data,
                headers=headers,
                timeout=self.timeout
            )
            
            # 检查响应状态
            status_code = int(response.headers.get("X-Api-Status-Code", 0))
            message = response.headers.get("X-Api-Message", "Unknown error")

            # 记录响应信息用于调试
            logger.info(f"ASR API响应 - 状态码: {status_code}, 消息: {message}")
            logger.info(f"HTTP状态码: {response.status_code}")
            logger.info(f"响应头: {dict(response.headers)}")
            if response.content:
                logger.info(f"响应体: {response.text}")

            if status_code != 20000000:
                # 特别处理TOS URL相关的错误
                if "不存在" in message or "过期" in message:
                    logger.error(f"音频文件访问失败 - URL: {audio_url}, 错误: {message}")
                    logger.error("可能的原因: 1) TOS文件权限问题 2) URL格式问题 3) 网络访问问题")
                self._handle_error(status_code, message)

            # 获取X-Tt-Logid用于后续查询
            x_tt_logid = response.headers.get("X-Tt-Logid", "")
            logger.info(f"X-Tt-Logid: {x_tt_logid}")

            # 检查响应体中是否有实际的任务ID
            actual_task_id = task_id  # 默认使用客户端生成的ID
            try:
                if response.content:
                    data = response.json()
                    if "id" in data:
                        actual_task_id = data["id"]
                        logger.info(f"Server returned task ID: {actual_task_id}")
                    elif "task_id" in data:
                        actual_task_id = data["task_id"]
                        logger.info(f"Server returned task ID: {actual_task_id}")
            except Exception as e:
                logger.debug(f"Could not parse response body: {e}")

            logger.info(f"Task submitted successfully: {actual_task_id}")

            # 存储X-Tt-Logid以供查询使用
            if not hasattr(self, '_task_logids'):
                self._task_logids = {}
            self._task_logids[actual_task_id] = x_tt_logid

            return actual_task_id
            
        except requests.RequestException as e:
            raise APIError(f"Failed to submit task: {str(e)}")
    
    def get_result(self, task_id: str) -> TaskStatus:
        """
        查询识别结果

        Args:
            task_id: 任务ID

        Returns:
            任务状态和结果
        """
        # 使用任务ID作为请求ID进行查询
        headers = self._get_headers(task_id)

        # 添加X-Tt-Logid（如果有的话）
        if hasattr(self, '_task_logids') and task_id in self._task_logids:
            headers["X-Tt-Logid"] = self._task_logids[task_id]
            logger.info(f"使用X-Tt-Logid进行查询: {self._task_logids[task_id]}")

        # 根据官方示例，查询时传递空的JSON对象
        request_data = {}

        try:
            logger.info(f"查询任务 - URL: {config.QUERY_URL}")
            logger.info(f"查询请求头: {headers}")
            logger.debug(f"查询请求数据: {request_data}")

            response = self.session.post(
                config.QUERY_URL,
                data=json.dumps(request_data),  # 使用data而不是json参数
                headers=headers,
                timeout=self.timeout
            )
            
            status_code = int(response.headers.get("X-Api-Status-Code", 0))
            message = response.headers.get("X-Api-Message", "Unknown error")
            
            # 解析结果
            result = None
            if status_code == 20000000 and response.content:
                try:
                    data = response.json()
                    if "result" in data:
                        result_data = data["result"]

                        # 处理audio_info
                        if "audio_info" in result_data and isinstance(result_data["audio_info"], dict):
                            from .models import AudioInfo
                            result_data["audio_info"] = AudioInfo(**result_data["audio_info"])

                        # 处理utterances
                        if "utterances" in result_data and isinstance(result_data["utterances"], list):
                            from .models import ASRUtterance
                            utterances = []
                            for utterance_data in result_data["utterances"]:
                                if isinstance(utterance_data, dict):
                                    utterances.append(ASRUtterance(**utterance_data))
                                else:
                                    utterances.append(utterance_data)
                            result_data["utterances"] = utterances

                        result = ASRResult(**result_data)
                except Exception as e:
                    logger.warning(f"Failed to parse result: {e}")
                    logger.debug(f"Raw response data: {data}")
            
            return TaskStatus(
                status_code=status_code,
                message=message,
                result=result
            )
            
        except requests.RequestException as e:
            raise APIError(f"Failed to query result: {str(e)}")
    
    def wait_for_result(
        self,
        task_id: str,
        timeout: int = 300,
        poll_interval: int = 2
    ) -> ASRResult:
        """
        等待识别完成并返回结果
        
        Args:
            task_id: 任务ID
            timeout: 超时时间（秒）
            poll_interval: 轮询间隔（秒）
            
        Returns:
            识别结果
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = self.get_result(task_id)
            
            if status.is_success:
                if status.result:
                    logger.info(f"Task completed: {task_id}")
                    return status.result
                else:
                    raise APIError("Task completed but no result returned")
            
            elif status.is_failed:
                self._handle_error(status.status_code, status.message)
            
            # 仍在处理中，等待
            logger.debug(f"Task {task_id} still processing: {status.message}")
            time.sleep(poll_interval)
        
        raise TimeoutError(f"Task {task_id} timeout after {timeout} seconds")

    def _validate_audio_url(self, url: str) -> bool:
        """验证音频URL的可访问性"""
        try:
            logger.info(f"验证音频URL可访问性: {url}")
            response = self.session.head(url, timeout=10)

            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                content_length = response.headers.get('content-length', '0')
                logger.info(f"URL验证成功 - 状态码: {response.status_code}, "
                           f"内容类型: {content_type}, 大小: {content_length} bytes")
                return True
            else:
                logger.warning(f"URL验证失败 - 状态码: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"URL验证异常: {str(e)}")
            # 如果HEAD请求失败，尝试GET请求的前几个字节
            try:
                logger.info("尝试GET请求验证URL...")
                response = self.session.get(url, timeout=10, stream=True)
                if response.status_code == 200:
                    # 只读取前1024字节来验证
                    next(response.iter_content(1024))
                    logger.info("GET请求验证成功")
                    return True
                else:
                    logger.warning(f"GET请求验证失败 - 状态码: {response.status_code}")
                    return False
            except Exception as e2:
                logger.error(f"GET请求验证也失败: {str(e2)}")
                return False

    def _handle_error(self, status_code: int, message: str):
        """处理错误"""
        exception_class = STATUS_CODE_EXCEPTIONS.get(status_code, APIError)
        raise exception_class(f"API Error {status_code}: {message}", status_code)
