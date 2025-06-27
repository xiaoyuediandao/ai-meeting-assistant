# Gunicorn配置文件
# 支持大文件上传的配置

# 绑定地址和端口
bind = "0.0.0.0:8080"

# 工作进程数
workers = 1

# 工作进程类型
worker_class = "sync"

# 超时设置 - 增加超时时间以支持AI生成任务
timeout = 1200  # 20分钟超时，支持长时间AI生成任务
keepalive = 2
graceful_timeout = 1200  # 优雅关闭超时时间

# 最大请求数
max_requests = 1000
max_requests_jitter = 100

# 内存限制 (macOS不支持/dev/shm，使用默认临时目录)
# worker_tmp_dir = "/dev/shm"

# 日志配置
accesslog = "-"
errorlog = "-"
loglevel = "info"

# 预加载应用 - 禁用以避免线程问题
preload_app = False

# 最大请求大小 (100MB)
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190

# 禁用请求大小限制，让应用层处理
worker_connections = 1000

# 启用调试模式
reload = True
reload_extra_files = ["app.py", "style.css", "script.js", "index.html"]

def when_ready(server):
    print("🚀 火山引擎语音识别Web演示已启动")
    print("="*50)
    print("📱 访问地址: http://localhost:8080")
    print("💾 文件上传限制: 100MB")
    print("🔧 使用 Gunicorn WSGI 服务器")
    print("="*50)

def post_worker_init(worker):
    """Worker启动后的回调"""
    print(f"🔧 Worker {worker.pid} 已启动，初始化异步任务管理器...")

def worker_int(worker):
    print(f"Worker {worker.pid} 收到中断信号")

def on_exit(server):
    print("🛑 服务器已停止")
