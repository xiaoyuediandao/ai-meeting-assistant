#!/usr/bin/env python3
"""
启动Web服务器脚本
支持大文件上传的Web服务器配置
"""

import os
import sys
from werkzeug.serving import WSGIRequestHandler

# 自定义请求处理器，增加文件大小限制
class CustomRequestHandler(WSGIRequestHandler):
    def setup(self):
        super().setup()
        # 设置TCP选项，避免网络错误
        try:
            if hasattr(self.rfile, '_sock') and self.rfile._sock:
                import socket
                self.rfile._sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        except (AttributeError, OSError):
            # 如果设置失败，忽略错误继续运行
            pass

def run_server():
    """启动Web服务器"""
    from app import app
    from config_manager import config_manager

    print("🚀 启动火山引擎语音识别Web演示")
    print("="*50)

    # 应用系统配置
    print("🔧 应用系统配置...")
    config_manager.apply_env_config()
    print("✅ 系统配置应用成功")

    print("📱 访问地址: http://localhost:8080")
    print("💾 文件上传限制: 100MB")
    print("🔧 使用自定义服务器配置支持大文件上传")
    print("\n按 Ctrl+C 停止服务")
    print("="*50)
    
    # 使用自定义配置启动服务器
    app.run(
        debug=True,
        host='0.0.0.0',
        port=8080,
        threaded=True,
        request_handler=CustomRequestHandler,
        use_reloader=True,
        use_debugger=True
    )

if __name__ == '__main__':
    run_server()
