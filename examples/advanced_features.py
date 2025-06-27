#!/usr/bin/env python3
"""
高级功能示例
"""

import os
import sys
import json

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from meetaudio import ByteDanceASRClient
from meetaudio.utils import setup_logging


def speaker_separation_example():
    """说话人分离示例"""
    print("🎭 说话人分离示例")
    
    client = ByteDanceASRClient()
    
    # 多人对话音频
    audio_url = "https://example.com/conversation.mp3"
    
    task_id = client.submit_audio(
        audio_url=audio_url,
        audio_format="mp3",
        enable_speaker_info=True,  # 启用说话人分离
        show_utterances=True,
        enable_punc=True
    )
    
    print(f"任务ID: {task_id}")
    result = client.wait_for_result(task_id)
    
    print(f"完整文本: {result.text}")
    
    if result.utterances:
        print("\n按说话人分组:")
        speakers = {}
        for utterance in result.utterances:
            speaker_id = utterance.speaker_id or "未知说话人"
            if speaker_id not in speakers:
                speakers[speaker_id] = []
            speakers[speaker_id].append(utterance.text)
        
        for speaker_id, texts in speakers.items():
            print(f"\n{speaker_id}:")
            for text in texts:
                print(f"  - {text}")


def dual_channel_example():
    """双声道识别示例"""
    print("\n🎧 双声道识别示例")
    
    client = ByteDanceASRClient()
    
    # 双声道音频
    audio_url = "https://example.com/stereo.wav"
    
    task_id = client.submit_audio(
        audio_url=audio_url,
        audio_format="wav",
        enable_channel_split=True,  # 启用双声道识别
        vad_segment=True,  # 使用VAD分句
        show_utterances=True
    )
    
    result = client.wait_for_result(task_id)
    
    if result.utterances:
        left_channel = []
        right_channel = []
        
        for utterance in result.utterances:
            if utterance.channel_id == 1:
                left_channel.append(utterance.text)
            elif utterance.channel_id == 2:
                right_channel.append(utterance.text)
        
        print("左声道内容:")
        for text in left_channel:
            print(f"  {text}")
        
        print("\n右声道内容:")
        for text in right_channel:
            print(f"  {text}")


def hotwords_example():
    """热词功能示例"""
    print("\n🔥 热词功能示例")
    
    client = ByteDanceASRClient()
    
    # 包含专业术语的音频
    audio_url = "https://example.com/technical.mp3"
    
    # 定义热词
    hotwords_context = json.dumps({
        "hotwords": [
            {"word": "人工智能"},
            {"word": "机器学习"},
            {"word": "深度学习"},
            {"word": "神经网络"}
        ]
    })
    
    task_id = client.submit_audio(
        audio_url=audio_url,
        audio_format="mp3",
        context=hotwords_context,  # 传入热词
        enable_itn=True,
        enable_punc=True
    )
    
    result = client.wait_for_result(task_id)
    print(f"识别结果: {result.text}")


def batch_processing_example():
    """批量处理示例"""
    print("\n📦 批量处理示例")
    
    client = ByteDanceASRClient()
    
    # 多个音频文件
    audio_files = [
        "https://example.com/audio1.mp3",
        "https://example.com/audio2.mp3", 
        "https://example.com/audio3.mp3"
    ]
    
    # 提交所有任务
    tasks = []
    for i, url in enumerate(audio_files, 1):
        print(f"提交任务 {i}/{len(audio_files)}: {url}")
        task_id = client.submit_audio(
            audio_url=url,
            audio_format="mp3",
            enable_itn=True,
            enable_punc=True
        )
        tasks.append((task_id, url))
    
    # 等待所有任务完成
    results = []
    for task_id, url in tasks:
        print(f"等待任务完成: {task_id}")
        try:
            result = client.wait_for_result(task_id, timeout=300)
            results.append({
                "url": url,
                "task_id": task_id,
                "text": result.text,
                "success": True
            })
        except Exception as e:
            results.append({
                "url": url,
                "task_id": task_id,
                "error": str(e),
                "success": False
            })
    
    # 输出结果
    print("\n批量处理结果:")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result['url']}")
        if result['success']:
            print(f"   ✅ {result['text']}")
        else:
            print(f"   ❌ {result['error']}")


def main():
    """主函数"""
    setup_logging("INFO")
    
    try:
        print("🚀 高级功能示例演示")
        print("=" * 50)
        
        # 注意：以下示例需要实际的音频URL才能运行
        # 请替换为您的音频文件URL
        
        # speaker_separation_example()
        # dual_channel_example() 
        # hotwords_example()
        # batch_processing_example()
        
        print("\n💡 提示: 请替换示例中的音频URL为实际文件后运行")
        
    except Exception as e:
        print(f"❌ 示例运行失败: {e}")


if __name__ == "__main__":
    main()
