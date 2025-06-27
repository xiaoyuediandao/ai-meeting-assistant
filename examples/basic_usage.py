#!/usr/bin/env python3
"""
基本使用示例
"""

import os
import sys
import time

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from meetaudio import ByteDanceASRClient
from meetaudio.utils import setup_logging, format_duration


def main():
    """主函数"""
    # 设置日志
    setup_logging("INFO")
    
    # 初始化客户端
    try:
        client = ByteDanceASRClient()
        print("✅ 客户端初始化成功")
    except Exception as e:
        print(f"❌ 客户端初始化失败: {e}")
        print("请确保设置了正确的环境变量 BYTEDANCE_APP_KEY 和 BYTEDANCE_ACCESS_KEY")
        return
    
    # 示例音频URL（请替换为实际的音频文件URL）
    audio_url = "https://example.com/sample.mp3"
    
    print(f"🎵 开始识别音频: {audio_url}")
    
    try:
        # 提交任务
        task_id = client.submit_audio(
            audio_url=audio_url,
            audio_format="mp3",
            enable_itn=True,
            enable_punc=True,
            show_utterances=True
        )
        
        print(f"📝 任务已提交，ID: {task_id}")
        
        # 等待结果
        print("⏳ 等待识别完成...")
        result = client.wait_for_result(task_id, timeout=300)
        
        # 输出结果
        print("\n🎉 识别完成!")
        print(f"📄 识别文本: {result.text}")
        
        if result.audio_info:
            print(f"⏱️  音频时长: {format_duration(result.audio_info.duration)}")
        
        if result.utterances:
            print(f"\n📋 分句详情 ({len(result.utterances)} 句):")
            for i, utterance in enumerate(result.utterances, 1):
                start = format_duration(utterance.start_time)
                end = format_duration(utterance.end_time)
                print(f"  {i:2d}. [{start:>6} - {end:>6}] {utterance.text}")
        
    except Exception as e:
        print(f"❌ 识别失败: {e}")


if __name__ == "__main__":
    main()
