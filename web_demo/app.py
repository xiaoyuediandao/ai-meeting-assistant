#!/usr/bin/env python3
"""
Web演示后端API
"""

import os
import sys
import json
import uuid
import io
import time
import tempfile
from datetime import datetime
from flask import Flask, request, jsonify, render_template, send_from_directory, send_file, Response
from flask_cors import CORS
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
import logging
from chunked_upload import ChunkedUploadHandler, create_chunked_upload_route
from async_task_manager import task_manager, TaskStatus
from config_manager import config_manager

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from meetaudio import ByteDanceASRClient
from meetaudio.enhanced_client import MeetingASRClient, MeetingResult
from meetaudio.ai_writer import AIWriter
from meetaudio.document_generator import document_generator
from meetaudio.exceptions import ByteDanceASRError
from meetaudio.utils import setup_logging

app = Flask(__name__)
CORS(app)

# 配置上传文件夹
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# 设置合理的文件大小限制（500MB）
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024

# 确保上传文件夹存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 创建分块上传处理器
chunked_upload_handler = ChunkedUploadHandler(UPLOAD_FOLDER)

# 创建云存储客户端
storage_client = None
def init_storage_client():
    """初始化存储客户端"""
    global storage_client
    try:
        storage_config = config_manager.get_config("storage")
        if (storage_config.get("tos_access_key") and
            storage_config.get("tos_secret_key") and
            storage_config.get("tos_bucket")):
            # 使用TOS存储
            from tos_client import TOSClient
            storage_client = TOSClient(
                access_key_id=storage_config["tos_access_key"],
                secret_access_key=storage_config["tos_secret_key"],
                region=storage_config.get("tos_region", "cn-beijing"),
                bucket_name=storage_config["tos_bucket"],
                endpoint=storage_config.get("tos_endpoint", "tos-cn-beijing.volces.com")
            )
            logger.info("TOS存储客户端初始化成功")
        else:
            # 使用本地存储（不依赖ngrok）
            storage_client = None
            logger.info("使用本地HTTP存储（无云存储配置）")
    except Exception as e:
        logger.warning(f"存储客户端初始化失败: {e}，将使用本地HTTP存储")
        storage_client = None

# 存储客户端将在logger初始化后再初始化

# 设置日志
setup_logging("INFO")
logger = logging.getLogger(__name__)

# 初始化存储客户端（现在logger已经可用）
init_storage_client()

# 全局客户端实例
asr_client = None
ai_writer = None

def handle_generate_minutes_task(task_data, task):
    """处理会议纪要生成任务"""
    try:
        original_task_id = task_data['task_id']
        logger.info(f"开始异步生成会议纪要: {original_task_id}")

        # 更新任务进度
        task.progress = 10

        # 获取会议结果 - 查询ASR结果
        if not asr_client:
            raise Exception("ASR服务未初始化")

        # 使用原始的ASR任务ID（不是异步任务ID）
        meeting_result = asr_client.get_meeting_result(original_task_id)
        if not meeting_result:
            raise Exception(f"获取会议结果失败: 任务未完成或不存在")

        task.progress = 30

        # 生成会议纪要
        task.progress = 50
        logger.info(f"开始AI生成会议纪要: {original_task_id}")

        meeting_info = {
            'topic': '工作会议',
            'date': '2024年12月20日',
            'location': '公司会议室',
            'host': '党委书记',
            'attendees': ['总经理', '相关部门负责人']
        }

        logger.info(f"调用AI生成接口: {original_task_id}")

        # 添加超时和重试机制
        import time
        start_time = time.time()
        max_duration = 1000  # 最大允许16分钟

        try:
            minutes_data = ai_writer.generate_meeting_minutes(
                meeting_result=meeting_result,
                meeting_info=meeting_info
            )

            duration = time.time() - start_time
            logger.info(f"AI生成接口返回: {original_task_id}, 耗时: {duration:.2f}秒")

        except Exception as ai_error:
            duration = time.time() - start_time
            logger.error(f"AI生成失败: {original_task_id}, 耗时: {duration:.2f}秒, 错误: {ai_error}")

            # 如果是超时或网络错误，提供更友好的错误信息
            error_msg = str(ai_error)
            if "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                raise Exception(f"AI生成超时，请稍后重试。耗时: {duration:.1f}秒")
            elif "connection" in error_msg.lower() or "network" in error_msg.lower():
                raise Exception(f"网络连接问题，请检查网络后重试。错误: {error_msg}")
            elif "不适当" in error_msg or "不相关" in error_msg:
                raise Exception(f"录音内容可能不适合生成会议纪要，请检查录音质量和内容。")
            else:
                raise Exception(f"AI生成失败: {error_msg}")

        if not minutes_data:
            raise Exception("AI生成返回空结果，请重试")

        task.progress = 90
        logger.info(f"会议纪要生成完成: {original_task_id}")

        # 返回结果
        result = {
            'success': True,
            'task_id': original_task_id,
            'minutes_data': minutes_data,
            'message': '会议纪要生成成功'
        }

        task.progress = 100
        return result

    except Exception as e:
        logger.error(f"异步生成会议纪要失败: {e}")
        raise e

