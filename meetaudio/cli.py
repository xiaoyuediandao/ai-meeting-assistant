"""
命令行工具
"""

import click
import json
import sys
from typing import Optional

from .client import ByteDanceASRClient
from .utils import setup_logging, format_duration, get_error_message
from .exceptions import ByteDanceASRError


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='启用详细日志')
@click.option('--app-key', help='ByteDance APP Key')
@click.option('--access-key', help='ByteDance Access Key')
@click.pass_context
def cli(ctx, verbose, app_key, access_key):
    """火山引擎语音识别命令行工具"""
    ctx.ensure_object(dict)
    
    # 设置日志
    log_level = "DEBUG" if verbose else "INFO"
    setup_logging(log_level)
    
    # 初始化客户端
    try:
        ctx.obj['client'] = ByteDanceASRClient(
            app_key=app_key,
            access_key=access_key
        )
    except Exception as e:
        click.echo(f"错误: 初始化客户端失败 - {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('url')
@click.option('--format', 'audio_format', default='mp3', 
              type=click.Choice(['mp3', 'wav', 'ogg', 'raw']),
              help='音频格式')
@click.option('--enable-itn/--disable-itn', default=True, help='启用文本规范化')
@click.option('--enable-punc/--disable-punc', default=False, help='启用标点符号')
@click.option('--enable-ddc/--disable-ddc', default=False, help='启用语义顺滑')
@click.option('--enable-speaker/--disable-speaker', default=False, help='启用说话人分离')
@click.option('--show-utterances/--hide-utterances', default=False, help='显示详细分句信息')
@click.option('--wait/--no-wait', default=True, help='等待识别完成')
@click.option('--timeout', default=300, help='等待超时时间（秒）')
@click.option('--output', '-o', help='输出文件路径')
@click.pass_context
def transcribe(ctx, url, audio_format, enable_itn, enable_punc, enable_ddc, 
               enable_speaker, show_utterances, wait, timeout, output):
    """转录音频文件"""
    client = ctx.obj['client']
    
    try:
        # 提交任务
        click.echo(f"提交音频文件: {url}")
        task_id = client.submit_audio(
            audio_url=url,
            audio_format=audio_format,
            enable_itn=enable_itn,
            enable_punc=enable_punc,
            enable_ddc=enable_ddc,
            enable_speaker_info=enable_speaker,
            show_utterances=show_utterances
        )
        
        click.echo(f"任务ID: {task_id}")
        
        if wait:
            click.echo("等待识别完成...")
            with click.progressbar(length=timeout, label='处理中') as bar:
                import time
                start_time = time.time()
                
                while time.time() - start_time < timeout:
                    status = client.get_result(task_id)
                    
                    if status.is_success:
                        bar.update(timeout)
                        break
                    elif status.is_failed:
                        click.echo(f"\n识别失败: {status.message}", err=True)
                        sys.exit(1)
                    
                    elapsed = int(time.time() - start_time)
                    bar.update(min(elapsed, timeout))
                    time.sleep(2)
                else:
                    click.echo(f"\n超时: 任务在{timeout}秒内未完成", err=True)
                    sys.exit(1)
            
            # 输出结果
            result = status.result
            if result:
                click.echo(f"\n识别完成!")
                if result.audio_info:
                    click.echo(f"音频时长: {format_duration(result.audio_info.duration)}")
                
                click.echo(f"\n识别结果:")
                click.echo(result.text)
                
                if show_utterances and result.utterances:
                    click.echo(f"\n详细分句信息:")
                    for i, utterance in enumerate(result.utterances, 1):
                        start_time = format_duration(utterance.start_time)
                        end_time = format_duration(utterance.end_time)
                        click.echo(f"  {i}. [{start_time} - {end_time}] {utterance.text}")
                
                # 保存到文件
                if output:
                    output_data = {
                        "task_id": task_id,
                        "text": result.text,
                        "audio_info": result.audio_info.dict() if result.audio_info else None,
                        "utterances": [u.dict() for u in result.utterances] if result.utterances else None
                    }
                    
                    with open(output, 'w', encoding='utf-8') as f:
                        json.dump(output_data, f, ensure_ascii=False, indent=2)
                    click.echo(f"\n结果已保存到: {output}")
        else:
            click.echo("任务已提交，使用以下命令查询结果:")
            click.echo(f"python -m meetaudio.cli query --task-id {task_id}")
            
    except ByteDanceASRError as e:
        click.echo(f"错误: {e.message}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"未知错误: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--task-id', required=True, help='任务ID')
@click.option('--output', '-o', help='输出文件路径')
@click.pass_context
def query(ctx, task_id, output):
    """查询识别结果"""
    client = ctx.obj['client']
    
    try:
        status = client.get_result(task_id)
        
        click.echo(f"任务ID: {task_id}")
        click.echo(f"状态: {get_error_message(status.status_code)}")
        
        if status.is_success and status.result:
            result = status.result
            click.echo(f"\n识别结果:")
            click.echo(result.text)
            
            if result.audio_info:
                click.echo(f"\n音频时长: {format_duration(result.audio_info.duration)}")
            
            if result.utterances:
                click.echo(f"\n分句数量: {len(result.utterances)}")
            
            # 保存到文件
            if output:
                output_data = {
                    "task_id": task_id,
                    "text": result.text,
                    "audio_info": result.audio_info.dict() if result.audio_info else None,
                    "utterances": [u.dict() for u in result.utterances] if result.utterances else None
                }
                
                with open(output, 'w', encoding='utf-8') as f:
                    json.dump(output_data, f, ensure_ascii=False, indent=2)
                click.echo(f"\n结果已保存到: {output}")
                
        elif status.is_processing:
            click.echo("任务仍在处理中，请稍后再试")
        else:
            click.echo(f"任务失败: {status.message}", err=True)
            sys.exit(1)
            
    except ByteDanceASRError as e:
        click.echo(f"错误: {e.message}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"未知错误: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    cli()
