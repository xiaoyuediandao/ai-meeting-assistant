"""
分块上传处理器
解决大文件上传的413错误问题
"""

import os
import uuid
import json
import logging
from flask import request, jsonify
from werkzeug.utils import secure_filename

logger = logging.getLogger(__name__)

class ChunkedUploadHandler:
    def __init__(self, upload_folder, max_file_size=500*1024*1024):
        self.upload_folder = upload_folder
        self.max_file_size = max_file_size
        self.allowed_extensions = {'mp3', 'wav', 'webm', 'ogg', 'raw', 'aiff', 'm4a'}
        
    def handle_upload(self):
        """处理文件上传"""
        try:
            # 检查是否有文件（支持多种字段名）
            file = None
            for field_name in ['audio_file', 'file']:
                if field_name in request.files:
                    file = request.files[field_name]
                    break

            if file is None:
                return self._error_response('没有上传文件', 400)
            if file.filename == '':
                return self._error_response('没有选择文件', 400)
            
            # 验证文件类型
            if not self._is_valid_file(file):
                return self._error_response(
                    f'不支持的文件格式。支持的格式：{", ".join(self.allowed_extensions)}', 
                    400
                )
            
            # 生成唯一文件名
            unique_filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
            file_path = os.path.join(self.upload_folder, unique_filename)
            
            # 分块保存文件
            try:
                self._save_file_chunked(file, file_path)
            except Exception as e:
                return self._error_response(f'文件保存失败: {str(e)}', 500)
            
            # 验证文件大小
            file_size = os.path.getsize(file_path)
            if file_size > self.max_file_size:
                os.remove(file_path)  # 删除过大的文件
                return self._error_response(
                    f'文件过大（{file_size // (1024*1024)}MB），最大支持 {self.max_file_size // (1024*1024)}MB',
                    413
                )
            
            # 生成文件URL - 使用可访问的URL
            # 注意：本地URL无法被外部API访问，需要使用云存储
            file_url = f"http://localhost:8080/uploads/{unique_filename}"
            
            return {
                'success': True,
                'file_path': file_path,
                'file_url': file_url,
                'file_size': file_size,
                'filename': unique_filename
            }
            
        except Exception as e:
            return self._error_response(f'上传处理失败: {str(e)}', 500)
    
    def _save_file_chunked(self, file, file_path, chunk_size=8192):
        """分块保存文件"""
        with open(file_path, 'wb') as f:
            while True:
                chunk = file.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
    
    def _is_valid_file(self, file):
        """验证文件类型"""
        if not file.filename:
            return False
        
        file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        return file_ext in self.allowed_extensions
    
    def _error_response(self, message, status_code):
        """生成错误响应"""
        return {
            'success': False,
            'error': message,
            'status_code': status_code
        }

def create_chunked_upload_route(app, upload_handler, asr_client, logger, storage_client=None):
    """创建分块上传路由"""
    
    @app.route('/api/upload_chunked', methods=['POST'])
    def upload_audio_chunked():
        """分块上传音频文件并提交识别任务"""
        try:
            # 处理文件上传
            upload_result = upload_handler.handle_upload()
            
            if not upload_result.get('success'):
                return jsonify(upload_result), upload_result.get('status_code', 500)
            
            # 获取配置
            config_str = request.form.get('config', '{}')
            try:
                config = json.loads(config_str)
            except:
                config = {}
            
            audio_format = request.form.get('format', 'wav')
            
            enable_itn = config.get('enable_itn', True)
            enable_punc = config.get('enable_punc', False)
            enable_speaker = config.get('enable_speaker', True)
            enable_dialect = config.get('enable_dialect', True)
            show_utterances = config.get('show_utterances', True)
            
            if not asr_client:
                # 清理上传的文件
                try:
                    os.remove(upload_result['file_path'])
                except:
                    pass
                return jsonify({
                    'success': False,
                    'error': 'ASR服务未初始化'
                }), 500
            
            logger.info(f"文件已保存到: {upload_result['file_path']}")
            logger.info(f"文件大小: {upload_result['file_size']} bytes")

            # 所有文件都尝试上传到云存储
            file_size_mb = upload_result['file_size'] / (1024 * 1024)
            final_url = upload_result['file_url']

            if storage_client:
                try:
                    logger.info(f"开始上传文件到云存储 ({file_size_mb:.1f}MB)...")
                    cloud_success, cloud_url, cloud_error = storage_client.upload_file(upload_result['file_path'])
                    if cloud_success:
                        logger.info(f"文件已成功上传到云存储: {cloud_url}")
                        final_url = cloud_url
                    else:
                        logger.warning(f"云存储上传失败: {cloud_error}")
                        # 清理上传的文件
                        try:
                            os.remove(upload_result['file_path'])
                        except:
                            pass
                        return jsonify({
                            'success': False,
                            'error': '云存储上传失败，无法处理音频文件。请联系管理员或使用演示模式。',
                            'suggestion': '您可以点击"演示模式"体验功能'
                        }), 503
                except Exception as e:
                    logger.warning(f"云存储上传异常: {e}")
                    # 清理上传的文件
                    try:
                        os.remove(upload_result['file_path'])
                    except:
                        pass
                    return jsonify({
                        'success': False,
                        'error': '云存储服务异常，无法处理音频文件。请联系管理员或使用演示模式。',
                        'suggestion': '您可以点击"演示模式"体验功能'
                    }), 503
            else:
                logger.warning(f"云存储不可用，本地文件无法被外部API访问")
                # 当云存储不可用时，返回错误而不是尝试使用本地URL
                return jsonify({
                    'success': False,
                    'error': '云存储服务不可用，无法处理音频文件。请联系管理员或使用演示模式。',
                    'suggestion': '您可以点击"演示模式"体验功能'
                }), 503

            try:
                # 提交会议音频任务
                task_id = asr_client.submit_meeting_audio(
                    audio_url=final_url,
                    audio_format=audio_format,
                    enable_speaker_separation=enable_speaker,
                    enable_dialect_support=enable_dialect,
                    enable_itn=enable_itn,
                    enable_punc=enable_punc,
                    show_utterances=show_utterances
                )
                
                logger.info(f"会议音频任务提交成功: {task_id}")
                
                return jsonify({
                    'success': True,
                    'task_id': task_id,
                    'file_url': final_url,
                    'file_size': upload_result['file_size'],
                    'storage_info': storage_client.get_storage_info() if storage_client else "本地存储",
                    'message': '文件上传成功，正在处理...'
                })
                
            except Exception as e:
                # 如果提交失败，删除已上传的文件
                try:
                    os.remove(upload_result['file_path'])
                except:
                    pass
                raise e
                
        except Exception as e:
            logger.error(f"分块上传失败: {e}")
            return jsonify({
                'success': False,
                'error': f'服务器错误: {str(e)}'
            }), 500
    
    return upload_audio_chunked