def init_clients():
    """初始化客户端"""
    global asr_client, ai_writer
    try:
        # 检查配置是否完整
        missing_configs = config_manager.get_missing_configs()
        if missing_configs:
            logger.warning(f"配置不完整，缺少: {', '.join(missing_configs)}")
            # 即使配置不完整也继续初始化，但会在使用时提示用户配置

        # 获取配置
        asr_config = config_manager.get_config("asr")
        ai_config = config_manager.get_config("ai")

        # 初始化会议ASR客户端
        if asr_config.get("asr_app_key") and asr_config.get("asr_access_key"):
            asr_client = MeetingASRClient(
                app_key=asr_config["asr_app_key"],
                access_key=asr_config["asr_access_key"]
            )
            logger.info("会议ASR客户端初始化成功")
        else:
            logger.warning("ASR配置不完整，ASR客户端未初始化")

        # 初始化AI撰稿引擎
        if ai_config.get("ark_api_key"):
            ai_writer = AIWriter(
                api_key=ai_config["ark_api_key"],
                model=ai_config.get("ark_model", "ep-20250618123643-dtts7"),
                base_url=ai_config.get("ark_base_url", "https://ark.cn-beijing.volces.com/api/v3"),
                timeout=ai_config.get("ark_timeout", 300)
            )
            logger.info("AI撰稿引擎初始化成功")
        else:
            logger.warning("AI配置不完整，AI撰稿引擎未初始化")

        # 启动异步任务管理器
        task_manager.register_handler("generate_minutes", handle_generate_minutes_task)
        task_manager.start()
        logger.info("异步任务管理器启动成功")

        return True
    except Exception as e:
        logger.error(f"客户端初始化失败: {e}")
        return False

def reinitialize_clients_for_section(section):
    """根据配置段重新初始化相应的客户端"""
    global asr_client, ai_writer
    result = {}

    try:
        if section == 'ai':
            # 重新初始化AI客户端
            ai_config = config_manager.get_config("ai")
            if ai_config.get("ark_api_key"):
                ai_writer = AIWriter(
                    api_key=ai_config["ark_api_key"],
                    model=ai_config.get("ark_model", "ep-20250618123643-dtts7"),
                    base_url=ai_config.get("ark_base_url", "https://ark.cn-beijing.volces.com/api/v3"),
                    timeout=ai_config.get("ark_timeout", 300)
                )
                logger.info("AI撰稿引擎重新初始化成功")
                result['ai'] = 'success'
            else:
                ai_writer = None
                logger.warning("AI配置不完整，AI客户端已清空")
                result['ai'] = 'cleared'

        elif section == 'asr':
            # 重新初始化ASR客户端
            asr_config = config_manager.get_config("asr")
            if asr_config.get("asr_app_key") and asr_config.get("asr_access_key"):
                asr_client = MeetingASRClient(
                    app_key=asr_config["asr_app_key"],
                    access_key=asr_config["asr_access_key"]
                )
                logger.info("ASR客户端重新初始化成功")
                result['asr'] = 'success'
            else:
                asr_client = None
                logger.warning("ASR配置不完整，ASR客户端已清空")
                result['asr'] = 'cleared'

        elif section == 'storage':
            # 存储配置更新，重新创建存储客户端
            init_storage_client()
            result['storage'] = 'success'

        return result

    except Exception as e:
        logger.error(f"重新初始化客户端失败 ({section}): {e}")
        result[section] = f'error: {str(e)}'
        return result

