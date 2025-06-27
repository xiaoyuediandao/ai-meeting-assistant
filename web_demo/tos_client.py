"""
火山引擎对象存储TOS客户端
用于上传音频文件到云存储
"""

import os
import uuid
import logging
import base64
from typing import Optional, Tuple
import tos

logger = logging.getLogger(__name__)


class TOSClient:
    """火山引擎TOS客户端"""

    def __init__(self, access_key_id=None, secret_access_key=None, region=None, bucket_name=None, endpoint=None):
        """初始化TOS客户端"""
        # 优先使用传入的参数，否则使用环境变量（向后兼容）
        self.access_key_id = access_key_id or os.getenv('TOS_ACCESS_KEY_ID')
        self.secret_access_key = secret_access_key or os.getenv('TOS_SECRET_ACCESS_KEY')
        self.region = region or os.getenv('TOS_REGION', 'cn-beijing')
        self.bucket_name = bucket_name or os.getenv('TOS_BUCKET_NAME', 'meetaudio')
        self.endpoint = endpoint or os.getenv('TOS_ENDPOINT', 'tos-cn-beijing.volces.com')

        if not self.access_key_id or not self.secret_access_key:
            raise ValueError("TOS配置不完整，请检查配置参数")

        # 尝试Base64解码Secret Key（如果需要的话）
        try:
            # 检查是否是Base64编码的
            if len(self.secret_access_key) > 40 and self.secret_access_key.isalnum():
                decoded_secret = base64.b64decode(self.secret_access_key).decode('utf-8')
                self.secret_access_key = decoded_secret
                logger.info("Secret Key已进行Base64解码")
        except Exception as e:
            logger.info(f"Secret Key无需Base64解码: {e}")

        logger.info("使用TOS配置参数初始化客户端")

        # 根据官方SDK示例初始化TOS客户端
        # 注意：endpoint不需要https://前缀
        self.client = tos.TosClientV2(
            ak=self.access_key_id,
            sk=self.secret_access_key,
            endpoint=self.endpoint,
            region=self.region
        )

        logger.info(f"TOS客户端初始化成功，区域: {self.region}, 存储桶: {self.bucket_name}")
        logger.info(f"Access Key ID: {self.access_key_id[:10]}... (长度: {len(self.access_key_id)})")
        logger.info(f"Secret Access Key: {self.secret_access_key[:10]}... (长度: {len(self.secret_access_key)})")
        logger.info(f"Endpoint: {self.endpoint}")

    def _is_base64(self, s: str) -> bool:
        """检查字符串是否为Base64编码"""
        try:
            # Base64字符串通常以=结尾，且长度是4的倍数
            if len(s) % 4 == 0 and s.endswith('='):
                base64.b64decode(s, validate=True)
                return True
            return False
        except Exception:
            return False

    def ensure_bucket_exists(self) -> bool:
        """确保存储桶存在并配置公共读取权限"""
        try:
            # 检查存储桶是否存在
            self.client.head_bucket(self.bucket_name)
            logger.info(f"存储桶 {self.bucket_name} 已存在")

            # 尝试设置公共读取权限
            try:
                self._configure_bucket_permissions()
                logger.info(f"存储桶 {self.bucket_name} 权限配置完成")
            except Exception as perm_error:
                logger.warning(f"配置存储桶权限失败: {perm_error}")

            return True
        except tos.exceptions.TosServerError as e:
            if e.status_code == 404:
                # 存储桶不存在，尝试创建
                try:
                    # 创建存储桶
                    self.client.create_bucket(
                        bucket=self.bucket_name
                    )
                    logger.info(f"存储桶 {self.bucket_name} 创建成功（公共读取）")

                    # 配置额外权限
                    try:
                        self._configure_bucket_permissions()
                        logger.info(f"存储桶 {self.bucket_name} 权限配置完成")
                    except Exception as perm_error:
                        logger.warning(f"配置存储桶权限失败: {perm_error}")

                    return True
                except Exception as create_error:
                    logger.error(f"创建存储桶失败: {create_error}")
                    return False
            else:
                logger.error(f"检查存储桶失败: {e}")
                return False
        except Exception as e:
            logger.error(f"存储桶操作失败: {e}")
            return False

    def _configure_bucket_permissions(self):
        """配置存储桶权限"""
        try:
            # 设置存储桶策略为公共读取
            import json
            policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid": "PublicReadGetObject",
                        "Effect": "Allow",
                        "Principal": "*",
                        "Action": "tos:GetObject",
                        "Resource": f"trn:tos:::{self.bucket_name}/*"
                    }
                ]
            }

            self.client.put_bucket_policy(
                bucket=self.bucket_name,
                policy=json.dumps(policy)
            )
            logger.info(f"存储桶 {self.bucket_name} 策略设置为公共读取")
        except Exception as e:
            logger.warning(f"设置存储桶策略失败: {e}")

        try:
            # 配置CORS规则
            from tos.models2 import CorsRule
            cors_rule = CorsRule(
                allowed_origins=['*'],
                allowed_methods=['GET', 'HEAD'],
                allowed_headers=['*'],
                max_age_seconds=3600
            )

            self.client.put_bucket_cors(
                bucket=self.bucket_name,
                cors_rules=[cors_rule]
            )
            logger.info(f"存储桶 {self.bucket_name} CORS规则配置完成")
        except Exception as e:
            logger.warning(f"配置CORS规则失败: {e}")
    
    def upload_file(self, file_path: str, object_key: Optional[str] = None) -> Tuple[bool, str, str]:
        """
        上传文件到TOS
        
        Args:
            file_path: 本地文件路径
            object_key: 对象键名，如果为None则自动生成
            
        Returns:
            (成功标志, 公开URL, 错误信息)
        """
        try:
            # 确保存储桶存在
            if not self.ensure_bucket_exists():
                return False, "", "存储桶不可用"
            
            # 生成对象键名
            if not object_key:
                file_name = os.path.basename(file_path)
                file_ext = os.path.splitext(file_name)[1]
                object_key = f"audio/{uuid.uuid4().hex}{file_ext}"
            
            # 上传文件
            logger.info(f"开始上传文件: {file_path} -> {object_key}")
            
            with open(file_path, 'rb') as f:
                self.client.put_object(
                    bucket=self.bucket_name,
                    key=object_key,
                    content=f,
                    content_type=self._get_content_type(file_path)
                )
            
            # 生成公开访问URL（使用正确的TOS URL格式）
            public_url = f"https://{self.bucket_name}.{self.endpoint}/{object_key}"
            
            logger.info(f"文件上传成功: {public_url}")
            return True, public_url, ""
            
        except Exception as e:
            error_msg = f"上传文件失败: {str(e)}"
            logger.error(error_msg)
            return False, "", error_msg
    
    def upload_file_content(self, file_content: bytes, file_name: str, content_type: str = None) -> Tuple[bool, str, str]:
        """
        上传文件内容到TOS
        
        Args:
            file_content: 文件内容
            file_name: 文件名
            content_type: 内容类型
            
        Returns:
            (成功标志, 公开URL, 错误信息)
        """
        try:
            # 确保存储桶存在
            if not self.ensure_bucket_exists():
                return False, "", "存储桶不可用"
            
            # 生成对象键名
            file_ext = os.path.splitext(file_name)[1]
            object_key = f"audio/{uuid.uuid4().hex}{file_ext}"
            
            # 确定内容类型
            if not content_type:
                content_type = self._get_content_type(file_name)
            
            # 上传文件内容
            logger.info(f"开始上传文件内容: {file_name} -> {object_key}")
            
            self.client.put_object(
                bucket=self.bucket_name,
                key=object_key,
                content=file_content,
                content_type=content_type
            )
            
            # 生成公开访问URL（使用正确的TOS URL格式）
            public_url = f"https://{self.bucket_name}.{self.endpoint}/{object_key}"
            
            logger.info(f"文件内容上传成功: {public_url}")
            return True, public_url, ""
            
        except Exception as e:
            error_msg = f"上传文件内容失败: {str(e)}"
            logger.error(error_msg)
            return False, "", error_msg
    
    def delete_file(self, object_key: str) -> bool:
        """
        删除TOS中的文件
        
        Args:
            object_key: 对象键名
            
        Returns:
            是否删除成功
        """
        try:
            self.client.delete_object(bucket=self.bucket_name, key=object_key)
            logger.info(f"文件删除成功: {object_key}")
            return True
        except Exception as e:
            logger.error(f"删除文件失败: {e}")
            return False
    
    def _get_content_type(self, file_path: str) -> str:
        """根据文件扩展名获取内容类型"""
        ext = os.path.splitext(file_path)[1].lower()
        content_types = {
            '.mp3': 'audio/mpeg',
            '.wav': 'audio/wav',
            '.ogg': 'audio/ogg',
            '.m4a': 'audio/mp4',
            '.aiff': 'audio/aiff',
            '.raw': 'audio/raw'
        }
        return content_types.get(ext, 'application/octet-stream')
    
    def test_connection(self) -> bool:
        """测试TOS连接"""
        try:
            # 列出存储桶来测试连接
            self.client.list_buckets()
            logger.info("TOS连接测试成功")
            return True
        except Exception as e:
            logger.error(f"TOS连接测试失败: {e}")
            return False


