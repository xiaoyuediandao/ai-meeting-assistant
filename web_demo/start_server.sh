#!/bin/bash

# 启动脚本 - 支持大文件上传的Web服务器

echo "🚀 启动火山引擎语音识别Web演示"
echo "=================================================="

# 检查环境变量
if [ -f "../.env" ]; then
    echo "📋 加载环境变量..."
    export $(cat ../.env | grep -v '^#' | xargs)
fi

# 检查必要的环境变量
if [ -z "$BYTEDANCE_APP_KEY" ] || [ -z "$BYTEDANCE_ACCESS_KEY" ]; then
    echo "❌ 缺少必要的环境变量"
    echo "💡 请确保设置了以下环境变量:"
    echo "   BYTEDANCE_APP_KEY=your_app_key"
    echo "   BYTEDANCE_ACCESS_KEY=your_access_key"
    echo "   ARK_API_KEY=your_ark_api_key"
    echo "   ARK_MODEL=your_model_endpoint"
    exit 1
fi

echo "✅ 环境变量检查通过"
echo "📱 访问地址: http://localhost:8080"
echo "💾 文件上传限制: 500MB"
echo "🔧 使用 Gunicorn WSGI 服务器"
echo "=================================================="

# 启动Gunicorn服务器
exec gunicorn -c gunicorn_config.py app:app