@app.route('/')
def index():
    """主页"""
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def static_files(filename):
    """静态文件服务"""
    response = send_from_directory('.', filename)

    # 对JavaScript和CSS文件添加缓存控制
    if filename.endswith(('.js', '.css')):
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'

    return response

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """提供上传的文件"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/api/status')
def api_status():
    """API状态检查"""
    # 检查配置状态
    config_status = config_manager.is_configured()
    missing_configs = config_manager.get_missing_configs()

    return jsonify({
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "config_status": config_status,
        "missing_configs": missing_configs,
        "ready": len(missing_configs) == 0
    })


@app.route('/api/submit', methods=['POST'])
def submit_audio():
    """提交音频识别任务（URL方式）"""
    try:
        data = request.get_json()

        if not data or 'audio_url' not in data:
            return jsonify({
                'success': False,
                'error': '缺少音频URL'
            }), 400

        audio_url = data['audio_url']
        audio_format = data.get('format', 'mp3')

        # 配置选项
        config = data.get('config', {})
        enable_itn = config.get('enable_itn', True)
        enable_punc = config.get('enable_punc', False)
        enable_speaker = config.get('enable_speaker', True)  # 会议场景默认开启
        enable_dialect = config.get('enable_dialect', True)
        show_utterances = config.get('show_utterances', True)

        if not asr_client:
            missing_configs = config_manager.get_missing_configs()
            if missing_configs:
                return jsonify({
                    'success': False,
                    'error': f'系统配置不完整，请先配置: {", ".join(missing_configs)}',
                    'missing_configs': missing_configs,
                    'need_config': True
                }), 400
            else:
                return jsonify({
                    'success': False,
                    'error': 'ASR服务未初始化，请重启应用'
                }), 500

        # 提交会议音频任务
        task_id = asr_client.submit_meeting_audio(
            audio_url=audio_url,
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
            'task_id': task_id
        })

    except ByteDanceASRError as e:
        logger.error(f"ASR API错误: {e.message}")
        return jsonify({
            'success': False,
            'error': f'ASR API错误: {e.message}',
            'error_code': e.status_code
        }), 400

    except Exception as e:
        logger.error(f"提交任务失败: {e}")
        return jsonify({
            'success': False,
            'error': f'服务器错误: {str(e)}'
        }), 500

@app.route('/api/upload', methods=['POST'])
def upload_audio():
    """上传音频文件并提交识别任务"""
    try:
        # 使用分块上传处理器
        upload_result = chunked_upload_handler.handle_upload()

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

        # 尝试使用云存储上传文件，失败时使用本地HTTP URL
        final_url = None

        if storage_client:
            try:
                cloud_success, cloud_url, cloud_error = storage_client.upload_file(upload_result['file_path'])
                if cloud_success:
                    logger.info(f"文件已上传到云存储: {cloud_url}")
                    final_url = cloud_url
                else:
                    logger.warning(f"云存储上传失败: {cloud_error}，使用本地HTTP URL")
            except Exception as e:
                logger.warning(f"云存储上传异常: {e}，使用本地HTTP URL")

        # 如果云存储失败，生成本地HTTP URL
        if not final_url:
            filename = os.path.basename(upload_result['file_path'])
            # 生成可访问的HTTP URL
            final_url = f"http://localhost:8080/uploads/{filename}"
            logger.info(f"使用本地HTTP URL: {final_url}")

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
                'storage_info': 'TOS云存储' if storage_client else '本地HTTP存储',
                'message': '文件上传成功，正在处理...'
            })

        except Exception as e:
            # 如果提交失败，删除已上传的文件
            try:
                os.remove(upload_result['file_path'])
            except:
                pass
            raise e

    except ByteDanceASRError as e:
        logger.error(f"ASR API错误: {e.message}")
        return jsonify({
            'success': False,
            'error': f'ASR API错误: {e.message}',
            'error_code': e.status_code
        }), 400

    except Exception as e:
        logger.error(f"上传文件失败: {e}")
        return jsonify({
            'success': False,
            'error': f'服务器错误: {str(e)}'
        }), 500

# 注意：演示模式已移除，现在只支持真实音频处理和现场录音

def create_mock_meeting_result(demo_data):
    """创建模拟的会议结果对象"""
    from meetaudio.enhanced_client import MeetingResult
    from meetaudio.models import ASRUtterance

    # 创建模拟的话语列表
    utterances = []
    for utt_data in demo_data['result']['utterances']:
        utterance = ASRUtterance(
            text=utt_data['text'],
            start_time=int(utt_data['start_time'] * 1000),  # 转换为毫秒
            end_time=int(utt_data['end_time'] * 1000),      # 转换为毫秒
            speaker_id=utt_data['speaker_id']
        )
        utterances.append(utterance)

    # 创建模拟的会议结果
    meeting_result = MeetingResult(
        full_text=demo_data['result']['text'],
        utterances=utterances,
        duration=demo_data['result']['audio_info']['duration']
    )

    return meeting_result

def generate_comprehensive_meeting_summary():
    """生成详细的会议摘要"""
    return """
## 会议背景与目的

根据公司年度工作安排和上级部署要求，为深入贯彻落实相关决策精神，统筹推进第四季度各项重点工作，确保完成年度目标任务，公司于2024年12月18日下午召开第四季度工作推进会议。

## 会议主要内容

### 一、前期工作总结

会议首先由党委书记对前三季度工作进行了全面总结。在市场拓展方面，公司成功开拓了三个新的区域市场，客户数量实现了25%的增长，为公司业务发展奠定了坚实基础。在产品研发方面，技术团队克服困难，推出了两款具有市场竞争力的新产品，获得了良好的市场反响和客户认可。

### 二、重点工作部署

**安全生产工作**：安全部长强调，安全生产是企业发展的生命线，必须始终把安全放在第一位。各部门要严格执行安全操作规程，建立健全安全责任制，确保不发生任何安全事故。要定期开展安全检查，及时消除安全隐患。

**运营管理优化**：运营总监提出，要继续优化业务流程，提高工作效率。通过数字化手段改进管理方式，加强成本控制，确保各项经营指标达到预期目标。要建立科学的绩效考核体系，激发员工工作积极性。

**人力资源建设**：人事部长汇报了人才队伍建设情况。计划在第四季度招聘50名新员工，充实各部门人员力量。同时要加强现有员工的培训工作，提升专业技能和综合素质，为公司发展提供人才保障。

**财务管理工作**：财务总监分析了前三季度财务状况。营收增长18%，利润率保持稳定，财务状况良好。第四季度要继续保持这个良好势头，加强预算管理，提高资金使用效率。

### 三、领导讲话要点

总经理在会议最后强调了几个重点：第一，各部门要加强协调配合，形成工作合力；第二，要严格按照时间节点完成各项任务，确保工作质量；第三，要建立定期汇报机制，及时反馈工作进展情况。

## 会议成果