def create_tos_client(config=None, skip_test=False) -> Optional[TOSClient]:
    """创建TOS客户端实例"""
    try:
        if config:
            # 使用传入的配置
            client = TOSClient(
                access_key_id=config.get('tos_access_key'),
                secret_access_key=config.get('tos_secret_key'),
                region=config.get('tos_region', 'cn-beijing'),
                bucket_name=config.get('tos_bucket', 'meetaudio'),
                endpoint=config.get('tos_endpoint', 'tos-cn-beijing.volces.com')
            )
        else:
            # 向后兼容，使用环境变量
            client = TOSClient()

        # 如果跳过测试或者连接测试成功，返回客户端
        if skip_test:
            logger.info("跳过TOS连接测试，直接返回客户端")
            return client
        elif client.test_connection():
            return client
        else:
            logger.error("TOS客户端连接测试失败")
            return None
    except Exception as e:
        logger.error(f"创建TOS客户端失败: {e}")
        return None


if __name__ == '__main__':
    # 测试TOS客户端
    import sys
    
    logging.basicConfig(level=logging.INFO)
    
    print("🔧 测试火山引擎TOS客户端")
    print("="*50)
    
    client = create_tos_client()
    if client:
        print("✅ TOS客户端创建成功")
        
        # 测试上传一个小文件
        test_content = b"Hello, TOS!"
        success, url, error = client.upload_file_content(
            test_content, 
            "test.txt", 
            "text/plain"
        )
        
        if success:
            print(f"✅ 测试上传成功: {url}")
        else:
            print(f"❌ 测试上传失败: {error}")
    else:
        print("❌ TOS客户端创建失败")
        sys.exit(1)