通过本次会议，与会人员统一了思想认识，明确了工作目标和任务，为第四季度各项工作的顺利开展奠定了基础。会议形成了多项重要决议，制定了具体的行动计划，确保各项工作能够落到实处。
"""

def generate_detailed_minutes_data(demo_data, meeting_info):
    """生成详细的会议纪要数据（降级处理）"""
    return {
        'title': f"{meeting_info.get('topic', '工作会议')}纪要",
        'header': {
            'meeting_name': meeting_info.get('topic', '工作会议'),
            'date': meeting_info.get('date', '2024年12月18日'),
            'time': meeting_info.get('time', ''),
            'location': meeting_info.get('location', ''),
            'host': meeting_info.get('host', '党委书记'),
            'attendees': meeting_info.get('attendees', ['总经理', '相关部门负责人']),
            'recorder': meeting_info.get('recorder', '办公室')
        },
        'content': {
            'summary': generate_comprehensive_meeting_summary(),
            'decisions': [
                '决定加强安全生产管理，建立健全安全责任制，确保各项安全措施落实到位，坚决防范各类安全事故发生',
                '同意财务预算调整方案，优化资源配置，加强成本控制，确保资金使用效率和效益最大化',
                '批准人力资源建设计划，加快人才引进步伐，完善培训体系，提升员工综合素质和专业能力',
                '通过运营管理优化方案，简化工作流程，提高工作效率，建立科学的绩效考核机制',
                '决定建立定期会议制度，加强部门间沟通协调，及时解决工作中遇到的问题和困难'
            ],
            'action_items': [
                '安全部门要立即组织开展全面的安全隐患排查，建立安全管理台账，制定整改措施和时间表，确保隐患及时消除',
                '财务部门要加强预算执行监控，建立月度财务分析报告制度，及时发现和报告财务异常情况',
                '人事部门要制定详细的招聘计划和培训方案，建立人才储备库，完善员工职业发展通道',
                '运营部门要梳理现有工作流程，识别效率瓶颈，制定流程优化方案，提高整体运营效率',
                '各部门要建立工作台账，明确责任人和完成时限，定期汇报工作进展情况'
            ],
            'next_steps': [
                '下周一召开专题会议，深入讨论各项工作的具体实施细节和推进计划',
                '本月底前完成各项整改工作，确保工作质量和进度符合要求',
                '建立周报制度，各部门每周五前提交工作进展报告，及时跟踪任务完成情况',
                '下月初组织工作检查，对各部门工作落实情况进行全面评估和考核',
                '建立问题反馈机制，及时收集和解决工作中遇到的新问题'
            ],
            'leadership_remarks': {
                '党委书记': '同志们，今天的会议非常重要。我们要深刻认识当前工作的重要性和紧迫性，提高政治站位，统一思想认识。各部门要切实履行职责，确保各项工作落到实处，为公司持续健康发展提供坚强保障。我们要以更加务实的作风、更加有力的措施，推动各项工作取得新成效。',
                '总经理': '各位同事，通过今天的讨论，我们明确了下一步的工作重点和方向。我要求各部门负责人要高度重视，加强组织领导，确保责任到人、措施到位。要建立健全工作机制，加强部门间协调配合，形成工作合力。我们要以时不我待的紧迫感，确保完成年度目标任务，推动公司实现高质量发展。'
            }
        },
        'footer': {
            'recorder': meeting_info.get('recorder', '办公室'),
            'review_date': '2024年12月18日'
        }
    }

@app.route('/api/query/<task_id>', methods=['GET'])
def query_result(task_id):
    """查询识别结果"""
    try:
        if not asr_client:
            return jsonify({
                'success': False,
                'error': 'ASR服务未初始化'
            }), 500

        # 查询结果，增加重试机制
        logger.info(f"开始查询任务结果: {task_id}")

        max_retries = 3
        retry_delay = 3  # 秒
        status = None

        for attempt in range(max_retries):
            try:
                logger.info(f"查询任务 {task_id}，第 {attempt + 1} 次尝试")
                status = asr_client.get_result(task_id)
                logger.info(f"查询完成，状态: {status.status_code}, 消息: {status.message}")

                # 如果不是"任务不存在"错误，直接返回结果
                if status.status_code != 45000000 or "cannot find task" not in status.message:
                    break

                # 如果是"任务不存在"且还有重试机会，等待后重试
                if attempt < max_retries - 1:
                    logger.warning(f"任务 {task_id} 暂时不存在，{retry_delay}秒后重试...")
                    time.sleep(retry_delay)
                    continue

            except Exception as e:
                logger.error(f"查询任务异常 (尝试 {attempt + 1}): {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                else:
                    raise

        # 检查是否是"任务不存在"错误
        if status and status.status_code == 45000000 and "cannot find task" in status.message:
            logger.warning(f"任务不存在: {task_id}，可能是API处理延迟或URL访问问题")
            return jsonify({
                'success': False,
                'error': '任务不存在或已过期',
                'error_code': status.status_code,
                'message': status.message,
                'suggestion': '请稍后重试，或检查音频文件URL是否可以被远程API访问'
            }), 404

        response_data = {
            'success': True,
            'status_code': status.status_code,
            'message': status.message,
            'is_success': status.is_success,
            'is_processing': status.is_processing,
            'is_failed': status.is_failed
        }

        if status.result:
            response_data['result'] = {
                'text': status.result.text,
                'audio_info': status.result.audio_info.model_dump() if status.result.audio_info else None,
                'utterances': [u.model_dump() for u in status.result.utterances] if status.result.utterances else None
            }

        return jsonify(response_data)

    except ByteDanceASRError as e:
        logger.error(f"查询结果失败: {e.message}")
        return jsonify({
            'success': False,
            'error': f'ASR API错误: {e.message}',
            'error_code': e.status_code
        }), 400

    except Exception as e:
        logger.error(f"查询结果失败: {e}")
        return jsonify({
            'success': False,
            'error': f'服务器错误: {str(e)}'
        }), 500

@app.route('/api/wait/<task_id>', methods=['GET'])
def wait_for_result(task_id):
    """等待识别完成（长轮询）"""
    try:
        timeout = request.args.get('timeout', 1800, type=int)  # 默认30分钟

        if not asr_client:
            return jsonify({
                'success': False,
                'error': 'ASR服务未初始化'
            }), 500

        logger.info(f"开始长轮询等待任务: {task_id}, 超时: {timeout}秒")

        # 等待结果
        result = asr_client.wait_for_result(task_id, timeout=timeout)

        response_data = {
            'success': True,
            'result': {
                'text': result.text,
                'audio_info': result.audio_info.model_dump() if result.audio_info else None,
                'utterances': [u.model_dump() for u in result.utterances] if result.utterances else None
            }
        }

        logger.info(f"长轮询完成: {task_id}")
        return jsonify(response_data)

    except Exception as e:
        logger.error(f"长轮询等待失败: {e}")

        # 提供更详细的错误信息
        error_msg = str(e)
        if "audio download failed" in error_msg:
            error_msg = "音频文件下载失败，请检查文件是否可访问或重新上传"
        elif "Invalid audio URI" in error_msg:
            error_msg = "音频文件URL无效，请重新上传文件"

        return jsonify({
            'success': False,
            'error': error_msg,
            'task_id': task_id,
            'details': str(e)
        }), 408

@app.route('/api/generate_minutes/<task_id>', methods=['POST'])
def generate_meeting_minutes(task_id):
    """异步生成会议纪要 - 提交任务"""
    try:
        data = request.get_json() or {}

        if not asr_client or not ai_writer:
            missing_configs = config_manager.get_missing_configs()
            if missing_configs:
                return jsonify({
                    'success': False,
                    'error': f'系统配置不完整，请先配置: {", ".join(missing_configs)}',
                    'missing_configs': missing_configs,
                    'need_config': True
                }), 400
            else:
                return jsonify({
                    'success': False,
                    'error': '服务未初始化，请重启应用'
                }), 500

        logger.info(f"提交异步会议纪要生成任务: {task_id}")

        # 准备任务数据
        task_data = {
            'task_id': task_id,
            'meeting_info': {
                'topic': data.get('topic', '工作会议'),
                'date': data.get('date', '2024年12月20日'),
                'time': data.get('time', ''),
                'location': data.get('location', ''),
                'host': data.get('host', '党委书记'),
                'attendees': data.get('attendees', ['总经理', '相关部门负责人']),
                'recorder': data.get('recorder', '办公室')
            },
            'options': {
                'focus_last_speakers': data.get('focus_last_speakers', True),
                'speaker_count': data.get('speaker_count', 2)
            }
        }

        # 提交异步任务
        async_task_id = task_manager.submit_task("generate_minutes", task_data, f"minutes_{task_id}")

        logger.info(f"异步任务已提交: {async_task_id}")

        return jsonify({
            'success': True,
            'async_task_id': async_task_id,
            'message': '会议纪要生成任务已提交，请使用async_task_id查询进度'
        })

    except Exception as e:
        logger.error(f"提交会议纪要生成任务失败: {e}")
        return jsonify({
            'success': False,
            'error': f'提交失败: {str(e)}'
        }), 500

@app.route('/api/async_task/<async_task_id>', methods=['GET'])
def get_async_task_status(async_task_id):
    """查询异步任务状态"""
    try:
        task_status = task_manager.get_task_status(async_task_id)

        if not task_status:
            return jsonify({
                'success': False,
                'error': '任务不存在'
            }), 404

        return jsonify({
            'success': True,
            'task_status': task_status
        })

    except Exception as e:
        logger.error(f"查询异步任务状态失败: {e}")
        return jsonify({
            'success': False,
            'error': f'查询失败: {str(e)}'
        }), 500

@app.route('/api/async_task/<async_task_id>/result', methods=['GET'])
def get_async_task_result(async_task_id):
    """获取异步任务结果"""
    try:
        task_result = task_manager.get_task_result(async_task_id)

        if task_result is None:
            task_status = task_manager.get_task_status(async_task_id)
            if not task_status:
                return jsonify({
                    'success': False,
                    'error': '任务不存在'
                }), 404
            elif task_status['status'] in ['pending', 'running']:
                return jsonify({
                    'success': False,
                    'error': '任务尚未完成',
                    'status': task_status['status'],
                    'progress': task_status['progress']
                }), 202
            else:
                return jsonify({
                    'success': False,
                    'error': '任务失败或无结果',
                    'task_error': task_status.get('error')
                }), 500

        return jsonify(task_result)

    except Exception as e:
        logger.error(f"获取异步任务结果失败: {e}")
        return jsonify({
            'success': False,
            'error': f'获取失败: {str(e)}'
        }), 500



@app.route('/api/enhance_content', methods=['POST'])
def enhance_content():
    """AI内容增强"""
    try:
        data = request.get_json()

        if not data or 'text' not in data:
            return jsonify({
                'success': False,
                'error': '缺少文本内容'
            }), 400

        text = data['text']
        enhancement_type = data.get('type', 'optimize')  # expand/rewrite/optimize

        if not ai_writer:
            return jsonify({
                'success': False,
                'error': 'AI服务未初始化'
            }), 500

        enhanced_text = ai_writer.enhance_content(text, enhancement_type)

        return jsonify({
            'success': True,
            'enhanced_text': enhanced_text,
            'original_text': text,
            'enhancement_type': enhancement_type
        })

    except Exception as e:
        logger.error(f"内容增强失败: {e}")
        return jsonify({
            'success': False,
            'error': f'增强失败: {str(e)}'
        }), 500

@app.route('/api/ai_text_process', methods=['POST'])
def ai_text_process():
    """AI文本处理 - 用于文本选择工具栏"""
    try:
        data = request.get_json()

        prompt = data.get('prompt', '')
        action = data.get('action', '')
        original_text = data.get('original_text', '')

        if not prompt or not original_text:
            return jsonify({
                'success': False,
                'error': '提示词和原始文本不能为空'
            }), 400

        logger.info(f"AI文本处理请求 - 动作: {action}, 文本长度: {len(original_text)}")

        # 直接从配置管理器获取AI配置
        ai_config = config_manager.get_config("ai")
        if not ai_config:
            return jsonify({
                'success': False,
                'error': 'AI配置未找到'
            }), 500

        ark_api_key = ai_config.get("ark_api_key", "")
        ark_model = ai_config.get("ark_model", "ep-20250618123643-dtts7")
        ark_base_url = ai_config.get("ark_base_url", "https://ark.cn-beijing.volces.com/api/v3")

        logger.info(f"配置检查 - API Key长度: {len(ark_api_key)}, Model: {ark_model}, Base URL: {ark_base_url}")

        if not ark_api_key:
            return jsonify({
                'success': False,
                'error': 'API密钥未配置'
            }), 500

        # 调用AI服务进行文本处理
        try:
            # 直接创建OpenAI客户端，使用配置中的参数
            import openai

            client = openai.OpenAI(
                api_key=ark_api_key,
                base_url=ark_base_url,
                timeout=60
            )

            response = client.chat.completions.create(
                model=ark_model,
                messages=[
                    {"role": "system", "content": "你是一个专业的文本处理助手。请根据用户的要求处理文本，直接返回处理后的结果，不要包含任何解释或说明。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000,
                timeout=60
            )

            processed_text = response.choices[0].message.content.strip()

            logger.info(f"AI文本处理成功 - 动作: {action}")

            return jsonify({
                'success': True,
                'processed_text': processed_text,
                'original_text': original_text,
                'action': action
            })

        except Exception as ai_error:
            logger.error(f"AI处理失败: {str(ai_error)}")
            return jsonify({
                'success': False,
                'error': f'AI处理失败: {str(ai_error)}'
            }), 500

    except Exception as e:
        logger.error(f"AI文本处理失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'处理失败: {str(e)}'
        }), 500

# 旧的Word下载API已删除，使用新的异步任务版本 /api/download_word/<async_task_id>

@app.route('/api/optimize_prompt', methods=['POST'])
def optimize_prompt():
    """AI优化提示词配置"""
    try:
        data = request.get_json()
        user_requirement = data.get('user_requirement', '').strip()

        if not user_requirement:
            return jsonify({
                'success': False,
                'error': '请描述您的会议纪要需求'
            }), 400

        logger.info(f"AI提示词优化请求 - 需求描述长度: {len(user_requirement)}")

        # 获取AI配置
        ai_config = config_manager.get_config("ai")
        if not ai_config:
            return jsonify({
                'success': False,
                'error': 'AI配置未找到'
            }), 500

        ark_api_key = ai_config.get("ark_api_key", "")
        ark_model = ai_config.get("ark_model", "ep-20250618123643-dtts7")
        ark_base_url = ai_config.get("ark_base_url", "https://ark.cn-beijing.volces.com/api/v3")

        if not ark_api_key:
            return jsonify({
                'success': False,
                'error': 'API密钥未配置'
            }), 500

        # 构建优化提示词的系统提示
        optimization_prompt = f"""你是一个专业的会议纪要生成系统配置专家。用户将描述他们的会议纪要需求，你需要根据需求生成专业的系统提示词和相关的行业术语词汇表。

用户需求：{user_requirement}

请参考以下现有的提示词模板结构，生成适合用户需求的配置：

现有模板参考：
系统提示词示例：
"你是一个专业的会议纪要生成助手。请根据提供的会议录音转录内容，生成规范的会议纪要。

要求：
1. 提取会议的关键信息和决策要点
2. 整理发言人的主要观点和建议
3. 突出重要的行动项和后续安排
4. 使用专业、简洁的语言
5. 保持客观中性的表述
6. 将口语化表达转换为书面语
7. 根据提供的行业术语词汇表，将相关术语标准化"

行业术语示例：
"塔台 - 控制塔
跑道 - 起降跑道
航班 - 航班号
机长 - 飞行员
副驾驶 - 副飞行员"

请根据用户的具体需求，生成定制化的配置。直接返回JSON格式的结果，包含system_prompt和glossary两个字段。不要包含任何解释或说明。

JSON格式示例：
{{
    "system_prompt": "定制的系统提示词内容...",
    "glossary": "相关的行业术语词汇表，每行一个术语..."
}}"""

        try:
            import openai

            client = openai.OpenAI(
                api_key=ark_api_key,
                base_url=ark_base_url,
                timeout=120
            )

            response = client.chat.completions.create(
                model=ark_model,
                messages=[
                    {"role": "system", "content": "你是一个专业的会议纪要系统配置专家，擅长根据用户需求生成专业的提示词配置。"},
                    {"role": "user", "content": optimization_prompt}
                ],
                temperature=0.3,
                max_tokens=3000,
                timeout=120
            )

            ai_response = response.choices[0].message.content.strip()
            logger.info(f"AI优化响应长度: {len(ai_response)}")

            # 尝试解析JSON响应
            try:
                import json
                # 提取JSON部分（如果AI返回了额外的文本）
                json_start = ai_response.find('{')
                json_end = ai_response.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = ai_response[json_start:json_end]
                    result = json.loads(json_str)

                    system_prompt = result.get('system_prompt', '')
                    glossary = result.get('glossary', '')

                    if system_prompt:
                        logger.info("AI提示词优化成功")
                        return jsonify({
                            'success': True,
                            'system_prompt': system_prompt,
                            'glossary': glossary
                        })
                    else:
                        raise ValueError("生成的提示词为空")

                else:
                    raise ValueError("无法解析AI响应中的JSON")

            except (json.JSONDecodeError, ValueError) as parse_error:
                logger.warning(f"JSON解析失败，尝试文本解析: {parse_error}")

                # 如果JSON解析失败，尝试从文本中提取内容
                lines = ai_response.split('\n')
                system_prompt = ""
                glossary = ""
                current_section = None

                for line in lines:
                    line = line.strip()
                    if '系统提示词' in line or 'system_prompt' in line.lower():
                        current_section = 'system'
                        continue
                    elif '术语' in line or 'glossary' in line.lower():
                        current_section = 'glossary'
                        continue
                    elif line and not line.startswith('{') and not line.startswith('}'):
                        if current_section == 'system':
                            system_prompt += line + '\n'
                        elif current_section == 'glossary':
                            glossary += line + '\n'

                if system_prompt.strip():
                    return jsonify({
                        'success': True,
                        'system_prompt': system_prompt.strip(),
                        'glossary': glossary.strip()
                    })
                else:
                    # 如果都失败了，返回原始响应作为系统提示词
                    return jsonify({
                        'success': True,
                        'system_prompt': ai_response,
                        'glossary': ''
                    })

        except Exception as ai_error:
            logger.error(f"AI优化失败: {str(ai_error)}")
            return jsonify({
                'success': False,
                'error': f'AI优化失败: {str(ai_error)}'
            }), 500

    except Exception as e:
        logger.error(f"提示词优化失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'优化失败: {str(e)}'
        }), 500


@app.route('/api/tasks', methods=['GET'])
def list_tasks():
    """列出所有任务状态"""
    try:
        # 这里可以添加任务历史记录功能
        # 目前返回空列表，可以后续扩展
        tasks = []

        return jsonify({
            'success': True,
            'tasks': tasks,
            'total': len(tasks)
        })
    except Exception as e:
        logger.error(f"获取任务列表失败: {e}")
        return jsonify({
            'success': False,
            'error': f'获取失败: {str(e)}'
        }), 500

@app.route('/api/status', methods=['GET'])
def get_status():
    """获取服务状态"""
    return jsonify({
        'success': True,
        'service': 'AI+会议助手系统',
        'asr_client_initialized': asr_client is not None,
        'ai_writer_initialized': ai_writer is not None,
        'storage_info': 'TOS云存储' if storage_client else '本地HTTP存储',
        'storage_test': storage_client.test_connection() if storage_client else True,
        'version': '2.0.0'
    })

@app.route('/api/clear_frontend_state', methods=['POST'])
def clear_frontend_state():
    """清除前端状态 - 用于解决卡住的任务查询"""
    return jsonify({
        'success': True,
        'message': '前端状态已清除，请刷新页面',
        'action': 'reload_page'
    })

@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({
        'success': False,
        'error': f'文件过大，最大支持 {app.config["MAX_CONTENT_LENGTH"] // (1024*1024)}MB'
    }), 413

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': '接口不存在'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': '服务器内部错误'
    }), 500

if __name__ == '__main__':
    print("🚀 启动火山引擎语音识别Web演示")
    print("="*50)

    # 初始化客户端
    if init_clients():
        print("✅ 客户端初始化成功")
    else:
        print("❌ 客户端初始化失败，请检查配置")
        print("💡 请确保设置了正确的环境变量:")
        print("   BYTEDANCE_APP_KEY=your_app_key")
        print("   BYTEDANCE_ACCESS_KEY=your_access_key")
        print("   ARK_API_KEY=your_ark_api_key")
        print("   ARK_MODEL=your_model_endpoint")

    print("\n🌐 Web服务启动中...")
    print("📱 访问地址: http://localhost:8080")
    print("🔧 API文档:")
    print("   POST /api/submit - 提交识别任务")
    print("   POST /api/upload - 上传文件识别")
    print("   GET  /api/query/<task_id> - 查询结果")
    print("   GET  /api/wait/<task_id> - 等待完成")
    print("   GET  /api/status - 服务状态")
    print("💾 文件上传限制: 100MB")
    print("\n按 Ctrl+C 停止服务")
    print("="*50)

    # 使用Gunicorn或其他WSGI服务器来处理大文件上传
    try:
        import gunicorn
        print("🔧 建议使用 Gunicorn 启动以支持大文件上传:")
        print("   gunicorn -w 1 -b 0.0.0.0:8080 --timeout 300 --max-requests-jitter 100 app:app")
    except ImportError:
        pass

# ==================== Word下载API ====================

@app.route('/api/download_word/<task_id>', methods=['GET'])
def download_word_minutes(task_id):
    """下载Word格式的会议纪要"""
    try:
        logger.info(f"开始下载Word文档，任务ID: {task_id}")

        # 检查是否是异步任务ID（以minutes_开头）
        if task_id.startswith('minutes_'):
            # 这是异步任务ID，直接使用
            async_task_id = task_id
        else:
            # 这是原始任务ID，需要构造异步任务ID
            async_task_id = f"minutes_{task_id}"

        logger.info(f"使用异步任务ID: {async_task_id}")

        # 获取异步任务状态
        task_status = task_manager.get_task_status(async_task_id)
        if not task_status:
            logger.error(f"任务不存在: {async_task_id}")
            return jsonify({
                'success': False,
                'error': '任务不存在'
            }), 404

        logger.info(f"任务状态: {task_status['status']}")
        if task_status['status'] != 'completed':
            return jsonify({
                'success': False,
                'error': '任务尚未完成'
            }), 400

        # 获取任务结果
        task_result = task_manager.get_task_result(async_task_id)
        if not task_result:
            logger.error(f"任务结果为空: {async_task_id}")
            return jsonify({
                'success': False,
                'error': '任务结果不存在'
            }), 400

        if not task_result.get('success'):
            logger.error(f"任务执行失败: {task_result}")
            return jsonify({
                'success': False,
                'error': '任务执行失败'
            }), 400

        # 获取会议纪要数据
        minutes_data = task_result.get('minutes_data')
        if not minutes_data:
            logger.error("会议纪要数据不存在")
            return jsonify({
                'success': False,
                'error': '会议纪要数据不存在'
            }), 400

        logger.info("开始生成Word文档")

        # 生成Word文档
        try:
            word_stream = ai_writer.generate_word_document(minutes_data)
            logger.info("Word文档生成成功")

            # 生成文件名
            title = minutes_data.get('title', '会议纪要')
            date = minutes_data.get('header', {}).get('date', datetime.now().strftime('%Y%m%d'))
            filename = f"{title}_{date}.docx"

            logger.info(f"准备下载Word文档: {filename}")

            # 对文件名进行URL编码以支持中文
            import urllib.parse
            encoded_filename = urllib.parse.quote(filename.encode('utf-8'))

            # 返回Word文件
            return Response(
                word_stream.getvalue(),
                mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                headers={
                    'Content-Disposition': f'attachment; filename*=UTF-8\'\'{encoded_filename}',
                    'Content-Type': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                }
            )

        except Exception as e:
            logger.error(f"生成Word文档失败: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'error': f'生成Word文档失败: {str(e)}'
            }), 500

    except Exception as e:
        logger.error(f"下载Word文档失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'下载失败: {str(e)}'
        }), 500

# ==================== 系统配置管理API ====================

@app.route('/api/config', methods=['GET'])
def get_config():
    """获取系统配置"""
    try:
        section = request.args.get('section')
        config = config_manager.get_config(section)

        # 创建配置副本并隐藏敏感信息（避免修改原始配置）
        import copy
        config = copy.deepcopy(config)

        if section == 'ai' or not section:
            if 'ai' in config:
                if config['ai'].get('ark_api_key'):
                    config['ai']['ark_api_key'] = config['ai']['ark_api_key'][:8] + '...'

        if section == 'storage' or not section:
            if 'storage' in config:
                if config['storage'].get('tos_secret_key'):
                    config['storage']['tos_secret_key'] = config['storage']['tos_secret_key'][:8] + '...'

        if section == 'asr' or not section:
            if 'asr' in config:
                if config['asr'].get('asr_access_key'):
                    config['asr']['asr_access_key'] = config['asr']['asr_access_key'][:8] + '...'

        return jsonify({
            'success': True,
            'config': config
        })

    except Exception as e:
        logger.error(f"获取配置失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'获取配置失败: {str(e)}'
        }), 500

@app.route('/api/config', methods=['POST'])
def update_config():
    """更新系统配置"""
    try:
        data = request.get_json()
        section = data.get('section')
        config = data.get('config', {})

        if not section:
            return jsonify({
                'success': False,
                'error': '缺少配置节名称'
            }), 400

        # 验证配置
        is_valid, message = config_manager.validate_config(section, config)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': message
            }), 400

        # 更新配置
        success = config_manager.update_config(section, config)
        if success:
            # 根据配置类型重新初始化相应的客户端
            reinit_result = reinitialize_clients_for_section(section)

            return jsonify({
                'success': True,
                'message': '配置更新成功',
                'reinit_result': reinit_result
            })
        else:
            return jsonify({
                'success': False,
                'error': '配置保存失败'
            }), 500

    except Exception as e:
        logger.error(f"更新配置失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'更新配置失败: {str(e)}'
        }), 500

@app.route('/api/config/reset', methods=['POST'])
def reset_config():
    """重置配置为默认值"""
    try:
        data = request.get_json()
        section = data.get('section') if data else None

        success = config_manager.reset_config(section)
        if success:
            return jsonify({
                'success': True,
                'message': '配置重置成功'
            })
        else:
            return jsonify({
                'success': False,
                'error': '配置重置失败'
            }), 500

    except Exception as e:
        logger.error(f"重置配置失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'重置配置失败: {str(e)}'
        }), 500

# ==================== 应用初始化 ====================

# 在模块加载时初始化客户端（用于Gunicorn等WSGI服务器）
# 只有在不是直接运行时才初始化，避免重复初始化
if __name__ != '__main__':
    init_clients()

# 直接创建分块上传路由
if asr_client:
    create_chunked_upload_route(app, chunked_upload_handler, asr_client, logger, storage_client)
    logger.info("分块上传路由已创建")
else:
    logger.warning("ASR客户端未初始化，分块上传路由未创建")

# ==================== 主程序入口 ====================

if __name__ == '__main__':
    # 初始化客户端
    init_clients()

    # 显示Gunicorn建议
    try:
        import gunicorn
        print("🔧 建议使用 Gunicorn 启动以支持大文件上传:")
        print("   gunicorn -w 1 -b 0.0.0.0:8080 --timeout 300 --max-requests-jitter 100 app:app")
    except ImportError:
        pass

    app.run(debug=True, host='0.0.0.0', port=8080, threaded=True)
